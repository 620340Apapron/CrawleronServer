import re
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
from db_service import insert_book
from utils import extract_isbn


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
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.select_one(".product_title") or soup.find("h1")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"

        publisher = "Jamsai" # ค่าเริ่มต้นสำหรับเว็บแจ่มใส
        pub_tag = soup.select_one(".product_meta .posted_in")
        if pub_tag and "สำนักพิมพ์" in pub_tag.text:
            publisher = normalize_text(pub_tag.text.replace("สำนักพิมพ์", "").replace("หมวดหมู่:", ""))

        price = 0
        price_tag = soup.select_one(".woocommerce-Price-amount") or soup.select_one(".price")
        if price_tag:
            m = re.search(r"[\d,.]+", price_tag.text)
            if m: price = float(m.group(0).replace(",", ""))

        isbn = extract_isbn(soup)
        image_tag = soup.find("meta", attrs={"property": "og:image"})
        image_url = image_tag.get("content") if image_tag else ""

        book_data = {
            "isbn": isbn, "title": title, "author": "Unknown",
            "publisher": publisher, "price": price, "image_url": image_url,
            "url": url, "source": "Jamsai"
        }
        insert_book(conn, book_data)
        print(f"📥 Saved: {title} from Jamsai")
    except Exception as e:
        print(f"❌ Error Jamsai: {e}")