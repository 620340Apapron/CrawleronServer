# jamsai.py
import time, re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from db_service import insert_book

def normalize_text(txt):
    if not txt:
        return ""
    return ' '.join(txt.replace('"', '').strip().split())

def scrape_jamsai_detail_page(driver, book_url):
    driver.get(book_url)
    try:
        # 1. เปลี่ยนจากรอ h1 เป็นรอแท็ก script ที่มีข้อมูล JSON แทน (โหลดเร็วและชัวร์กว่า)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )
    except TimeoutException:
        print(f"[*] [jamsai] Timeout: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    try:
        # 2. ดึงก้อน JSON ออกมา (ก้อนเดียวจบ ไม่ต้องหาแท็บอื่น)
        json_tag = soup.find('script', id='__NEXT_DATA__')
        if not json_tag: return None
        
        js_data = json.loads(json_tag.string)
        product = js_data['props']['pageProps']['product']

        # 3. แมพข้อมูลจาก JSON เข้า Dictionary (สะอาดและแม่นยำ)
        return {
            "isbn": product.get('skuid', 'Unknown'), # ISBN อยู่ตรงนี้
            "title": normalize_text(product.get('display_name')),
            "author": product['writers'][0]['name'] if product.get('writers') else "Unknown",
            "publisher": product['brands'][0]['name'] if product.get('brands') else "Jamsai",
            "price": int(product.get('special_price', 0)), # ราคาขายจริง
            "url": book_url,
            "source": "jamsai"
        }
    except Exception as e:
        print(f"[!] Error แกะ JSON บน {book_url}: {e}")
        return None

def get_all_book_urls(driver, max_pages=999):
    urls = set()
    # เปลี่ยน URL หน้ารวมสินค้า
    base_url = "https://www.jamsai.com/shop"
    
    for p in range(1, max_pages + 1):
        print(f"[*] [jamsai] กำลังรวบรวม URL จากหน้า {p}...")
        
        try:
            driver.get(f"{base_url}{p}")
        except TimeoutException:
            print(f"[*] [jamsai] ไม่พบข้อมูลในหน้า {p}, สิ้นสุดการทำงาน")
            break

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "/html/body/div/div/div/section[2]/div/div/div[2]/div/div[2]/div/div/div/div[1]/div/div[2]/h3/a"))
            )
        except TimeoutException:
                print(f"[*] [naiin] ไม่มีสินค้าในหน้า {p}, จบหมวดนี้")
                break
        
        links = driver.find_elements(By.XPATH, "/html/body/div/div/div/section[2]/div/div/div[2]/div/div[2]/div/div/div/div[1]/div/div[2]/h3/a")
        for link in links:
            href = link.get_attribute("href")
            if href and "product" in href:
                urls.add(href)
    return list(urls)

def scrape_jamsai_all_pages(driver, conn, max_pages=999):
    all_products = []
    
    all_urls = get_all_book_urls(driver, max_pages)

    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_jamsai_detail_page(driver, url)
        if book_data:
           insert_book(conn, book_data)

    return 