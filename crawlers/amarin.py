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


def get_all_book_urls(driver, max_pages=999):

    urls = set()
    base_url = "https://amarinbooks.com/shop/?orderby=date&page={}"

    for p in range(1, max_pages + 1):

        driver.get(base_url.format(p))

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.woocommerce-LoopProduct-link")
                )
            )
        except TimeoutException:
            print(f"[amarin] ไม่พบหน้า {p}")
            break

        links = driver.find_elements(By.CSS_SELECTOR, "a.woocommerce-LoopProduct-link")

        for link in links:
            href = link.get_attribute("href")
            if href:
                urls.add(href)

    return list(urls)


def scrape_amarin_detail_page(driver, conn, book_url):

    driver.get(book_url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product_title"))
        )
    except TimeoutException:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    isbn = "Unknown"
    isbn_tag = soup.find("meta", attrs={"property": "book:isbn"})
    if isbn_tag:
        isbn = isbn_tag.get("content")

    title = "Unknown"
    title_tag = soup.select_one("h1.product_title")
    if title_tag:
        title = normalize_text(title_tag.text)

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
        "author": "Unknown",
        "publisher": "Unknown",
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "amarin"
    }

    insert_book(conn, book_data)

    return book_data