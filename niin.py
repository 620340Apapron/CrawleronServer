import re
from bs4 import BeautifulSoup


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from db_service import insert_book
from utils import extract_isbn
import time


def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_naiin_all_pages(driver, conn, max_books=50, **kwargs):
    total_scraped = 0
    for page in range(1, 6):
        if total_scraped >= max_books: break
        driver.get(f"https://www.naiin.com/category?category_1_code=2&product_type_id=1")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select(".product-list-item a")
        for link in links:
            if total_scraped >= max_books: break
            href = link.get("href")
            if href:
                scrape_naiin_detail_page(driver, conn, href)
                total_scraped += 1
           

def scrape_naiin_detail_page(driver, conn, book_url):
    driver.get(book_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = soup.select_one('meta[property="og:title"]')["content"] if soup.select_one('meta[property="og:title"]') else "Unknown"
    author = normalize_text(soup.select_one(".AuthorName").text) if soup.select_one(".AuthorName") else "Unknown"
    
    # FIXED: Was saving into 'author' variable in your original file
    publisher = "Unknown"
    publisher_tag = soup.select_one(".PublisherName")
    if publisher_tag:
        publisher = normalize_text(publisher_tag.text)

    price = 0
    price_tag = soup.select_one(".price")

    if price_tag:
        m = re.search(r"[\d,.]+", price_tag.text)

        if m:
            price = int(float(m.group(0).replace(",", "")))

    isbn = extract_isbn(soup)

    image_url = ""
    image_tag = soup.find("meta", attrs={"property": "og:image"})

    if image_tag:
        image_url = image_tag.get("content")

    final_image_url = image_url

    book_data = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "naiin"
    }

    try:
        insert_book(conn, book_data)
    except Exception as e:
        print("DB error:", e)