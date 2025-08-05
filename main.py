import time
import ssl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
# นำเข้า create_tables
from db_service import create_connection, create_tables, insert_book, get_all_books, clear_raw_books_table
from book_history import update_history
from crawlers.amarin import scrape_amarin_all_pages
from crawlers.b2s import scrape_b2s_all_pages
from crawlers.jamsai import scrape_jamsai_all_pages
from crawlers.niin import scrape_naiin_all_pages
from crawlers.seed import scrape_seed_all_pages

ssl._create_default_https_context = ssl._create_unverified_context

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    conn = create_connection()
    if conn is None:
        print("[ERROR] ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
        return

    # เรียกใช้ฟังก์ชันนี้เพื่อสร้างตารางหากยังไม่มี
    create_tables(conn)

    driver = get_driver()
    
    sites = [
        {"name": "niin", "scraper": scrape_naiin_all_pages},
        {"name": "amarin", "scraper": scrape_amarin_all_pages},
        {"name": "b2s", "scraper": scrape_b2s_all_pages},
        {"name": "jamsai", "scraper": scrape_jamsai_all_pages},
        {"name": "se-ed", "scraper": scrape_seed_all_pages},
    ]

    # ล้างข้อมูลเก่าก่อนเริ่มดึงข้อมูลใหม่
    clear_raw_books_table(conn)

    for site in sites:
        source, scraper = site['name'], site['scraper']
        print(f"\n=== ดึงข้อมูลจากเว็บ: {source} ===")
        
        try:
            products = scraper(driver, 10)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจาก {source} ได้: {e}")
            continue

        print(f"[{source}] พบข้อมูล {len(products)} รายการ")
        for book in products:
            if isinstance(book, dict):
                insert_book(conn, book)
            else:
                print(f"[ERROR] ข้อมูลหนังสือไม่ถูกต้อง: {book}")
    
    update_history(conn)

    print("\n✅ การดึงข้อมูลและอัปเดตฐานข้อมูลเสร็จสิ้น")
    driver.quit()
    conn.close()

if __name__ == "__main__":
    main()