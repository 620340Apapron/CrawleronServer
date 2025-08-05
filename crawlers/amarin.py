from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

def normalize_text(text):
    """ฟังก์ชันสำหรับทำความสะอาดและจัดรูปแบบข้อความ"""
    if not text:
        return ""
    # ลบช่องว่างที่ไม่จำเป็นและเครื่องหมายคำพูด
    return ' '.join(text.replace('"', '').strip().split())

def scrape_amarin_detail_page(driver):
    """
    ฟังก์ชันสำหรับดึงข้อมูลจากหน้ารายละเอียดของหนังสือแต่ละเล่ม
    """
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # --- ใช้ CSS Selector ที่เสถียรกว่าในการค้นหาข้อมูล ---

    # ดึงชื่อหนังสือ
    try:
        title_tag = soup.find("h1", class_="product_title")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"
    except Exception:
        title = "Unknown"

    # ดึงชื่อผู้เขียน
    try:
        # ผู้เขียนมักจะอยู่ใน <p> ที่มี class 'product-short-description'
        author_tag = soup.find("div", class_="product-short-description")
        author = normalize_text(author_tag.p.text) if author_tag and author_tag.p else "Unknown"
    except Exception:
        author = "Unknown"

    # ดึงชื่อสำนักพิมพ์
    try:
        # สำนักพิมพ์อยู่ใน span ที่มี class 'posted_in'
        publisher_tag = soup.find("span", class_="brand")
        publisher = normalize_text(publisher_tag.a.text) if publisher_tag and publisher_tag.a else "Amarin Publisher"
    except Exception:
        publisher = "Amarin Publisher"

    # ดึงราคา
    price = "0"
    try:
        # ลองหาป้ายราคาลดก่อน (ins)
        price_tag = soup.select_one(".price-wrapper .price ins .woocommerce-Price-amount bdi")
        if not price_tag:
            # ถ้าไม่มีราคาลด ให้หาราคาปกติ
            price_tag = soup.select_one(".price-wrapper .price .woocommerce-Price-amount bdi")
        
        if price_tag:
            # ลบสัญลักษณ์สกุลเงินและคอมมา
            price = normalize_text(price_tag.text).replace("฿", "").replace(",", "")

    except Exception:
        price = "0"

    # ดึงหมวดหมู่
    try:
        category_tag = soup.find("span", class_="posted_in")
        category = normalize_text(category_tag.a.text) if category_tag and category_tag.a else "General"
    except Exception:
        category = "General"

    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
        "category": category,
        "url": driver.current_url,
        "source": "amarin"
    }

def scrape_amarin_cards_on_page(driver):
    """
    ฟังก์ชันสำหรับค้นหา URL ของหนังสือทั้งหมดในหน้าปัจจุบัน และเข้าไปดึงข้อมูลทีละเล่ม
    """
    products = []
    main_window = driver.current_window_handle

    # รอให้การ์ดสินค้าโหลดจนครบ
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".shop-container .product-title a"))
        )
    except TimeoutException:
        print("[amarin] ไม่พบการ์ดหนังสือในหน้านี้หลังจากรอ 15 วินาที")
        return [], driver

    # ใช้ CSS Selector เพื่อหาลิงก์ของหนังสือทั้งหมดในการ์ด
    card_elements = driver.find_elements(By.CSS_SELECTOR, ".shop-container .product-title a")
    print(f"[amarin] พบ {len(card_elements)} การ์ดหนังสือในหน้านี้")

    book_urls = [elem.get_attribute("href") for elem in card_elements if elem.get_attribute("href")]

    # วนลูปเพื่อเปิดลิงก์ในแท็บใหม่และดึงข้อมูล
    for index, book_url in enumerate(book_urls):
        try:
            print(f"[amarin] กำลังดึงข้อมูลเล่มที่ {index + 1}/{len(book_urls)}: {book_url}")
            driver.execute_script("window.open(arguments[0], '_blank');", book_url)
            
            # รอให้มีแท็บใหม่เปิดขึ้นมา
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            
            # สลับไปทำงานในแท็บใหม่
            new_window = [w for w in driver.window_handles if w != main_window][0]
            driver.switch_to.window(new_window)

            # รอให้ title ของหน้าใหม่โหลดเสร็จ (เป็นสัญญาณว่าหน้าพร้อม)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product_title")))

            # เรียกฟังก์ชันดึงข้อมูล
            detail = scrape_amarin_detail_page(driver)
            products.append(detail)

        except Exception as e:
            print(f"[amarin] เกิดข้อผิดพลาดในการประมวลผล URL {book_url}: {e}")
        finally:
            # ปิดแท็บปัจจุบันและสลับกลับไปหน้าหลักเสมอ
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(main_window)

    return products, driver

def scrape_amarin_all_pages(driver, max_pages=10):
    """
    ฟังก์ชันหลักสำหรับวนลูปข้ามหน้าเพื่อดึงข้อมูลทั้งหมด
    """
    all_products = []
    page = 1

    while page <= max_pages:
        print(f"[*] [amarin] กำลัง Scraping หน้าที่ {page}...")

        try:
            products, driver = scrape_amarin_cards_on_page(driver)
            if not products:
                print(f"[*] [amarin] ไม่พบข้อมูลในหน้า {page}, สิ้นสุดการทำงาน")
                break
            all_products.extend(products)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page} ได้: {e}")
            break

        # --- ส่วนของการเปลี่ยนหน้า (Pagination) ---
        try:
            # หาปุ่ม "Next" โดยใช้ class และสัญลักษณ์ (มีความเสถียรกว่าการอิงตำแหน่ง li)
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next.page-numbers"))
            )
            driver.execute_script("arguments[0].click();", next_button)
            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (กำลังไปหน้า {page + 1})")
            
            # รอสักครู่เพื่อให้หน้าใหม่โหลดข้อมูล
            time.sleep(3) 
            page += 1
        except TimeoutException:
            print("[*] [amarin] ไม่พบปุ่ม 'ถัดไป' แล้ว น่าจะเป็นหน้าสุดท้าย")
            break
        except Exception as e:
            print(f"[ERROR] ไม่สามารถคลิกปุ่ม 'ถัดไป' ได้: {e}")
            break

    print(f"\n[SUCCESS] ดึงข้อมูลจาก Amarin ทั้งหมด {len(all_products)} รายการ จาก {page-1} หน้า")
    return all_products