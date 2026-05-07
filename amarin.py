import re,time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


from bs4 import BeautifulSoup
from db_service import insert_book
from utils import extract_isbn




def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_amarin_all_pages(driver, conn, max_books=50):
    base_url = "https://amarinbooks.com/product-category/%e0%b8%a7%e0%b8%a3%e0%b8%a3%e0%b8%93%e0%b8%81%e0%b8%a3%e0%b8%a3%e0%b8%a1/"
    driver.get(base_url)
    time.sleep(2)

    total_scraped = 0
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = soup.select("li.product a.woocommerce-LoopProduct-link")

    for link in links:
        if total_scraped >= max_books: break
        href = link.get("href")
        if href and "/product/" in href:
            scrape_amarin_detail_page(driver, conn, href)
            total_scraped += 1
            


def scrape_amarin_detail_page(driver, conn, book_url):

    try:

        driver.get(book_url)

        html = driver.page_source

    except Exception as e:

        print("Chrome crashed at:", book_url)

        return

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = "Unknown"
    tag = soup.select_one("h1")

    if tag:
        title = normalize_text(tag.text)

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
        "publisher": "Amarin",
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "amarin"
    }

    try:
        insert_book(conn, book_data)
    except Exception as e:
        print("DB error:", e)