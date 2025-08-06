# niin.py
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

def scrape_naiin_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-info-name"))
        )
    except TimeoutException:
        print(f"[*] [naiin] Timeout ขณะรอโหลดหน้ารายละเอียด: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Title
    title_tag = soup.find("h1", class_="title-topic")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    author_tag = soup.find("div", class_="inline-block link-book-detail")
    if author_tag:
        author = normalize_text(author_tag.text)

    # Publisher
    publisher_tag = driver.find_elements(By.XPATH,"/html/body/div/div[2]/div[1]/div/div/div[3]/div[2]/div[1]/div[1]/p[2]/a")
    if publisher_tag:
        publisher = normalize_text(publisher_tag.text)

    # Price
    price_tag = soup.find("p", class_="price")
    if price_tag:
        price_span = price_tag.find("p", class_="price")
        if price_span:
            price_text = normalize_text(price_span.text)
            match = re.search(r'[\d,.]+', price_text)
            if match:
                price = int(float(match.group(0).replace(",", "")))
        
    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "url": book_url,
        "source": "naiin"
    }

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    base_url = ["https://www.naiin.com/category?category_1_code=13&product_type_id=1","https://www.naiin.com/category?category_1_code=2&product_type_id=1&categoryLv2Code=8","https://www.naiin.com/category?categoryLv2Code=95&category_1_code=3&product_type_id=1","https://www.naiin.com/category?category_1_code=28&product_type_id=1","https://www.naiin.com/category?category_1_code=33&product_type_id=1","https://www.naiin.com/category?category_1_code=33&product_type_id=1","https://www.naiin.com/category?category_1_code=14&product_type_id=1","https://www.naiin.com/category?category_1_code=2&product_type_id=1&categoryLv2Code=134","https://www.naiin.com/category?category_1_code=15&product_type_id=1","https://www.naiin.com/category?category_1_code=5&product_type_id=1"]
    
    for cat_url in base_url:
        for p in range(1, max_pages + 1):
            page_url = f"{cat_url}&page={p}"
            print(f"[*] [naiin] จะโหลด: {page_url}")

            try:
                driver.get(page_url)
            except TimeoutException:
                print(f"[ERROR] ไม่สามารถโหลด URL นี้ได้ → {page_url} : {e}")
                break

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH,
                        "/html/body/div[1]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[2]/div/div[1]/div[3]/p[1]/a"
                    ))
                )
            except TimeoutException:
                print(f"[*] [naiin] ไม่มีสินค้าในหน้า {p}, จบหมวดนี้")
                break
        
            links = driver.find_elements(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[2]/div/div[1]/div[3]/p[1]/a")
            print(f"เจอ {len(links)} ลิงก์")
            for link in links:
                href = link.get_attribute("href")
                urls.add(href)

    return list(urls)

def scrape_naiin_all_pages(driver, conn, max_pages=999):
    all_products = []
    
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_naiin_detail_page(driver, url)
        if book_data:
            insert_book(conn, book_data)

    return 