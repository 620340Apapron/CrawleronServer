import re
from bs4 import BeautifulSoup
from db_service import insert_book
from utils import extract_isbn


def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_b2s_all_pages(driver, conn, max_pages=10):

    base_url = "https://www.b2s.co.th/en/book?page={}"

    for page in range(1, max_pages + 1):

        url = base_url.format(page)

        print("เปิดหน้า:", url)

        driver.get(url)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        links = soup.select("a")

        book_urls = []

        for link in links:

            href = link.get("href")

            if href and "/product/" in href:

                if href.startswith("/"):
                    href = "https://www.b2s.co.th" + href

                book_urls.append(href)

        book_urls = list(set(book_urls))

        for book_url in book_urls:
            scrape_b2s_detail_page(driver, conn, book_url)


def scrape_b2s_detail_page(driver, conn, book_url):

    driver.get(book_url)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = "Unknown"
    tag = soup.select_one("h1")

    if tag:
        title = normalize_text(tag.text)

    author = "Unknown"
    author_tag = soup.select_one(".author")

    if author_tag:
        author = normalize_text(author_tag.text)

    price = 0
    price_tag = soup.select_one(".price")

    if price_tag:
        m = re.search(r"[\d,.]+", price_tag.text)

        if m:
            price = int(float(m.group(0).replace(",", "")))

    isbn = extract_isbn(soup)

    img = ""
    img_tag = soup.select_one("img")

    if img_tag:
        img = img_tag.get("src")

    final_image = ""

    if img:
        final_image = upload_book_cover(img, isbn)

    book = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": "B2S",
        "price": price,
        "image_url": final_image,
        "url": book_url,
        "source": "b2s"
    }

    insert_book(conn, book)