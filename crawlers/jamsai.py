# crawlers/jamsai.py
import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def normalize_text(txt):
    if not txt:
        return ""
    return ' '.join(txt.replace('"','').strip().split())

def get_all_book_urls(driver, max_pages=10):
    urls = set()
    base = "https://www.jamsai.com/shop/products/all?page={}"
    for p in range(1, max_pages+1):
        driver.get(base.format(p))
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".col-xxl-3 col-xl-3 col-lg-4 col-md-4 col-sm-6 col-6"))
            )
        except TimeoutException:
            break
        for a in driver.find_elements(By.CSS_SELECTOR, ".col-xxl-3 col-xl-3 col-lg-4 col-md-4 col-sm-6 col-6"):
            href = a.get_attribute("href")
            if href:
                urls.add(href)
    return list(urls)

def scrape_one(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            # แก้ไข CSS Selector ให้ถูกต้อง
            EC.presence_of_element_located((By.CSS_SELECTOR, ".tp-product-title-2.truncate-text-line-2"))
        )
    except TimeoutException:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # title
    # แก้ไข CSS Selector ให้ถูกต้อง
    t = soup.select_one("h3.tp-product-title-2.truncate-text-line-2")
    title = normalize_text(t.text) if t else "Unknown"
    
    # author
    # แก้ไข CSS Selector ให้ถูกต้อง
    auth_div = soup.find("div", class_="tp-product-tag-2 truncate-text-line-1")
    author = normalize_text(auth_div.text.replace("ผู้เขียน/ผู้แปล :","")) if auth_div else "Unknown"
    
    # price
    price = "0"
    p_tag = soup.find("span", class_="tp-product-price-2 new-price")
    if p_tag:
        m = re.search(r'[\d,.]+', p_tag.text)
        if m:
            price = m.group(0).replace(",", "")
    
    return {
        "title":     title,
        "author":    author,
        "publisher": "Jamsai Publisher",
        "price":     int(float(price)),
        "url":       book_url,
        "source":    "jamsai"
    }

def scrape_jamsai_all_pages(driver, max_pages=10):
    all_urls = get_all_book_urls(driver, max_pages)
    results = []
    for u in all_urls:
        data = scrape_one(driver, u)
        if data:
            results.append(data)
        time.sleep(0.5)   # be gentle on their server
    print(f"[jamsai] collected {len(results)} books")
    return results
