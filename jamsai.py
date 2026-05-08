import re
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
from db_service import insert_book


def normalize_text(txt):
    if not txt:
        return ""
    return ' '.join(txt.strip().split())


def scrape_jamsai_all_pages(driver, conn, max_books=50):
    total_scraped = 0
    for page in range(1, 6):
        if total_scraped >= max_books: break
        driver.get(f"https://www.jamsai.com/shop/?page={page}")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select(".product-item a")
        for link in links:
            if total_scraped >= max_books: break
            href = link.get("href")
            if href and "/product/" in href:
                scrape_jamsai_detail_page(driver, conn, href)
                total_scraped += 1


def scrape_jamsai_detail_page(driver, conn, url):

    try:
        driver.get(url)
        # ไม่ต้องรอจนโหลดเสร็จทั้งหน้า เอาแค่หัวข้อขึ้นก็พอ
        time.sleep(1) 
    except Exception as e:
        print(f"⚠️ ข้ามหน้า {url} เพราะโหลดช้าเกินไป")
        return

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    current_browser_url = driver.current_url 

    soup = BeautifulSoup(driver.page_source, "html.parser")

    isbn = "Unknown"
    isbn_tag = soup.find("meta", attrs={"property": "book:isbn"})
    if isbn_tag:
        isbn = isbn_tag.get("content")

    title = soup.select_one(".product_title") or soup.find("h1")

    price_tag = soup.select_one(".woocommerce-Price-amount") or soup.select_one(".price")

    author = "Unknown"
    author_tag = soup.select_one(".author")
    if author_tag:
        author = normalize_text(author_tag.text)

    publisher = "Jamsai"

    if price_tag:
        m = re.search(r'[\d,.]+', price_tag.text)
        if m:
            price = float(m.group(0).replace(",", ""))

    image_url = ""
    image_tag = soup.find("meta", attrs={"property": "og:image"})
    if image_tag:
        image_url = image_tag.get("content")

    book_data = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "image_url": image_url,
        "url": current_browser_url,
        "source": "jamsai"
    }

    try:
        insert_book(conn, book_data)
    except Exception as e:
        print("DB error:", e)