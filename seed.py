import re
from bs4 import BeautifulSoup

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from db_service import insert_book
from utils import extract_isbn
import time

def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_seed_all_pages(driver, conn, max_books = 50):
    total_scraped = 0
    for page in range(1, 6):
        if total_scraped >= max_books: break
        driver.get(f"https://www.se-ed.com/product-category/book?page={page}")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select(".product-list-item a")
        for link in links:
            if total_scraped >= max_books: break
            href = link.get("href")
            if href:
                scrape_seed_detail_page(driver, conn, href)
                total_scraped += 1
          


def scrape_seed_detail_page(driver, conn, book_url):
    try:
        driver.get(book_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.find("h1")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"

        # ซีเอ็ดมักระบุสำนักพิมพ์ในหน้าข้อมูลสินค้า
        pub_tag = soup.find("a", href=re.compile("publisher")) or soup.find("span", string=re.compile("สำนักพิมพ์"))
        publisher = "Se-ed"
        if pub_tag:
            publisher = normalize_text(pub_tag.text)

        price = 0
        price_tag = soup.select_one(".price-cyber") or soup.select_one(".price")
        if price_tag:
            m = re.search(r"[\d,.]+", price_tag.text)
            if m: price = float(m.group(0).replace(",", ""))

        isbn = extract_isbn(soup)
        image_tag = soup.find("meta", attrs={"property": "og:image"})
        image_url = image_tag.get("content") if image_tag else ""

        book_data = {
            "isbn": isbn, "title": title, "author": "Unknown",
            "publisher": publisher, "price": price, "image_url": image_url,
            "url": book_url, "source": "Seed"
        }
        insert_book(conn, book_data)
        print(f"📥 Saved: {title} from Seed")
    except Exception as e:
        print(f"❌ Error Seed: {book_url} - {e}")