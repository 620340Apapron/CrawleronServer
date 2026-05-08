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


def scrape_jamsai_detail_page(driver, conn, book_url):

    try:

        driver.get(book_url)

        html = driver.page_source

    except Exception as e:

        print("Chrome crashed at:", book_url)

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

    title = "Unknown"
    title_tag = soup.select_one("h1")
    if title_tag:
        title = normalize_text(title_tag.text)

    author = "Unknown"
    author_tag = soup.select_one(".author")
    if author_tag:
        author = normalize_text(author_tag.text)

    publisher = "Jamsai"

    price = 0
    price_tag = soup.select_one(".price")

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