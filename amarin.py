import re,time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.find("h1")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"

        author_tag = soup.select_one(".product_meta .author") or soup.find("span", string=re.compile("ผู้เขียน"))
        author = "Unknown"
        if author_tag:
            author = normalize_text(author_tag.text.replace("ผู้เขียน:", ""))

        pub_tag = soup.select_one(".product_meta .posted_in")
        publisher = "Amarin"
        if pub_tag:
            publisher = normalize_text(pub_tag.text.replace("สำนักพิมพ์:", "").replace("หมวดหมู่:", ""))

        price = 0
        price_tag = soup.select_one(".price ins .amount")
        if price_tag:
            m = re.search(r"[\d,.]+", price_tag.text)
            if m: price = float(m.group(0).replace(",", ""))

        isbn = extract_isbn(soup) or soup.find("td.woocommerce-product-attributes-item__value")
        image_tag = soup.find("meta", attrs={"property": "og:image"})
        image_url = image_tag.get("content") if image_tag else ""

        book_data = {
            "isbn": isbn, "title": title, "author": author,
            "publisher": publisher, "price": price, "image_url": image_url,
            "url": book_url, "source": "Amarin"
        }
        insert_book(conn, book_data)
        print(f"📥 Saved: {title} from Amarin")
    except Exception as e:
        print(f"❌ Error Amarin: {e}")