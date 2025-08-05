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

def get_all_book_urls(driver, max_pages):
    urls = set()
    base = "https://www.jamsai.com/shop"
    for p in range(1, max_pages + 1):
        driver.get(base.format(p))
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".col-xxl-3 col-xl-3 col-lg-4 col-md-4 col-sm-6 col-6 div"))
            )
        except TimeoutException:
            print(f"[jamsai] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, ".tp-product-title-2 truncate-text-line-2 h3")
        for link in links:
            href = link.get_attribute("href")
            if href:
                urls.add(href)
    return list(urls)

def scrape_one(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h3.tp-product-title-2 truncate-text-line-2"))
        )
    except TimeoutException:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    t = soup.select_one("h3.tp-product-details-title mt-1 mb-1")
    title = normalize_text(t.text) if t else "Unknown"

    auth_div = soup.find("h3", class_="tp-product-details-variation-title mb-4")
    author = normalize_text(auth_div.text.replace("ผู้เขียน/ผู้แปล :","")) if auth_div else "Unknown"

    p_tag = soup.find("span", class_="tp-product-details-price new-price")
    if p_tag:
        m = re.search(r'[\d,.]+', p_tag.text)
        if m:
            price = m.group(0).replace(",", "")
    else:
        p_tag = soup.find("span", class_="tp-product-details-price new-price")
        if p_tag:
            m = re.search(r'[\d,.]+', p_tag.text)
            if m:
                price = m.group(0).replace(",", "")

    return {
        "title": title,
        "author": author,
        "publisher": "Jamsai Publisher",
        "price": price,
        "url": book_url,
        "source": "jamsai"
    }

def scrape_jamsai_all_pages(driver, max_pages):
    all_urls = get_all_book_urls(driver, max_pages)
    results = []
    for u in all_urls:
        data = scrape_one(driver, u)
        if data:
            results.append(data)
        time.sleep(0.5)
    print(f"[jamsai] collected {len(results)} books")
    return results