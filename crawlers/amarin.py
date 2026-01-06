import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book
from image_service import upload_book_cover

def normalize_text(txt):
    if not txt:
        return ""
    return ' '.join(txt.replace('"', '').strip().split())

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    base_url = "https://amarinbooks.com/shop/?orderby=date"
    for p in range(1, max_pages + 1):
        driver.get(base_url.format(p))
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#main > div > div.col.large-9 > div > div.products.row.row-small.large-columns-3.medium-columns-3.small-columns-2 > div.product-small.col.has-hover.product.type-product.post-746196.status-publish.first.instock.product_cat-309.product_cat-2345.has-post-thumbnail.shipping-taxable.purchasable.product-type-simple > div > div.product-small.box > div.box-text.box-text-products.text-center.grid-style-2 > div.title-wrapper > p > a"))
            )
        except TimeoutException:
            print(f"[amarin] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break
        
        links = driver.find_elements(By.CSS_SELECTOR, "#main > div > div.col.large-9 > div > div.products.row.row-small.large-columns-3.medium-columns-3.small-columns-2 > div.product-small.col.has-hover.product.type-product.post-746196.status-publish.first.instock.product_cat-309.product_cat-2345.has-post-thumbnail.shipping-taxable.purchasable.product-type-simple > div > div.product-small.box > div.box-text.box-text-products.text-center.grid-style-2 > div.title-wrapper > p > a")
        for link in links:
            href = link.get_attribute("href")
            if href:
                urls.add(href)
    return list(urls)

def scrape_amarin_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#main > div > div.col.large-9 > div > div.products.row.row-small.large-columns-3.medium-columns-3.small-columns-2 > div.product-small.col.has-hover.product.type-product.post-746196.status-publish.first.instock.product_cat-309.product_cat-2345.has-post-thumbnail.shipping-taxable.purchasable.product-type-simple > div > div.product-small.box > div.box-text.box-text-products.text-center.grid-style-2 > div.title-wrapper > p > a"))
        )
    except TimeoutException:
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    isbn_tag = soup.find("meta", attrs={"property": "book:isbn"})
    isbn = isbn_tag.get("content") if isbn_tag else "Unknown"
    
    title_tag = soup.find(By.CSS_SELECTOR,"#product-746196 > div > div.product-main > div > div.product-info.summary.col-fit.col.entry-summary.product-summary.text-left > h1")
    title = normalize_text(title_tag.text) if title_tag else "Unknown"

    author_tag = soup.find(By.CSS_SELECTOR,"#product-746196 > div > div.product-main > div > div.product-info.summary.col-fit.col.entry-summary.product-summary.text-left > div.product-short-description > p:nth-child(1) > strong")
    author = normalize_text(author_tag.text) if author_tag else "Unknown"

    publisher_tag = soup.find(By.CSS_SELECTOR,"#product-746196 > div > div.product-main > div > div.product-info.summary.col-fit.col.entry-summary.product-summary.text-left > div.product_meta > span:nth-child(3) > a")
    publisher = normalize_text(publisher_tag.text) if publisher_tag else "Unknown"
    
    p_tag = soup.find(By.CSS_SELECTOR,"#product-746196 > div > div.product-main > div > div.product-info.summary.col-fit.col.entry-summary.product-summary.text-left > div.price-wrapper > p > ins > span > bdi")
    if p_tag:
        m = re.search(r'[\d,.]+', p_tag.text)
        if m:
            price = m.group(0).replace(",", "")
    
    try:
        price = int(float(price))
    except (ValueError, TypeError):
        price = 0

    return {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "image_url": image_url,
        "url": book_url,
        "source": "amarin"
    }

def scrape_amarin_all_pages(driver, conn, max_pages=999):
    all_products = []
    
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_amarin_detail_page(driver, url)
        if book_data:
            insert_book(conn, book_data)

    return 