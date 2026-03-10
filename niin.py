import re
from bs4 import BeautifulSoup
from db_service import insert_book
from utils import extract_isbn


def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_naiin_all_pages(driver, conn, max_pages=10):

    base_url = "https://www.naiin.com/category?page={}"

    for page in range(1, max_pages + 1):

        url = base_url.format(page)

        print("เปิดหน้า:", url)

        driver.get(url)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        links = soup.select("a")

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

    driver.get(book_url)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = "Unknown"
    title_tag = soup.select_one("h1")

    if title_tag:
        title = normalize_text(title_tag.text)

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

    image_url = ""
    image_tag = soup.find("meta", attrs={"property": "og:image"})

    if image_tag:
        image_url = image_tag.get("content")

    final_image_url = image_url

    book = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": "Naiin",
        "price": price,
        "image_url": final_image_url,
        "url": book_url,
        "source": "naiin"
    }

    insert_book(conn, book)