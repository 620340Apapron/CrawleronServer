# seed.py
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

def scrape_seed_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.text-book-name"))
        )
    except TimeoutException:
        print(f"[*] [se-ed] Timeout ขณะรอโหลดหน้ารายละเอียด: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Title
    title_tag = soup.find("h1", class_="text-book-name")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    author = "Unknown"
    author_tag = soup.find("span", class_="author-name")
    if author_tag:
        author = normalize_text(author_tag.text)

    # Publisher
    publisher = "Unknown"
    publisher_tag = soup.find("a", class_="publisher-link")
    if publisher_tag:
        publisher = normalize_text(publisher_tag.text)

    # Price
    price = 0
    price_tag = soup.find("span", class_="product-price")
    if price_tag:
        price_text = normalize_text(price_tag.text)
        match = re.search(r'[\d,.]+', price_text)
        if match:
            price = int(float(match.group(0).replace(",", "")))

    # Category
    category = "General"
    breadcrumb_tags = soup.select("ul.breadcrumb a")
    if len(breadcrumb_tags) > 1:
        category = normalize_text(breadcrumb_tags[-1].text)
        
    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "category": category,
        "url": book_url,
        "source": "se-ed"
    }

def get_all_book_urls(driver, max_pages=10):
    urls = set()
    base_url = "https://se-ed.com/book-cat.book?filter.productTypes=PRODUCT_TYPE_BOOK_PHYSICAL&page="
    
    for p in range(1, max_pages + 1):
        print(f"[*] [se-ed] กำลังรวบรวม URL จากหน้า {p}...")
        driver.get(f"{base_url}{p}")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-list-card a.product-list-image"))
            )
        except TimeoutException:
            print(f"[*] [se-ed] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, "div.product-list-card a.product-list-image")
        for link in links:
            href = link.get_attribute("href")
            if href and "product" in href:
                urls.add(href)
    return list(urls)

def scrape_seed_all_pages(driver, max_pages=10):
    all_products = []
    
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_seed_detail_page(driver, url)
        if book_data:
            all_products.append(book_data)

    return all_products