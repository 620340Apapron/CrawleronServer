import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book

def normalize_text(txt):
    if not txt: return ""
    # ตัดคำว่า "Books | ร้านหนังสือนายอินทร์" ออกจากชื่อเรื่องถ้ามี
    txt = txt.replace("Books | ร้านหนังสือนายอินทร์", "")
    return ' '.join(txt.replace('"', '').strip().split())

def scrape_naiin_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        # รอแค่ให้หน้าเว็บโหลดเสร็จ
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//meta[@property='book:isbn']")))
    except:
        print(f"[*] [naiin] ไม่สามารถโหลดหน้าหรือหา ISBN ไม่เจอ: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # ISBN
    isbn_tag = soup.find("meta", attrs={"property": "book:isbn"})
    isbn = isbn_tag.get("content") if isbn_tag else "Unknown"

    # Title 
    title_tag = soup.find("meta", attrs={"property": "og:title"})
    title = normalize_text(title_tag.get("content")) if title_tag else "Unknown"

    # Price
    price = 0
    price_tag = soup.find("meta", attrs={"property": "og:product:sale_price:amount"})
    if not price_tag: # ถ้าไม่มีราคาลด ให้หาราคาเต็ม
        price_tag = soup.find("meta", attrs={"property": "og:product:price:amount"})
    
    if price_tag:
        price = int(float(price_tag.get("content")))

    # Author & Publisher
    author = "Unknown"
    publisher = "Unknown"
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        desc_text = desc_tag.get("content")
        # ใช้ Regex ดึงคำที่อยู่หลัง "ผู้เขียน" และก่อน "สำนักพิมพ์"
        author_match = re.search(r"ผู้เขียน\s+(.*?)\s+สำนักพิมพ์", desc_text)
        if author_match:
            author = author_match.group(1).strip()
        
        # ดึงคำที่อยู่หลัง "สำนักพิมพ์"
        pub_match = re.search(r"สำนักพิมพ์\s+(.*)", desc_text)
        if pub_match:
            publisher = pub_match.group(1).strip()

    return {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "url": book_url,
        "source": "naiin"
    }

def get_all_book_urls(driver, max_pages=5):
    urls = set()
    
    for code in range(1, 36): 
        base_url = f"https://www.naiin.com/category?category_1_code={code}&product_type_id=1"
        print(f"\n[*] [naiin] กำลังเริ่มเก็บหมวดหมู่รหัส: {code}")

        for p in range(1, max_pages + 1):
            # นำ base_url ที่สร้างมาต่อกับ &page={p}
            target_url = f"{base_url}&page={p}"
            driver.get(target_url)
            
            # หน่วงเวลา
            time.sleep(2) 
            
            # หาลิงก์สินค้า
            links = driver.find_elements(By.CSS_SELECTOR, "a.item-name")
            
            # ถ้าหน้าจอนี้ไม่มีสินค้า (links ว่างเปล่า) ให้ break ออกจากลูปหน้า (ไปหมวดถัดไป)
            if not links:
                print(f"[*] [naiin] รหัสหมวด {code} หมดที่หน้า {p-1}")
                break
            
            count_before = len(urls)
            for link in links:
                href = link.get_attribute("href")
                if href:
                    urls.add(href)
            
            print(f"[*] [naiin] หมวด {code} หน้า {p} - เจอใหม่ {len(urls) - count_before} ลิงก์ (รวมสะสม {len(urls)})")
            
    return list(urls)

def scrape_naiin_all_pages(driver, conn, max_pages=5):
    all_urls = get_all_book_urls(driver, max_pages)
    for i, url in enumerate(all_urls):
        print(f"--- [naiin] เล่มที่ {i+1}/{len(all_urls)} ---")
        book_data = scrape_naiin_detail_page(driver, url)
        if book_data:
            print(f"ได้ข้อมูล: {book_data['title']} | ISBN: {book_data['isbn']} | ราคา: {book_data['price']}")
            insert_book(conn, book_data)