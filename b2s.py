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
        links = soup.select("a.product-item-link")
        for link in links:
            href = link.get("href")
            if href:
                print(f"🔗 พบลิงก์ B2S: {href}")
                scrape_b2s_detail_page(driver, conn, href)


def scrape_b2s_detail_page(driver, conn, book_url):
    try:
        driver.get(book_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.page-title")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        

        title_tag = soup.select_one("h1.page-title")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"
        
        pub_tag = soup.find("td", {"data-th": "Publisher"}) or soup.select_one(".mr-3.fw-bold")
        publisher = normalize_text(pub_tag.text) if pub_tag else "B2S"

        author_tag = soup.find("td", {"data-th": "Author"})
        author = normalize_text(author_tag.text) if author_tag else "Unknown"

        isbn_tag = soup.find("td", {"data-th": "ISBN"})
        isbn = isbn_tag.text.strip() if isbn_tag else extract_isbn(soup)

        price = 0
        price_tag = soup.select_one("[data-price-type='finalPrice'] .price")
        if price_tag:
            m = re.search(r"[\d,.]+", price_tag.text)
            if m: price = float(m.group(0).replace(",", ""))

        image_tag = soup.find("meta", attrs={"property": "og:image"})
        image_url = image_tag.get("content") if image_tag else ""

        book_data = {
            "isbn": isbn, "title": title, "author": author,
            "publisher": publisher, "price": price, "image_url": image_url,
            "url": book_url, "source": "B2S"
        }
        insert_book(conn, book_data)
        print(f"📥 Saved: {title} from B2S")
    except Exception as e:
        print(f"❌ Error B2S: {e}")