import time, re, json
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book

def normalize_text(txt):
    if not txt: return ""
    return ' '.join(txt.replace('"', '').strip().split())

def scrape_seed_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        # รอให้ id="__next" โหลด (ซึ่งครอบคลุมทั้งหน้า)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "__next")))
    except TimeoutException:
        print(f"[*] [se-ed] Timeout: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # --- ดึงข้อมูลจากก้อน JSON (__NEXT_DATA__) เพื่อความแม่นยำสูงสุด ---
    try:
        json_tag = soup.find('script', id='__NEXT_DATA__')
        if not json_tag:
            return None
        
        js_data = json.loads(json_tag.string)
        product_info = js_data['props']['pageProps']['meta']['physicalProduct']
        extended_info = js_data['props']['pageProps'].get('extendedOrderProduct', {})

        # 1. ISBN
        isbn = product_info['variants'][0].get('sku', 'Unknown')
        
        # 2. Title
        title = product_info.get('name', 'Unknown')

        # 3. Price (SE-ED เก็บเป็นเลขจำนวนเต็มหลักร้อยล้าน ต้องหาร 1,000,000)
        # ลองดึงจาก priceAfterDiscount ถ้าไม่มีให้ดึงจาก price ปกติ
        price_raw = 0
        variant = extended_info.get('physical', {}).get('variants', [{}])[0]
        price_raw = variant.get('priceAfterDiscount') or variant.get('price', 0)
        price = int(float(price_raw) / 1000000)

        # 4. Author & Publisher (ส่วนนี้ใน JSON ดึงยาก ผมจึงใช้วิธีหาจากลิงก์ในหน้าเว็บแทน)
        # หาจากลิงก์ที่มี keyword การค้นหาชื่อผู้แต่ง/สำนักพิมพ์
        author = "Unknown"
        publisher = "Unknown"
        
        # ค้นหาลิงก์ที่มี URL pattern ของการค้นหาใน SE-ED
        all_links = soup.find_all("a", href=True)
        for link in all_links:
            href = link['href']
            # ปกติชื่อผู้แต่งจะอยู่ในหน้าที่มี keyword search
            if "search?filter.keyword=" in href:
                text = link.get_text().strip()
                # ตรรกะง่ายๆ: ถ้าเจอคำว่า 'สนพ.' หรืออยู่ในตำแหน่งที่น่าจะเป็นสำนักพิมพ์
                if any(x in text for x in ["สนพ.", "สำนักพิมพ์"]):
                    publisher = text
                else:
                    # ถ้าไม่ใช่สำนักพิมพ์ และไม่ใช่คำทั่วไป ให้ถือว่าเป็นผู้แต่ง
                    if text not in ["หนังสือ", "E-Book", "หน้าแรก"]:
                        author = text

    except Exception as e:
        print(f"[!] Error parsing JSON on {book_url}: {e}")
        return None
        
    return {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "image_url": image_url,
        "url": book_url,
        "source": "se-ed"
    }

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    # URL สำหรับหนังสือเล่ม (Physical Books)
    base_url = "https://www.se-ed.com/book-cat.book?filter.productTypes=PRODUCT_TYPE_BOOK_PHYSICAL&page="
    
    for p in range(1, max_pages + 1):
        print(f"[*] [se-ed] กำลังรวบรวม URL จากหน้า {p}...")
        driver.get(f"{base_url}{p}")
        
        try:
            # รอให้ลิงก์สินค้าโหลดขึ้นมา (ใช้ Selector ที่เจาะจงที่ตัวสินค้า)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/physical/']"))
            )
            
            # ดึงทุกลิงก์ที่มีคำว่า /physical/
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/physical/']")
            page_urls = [l.get_attribute("href") for l in links if "/physical/" in l.get_attribute("href")]
            
            if not page_urls:
                break
                
            for url in page_urls:
                urls.add(url)
                
            # เลื่อนหน้าจอลงเพื่อป้องกัน lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
        except TimeoutException:
            print(f"[*] [se-ed] หน้า {p} โหลดไม่สำเร็จหรือไม่มีสินค้าเพิ่ม")
            break

    return list(urls)

def scrape_seed_all_pages(driver, conn, max_pages=999):
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่พบ URL สินค้า")
        return

    for i, url in enumerate(all_urls):
        print(f"--- [se-ed] เล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_seed_detail_page(driver, url)
        if book_data:
            print(f"พบ: {book_data['title']} | ISBN: {book_data['isbn']} | ราคา: {book_data['price']}")
            insert_book(conn, book_data)