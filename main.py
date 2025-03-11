import time
import ssl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import InvalidSessionIdException

from db_service import create_connection, create_table, insert_book
from crawlers.niin import scrape_niin_all_pages
from crawlers.b2s import scrape_b2s_all_pages
from crawlers.jamsai import scrape_jamsai_all_pages
from crawlers.seed import scrape_seed_all_pages
from crawlers.amarin import scrape_amarin_all_pages

# แก้ปัญหา SSL handshake failed
ssl._create_default_https_context = ssl._create_unverified_context

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # รันแบบไม่มี UI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # กำหนดพาธของ Google Chrome และ Chromedriver
    options.binary_location = "/usr/bin/google-chrome"
    service = Service("/usr/local/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=options)
    return driver

if __name__ == "__main__":
    conn = create_connection("books.db")
    create_table(conn)
    
    driver = get_driver()
    
    # รายการเว็บที่ต้องดึงข้อมูล
    sites = [
        
        {"name": "amarin", "url": "https://amarinbooks.com/shop/?orderby=date"},
        {"name": "se-ed", "url": "https://www.se-ed.com/book-cat.book?option.skip=0&filter.productTypes=PRODUCT_TYPE_BOOK_PHYSICAL"},      
        {"name": "niin", "url": "https://www.naiin.com/category?type_book=best_seller"},
        {"name": "jamsai", "url": "https://www.jamsai.com/shop/"},
        {"name": "b2s", "url": "https://www.b2s.co.th/widget/promotion/%E0%B8%AB%E0%B8%99%E0%B8%B1%E0%B8%87%E0%B8%AA%E0%B8%B7%E0%B8%AD"},  


    ]
    
    for site in sites:
        source = site["name"]
        url = site["url"]
        print(f"\n=== ดึงข้อมูลจากเว็บ: {source} ===")
        driver.get(url)

        # ใช้ WebDriverWait แทน time.sleep()
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            print(f"[ERROR] ไม่สามารถโหลดหน้าเว็บ {source}: {e}")
            continue
        
        products = []
        if source == "niin":
            products = scrape_niin_all_pages(driver)
        elif source == "b2s":
            products = scrape_b2s_all_pages(driver)
        elif source == "jamsai":
            products = scrape_jamsai_all_pages(driver)
        elif source == "se-ed":
            products = scrape_seed_all_pages(driver)
        elif source == "amarin":
            products = scrape_amarin_all_pages(driver)
        
        print(f"[{source}] พบข้อมูล {len(products)} รายการ")
        
        for i in range(len(products)):
            if isinstance(products[i], dict):  # ตรวจสอบว่าเป็น dictionary
                products[i]["url"] = url  # ใช้ URL หน้าหลักแทน
            else:
                print(f"[ERROR] Product at index {i} is not a dictionary: {products[i]}")
        
        insert_book(conn, products)

    if driver.session_id is None:
        print("[ERROR] WebDriver session is invalid. Restarting driver...")
        driver.quit()
        driver = get_driver()  # ฟังก์ชันที่ใช้สร้าง WebDriver ใหม่
    
    try:
        driver.get(url)
    except InvalidSessionIdException:
        print("[ERROR] WebDriver session expired. Restarting WebDriver...")
        driver.quit()
        driver = get_driver()
        driver.get(url)
    
    driver.quit()
    conn.close()
    
    print("ดึงข้อมูลจากทุกเว็บและบันทึกลงฐานข้อมูลเรียบร้อย")

# python main.py