from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def start_new_driver():
    options = webdriver.ChromeOptions()
    # สำหรับดีบัก ลองปิด headless ชั่วคราว
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # เพิกเฉยปัญหา SSL
    options.add_argument("--ignore-certificate-errors")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_niin_detail(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "main"))
        )
    except TimeoutException:
        print("[niin] Timeout waiting for detail page to load.")
    
    try:
        title = normalize_text(driver.find_element(By.XPATH, '//*[@id="main"]/div/div/div[3]/div[2]/div[1]/div[1]/h1').text)
    except Exception:
        title = "Unknown"

    try:
        author = normalize_text(driver.find_element(By.XPATH, '//*[@id="main"]/div/div/div[3]/div[2]/div[1]/div[1]/p[1]/a').text)
    except Exception:
        author = "Unknown"

    try:
        publisher = normalize_text(driver.find_element(By.XPATH, '//*[@id="main"]/div/div/div[3]/div[2]/div[1]/div[1]/p[2]/a').text)
    except Exception:
        publisher = "Unknown"

    try:
        price = normalize_text(driver.find_element(By.CLASS_NAME, '//*[@id="discount-price"]').text).replace(",", "")
    except Exception:
        price = "0"

    try:
        category = normalize_text(driver.find_element(By.XPATH, '//*[@id="main"]/div/div/div[3]/div[2]/div[1]/div[1]/p[3]/a[1]').text)
    except Exception:
        category = "General"

    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
        "category": category,
        "url": driver.current_url,
        "source": "niin"
    }

def scrape_niin_cards(driver):
    products = []
    main_window = driver.current_window_handle

    # เลื่อนหน้าจอหลายครั้งเพื่อให้โหลดการ์ดหนังสือ (Lazy Load)
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # บันทึก HTML สำหรับตรวจสอบ DOM
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    # ใช้ XPATH แบบกว้างเพื่อดึงทุกลิงก์ในทุกการ์ดที่มีคลาส 'productitem'
    book_link_elements = driver.find_elements(By.XPATH, '//*[@id="for-book-list"]//div[contains(@class,"item-cover")]//a')
    print(f"[niin] พบ {len(book_link_elements)} ลิงก์หนังสือในหน้านี้ (หลัง scroll)")

    book_urls = []
    for elem in book_link_elements:
        url = elem.get_attribute("href")
        if url and url not in book_urls:
            book_urls.append(url)

    if len(book_urls) < 2:
        print("[niin] ไม่พบลิงก์หนังสือครบตามที่คาด กรุณาตรวจสอบ debug.html และปรับ XPATH ให้ตรงกับ DOM")
        return [], driver

    for index, book_url in enumerate(book_urls):
        try:
            print(f"[niin] Processing book {index+1}/{len(book_urls)}: {book_url}")
            driver.execute_script("window.open(arguments[0]);", book_url)
            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
            new_window = [w for w in driver.window_handles if w != main_window][0]
            driver.switch_to.window(new_window)

            detail = scrape_niin_detail(driver)
            products.append(detail)
            
            driver.close()
            driver.switch_to.window(main_window)
        except Exception as e:
            print(f"[niin] Error processing book {index+1}: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            continue

    return products, driver

def scrape_niin_all_pages(driver):
    all_products = []
    page = 1

    while True:
        print(f"[niin] Scraping page {page} ...")

        try:
            products, driver = scrape_niin_cards(driver)
            if not products:
                print(f"[niin] ไม่พบข้อมูลในหน้า {page}, หยุดทำงาน")
                break
            all_products.extend(products)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page}: {e}")
            break

        # คลิกปุ่ม 'ถัดไป'
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="for-book-list"]/div[3]/ul/li[15]/a'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            next_button.click()
            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (ไปหน้า {page+1})")
            page += 1
        except Exception as e:
            print("[ERROR] ไม่สามารถคลิกปุ่มถัดไป:", e)
            break

    return all_products

if __name__ == "__main__":
    driver = start_new_driver()
    driver.get("https://www.naiin.com/category?type_book=best_seller")
    data = scrape_niin_all_pages(driver)
    print(f"พบข้อมูลทั้งหมด {len(data)} รายการ")
    driver.quit()
