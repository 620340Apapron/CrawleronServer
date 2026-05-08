import ssl
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

from db_service import create_connection, create_tables
from book_history import update_history
from process_books import process_books

from amarin import scrape_amarin_all_pages
from b2s import scrape_b2s_all_pages
from jamsai import scrape_jamsai_all_pages
from niin import scrape_naiin_all_pages
from seed import scrape_seed_all_pages

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # เพิ่ม 3 บรรทัดนี้
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--js-flags='--max-old-space-size=512'") # จำกัด RAM ของ JS
    
    options.add_argument("--blink-settings=imagesEnabled=false") 
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30) # เพิ่มเวลา timeout เผื่อเน็ตช้า
    return driver

def run_crawler():
    print("🚀 เริ่มระบบ Crawler (Standalone Mode)")
    conn = create_connection()
    if not conn:
        print("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
        return

    try:
        print("📦 กำลังตรวจสอบตาราง...")
        create_tables(conn)

        
        scrapers = [
            ("Naiin", scrape_naiin_all_pages),
            ("B2S", scrape_b2s_all_pages),
            ("Jamsai", scrape_jamsai_all_pages),
            ("Seed", scrape_seed_all_pages),
            ("Amarin", scrape_amarin_all_pages),
        ]

        for name, scrape_func in scrapers:
            driver = None
            try:
                if not conn or not conn.is_connected():
                    conn = create_connection()      
                driver = get_driver()
                print(f"🔍 กำลังเริ่มดึงข้อมูลจาก: {name}")
                scrape_func(driver, conn, max_books=10)            
            except Exception as e:
                print(f"❌ Error ในร้าน {name}: {e}")
            finally:
                if driver:
                    try:
                        driver.close()
                        driver.quit()
                    except:
                        pass
                time.sleep(5)

        
        print("🔄 กำลังประมวลผลข้อมูล (Process Books)...")
        process_books(conn)
        update_history(conn)
        
        print("✅ เสร็จสมบูรณ์! ข้อมูลถูกบันทึกลง MySQL แล้ว")

    finally:
        conn.close()

if __name__ == '__main__':
    run_crawler()