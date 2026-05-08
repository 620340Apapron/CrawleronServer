import ssl
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json
from decimal import Decimal
from datetime import date, datetime
from dotenv import load_dotenv

from db_service import create_connection, create_tables
from book_history import update_history
from process_books import process_books
from db_service import get_books

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
    
    options.add_argument("--blink-settings=imagesEnabled=false") # ไม่โหลดรูปภาพ
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.page_load_strategy = 'eager' # โหลดเฉพาะ HTML ไม่ต้องรอ script อื่นๆ
    
    path = shutil.which("chromium") or shutil.which("chromium-browser")
    if path:
        options.binary_location = path
        
    return webdriver.Chrome(options=options)
    
def run_crawler_standalone():
    print("🚀 เริ่มระบบ Crawler (Standalone Mode)")
    conn = create_connection()
    if not conn:
        print("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
        return

    try:
        # 1. เตรียมตาราง
        create_tables(conn)

        # 2. เริ่มดึงข้อมูล
        scrapers = [
            ("Naiin", scrape_naiin_all_pages),
            ("B2S", scrape_b2s_all_pages),
            ("Jamsai", scrape_jamsai_all_pages),
            ("Seed", scrape_seed_all_pages),
            ("Amarin", scrape_amarin_all_pages),
        ]

        for name, scrape_func in scrapers:
            driver = get_driver()
            try:
                print(f"กำลังดึงข้อมูลจาก: {name}...")
                scrape_func(driver, conn, max_books=20)
            except Exception as e:
                print(f"❌ Error scraping {name}: {e}")
            finally:
                if driver:
                    driver.quit()

        # 3. ย้ายข้อมูลจาก raw_books -> books
        print("📦 กำลังย้ายข้อมูลและอัปเดตประวัติราคา...")
        process_books(conn)
        update_history(conn)
        
        print("✅ ดึงข้อมูลเสร็จสมบูรณ์ 100%!")

    finally:
        conn.close()
def main():
    conn = create_connection()
    if not conn: return
    
    create_tables(conn) # ตรวจสอบ/สร้างตาราง
    
    scrapers = [
        ("Naiin", scrape_naiin_all_pages),
        ("B2S", scrape_b2s_all_pages),
        ("Jamsai", scrape_jamsai_all_pages),
        ("Seed", scrape_seed_all_pages),
        ("Amarin", scrape_amarin_all_pages),
    ]

    for name, scrape_func in scrapers:
        driver = get_driver()
        try:
            print(f"กำลังดึงข้อมูลจาก: {name}")
            scrape_func(driver, conn, max_books=20)
        except Exception as e:
            print(f"Error scraping {name}: {e}")
        finally:
            if driver: driver.quit()

    print("กำลังย้ายข้อมูลไปตารางหลัก...")
    process_books(conn)   
    update_history(conn)

if __name__ == '__main__':
    conn = create_connection()
    if conn:
        create_tables(conn)
        conn.close()

   