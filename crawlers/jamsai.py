# jamsai.py
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

def scrape_jamsai_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-title"))
        )
    except TimeoutException:
        print(f"[*] [jamsai] Timeout ขณะรอโหลดหน้ารายละเอียด: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Title
    title_tag = soup.find("h3", class_="tp-product-details-title mt-1 mb-1")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    author = "Unknown"
    author_tag = soup.find("h3", class_="tp-product-details-variation-title mb-4")
    if author_tag:
        author_span = author_tag.find("span", class_="authors-name")
        if author_span:
            author = normalize_text(author_span.text)

    # Publisher
    publisher = "Jamsai Publisher"
    publisher_tag = soup.find("div", class_="product-publisher")
    if publisher_tag:
        publisher_span = publisher_tag.find("span", class_="publisher-name")
        if publisher_span:
            publisher = normalize_text(publisher_span.text)

    # Price
    price = 0
    price_tag = soup.find("span", class_="tp-product-details-price new-price")
    if price_tag:
        price_span = price_tag.find("span", class_="price-value")
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
        "source": "jamsai"
    }

def get_all_book_urls(driver, max_pages=10):
    urls = set()
    # เปลี่ยน URL หน้ารวมสินค้า
    base_url = "https://www.jamsai.com/shop"
    
    for p in range(1, max_pages + 1):
        print(f"[*] [jamsai] กำลังรวบรวม URL จากหน้า {p}...")
        driver.get(f"{base_url}{p}")
        try:
            WebDriverWait(driver, 15).until(
                # อัปเดต CSS selector ให้ตรงกับโครงสร้างปัจจุบัน
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-list a.product-image"))
            )
        except TimeoutException:
            print(f"[*] [jamsai] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, "div.product-list a.product-image")
        for link in links:
            href = link.get_attribute("href")
            if href and "product" in href:
                urls.add(href)
    return list(urls)

def scrape_jamsai_all_pages(driver, max_pages=10):
    all_products = []
    
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_jamsai_detail_page(driver, url)
        if book_data:
            all_products.append(book_data)

    return all_products