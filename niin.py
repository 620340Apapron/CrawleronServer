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


def scrape_naiin_all_pages(driver, conn, max_pages=10):

    base_url = "https://www.naiin.com/category?category_1_code=2&product_type_id=1"

    url = base_url

    print("เปิดหน้า:", url)

    driver.get(url)
    time.sleep(5)
    
    try:
        WebDriverWait(driver,30).until(
            EC.presence_of_element_located((By.TAG_NAME,"body"))
            )
    except TimeoutException:

        print("Jamsai: หน้าโหลดไม่สำเร็จ")
        return

    soup = BeautifulSoup(driver.page_source, "html.parser")

    links = links = soup.select("a[href*='/product/detail/']")

    book_urls = []

    for link in links:

            href = link.get("href")

            if href and "/product/detail/" in href:

                if href.startswith("/"):
                    href = "https://www.naiin.com" + href

                book_urls.append(href)

    book_urls = list(set(book_urls))


    for book_url in book_urls:
            scrape_naiin_detail_page(driver, conn, book_url)
           

def scrape_naiin_detail_page(driver, conn, book_url):

    try:

        driver.get(book_url)

        html = driver.page_source

    except Exception as e:

        print("Chrome crashed at:", book_url)

        return

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = "Unknown"
    title_tag = soup.select_one('meta[property="og:title"]')

    if title_tag:
        title = title_tag["content"] if title_tag else None

    author = "Unknown"
    author_tag = soup.select_one(".AuthorName")
    if author_tag:
        author = normalize_text(author_tag.text)

    publisher = "Unknown"
    publisher_tag = soup.select_one("PublisherName")
    if publisher_tag:
        author = normalize_text(publisher_tag.text)

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