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

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    base_url = "https://amarinbooks.com/shop/?orderby=date"
    for p in range(1, max_pages + 1):
        driver.get(base_url.format(p))
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.woocommerce-LoopProduct-link"))
            )
        except TimeoutException:
            print(f"[amarin] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, "a.woocommerce-LoopProduct-link")
        for link in links:
            href = link.get_attribute("href")
            if href:
                urls.add(href)
    return list(urls)

def scrape_one(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product_title"))
        )
    except TimeoutException:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    title_tag = soup.find(By.CSS_SELECTOR,"h1.product_title")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    author_tag = soup.find(By.CSS_SELECTOR,"div.product-author > span")
    author = normalize_text(author_tag.text) if author_tag else "Unknown"

    publisher_tag = soup.find(By.CSS_SELECTOR,"span.product-publisher a")
    publisher = normalize_text(publisher_tag.text) if publisher_tag else "Unknown"
    
    p_tag = soup.find(By.CSS_SELECTOR,"div.product-page-price > p.price > span.woocommerce-Price-amount")
    if p_tag:
        m = re.search(r'[\d,.]+', p_tag.text)
        if m:
            price = m.group(0).replace(",", "")
    
    try:
        price = int(float(price))
    except (ValueError, TypeError):
        price = 0

    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "url": book_url,
        "source": "amarin"
    }

def scrape_amarin_all_pages(driver, max_pages=999):
    all_urls = get_all_book_urls(driver, max_pages)
    results = []
    for u in all_urls:
        data = scrape_one(driver, u)
        if data:
            results.append(data)
        time.sleep(0.5)
    print(f"[amarin] collected {len(results)} books")
    return results