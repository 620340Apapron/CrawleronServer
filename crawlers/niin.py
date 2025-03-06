# crawlers/niin.py
from bs4 import BeautifulSoup
import time

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def scrape_niin_detail(driver):
    """
    ดึงข้อมูลรายละเอียดจากหน้า detail ของหนังสือในเว็บ niin  
    (ปรับ selector ให้ตรงกับ HTML จริง)
    """
    time.sleep(2)  # รอให้หน้า detail โหลด
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    image_tag = soup.find("img", {"class": "img-relative"})
    image = normalize_text(image_tag["src"]) if image_tag and image_tag.has_attr("src") else ""
    
    title_tag = soup.find("h1", {"class": "title-topic"})
    title = normalize_text(title_tag.get_text()) if title_tag else ""
    
    author_tag = soup.find("span", {"class": "inline-block link-book-detail"})
    author = normalize_text(author_tag.get_text()) if author_tag else ""
    
    publisher_tag = soup.find("span", {"class": "inline-block link-book-detail"})
    publisher = normalize_text(publisher_tag.get_text()) if publisher_tag else ""
    
    price_tag = soup.find("span", {"class": "price"})
    price = normalize_text(price_tag.get_text()) if price_tag else ""
    
    category_tag = soup.find("span", {"class": "inline-block link-book-detail"})
    category = normalize_text(category_tag.get_text()) if category_tag else ""
    
    return {
        "image": image,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "category": category,
        "source": "niin"
    }

def scrape_niin_cards(driver):
    """
    คลิกเข้าไปในแต่ละ card ในหน้า listing ของเว็บ niin  
    แล้วดึงข้อมูลจากหน้า detail จากนั้นกลับไปหน้ารายการ
    """
    products = []
    time.sleep(3)  # รอให้หน้า listing โหลด
    # ปรับ XPath ให้ตรงกับ card ของเว็บ niin
    product_cards = driver.find_elements("xpath", "/html/body/div[1]/div[2]/div/div/div[5]/div/div[1]/div/div[1]/div/div[1]/div")
    
    for index in range(len(product_cards)):
        try:
            product_cards = driver.find_elements("xpath", "/html/body/div[1]/div[2]/div/div/div[5]/div/div[1]/div/div[1]/div/div[1]/div")
            card = product_cards[index]
            card.click()  # คลิกเข้าไปดูรายละเอียด
            time.sleep(3)  # รอหน้า detail โหลด
            detail = scrape_niin_detail(driver)
            products.append(detail)
            driver.back()  # กลับไปหน้ารายการ
            time.sleep(3)
        except Exception as e:
            print(f"[niin] Error at card {index}: {e}")
            try:
                driver.back()
            except:
                pass
            time.sleep(3)
    return products

def scrape_niin_all_pages(driver):
    """
    วนลูปดึงข้อมูลจากทุกหน้าของเว็บ niin โดยคลิกปุ่ม "ถัดไป"
    """
    all_products = []
    page = 1
    while True:
        print(f"[niin] Scraping page {page} ...")
        products = scrape_niin_cards(driver)
        if not products:
            print("[niin] No products found on this page.")
            break
        all_products.extend(products)
        try:
            # ปรับ XPath ให้ตรงกับปุ่ม "ถัดไป" ของเว็บ niin
            next_button = driver.find_element("xpath", "/html/body/div[1]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[3]/ul/li[15]/a")
            next_button.click()
            time.sleep(3)
            page += 1
        except Exception as e:
            print(f"[niin] No next page or error: {e}")
            break
    return all_products
