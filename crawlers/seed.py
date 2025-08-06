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
            EC.presence_of_element_located("span", class_="MuiTypography-root MuiTypography-body line-clamp-2 css-1yy1czf")
        )
    except TimeoutException:
        print(f"[*] [se-ed] Timeout ขณะรอโหลดหน้ารายละเอียด: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    #ISBN
    isbn_tag = soup.find(By.CSS_SELECTOR,"#mpe-editor > div > p:nth-child(13) > span")
    
    # Title
    title_tag = soup.find("h1", class_="MuiTypography-root MuiTypography-h4 css-18oprtn")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    # Author
    try:
        author_tag = driver.find_element(By.XPATH, "//*[@id='mpe-editor']/div/p[1]/a")
        author = normalize_text(author_tag.text)
    except NoSuchElementException:
        author = "Unknown"

    # Publisher
    try:
        publisher_tag = driver.find_element(By.XPATH, "//*[@id='mpe-editor']/div/p[15]/a")
        publisher = normalize_text(publisher_tag.text)
    except NoSuchElementException:
        publisher = "Unknown"

    # Price
    price_tag = soup.find("p", class_="MuiTypography-root MuiTypography-h3 truncate css-muszlw")
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
        "source": "se-ed"
    }

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    base_url = "https://se-ed.com/book-cat.book?filter.productTypes=PRODUCT_TYPE_BOOK_PHYSICAL&page="
    
    for p in range(1, max_pages + 1):
        print(f"[*] [se-ed] กำลังรวบรวม URL จากหน้า {p}...")
        driver.get(f"{base_url}{p}")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    "/html/body/div[1]/div/div/main/main/div[2]/div/div[2]/div[2]/div/div[1]/a"
                ))
            )
        except TimeoutException:
            print(f"[*] [se-ed] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break

        links = driver.find_elements(By.XPATH,"/html/body/div[1]/div/div/main/main/div[2]/div/div[2]/div[2]/div/div[1]/a")
        for link in links:
            href = link.get_attribute("href")
            if href and "product" in href:
                urls.add(href)
    return list(urls)

def scrape_seed_all_pages(driver, max_pages=999):
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