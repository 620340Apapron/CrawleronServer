import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book
from image_service import upload_book_cover

def normalize_text(txt):
    if not txt: return ""
    # ตัดคำว่า "Books | ร้านหนังสือนายอินทร์" ออกจากชื่อเรื่องถ้ามี
    txt = txt.replace("Books | ร้านหนังสือนายอินทร์", "")
    return ' '.join(txt.replace('"', '').strip().split())

def scrape_naiin_detail_page(driver, conn, book_url): # เพิ่ม conn เข้ามา
    driver.get(book_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//meta[@property='book:isbn']")))
    except:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    isbn_tag = soup.find("meta", attrs={"property": "book:isbn"})
    isbn = isbn_tag.get("content") if isbn_tag else "Unknown"

    title_tag = soup.find("meta", attrs={"property": "og:title"})
    title = normalize_text(title_tag.get("content")) if title_tag else "Unknown"

    price = 0
    price_tag = soup.find("meta", attrs={"property": "og:product:sale_price:amount"})
    if not price_tag: price_tag = soup.find("meta", attrs={"property": "og:product:price:amount"})
    if price_tag: price = int(float(price_tag.get("content")))

    author, publisher = "Unknown", "Unknown"
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        desc_text = desc_tag.get("content")
        author_match = re.search(r"ผู้เขียน\s+(.*?)\s+สำนักพิมพ์", desc_text)
        if author_match: author = author_match.group(1).strip()
        pub_match = re.search(r"สำนักพิมพ์\s+(.*)", desc_text)
        if pub_match: publisher = pub_match.group(1).strip()

    image_tag = soup.find("meta", attrs={"property": "og:image"})
    final_image_url = ""
    if image_tag:
        raw_img_url = image_tag.get("content")
        final_image_url = upload_book_cover(raw_img_url, isbn)
    else:
        print(f"⚠️ [naiin] ไม่พบรูปภาพสำหรับ ISBN: {isbn}")

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
    if conn and conn.is_connected():
        insert_book(conn, book_data) 
    else:
        print("❌ [naiin] การเชื่อมต่อฐานข้อมูลหลุด ไม่สามารถบันทึกได้")
    
    return book_data

def scrape_naiin_all_pages(driver, conn, max_pages=10):
    all_urls = get_all_book_urls(driver, max_pages)
    for i, url in enumerate(all_urls):
        print(f"--- [naiin] เล่มที่ {i+1}/{len(all_urls)} ---")
        scrape_naiin_detail_page(driver, conn, url)

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    
    for code in range(1, 36): 
        base_url = f"https://www.naiin.com/category?category_1_code={code}&product_type_id=1"
        print(f"\n[*] [naiin] กำลังเริ่มเก็บหมวดหมู่รหัส: {code}")

        for p in range(1, max_pages + 1):
            target_url = f"{base_url}&page={p}"
            driver.get(target_url)

            time.sleep(2) 

            links = driver.find_elements(By.CSS_SELECTOR, "a.item-name")
            
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