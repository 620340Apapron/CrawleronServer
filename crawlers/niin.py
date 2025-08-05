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

def get_all_book_urls(driver, max_pages=10):
    urls = set()
    base_url = "https://www.naiin.com/product/view-all?product_type_id=1&product_category=list-book-category&page={}"
    for p in range(1, max_pages + 1):
        driver.get(base_url.format(p))
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product_items_list a.link_to_product"))
            )
        except TimeoutException:
            print(f"[niin] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, ".product_items_list a.link_to_product")
        for link in links:
            href = link.get_attribute("href")
            if href:
                urls.add(href)
    return list(urls)

def scrape_one(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-detail-name"))
        )
    except TimeoutException:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Title
    title_tag = soup.find("h1", class_="name")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    author_tag = soup.find("p", class_="writer")
    author = normalize_text(author_tag.text) if author_tag else "Unknown"
    
    # Publisher
    publisher_tag = soup.find("p", class_="publisher-wrapper")
    publisher = normalize_text(publisher_tag.text) if publisher_tag else "Unknown"

    # Price
    price = 0
    price_tag = soup.find("p", class_="price")
    if price_tag:
        match = re.search(r'[\d,.]+', price_tag.text)
        if match:
            price_str = match.group(0).replace(",", "")
            price = int(float(price_str)) if price_str.replace('.', '', 1).isdigit() else 0
    
    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "url": book_url,
        "source": "niin"
    }

def scrape_niin_all_pages(driver, max_pages=10):
    all_urls = get_all_book_urls(driver, max_pages)
    results = []
    for u in all_urls:
        data = scrape_one(driver, u)
        if data:
            results.append(data)
        time.sleep(0.5)
    print(f"[niin] collected {len(results)} books")
    return results