import re
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
from db_service import insert_book
from utils import extract_isbn


def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_b2s_all_pages(driver, conn, max_books=10, **kwargs):
    total_scraped = 0
    for page in range(1, 6):
        if total_scraped >= max_books: break
        driver.get(f"https://www.b2s.co.th/en/category/books?page={page}")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select(".product-box-inner")
        for link in links:
            if total_scraped >= max_books: break
            href = link.get("href")
            if href:
                scrape_b2s_detail_page(driver, conn, href)
                total_scraped += 1


def scrape_b2s_detail_page(driver, conn, book_url):
    try:
        driver.get(book_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        current_browser_url = driver.current_url 
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title = soup.select_one("h1.page-title") or soup.select_one("[data-ui-id='page-title-wrapper']")
        title = normalize_text(title.text) if title else "Unknown"

        author = normalize_text(soup.select_one(".product.attribute.author").text) if soup.select_one(".product.attribute.author") else "Unknown"
    
        publisher_tag = soup.select_one(".mr-3.fw-bold") 
        publisher = normalize_text(publisher_tag.text) if publisher_tag else "Unknown"

        isbn_tag = soup.find("td", {"data-th": "ISBN"})
        isbn = isbn_tag.text.strip() if isbn_tag else extract_isbn(soup)

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
        "url": current_browser_url,
        "source": "b2s"
    }
        from db_service import insert_book
        insert_book(conn, book_data)
        print(f"📥 บันทึกชั่วคราวสำเร็จ: {title}")

    except Exception as e:
        print(f"B2S Detail Error ({book_url}): {e}")