import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from main import get_driver
from db_service import insert_book
from utils import extract_isbn
import time

def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_seed_all_pages(driver, conn, max_pages=10):

    base_url = "https://www.se-ed.com/product-category/book?page={}"

    for page in range(1,11):

        url = base_url.format(page)

        print("เปิดหน้า:", url)

        driver.get(url)
        time.sleep(2)
        
        WebDriverWait(driver,20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,".product-list-item"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        links = soup.select(".product-list-item a")

        book_urls = []

        for link in links:

            href = link.get("href")

            if href and "/product/" in href:
                book_urls.append(href)

        book_urls = list(set(book_urls))
        
        count = 0
        for book_url in book_urls:
            scrape_seed_detail_page(driver, conn, book_url)
            count += 1

            if count % 30 == 0:
                driver.quit()
                driver = get_driver()


def scrape_seed_detail_page(driver, conn, book_url):

    try:

        driver.get(book_url)

        html = driver.page_source

    except Exception as e:

        print("Chrome crashed at:", book_url)

        return

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = "Unknown"
    title_tag = soup.select_one("h1")

    if title_tag:
        title = normalize_text(title_tag.text)

    author = "Unknown"

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
        "publisher": "SE-ED",
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "seed"
    }

    try:
        insert_book(conn, book_data)
    except Exception as e:
        print("DB error:", e)