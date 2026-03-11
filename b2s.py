import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from main import get_driver
import time
from db_service import insert_book


def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_b2s_all_pages(driver, conn, max_pages=5):

    base_url = "https://www.b2s.co.th/en/category/books?page={}"
    

    for page in range(1,11):

        url = base_url.format(page)

        print("กำลังเปิด:", url)

        driver.get(url)
        time.sleep(2)

        WebDriverWait(driver,20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,".product-card"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        books = soup.select("a[href*='/product/']")

        print("พบ", len(books), "เล่ม")


        for book_url in book_urls:

            book_url = b.get("href")

            if book_url:

                if not book_url.startswith("http"):
                    book_url = "https://www.b2s.co.th" + book_url

                scrape_b2s_detail_page(driver, conn, book_url)


def scrape_b2s_detail_page(driver, conn, book_url):

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
    author_tag = soup.select_one(".product.attribute.author")

    if author_tag:
        author = normalize_text(author_tag.text)

    publisher = "B2S"

    isbn = "Unknown"

    text = soup.get_text()

    m = re.search(r"ISBN\s*[:\-]?\s*(\d+)", text)

    if m:
        isbn = m.group(1)

    price = 0
    price_tag = soup.select_one(".price")

    if price_tag:
        m = re.search(r"[\d,.]+", price_tag.text)

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
        "url": book_url,
        "source": "b2s"
    }

    try:
        insert_book(conn, book_data)
    except Exception as e:
        print("DB error:", e)