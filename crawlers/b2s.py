# b2s.py
import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book
from image_service import upload_book_cover

def normalize_text(txt):
    if not txt:
        return ""
    return ' '.join(txt.replace('"', '').strip().split())

def scrape_b2s_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product_title"))
        )
    except TimeoutException:
        print(f"[*] [b2s] Timeout ขณะรอโหลดหน้ารายละเอียด: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    isbn_tag = soup.find("meta", attrs={"property": "book:isbn"})
    isbn = isbn_tag.get("content") if isbn_tag else "Unknown"

    # Title
    title_tag = soup.find("h1", class_="title mb-2 fw-bold fs-24")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    author_tag = soup.find("span", class_="author-name")
    if author_tag:
        author = normalize_text(author_tag.text)

    # Publisher
    publisher_tag = soup.find("a", class_="mr-3 fw-bold")
    if publisher_tag:
        publisher = normalize_text(publisher_tag.text)

    # Price
    price_tag = soup.find("label", class_="price")
    if price_tag:
        price_text = normalize_text(price_tag.text)
        match = re.search(r'[\d,.]+', price_text)
        if match:
            price = int(float(match.group(0).replace(",", "")))

    image_tag = soup.find("meta", attrs={"property": "og:image"})  
    image_url = image_tag.get("content")
    final_image_url = upload_book_cover(image_url, isbn)

    return {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "b2s"
    }

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    # เปลี่ยน URL หน้ารวมสินค้า
    base_url = ["https://shorturl.at/xMaPH","https://shorturl.at/nwkp9","https://shorturl.at/oCfXO","https://shorturl.at/Bqqpu","https://shorturl.asia/BEAvO","https://shorturl.asia/AUefZ","https://shorturl.asia/5xIER"]
    
    for cat_url in base_url:
        for p in range(1, max_pages + 1):
            page_url = f"{cat_url}&page={p}"
            print(f"[*] [b2s] จะโหลด: {page_url}")
        
            try:
                driver.get(page_url)
            except TimeoutException:
                print(f"[ERROR] ไม่สามารถโหลด URL นี้ได้ → {page_url} : {e}")
                break

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH,
                        "/html/body/div[1]/div/div/div[3]/div/div/div[2]/div[2]/div[2]/div[3]/div/div[1]/div/div[1]/div[1]/div[1]/a"
                    ))
                )
            except TimeoutException:
                print(f"[*] [b2s] ไม่มีสินค้าในหน้า {p}, จบหมวดนี้")
                break
        
            links = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div/div[3]/div/div/div[2]/div[2]/div[2]/div[3]/div/div[1]/div/div[1]/div[1]/div[1]/a")
            print(f"เจอ {len(links)} ลิงก์")
            for link in links:
                href = link.get_attribute("href")
                urls.add(href)
    return list(urls)

def scrape_b2s_all_pages(driver, conn,  max_pages=999):
    all_products = []
    
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_b2s_detail_page(driver, url)
        if book_data:
            insert_book(conn, book_data)

    return 