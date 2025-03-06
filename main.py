# main.py
import time
<<<<<<< HEAD
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
=======
import crawler_naiin
import crawler_b2s
import crawler_jamsai
import crawler_amarin
import crawler_seed
import os
import mysql.connector


# ฟังก์ชันเชื่อมต่อกับ Database
def connect_to_database():
    return mysql.connector.connect(
        host=os.getenv("mysql.railway.internal"),
        user=os.getenv("root"),
        password=os.getenv("jfYnLvcFdUEEVzrvcfceFwTFuMdUBVOc"),
        database=os.getenv("MySQL"),
        port=os.getenv("3306")
    )

# ฟังก์ชันบันทึกข้อมูลลง Database
def save_to_database(cursor, books_data, source):
    for _, row in books_data.iterrows():
        cursor.execute("""
            INSERT INTO books (name, price, author, source)
            VALUES (%s, %s, %s, %s)
        """, (row['name'], row['price'], row['author'], source))
>>>>>>> a47718275b27b68f191a1fcd967733c1f0f50585

from db_service import create_connection, create_table, insert_book
from crawlers.niin import scrape_niin_all_pages
from crawlers.b2s import scrape_b2s_all_pages
from crawlers.jamsai import scrape_jamsai_all_pages
from crawlers.seed import scrape_seed_all_pages
from crawlers.amarin import scrape_amarin_all_pages

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

if __name__ == "__main__":
    conn = create_connection("books.db")
    create_table(conn)
    
    driver = get_driver()
    
    # รายการเว็บทั้ง 5 พร้อม URL เริ่มต้น (ปรับให้ตรงกับเว็บจริง)
    sites = [
        {"name": "niin", "url": "https://www.naiin.com/category?category_1_code=13&product_type_id=1"},
        {"name": "b2s", "url": "https://www.naiin.com/category?category_1_code=2&product_type_id=1"},
        {"name": "jamsai", "url": "https://www.naiin.com/category?type_book=best_seller&product_type_id=1"},
        {"name": "se-ed", "url": "https://www.naiin.com/category?type_book=new_arrival&product_type_id=1"},
        {"name": "amarin", "url": "https://www.naiin.com/category?category_1_code=2&product_type_id=1&categoryLv2Code=8"}
    ]
    
    for site in sites:
        source = site["name"]
        url = site["url"]
        print(f"\n=== ดึงข้อมูลจากเว็บ: {source} ===")
        driver.get(url)
        time.sleep(3)
        
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
        for product in products:
            insert_book(conn, product)
    
    driver.quit()
    conn.close()
    
    print("ดึงข้อมูลจากทุกเว็บและบันทึกลงฐานข้อมูลเรียบร้อย")
