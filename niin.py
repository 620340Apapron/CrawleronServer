import re
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from db_service import insert_book
from utils import extract_isbn
import time


def normalize_text(txt):
    if not txt:
        return ""
    return " ".join(txt.strip().split())


def scrape_naiin_all_pages(driver, conn, max_books=10, **kwargs):
    total_scraped = 0
    for page in range(1, 6):
        if total_scraped >= max_books: break
        driver.get(f"https://www.naiin.com/category?category_1_code=2&product_type_id=1&page={page}")

        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select(".item-info a")

        for link in links:
            if total_scraped >= max_books: break
            href = link.get("href")
            if href:
                scrape_naiin_detail_page(driver, conn, href)
                total_scraped += 1
           

def scrape_naiin_detail_page(driver, conn, book_url):
    try:
        driver.get(book_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        final_url = driver.current_url
        
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.find("h1") or soup.find("meta", property="og:title")
        title = normalize_text(title_tag.text if hasattr(title_tag, 'text') else title_tag.get("content", "Unknown"))
        
        author_tag = soup.select_one("a.author-name") or soup.select_one(".AuthorName")
        author = normalize_text(author_tag.text) if author_tag else "Unknown"
        
        publisher_tag = soup.select_one("a.publisher-name") or soup.select_one(".PublisherName")
        publisher = normalize_text(publisher_tag.text) if publisher_tag else "Unknown"

        price_tag = soup.select_one(".product-price-actual") or soup.select_one(".price")
        if price_tag:
            m = re.search(r"[\d,.]+", price_tag.text)
            price = float(m.group(0).replace(",", "")) if m else 0

        isbn = extract_isbn(soup)
        
        image_tag = soup.find("meta", attrs={"property": "og:image"})
        image_url = image_tag.get("content") if image_tag else ""

        book_data = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": "Amarin",
        "price": price,
        "image_url": image_url,
        "url": book_url,
        "source": "Amarin"
    }
    
        # สำคัญมาก: ต้องมีบรรทัดนี้ ข้อมูลถึงจะเข้า raw_books!
        from db_service import insert_book
        insert_book(conn, book_data)
        print(f"📥 บันทึกชั่วคราวสำเร็จ: {title}")

    except Exception as e:
        print(f"❌ โหลดหน้า {book_url} ไม่สำเร็จ: {e}")