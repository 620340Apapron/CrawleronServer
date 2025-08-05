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
    base_url = "https://www.central.co.th/th/b2s/home-lifestyle/books-movies-music/books"
    for p in range(1, max_pages + 1):
        driver.get(base_url.format(p))
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-card-link"))
            )
        except TimeoutException:
            print(f"[b2s] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, "a.product-card-link")
        for link in links:
            href = link.get_attribute("href")
            if href:
                urls.add(href)
    return list(urls)

def scrape_one(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.title"))
        )
    except TimeoutException:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    title_tag = soup.find("h1", class_="title")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    author = "Unknown"
    auth_tag = soup.find("a", class_="author-text")
    if auth_tag:
        author = normalize_text(auth_tag.text)

    publisher = "Unknown"
    pub_tag = soup.find("div", class_="publisher-text")
    if pub_tag:
        publisher = normalize_text(pub_tag.text)

    price = 0
    price_tag = soup.find("p", class_="price-with-discount-text")
    if price_tag:
        match = re.search(r'[\d,.]+', price_tag.text)
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

def scrape_b2s_all_pages(driver, max_pages=10):
    all_urls = get_all_book_urls(driver, max_pages)
    results = []
    for u in all_urls:
        data = scrape_one(driver, u)
        if data:
            results.append(data)
        time.sleep(0.5)
    print(f"[b2s] collected {len(results)} books")
    return results