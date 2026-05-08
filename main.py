import ssl
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json
from decimal import Decimal
from datetime import date, datetime
from flask import Flask, jsonify, Response
from flask_cors import CORS
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
app = Flask(__name__)
CORS(app)

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

@app.route('/books', methods=['GET'])
def get_bookdetail():
    try:
        raw = get_books()
        books = []
        for row in raw:
            clean = {}
            for k, v in row.items():
                if isinstance(v, Decimal):
                    clean[k] = float(v)
                elif isinstance(v, (datetime, date)):
                    clean[k] = v.isoformat()
                elif v is None:
                    clean[k] = 0.0 if k == "price" else ""
                else:
                    clean[k] = v
            books.append(clean)

        # ใช้ ensure_ascii=False เพื่อให้แสดงภาษาไทยได้ถูกต้อง
        payload = json.dumps(books, ensure_ascii=False)

        return Response(
            payload,
            content_type='application/json; charset=utf-8',
            status=200
        )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": str(e)}), 500

def main():
    print("เริ่มระบบ crawler")
    conn = create_connection() #
    create_tables(conn) #
    limit = 50

    scrapers = [
        ("Naiin", scrape_naiin_all_pages),
        ("B2S", scrape_b2s_all_pages),
        ("Jansai", scrape_jamsai_all_pages),
        ("Seed", scrape_seed_all_pages),
        ("Amarin", scrape_amarin_all_pages),
    ]

    for name, scrape_func in scrapers:
        driver = None
        try:
            print(f"กำลังเริ่มดึงข้อมูลจาก: {name}")
            driver = get_driver() # เปิดใหม่ทุกร้าน
            scrape_func(driver, conn, max_books=limit) # ส่งค่า limit เข้าไป
        except Exception as e:
            print(f"เกิดข้อผิดพลาดที่ร้าน {name}: {e}")
        finally:
            if driver:
                driver.quit() # ปิดทันทีเพื่อคืน RAM

    process_books(conn)
    update_history(conn)
    conn.close()

if __name__ == "__main__":
    print("🚀 กำลังเตรียมระบบ...")
    conn = create_connection()
    if conn:
        create_tables(conn)  # สร้างตาราง
        conn.close()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)