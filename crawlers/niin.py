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
    return ' '.join(text.replace('"', '').strip().split())

def scrape_niin_detail_page(driver, book_url):
    """
    ดึงข้อมูลจากหน้ารายละเอียดของหนังสือแต่ละเล่ม (ปรับปรุงใหม่)
    """
    try:
        driver.get(book_url)
        # รอให้ส่วนข้อมูลหลักของสินค้าโหลดเสร็จ
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-detail-main"))
        )
    except TimeoutException:
        print(f"[niin] Timeout ขณะรอโหลดหน้ารายละเอียด: {book_url}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # --- ใช้ CSS Selector ที่เสถียรกว่าในการค้นหาข้อมูล ---
    
    # ดึงชื่อหนังสือ
    try:
        title_tag = soup.select_one("div.product-detail-main h1.name")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"
    except Exception:
        title = "Unknown"

    # ดึงชื่อผู้เขียน
    try:
        # ผู้เขียนมักจะอยู่ใน p แรกที่เป็นลิงก์ ถัดจาก h1
        author_tag = soup.select_one("div.product-detail-main p.writer a")
        author = normalize_text(author_tag.text) if author_tag else "Unknown"
    except Exception:
        author = "Unknown"

    # ดึงชื่อสำนักพิมพ์ (แก้ไขตรรกะให้ถูกต้อง)
    publisher = "Unknown"
    try:
        # หา p ที่มีข้อความ "สำนักพิมพ์" แล้วดึงข้อมูลจากลิงก์ที่อยู่ข้างใน
        publisher_p = soup.find("p", class_="publisher-wrapper")
        if publisher_p:
            publisher_a = publisher_p.find("a")
            if publisher_a:
                publisher = normalize_text(publisher_a.text)
    except Exception:
        publisher = "Unknown"

    # ดึงราคา
    price = "0"
    try:
        # ราคาส่วนลดมักจะอยู่ใน id="discount-price" หรือ class .price-discount
        price_tag = soup.select_one("#discount-price, .price-discount")
        if not price_tag:
            # ถ้่าไม่มีส่วนลด ให้หาราคาปกติใน class .price
            price_tag = soup.select_one("p.price")
            
        if price_tag:
            price_match = re.search(r'[\d,.]+', price_tag.text)
            if price_match:
                price = price_match.group(0).replace(",", "")
    except Exception:
        price = "0"
    
    # ดึงหมวดหมู่ (จาก Breadcrumb)
    category = "General"
    try:
        breadcrumb_items = soup.select("ol.breadcrumb li.breadcrumb-item a")
        # หมวดหมู่มักจะเป็นลำดับที่ 2 หรือ 3 (ข้าม "หน้าแรก")
        if len(breadcrumb_items) > 1:
            category = normalize_text(breadcrumb_items[1].text)
    except Exception:
        category = "General"
    
    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
        "category": category,
        "url": driver.current_url,
        "source": "niin"
    }

def scrape_niin_cards_on_page(driver):
    """
    ค้นหา URL ของหนังสือทั้งหมดในหน้าปัจจุบัน และวนลูปเพื่อดึงข้อมูล
    """
    products = []
    main_window = driver.current_window_handle

    # รอให้สินค้าโหลด (Lazy Loading) โดยการเลื่อนหน้าจอ 4 ครั้ง
    # อาจต้องปรับจำนวนครั้งนี้หากหน้าเว็บมีการโหลดที่แตกต่างไป
    for _ in range(4):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
    try:
        # ใช้ CSS Selector ที่แม่นยำกว่าในการหาลิงก์ของหนังสือแต่ละเล่ม
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#for-book-list div.item-cover a"))
        )
        card_elements = driver.find_elements(By.CSS_SELECTOR, "#for-book-list div.item-cover a")
        print(f"[niin] พบ {len(card_elements)} การ์ดหนังสือในหน้านี้")
    except TimeoutException:
        print("[niin] ไม่พบการ์ดหนังสือในหน้านี้")
        return [], driver

    book_urls = [elem.get_attribute("href") for elem in card_elements if elem.get_attribute("href")]

    for index, book_url in enumerate(book_urls):
        try:
            print(f"[niin] กำลังดึงข้อมูลเล่มที่ {index + 1}/{len(book_urls)}")
            # เปิดแท็บใหม่เพื่อดึงข้อมูลรายละเอียด
            driver.execute_script("window.open(arguments[0], '_blank');", book_url)
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            
            new_window = [w for w in driver.window_handles if w != main_window][0]
            driver.switch_to.window(new_window)
            
            detail = scrape_niin_detail_page(driver, book_url)
            if detail:
                products.append(detail)

        except Exception as e:
            print(f"[niin] เกิดข้อผิดพลาดในการประมวลผล URL {book_url}: {e}")
        finally:
            # รับประกันว่าแท็บจะถูกปิดและสลับกลับเสมอ
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(main_window)
    
    return products, driver

def scrape_niin_all_pages(driver, start_url, max_pages=10):
    """
    ฟังก์ชันหลักสำหรับวนลูปข้ามหน้าเพื่อดึงข้อมูลทั้งหมด
    """
    driver.get(start_url)
    all_products = []
    
    for page in range(1, max_pages + 1):
        print(f"[*] [niin] กำลัง Scraping หน้าที่ {page}...")
        
        try:
            products, driver = scrape_niin_cards_on_page(driver)
            if not products:
                print(f"[*] [niin] ไม่พบข้อมูลในหน้า {page}, สิ้นสุดการทำงาน")
                break
            all_products.extend(products)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page} ได้: {e}")
            break

        # --- ส่วนของการเปลี่ยนหน้าที่เสถียรขึ้น ---
        try:
            # หาปุ่ม "ถัดไป" จาก text ที่เป็นสัญลักษณ์ `›`
            # หมายเหตุ: หากโค้ดทำงานผิดพลาด อาจต้องเปลี่ยนไปใช้ CSS selector ที่แม่นยำกว่านี้
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "›"))
            )
            # เลื่อนหน้าจอให้ปุ่ม "ถัดไป" อยู่ในมุมมอง
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});", next_button)
            time.sleep(1) # รอเล็กน้อยหลัง scroll
            next_button.click()
            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (กำลังไปหน้า {page + 1})")

            # รอให้การ์ดหนังสือหน้าใหม่โหลดขึ้นมาอย่างน้อย 1 การ์ด
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#for-book-list div.item-cover a"))
            )

        except TimeoutException:
            print("[*] [niin] ไม่พบปุ่ม 'ถัดไป' หรือไม่พบการ์ดหนังสือในหน้าถัดไปแล้ว น่าจะเป็นหน้าสุดท้าย")
            break
        except Exception as e:
            print(f"[ERROR] ไม่สามารถคลิกปุ่ม 'ถัดไป' ได้: {e}")
            break

    print(f"\n[SUCCESS] ดึงข้อมูลจาก Naiin ทั้งหมด {len(all_products)} รายการ จาก {page} หน้า")
    return all_products