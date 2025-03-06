# crawlers/amarin.py
from bs4 import BeautifulSoup
import time

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def scrape_amarin_detail(driver):
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    image_tag = soup.find("img", {"class": "wp-post-image skip-lazy"})
    image = normalize_text(image_tag["src"]) if image_tag and image_tag.has_attr("src") else ""
    
    title_tag = soup.find("h1", {"class": "product-title product_title entry-title"})
    title = normalize_text(title_tag.get_text()) if title_tag else ""
    
    author_tag = soup.find("p", {"class": "product-short-description"})
    author = normalize_text(author_tag.get_text()) if author_tag else ""
    
    publisher_tag = soup.find("a", {"class": "posted_in"})
    publisher = normalize_text(publisher_tag.get_text()) if publisher_tag else ""
    
    price_tag = soup.find("span", {"class": "woocommerce-Price-amount amount"})
    price = normalize_text(price_tag.get_text()) if price_tag else ""
    
    category_tag = soup.find("span", {"class": "posted_in"})
    category = normalize_text(category_tag.get_text()) if category_tag else ""
    
    return {
        "image": image,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "category": category,
        "source": "amarin"
    }

def scrape_amarin_cards(driver):
    products = []
    time.sleep(3)
    product_cards = driver.find_elements("xpath", "//div[contains(@class, 'amarin-card')]")
    for index in range(len(product_cards)):
        try:
            product_cards = driver.find_elements("xpath", "//div[contains(@class, 'amarin-card')]")
            card = product_cards[index]
            card.click()
            time.sleep(3)
            detail = scrape_amarin_detail(driver)
            products.append(detail)
            driver.back()
            time.sleep(3)
        except Exception as e:
            print(f"[amarin] Error at card {index}: {e}")
            try:
                driver.back()
            except:
                pass
            time.sleep(3)
    return products

def scrape_amarin_all_pages(driver):
    all_products = []
    page = 1
    while True:
        print(f"[amarin] Scraping page {page} ...")
        products = scrape_amarin_cards(driver)
        if not products:
            break
        all_products.extend(products)
        try:
            next_button = driver.find_element("xpath", "//a[contains(text(),'ถัดไป')]")
            next_button.click()
            time.sleep(3)
            page += 1
        except Exception as e:
            print(f"[amarin] No next page or error: {e}")
            break
    return all_products
