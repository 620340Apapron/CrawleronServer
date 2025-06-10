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

from db_service import create_connection
from crawlers.niin import scrape_niin_all_pages
from crawlers.b2s import scrape_b2s_all_pages
from crawlers.jamsai import scrape_jamsai_all_pages
from crawlers.seed import scrape_seed_all_pages
from crawlers.amarin import scrape_amarin_all_pages

# แก้ปัญหา SSL handshake failed
ssl._create_default_https_context = ssl._create_unverified_context

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  
    options.add_argument("--disable-dev-shm-usage")  # ลดการใช้ shared memory
    options.add_argument("--no-sandbox")  # ป้องกันการ crash
    options.add_argument("--disable-gpu")  # ปิด GPU acceleration
    options.add_argument("--remote-debugging-port=9222")  # เปิด debugging mode
    options.add_argument("--disable-software-rasterizer")  # ลดการใช้กราฟิก
    options.add_argument("--disable-features=VizDisplayCompositor")  # ลดโหลด GPU
    options.add_argument("--disable-popup-blocking")  # ป้องกัน popups
    options.add_argument("--disable-extensions")  # ปิดส่วนขยาย
    options.add_argument("--disable-background-networking")  # ปิดการเชื่อมต่อพื้นหลัง
    options.add_argument("--disable-background-timer-throttling")  # ปิด timer throttling
    options.add_argument("--disable-backgrounding-occluded-windows")  # ปิด backgrounding
    options.add_argument("--disable-breakpad")  # ปิด crash reporting
    options.add_argument("--disable-component-extensions-with-background-pages")  # ปิด background pages
    options.add_argument("--disable-infobars")  # ปิดแถบ info
    options.add_argument("--disable-notifications")  # ปิดการแจ้งเตือน
    options.add_argument("--ignore-certificate-errors")  # ข้าม SSL errors
    options.add_argument("--log-level=3")  # ลด log verbosity

    # ใช้ ChromeDriverManager เพื่อติดตั้งเวอร์ชันที่ตรงกับ Chrome เวอร์ชันที่ใช้งาน
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def create_table(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        source VARCHAR(255),
        title VARCHAR(500),
        author VARCHAR(255),
        price DECIMAL(10,2),
        url TEXT
    )
    """
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()

def insert_book(conn, book):
    sql = """
    INSERT INTO books (source, title, author, price, url)
    VALUES (?, ?, ?, ?, ?)
    """
    params = (
        book.get('source'),
        book.get('title'),
        book.get('author'),
        book.get('price'),
        book.get('url'),
    )
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()


def main():
    conn = create_connection()
    create_table(conn)
    
    driver = get_driver()
    
    sites = [
        
        {"name": "jamsai", "url": "https://www.jamsai.com/shop/"},
        {"name": "b2s", "url": "https://shorturl.asia/JgZ0L"},{"name": "b2s", "url": "https://shorturl.asia/AUefZ"},{"name": "b2s", "url": "https://shorturl.asia/sQXyv"},{"name": "b2s", "url": "https://shorturl.asia/Xnrm3"},{"name": "b2s", "url": "https://shorturl.asia/ojOVW"},{"name": "b2s", "url": "https://shorturl.asia/QoKyp"},{"name": "b2s", "url": "https://shorturl.asia/BEAvO"},{"name": "b2s", "url": "https://shorturl.asia/ldz6p"},{"name": "b2s", "url": "https://shorturl.asia/g8b2m"},{"name": "b2s", "url": "https://shorturl.asia/m9nio"},{"name": "b2s", "url": "https://shorturl.asia/5xIER"},{"name": "b2s", "url": "https://shorturl.asia/QZ0Er"},{"name": "b2s", "url": "https://shorturl.asia/ZNRq2"},{"name": "b2s", "url": "https://shorturl.asia/OMYZv"},
        {"name": "amarin", "url": "https://amarinbooks.com/shop/?orderby=date"},
        {"name": "se-ed", "url": "https://www.se-ed.com/book-cat.book?option.skip=0&filter.productTypes=PRODUCT_TYPE_BOOK_PHYSICAL"},      
        {"name": "niin", "url": "https://www.naiin.com/category?category_1_code=2&product_type_id=1"},{"name": "niin", "url": "https://www.naiin.com/category?category_1_code=13&product_type_id=1"}, {"name": "niin", "url": "https://www.naiin.com/category?category_1_code=33&product_type_id=1"},{"name": "niin", "url": "https://www.naiin.com/category?category_1_code=14&product_type_id=1"},{"name": "niin", "url": "https://www.naiin.com/category?category_1_code=2&product_type_id=1&categoryLv2Code=134"},{"name": "niin", "url": "https://www.naiin.com/category?category_1_code=19&product_type_id=1"},{"name": "niin", "url": "https://www.naiin.com/category?category_1_code=15&product_type_id=1"},{"name": "niin", "url": " https://www.naiin.com/category?category_1_code=5&product_type_id=1"},
    
    ]
    
    for site in sites:
        source = site["name"]
        url = site["url"]
        print(f"\n=== ดึงข้อมูลจากเว็บ: {source} ===")
        driver.get(url)

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

        # **🛠 แก้ไขการบันทึกข้อมูล**
        for book in products:
            if isinstance(book, dict):
                insert_book(conn, book)  # ✅ บันทึกทีละเล่ม
            else:
                print(f"[ERROR] ข้อมูลหนังสือไม่ถูกต้อง: {book}")
    

    # ปิด WebDriver
    driver.quit()
    conn.close()
    
    print("✅ ดึงข้อมูลจากทุกเว็บและบันทึกลงฐานข้อมูลเรียบร้อย")

main()