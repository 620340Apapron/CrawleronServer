import time
import ssl
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fix_mysql import run_emergency_fix

# ฟังก์ชันจัดการฐานข้อมูล
from db_service import create_connection, create_tables
from book_history import update_history

# Scrapers
from crawlers.amarin import scrape_amarin_all_pages
from crawlers.b2s import scrape_b2s_all_pages
from crawlers.jamsai import scrape_jamsai_all_pages
from crawlers.niin import scrape_naiin_all_pages
from crawlers.seed import scrape_seed_all_pages 

ssl._create_default_https_context = ssl._create_unverified_context

def get_driver():
    """ตั้งค่า Chrome Driver ให้ทำงานบน Server (Headless)"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    run_emergency_fix() 
    # เชื่อมต่อฐานข้อมูล
    conn = create_connection()
    if conn is None:
        print("[ERROR] ไม่สามารถเชื่อมต่อ MySQL ได้ ตรวจสอบ Variables บน Railway")
        return

    # เตรียมตาราง
    create_tables(conn)

    # เปิด Browser
    driver = get_driver()
    
    # รายการเว็บที่จะไปดึง
    sites = [
        {"name": "niin", "scraper": scrape_naiin_all_pages},
        {"name": "se-ed", "scraper": scrape_seed_all_pages},
        {"name": "jamsai", "scraper": scrape_jamsai_all_pages},
        {"name": "b2s", "scraper": scrape_b2s_all_pages},
        {"name": "amarin", "scraper": scrape_amarin_all_pages},
    ]

    max_pages_to_scrape = 100

    for site in sites:
        source = site['name']
        scraper_func = site['scraper']
        
        print(f"\n🚀 เริ่มดึงข้อมูลจาก: {source.upper()}")
        try:
            scraper_func(driver, conn, max_pages=max_pages_to_scrape)
        except Exception as e:
            print(f"[ERROR] เว็บ {source} เกิดปัญหา: {e}")
            continue

    print("\n📊 กำลังวิเคราะห์ข้อมูลและอัปเดตประวัติราคา (update_history)...")
    update_history(conn)

    print("\n✨ ภารกิจเสร็จสิ้น! ข้อมูลถูกเก็บลง Database และรูปถูกส่งไป Supabase แล้ว")
    
    driver.quit()
    conn.close()

if __name__ == "__main__":
    main()