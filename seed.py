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
        links = soup.select(".product-box a") or soup.select("a.link-product")
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

        title = normalize_text(soup.find("h1").text) if soup.find("h1") else "Unknown"

        # ค้นหาคำว่าสำนักพิมพ์ในหน้าเว็บ
        pub_tag = soup.find("a", href=re.compile("publisher")) or soup.find("span", string=re.compile("สำนักพิมพ์"))
        publisher = normalize_text(pub_tag.text) if pub_tag else "Se-ed"

        author_tag = soup.find("a", href=re.compile(r"author", re.I))
        author = normalize_text(author_tag.text) if author_tag else "Unknown"

        price_tag = soup.select_one(".price-cyber") or soup.select_one(".product-price")
        price = 0
        if price_tag:
            m = re.search(r"[\d,.]+", price_tag.text)
            if m: price = float(m.group(0).replace(",", ""))

        isbn = extract_isbn(soup)
        image_tag = soup.find("meta", attrs={"property": "og:image"})
        image_url = image_tag.get("content") if image_tag else ""

        book_data = {
            "isbn": isbn, "title": title, "author": author,
            "publisher": publisher, "price": price, "image_url": image_url,
            "url": book_url, "source": "Seed"
        }
        insert_book(conn, book_data)
        print(f"📥 Saved: {title} from Seed")
    except Exception as e:
        print(f"❌ Error Seed: {e}")