import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from db_service import insert_book
from image_service import upload_book_cover


def normalize_text(txt):
    if not txt:
        return ""
    return ' '.join(txt.replace('"', '').strip().split())

def scrape_jamsai_all_pages(driver, conn, max_pages=10):

    base_url = "https://www.jamsai.com/shop/?page={}"

    for page in range(1, max_pages + 1):

        url = base_url.format(page)

        driver.get(url)

        print("กำลังเปิด:", url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a"))
            )
        except TimeoutException:
            print("โหลดหน้าไม่สำเร็จ")
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")

        book_links = soup.select("a")

        for link in book_links:

            href = link.get("href")

            if href and "/product/" in href:

                print("พบหนังสือ:", href)

                try:
                    scrape_jamsai_detail_page(driver, conn, href)
                except Exception as e:
                    print("error:", e)


def scrape_jamsai_detail_page(driver, conn, book_url):

    driver.get(book_url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
    except TimeoutException:
        return None

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
    author_tag = soup.select_one(".product-author")
    if author_tag:
        author = normalize_text(author_tag.text)

    publisher = "Jamsai"

    price = 0
    price_tag = soup.select_one(".price")
    if price_tag:
        m = re.search(r'[\d,.]+', price_tag.text)
        if m:
            price = int(float(m.group(0).replace(",", "")))

    image_url = ""
    image_tag = soup.find("meta", attrs={"property": "og:image"})
    if image_tag:
        image_url = image_tag.get("content")

    final_image_url = ""
    if image_url:
        final_image_url = upload_book_cover(image_url, isbn)

    book_data = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "jamsai"
    }

    insert_book(conn, book_data)

    return book_data