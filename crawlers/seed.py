import time, re, json
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book
from image_service import upload_book_cover

def normalize_text(txt):
    if not txt: return ""
    return ' '.join(txt.replace('"', '').strip().split())

def scrape_seed_detail_page(driver, conn, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "__next")))
    except TimeoutException:
        print(f"[*] [se-ed] Timeout: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    try:
        json_tag = soup.find('script', id='__NEXT_DATA__')
        if json_tag:
            js_data = json.loads(json_tag.string)
            product_info = js_data['props']['pageProps']['meta']['physicalProduct']
            extended_info = js_data['props']['pageProps'].get('extendedOrderProduct', {})

            isbn = product_info['variants'][0].get('sku', 'Unknown')
            title = product_info.get('name', 'Unknown')

            variant = extended_info.get('physical', {}).get('variants', [{}])[0]
            price_raw = variant.get('priceAfterDiscount') or variant.get('price', 0)
            price = int(float(price_raw) / 1000000)

        all_links = soup.find_all("a", href=True)
        for link in all_links:
            href = link['href']
            if "search?filter.keyword=" in href:
                text = link.get_text().strip()
                if any(x in text for x in ["สนพ.", "สำนักพิมพ์"]):
                    publisher = text
                elif text not in ["หนังสือ", "E-Book", "หน้าแรก", title]:
                    author = text

        img_tag = soup.find("meta", attrs={"property": "og:image"})
        if img_tag:
            raw_img_url = img_tag.get("content")

    except Exception as e:
        print(f"[!] Error parsing data on {book_url}: {e}")
        return None
    
    final_image_url = ""
    if raw_img_url:
        final_image_url = upload_book_cover(raw_img_url, isbn)
        
    book_data = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "naiin"
    }

    insert_book(conn, book_data) 
    
    return book_data

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    # URL สำหรับหนังสือเล่ม (Physical Books)
    base_url = "https://www.se-ed.com/book-cat.book?filter.productTypes=PRODUCT_TYPE_BOOK_PHYSICAL&page="
    
    for p in range(1, max_pages + 1):
        print(f"[*] [se-ed] กำลังรวบรวม URL จากหน้า {p}...")
        driver.get(f"{base_url}{p}")
        
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/physical/']"))
            )
            
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/physical/']")
            page_urls = [l.get_attribute("href") for l in links if "/physical/" in l.get_attribute("href")]
            
            if not page_urls:
                break
                
            for url in page_urls:
                urls.add(url)
                
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