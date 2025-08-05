# niin.py
import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
    title_tag = soup.find("h1", class_="product-info-name")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    author = "Unknown"
    author_tag = soup.find("div", class_="product-authors")
    if author_tag:
        author = normalize_text(author_tag.text)

    # Publisher
    publisher = "Unknown"
    publisher_tag = soup.find("div", class_="product-publisher")
    if publisher_tag:
        publisher = normalize_text(publisher_tag.text)

    # Price
    price = 0
    price_tag = soup.find("span", class_="special-price")
    if price_tag:
        price_span = price_tag.find("span", class_="price")
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

def get_all_book_urls(driver, max_pages=10):
    urls = set()
    base_url = "https://www.naiin.com/search?q=book&page="
    
    for p in range(1, max_pages + 1):
        print(f"[*] [naiin] กำลังรวบรวม URL จากหน้า {p}...")
        driver.get(f"{base_url}{p}")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-card a.product-item-link"))
            )
        except TimeoutException:
            print(f"[*] [naiin] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, "div.product-card a.product-item-link")
        for link in links:
            href = link.get_attribute("href")
            if href and "product" in href:
                urls.add(href)
    return list(urls)

def scrape_naiin_all_pages(driver, max_pages=10):
    all_products = []
    
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_naiin_detail_page(driver, url)
        if book_data:
            all_products.append(book_data)

    return all_products