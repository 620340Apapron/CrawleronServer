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

def _get_detail_by_label(driver, label_text):
    """
    ฟังก์ชันผู้ช่วย: ค้นหาข้อมูลจาก Label (เช่น "ผู้เขียน:", "สำนักพิมพ์:")
    ซึ่งเป็นวิธีที่เสถียรกว่าการใช้ XPath แบบเต็ม
    """
    try:
        # หา p tag ที่มีข้อความของ label และดึงข้อมูลจาก a tag ที่อยู่ถัดไป
        # ตัวอย่าง XPath: //p[contains(text(),'ผู้เขียน')]/following-sibling::a
        element = driver.find_element(By.XPATH, f"//p[contains(text(),'{label_text}')]/following-sibling::div//a")
        return normalize_text(element.text)
    except NoSuchElementException:
        # ลองหาแบบที่ไม่มี a tag
        try:
            element = driver.find_element(By.XPATH, f"//p[contains(text(),'{label_text}')]/following-sibling::div")
            return normalize_text(element.text)
        except NoSuchElementException:
            return "Unknown"

def scrape_b2s_detail(driver):
    """ ดึงข้อมูลจากหน้ารายละเอียดของหนังสือ (detail page) """
    try:
        # รอให้หัวข้อสินค้าโหลดเสร็จ ซึ่งเป็นสัญญาณว่าหน้าพร้อมแล้ว
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.title"))
        )
    except TimeoutException:
        print("[b2s] หน้ารายละเอียดใช้เวลาโหลดนานเกินไป หรือไม่พบหัวข้อสินค้า")
        return None # คืนค่า None เพื่อบอกให้รู้ว่าหน้านี้มีปัญหา

    # --- ใช้ CSS Selector และ XPath ที่เสถียรกว่าในการค้นหาข้อมูล ---
    
    # ดึงชื่อหนังสือ
    try:
        title_tag = driver.find_element(By.CSS_SELECTOR, "h1.title")
        title = normalize_text(title_tag.text)
    except NoSuchElementException:
        title = "Unknown"

    # ดึงชื่อผู้เขียน, สำนักพิมพ์, และหมวดหมู่โดยใช้ฟังก์ชันผู้ช่วย
    author = _get_detail_by_label(driver, "ผู้เขียน")
    publisher = _get_detail_by_label(driver, "สำนักพิมพ์")
    category = _get_detail_by_label(driver, "หมวดหมู่")
    
    # ดึงราคา
    price = "0"
    try:
        # ลองหาราคาลดก่อน (มี class -special)
        price_tag = driver.find_element(By.CSS_SELECTOR, ".price.-special")
    except NoSuchElementException:
        # ถ้าไม่มี ให้หาราคาปกติ
        try:
            price_tag = driver.find_element(By.CSS_SELECTOR, ".product-price-box .price")
        except NoSuchElementException:
            price_tag = None

    if price_tag:
        # ใช้ re.search เพื่อหาตัวเลขและจุดทศนิยม
        price_match = re.search(r'[\d,.]+', price_tag.text)
        if price_match:
            price = price_match.group(0).replace(",", "")

    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
        "category": category,
        "url": driver.current_url,
        "source": "b2s"
    }

def scrape_b2s_cards_on_page(driver):
    """ ค้นหา URL ของหนังสือทั้งหมดในหน้าปัจจุบัน และดึงข้อมูลทีละเล่ม """
    products = []
    main_window = driver.current_window_handle

    # เลื่อนหน้าจอลงเพื่อโหลดสินค้าทั้งหมด (Lazy Loading)
    for i in range(4): # เพิ่มการ scroll เพื่อความแน่นอน
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    # ใช้ CSS Selector ที่แม่นยำเพื่อหาลิงก์ของสินค้า
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-item-title-link"))
        )
        card_elements = driver.find_elements(By.CSS_SELECTOR, "a.product-item-title-link")
        print(f"[b2s] พบ {len(card_elements)} การ์ดหนังสือในหน้านี้")
    except TimeoutException:
        print("[b2s] ไม่พบการ์ดหนังสือในหน้านี้")
        return [], driver

    book_urls = [elem.get_attribute("href") for elem in card_elements if elem.get_attribute("href")]

    # วนลูปเพื่อเปิดลิงก์ในแท็บใหม่และดึงข้อมูล
    for index, book_url in enumerate(book_urls):
        try:
            print(f"[b2s] กำลังดึงข้อมูลเล่มที่ {index + 1}/{len(book_urls)}: {book_url}")
            driver.execute_script("window.open(arguments[0], '_blank');", book_url)
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            
            new_window = [w for w in driver.window_handles if w != main_window][0]
            driver.switch_to.window(new_window)
            
            detail = scrape_b2s_detail(driver)
            if detail: # ตรวจสอบว่าได้ข้อมูลกลับมาหรือไม่
                products.append(detail)

        except Exception as e:
            print(f"[b2s] เกิดข้อผิดพลาดในการประมวลผล URL {book_url}: {e}")
        finally:
            # ใช้ finally เพื่อให้แน่ใจว่าแท็บจะถูกปิดและสลับกลับเสมอ
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(main_window)
            
    return products, driver

def scrape_b2s_all_pages(driver, max_pages=10):
    """ ฟังก์ชันหลักสำหรับวนลูปข้ามหน้าเพื่อดึงข้อมูลทั้งหมด """
    all_products = []
    page = 1

    while page <= max_pages:
        print(f"[*] [b2s] กำลัง Scraping หน้าที่ {page}...")
        
        try:
            products, driver = scrape_b2s_cards_on_page(driver)
            if not products:
                print(f"[*] [b2s] ไม่พบข้อมูลในหน้า {page}, สิ้นสุดการทำงาน")
                break
            all_products.extend(products)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page} ได้: {e}")
            break

        # --- ส่วนของการเปลี่ยนหน้า (Pagination) ที่เสถียรขึ้น ---
        try:
            # หาปุ่ม 'ถัดไป' จาก class ของ li ที่ครอบมันอยู่
            next_button_li = driver.find_element(By.CSS_SELECTOR, "li.pagination-next")
            
            # ตรวจสอบว่าปุ่มไม่ได้ถูกปิดการใช้งาน (disabled)
            if "disabled" in next_button_li.get_attribute("class"):
                print("[*] [b2s] ไม่พบปุ่ม 'ถัดไป' ที่ใช้งานได้ (หน้าสุดท้าย)")
                break

            next_button = next_button_li.find_element(By.TAG_NAME, "button")
            driver.execute_script("arguments[0].click();", next_button)
            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (กำลังไปหน้า {page + 1})")
            
            time.sleep(3) # รอให้หน้าใหม่โหลด
            page += 1
        except NoSuchElementException:
            print("[*] [b2s] ไม่พบปุ่ม 'ถัดไป' แล้ว น่าจะเป็นหน้าสุดท้าย")
            break
        except Exception as e:
            print(f"[ERROR] ไม่สามารถคลิกปุ่ม 'ถัดไป' ได้: {e}")
            break

    print(f"\n[SUCCESS] ดึงข้อมูลจาก B2S ทั้งหมด {len(all_products)} รายการ จาก {page-1} หน้า")
    return all_products