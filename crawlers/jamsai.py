from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re

def normalize_text(text):
    """ฟังก์ชันสำหรับทำความสะอาดและจัดรูปแบบข้อความ"""
    if not text:
        return ""
    # ลบช่องว่างที่ไม่จำเป็นและเครื่องหมายคำพูด
    return ' '.join(text.replace('"', '').strip().split())

def get_all_book_urls(driver, max_pages=10):
    """
    ขั้นตอนที่ 1: รวบรวม URL ของหนังสือทั้งหมดจากทุกหน้า
    """
    book_urls = set() # ใช้ set เพื่อป้องกัน URL ซ้ำ
    
    for page_number in range(1, max_pages + 1):
        url = f"https://www.jamsai.com/products/all?page={page_number}"
        print(f"[*] [jamsai] กำลังรวบรวม URL จากหน้า {page_number}...")
        driver.get(url)
        
        try:
            # รอให้การ์ดสินค้าโหลดขึ้นมา
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-card a"))
            )
            
            # ดึง element ของลิงก์ทั้งหมด
            link_elements = driver.find_elements(By.CSS_SELECTOR, "div.product-card a")
            if not link_elements:
                print(f"[*] [jamsai] ไม่พบ URL ในหน้า {page_number}, สิ้นสุดการรวบรวม")
                break
            
            for elem in link_elements:
                href = elem.get_attribute('href')
                if href:
                    book_urls.add(href)
        
        except TimeoutException:
            print(f"[ERROR] Timeout ขณะรอข้อมูลในหน้า {page_number}")
            break
        except Exception as e:
            print(f"[ERROR] เกิดข้อผิดพลาดในการรวบรวม URL: {e}")
            break
            
    print(f"[*] [jamsai] รวบรวม URL ทั้งหมดได้ {len(book_urls)} รายการ")
    return list(book_urls)

def scrape_jamsai_detail_page(driver, book_url):
    """
    ขั้นตอนที่ 2: ดึงข้อมูลจากหน้ารายละเอียดของหนังสือแต่ละเล่ม
    """
    try:
        driver.get(book_url)
        # รอให้หัวข้อหนังสือปรากฏขึ้น
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-info-title"))
        )
    except TimeoutException:
        print(f"[ERROR] ไม่สามารถโหลดหน้ารายละเอียดได้: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ดึงชื่อหนังสือ
    try:
        title_tag = soup.find("h1", class_="product-info-title")
        title = normalize_text(title_tag.text)
    except Exception:
        title = "Unknown"

    # ดึงข้อมูลผู้เขียน/ผู้แปล
    author = "Unknown"
    try:
        # ข้อมูลมักจะอยู่ใน div ที่มี class 'product-info-author'
        author_div = soup.find("div", class_="product-info-author")
        if author_div:
            author_text = normalize_text(author_div.text)
            # ลบคำว่า "ผู้เขียน/ผู้แปล :" ออกไป
            author = author_text.replace("ผู้เขียน/ผู้แปล :", "").strip()
    except Exception:
        author = "Unknown" # หากไม่พบ ให้เป็นค่าเริ่มต้น
        
    # ดึงราคา
    price = "0"
    try:
        # ราคาจะอยู่ใน span ที่มี class 'product-price-value'
        price_tag = soup.find("span", class_="product-price-value")
        if price_tag:
            price_match = re.search(r'[\d,.]+', price_tag.text)
            if price_match:
                price = price_match.group(0).replace(",", "")
    except Exception:
        price = "0"
        
    # ดึงหมวดหมู่ (จาก breadcrumb)
    category = "General"
    try:
        # Breadcrumb อยู่ใน 'ol.breadcrumb' และเรามักจะต้องการ text ของ li ตัวที่สอง
        breadcrumb_items = soup.select("ol.breadcrumb li.breadcrumb-item a")
        if len(breadcrumb_items) > 1:
            category = normalize_text(breadcrumb_items[1].text)
    except Exception:
        category = "General"

    return {
        "title": title,
        "author": author,
        "publisher": "Jamsai Publisher", # สำนักพิมพ์เป็นค่าคงที่
        "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
        "category": category,
        "url": book_url,
        "source": "jamsai"
    }

def scrape_jamsai_all_data(driver, max_pages=10):
    """
    ฟังก์ชันหลักสำหรับควบคุมการทำงานทั้งหมด
    """
    # 1. รวบรวม URL ทั้งหมดก่อน
    all_urls = get_all_book_urls(driver, max_pages)
    
    if not all_urls:
        print("[ERROR] ไม่สามารถรวบรวม URL ใดๆ ได้เลย โปรแกรมจะสิ้นสุดการทำงาน")
        return []

    all_books_data = []
    # 2. วนลูปเพื่อเข้าไปดึงข้อมูลทีละ URL
    for i, url in enumerate(all_urls):
        print(f"--- กำลังดึงข้อมูลเล่มที่ {i + 1}/{len(all_urls)} ---")
        book_data = scrape_jamsai_detail_page(driver, url)
        if book_data:
            all_books_data.append(book_data)
            print(f"✅ ดึงข้อมูลสำเร็จ: {book_data['title']}")
        
        # หน่วงเวลาเล็กน้อยเพื่อลดภาระของเซิร์ฟเวอร์
        time.sleep(1) 

    print(f"\n[SUCCESS] ดึงข้อมูลจาก Jamsai ทั้งหมด {len(all_books_data)} รายการ")
    return all_books_data