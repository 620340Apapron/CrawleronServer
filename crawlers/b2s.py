# b2s.py
import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book

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
    
    # Title
    title_tag = soup.find("div", class_="pdp-productDetail__desc")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    author_tag = soup.find("div", class_="author-name")
    if author_tag:
        author = normalize_text(author_tag.text)

    # Publisher
    publisher_tag = soup.find("div", class_="publisher-name")
    if publisher_tag:
        publisher = normalize_text(publisher_tag.text)

    # Price
    price_tag = soup.find("div", class_="product-price")
    if price_tag:
        price_text = normalize_text(price_tag.text)
        match = re.search(r'[\d,.]+', price_text)
        if match:
            price = int(float(match.group(0).replace(",", "")))
    
    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "url": book_url,
        "source": "b2s"
    }

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    # เปลี่ยน URL หน้ารวมสินค้า
    base_url = "https://www.central.co.th/th/b2s/home-lifestyle/books-movies-music/books"
    
    for p in range(1, max_pages + 1):
        print(f"[*] [b2s] กำลังรวบรวม URL จากหน้า {p}...")
        driver.get(f"{base_url}{p}")
        try:
            WebDriverWait(driver, 15).until(
                # อัปเดต CSS selector ให้ตรงกับโครงสร้างปัจจุบัน
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-card-wrap a"))
            )
        except TimeoutException:
            print(f"[*] [b2s] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, "div.product-card-wrap a")
        for link in links:
            href = link.get_attribute("href")
            if href and "product" in href:
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