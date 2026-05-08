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
    return " ".join(txt.strip().split())


def scrape_b2s_all_pages(driver, conn, max_books=10, **kwargs):
    total_scraped = 0
    for page in range(1, 6):
        if total_scraped >= max_books: break
        driver.get(f"https://www.b2s.co.th/en/category/books?page={page}")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select(".product-box-inner")
        for link in links:
            if total_scraped >= max_books: break
            href = link.get("href")
            if href:
                scrape_b2s_detail_page(driver, conn, href)
                total_scraped += 1


def scrape_b2s_detail_page(driver, conn, book_url):
    try:
        driver.get(book_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.page-title")))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title = normalize_text(soup.select_one("h1.page-title").text) if soup.select_one("h1.page-title") else "Unknown"

        # B2S ใช้คลาส mr-3 fw-bold สำหรับบอกสำนักพิมพ์ในหน้ารายละเอียด
        pub_tag = soup.select_one(".mr-3.fw-bold") or soup.find("td", {"data-th": "Publisher"})
        publisher = normalize_text(pub_tag.text) if pub_tag else "B2S"
        
        # ISBN จากตาราง More Information
        isbn_tag = soup.find("td", {"data-th": "ISBN"})
        isbn = isbn_tag.text.strip() if isbn_tag else extract_isbn(soup)

        price = 0
        price_tag = soup.select_one(".price-wrapper .price") or soup.select_one(".price")
        if price_tag:
            m = re.search(r"[\d,.]+", price_tag.text)
            if m: price = float(m.group(0).replace(",", ""))

        book_data = {
            "isbn": isbn, "title": title, "author": "Unknown",
            "publisher": publisher, "price": price, "image_url": "",
            "url": book_url, "source": "B2S"
        }
        insert_book(conn, book_data)
        print(f"📥 Saved: {title} from B2S")

    except Exception as e:
        print(f"❌ Error B2S: {book_url} - {e}")