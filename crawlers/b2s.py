from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def scrape_b2s_detail(driver):
    """ ดึงข้อมูลจากหน้ารายละเอียดของหนังสือ (detail page) """
    time.sleep(2)  # รอให้หน้ารายละเอียดโหลด (ปรับได้ตามความเหมาะสม)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    try:
        title_tag = soup.find("h1", class_="title mb-2 fw-bold fs-24")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"
    except Exception:
        title = "Unknown"
    
    try:
        author_tag = driver.find_element(By.XPATH, '//*[@id="__layout"]/div/div[3]/div/div[2]/div/div[1]/div/div[1]/div[2]/div/h1')
        author = normalize_text(author_tag.text) if author_tag else "Unknown"
    except Exception:
        author = "Unknown"
    
    try:
        publisher_tag = driver.find_element(By.XPATH, '//*[@id="__layout"]/div/div[3]/div/div[2]/div/div[1]/div/div[1]/div[2]/div/div[3]/div[1]/a/span')
        publisher = normalize_text(publisher_tag.text) if publisher_tag else "Unknown"
    except Exception:
        publisher = "Unknown"
    
    try:
        price_tag = driver.find_element(By.XPATH, '//*[@id="__layout"]/div/div[3]/div/div[2]/div/div[1]/div/div[1]/div[2]/div/div[6]/label')
        price = normalize_text(price_tag.text).replace(",", "") if price_tag else "0"
    except Exception:
        price = "0"
    
    try:
        category_tag = driver.find_element(By.XPATH, '//*[@id="__layout"]/div/div[3]/div/div[2]/div/div[1]/div/div[1]/div[3]/div/div/p[2]/span/text()[3]')
        category = normalize_text(category_tag.text) if category_tag else "General"
    except Exception:
        category = "General"
    
    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
        "category": category,
        "url": driver.current_url,
        "source": "b2s"
    }

def scrape_b2s_cards(driver):
    products = []
    main_window = driver.current_window_handle

    # เลื่อนหน้าจอหลายครั้งเพื่อกระตุ้นให้โหลดการ์ดครบ
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    with open("debug_b2s.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    # ใช้ XPATH แบบกว้างเพื่อดึงลิงก์จากการ์ด               
    card_elements = driver.find_elements(By.XPATH, '//*[@class="product-result"]//div[contains(@class,"media-item-top")]//a')
    print(f"[b2s] พบ {len(card_elements)} ลิงก์หนังสือในหน้านี้ (หลัง scroll)")
    
    book_urls = []
    for elem in card_elements:
        url = elem.get_attribute("href")
        if url and url not in book_urls:
            book_urls.append(url)
    
    if len(book_urls) < 2:
        print("[b2s] ไม่พบลิงก์หนังสือครบตามที่คาด กรุณาตรวจสอบ debug_b2s.html และปรับ XPATH ให้ตรงกับ DOM")
        return [], driver

    for index, book_url in enumerate(book_urls):
        try:
            print(f"[b2s] Processing book {index+1}/{len(book_urls)}: {book_url}")
            # เปิดลิงก์หนังสือในแท็บใหม่
            driver.execute_script("window.open(arguments[0]);", book_url)
            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
            new_window = [w for w in driver.window_handles if w != main_window][0]
            driver.switch_to.window(new_window)
            
            # รอให้รายละเอียดโหลด จากนั้นดึงข้อมูล
            time.sleep(2)
            detail = scrape_b2s_detail(driver)
            products.append(detail)
            
            driver.close()
            driver.switch_to.window(main_window)
        except Exception as e:
            print(f"[b2s] Error processing book {index+1}: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            continue
    
    return products, driver

def scrape_b2s_all_pages(driver):
    all_products = []
    page = 1

    while page <= 175:
        print(f"[b2s] Scraping page {page} ...")
        try:
            products, driver = scrape_b2s_cards(driver)
            if not products:
                print(f"[b2s] ไม่พบข้อมูลในหน้า {page}, หยุดทำงาน")
                break
            all_products.extend(products)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page}: {e}")
            break

        # คลิกปุ่ม 'ถัดไป'
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="__layout"]/div/div[3]/div/div[4]/div[2]/div[3]/div/div/ul/li[8]/button'))
            )
            driver.execute_script("arguments[0].click();", next_button)
            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (ไปหน้า {page+1})")
            time.sleep(3)
            page += 1
        except Exception as e:
            print("[ERROR] ไม่สามารถคลิกปุ่มถัดไป:", e)
            break

    return all_products
