from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def scrape_jamsai_detail(driver):
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    books = []
    
    for book_div in soup.find_all("div", class_="col-xxl-3 col-xl-3 col-lg-4 col-md-4 col-sm-6 col-6"):
        try:
            title_tag = book_div.find_element(By.XPATH, '//*[@id="grid-tab-pane"]/div/div[1]/div/div[2]/h3/a')
            title = normalize_text(title_tag.text) if title_tag else "Unknown"

            author_tag = book_div.find_element(By.XPATH, '//*[@id="grid-tab-pane"]/div/div[1]/div/div[2]/div[1]')
            author = normalize_text(author_tag.text) if author_tag else "Unknown"

            #publisher_tag = book_div.find(By.XPATH,)
            publisher = "Jamsai Publisher"
            #publisher = normalize_text(publisher_tag.text) if publisher_tag else "Jamsai Publisher"

            price_tag = book_div.find_element(By.XPATH, '//*[@id="grid-tab-pane"]/div/div[1]/div/div[2]/div[4]/span[1]')
            price = normalize_text(price_tag.text).replace(",", "") if price_tag else "0"

            url_tag = book_div.find("a", class_="tp-product-title-2 truncate-text-line-2")
            url = url_tag["href"] if url_tag else driver.current_url

            category_tag = book_div.find_element(By.XPATH, )
            category = normalize_text(category_tag.text) if category_tag else "General"

            books.append({
                "title": title,
                "author": author,
                "publisher": publisher,
                "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
                "category": category,
                "url": url,
                "source": "jamsai"
            })

        except Exception as e:
            print("[ERROR] ไม่สามารถดึงข้อมูลหนังสือ:", e)

    return books



def scrape_jamsai_all_pages(driver):
    all_products = []
    page = 1

    while page <= 175:
        print(f"[jamsai] Scraping page {page} ...")

        try:
            products = scrape_jamsai_detail(driver)
            if not products or len(products) == 0:
                print(f"[jamsai] ไม่พบข้อมูลในหน้า {page}, หยุดทำงาน")
                break
            all_products.extend(products)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page}: {e}")
            break

        try:
            # ตรวจสอบว่ามีปุ่มถัดไปหรือไม่
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "next.page-numbers"))
            )

            # ใช้ ActionChains เพื่อคลิกปุ่ม
            actions = ActionChains(driver)
            actions.move_to_element(next_button).click().perform()

            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (ไปหน้า {page+1})")
            time.sleep(3)
            page += 1

        except Exception as e:
            print("[ERROR] ไม่สามารถคลิกปุ่มถัดไป:", e)
            break

    return all_products
