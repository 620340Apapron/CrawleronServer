# crawlers/b2s.py
from bs4 import BeautifulSoup
import time

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def scrape_b2s_detail(driver):
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    image_tag = soup.find("img", {"class": "b2s-detail-image"})
    image = normalize_text(image_tag["src"]) if image_tag and image_tag.has_attr("src") else ""
    
    title_tag = soup.find("h1", {"class": "b2s-detail-title"})
    title = normalize_text(title_tag.get_text()) if title_tag else ""
    
    author_tag = soup.find("span", {"class": "b2s-detail-author"})
    author = normalize_text(author_tag.get_text()) if author_tag else ""
    
    publisher_tag = soup.find("span", {"class": "b2s-detail-publisher"})
    publisher = normalize_text(publisher_tag.get_text()) if publisher_tag else ""
    
    price_tag = soup.find("span", {"class": "b2s-detail-price"})
    price = normalize_text(price_tag.get_text()) if price_tag else ""
    
    category_tag = soup.find("span", {"class": "b2s-detail-category"})
    category = normalize_text(category_tag.get_text()) if category_tag else ""
    
    return {
        "image": image,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "category": category,
        "source": "b2s"
    }

def scrape_b2s_cards(driver):
    products = []
    time.sleep(3)
    product_cards = driver.find_elements("xpath", "//div[contains(@class, 'b2s-card')]")
    for index in range(len(product_cards)):
        try:
            product_cards = driver.find_elements("xpath", "//div[contains(@class, 'b2s-card')]")
            card = product_cards[index]
            card.click()
            time.sleep(3)
            detail = scrape_b2s_detail(driver)
            products.append(detail)
            driver.back()
            time.sleep(3)
        except Exception as e:
            print(f"[b2s] Error at card {index}: {e}")
            try:
                driver.back()
            except:
                pass
            time.sleep(3)
    return products

def scrape_b2s_all_pages(driver):
    all_products = []
    page = 1
    while True:
        print(f"[b2s] Scraping page {page} ...")
        products = scrape_b2s_cards(driver)
        if not products:
            break
        all_products.extend(products)
        try:
            next_button = driver.find_element("xpath", "//a[contains(text(),'ถัดไป')]")
            next_button.click()
            time.sleep(3)
            page += 1
        except Exception as e:
            print(f"[b2s] No next page or error: {e}")
            break
    return all_products
