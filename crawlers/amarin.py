from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def scrape_amarin_detail_page(driver):

    time.sleep(2)  # รอให้หน้ารายละเอียดโหลด

    soup = BeautifulSoup(driver.page_source, "html.parser")

    try:
        title_tag = soup.find("h1", class_="product-title product_title entry-title")
        title = normalize_text(title_tag.text) if title_tag else "Unknown"
    except:
        title = "Unknown"

    try:
        author_tag = soup.find("p", class_="product-short-description")
        author = normalize_text(author_tag.text) if author_tag else "Unknown"
    except:
        author = "Unknown"

    try:
        publisher_tag = driver.find_elements(By.XPATH, '//*[@id="product-743013"]/div/div[1]/div/div[2]/div[3]/span[3]/a')
        publisher = normalize_text(publisher_tag.text) if publisher_tag else "Amarin Publisher"
    except:
        publisher = "Amarin Publisher"

    try:
        price_tag = driver.find_elements(By.XPATH, '//*[@id="product-743013"]/div/div[1]/div/div[2]/div[2]/p/ins/span/bdi/text()')
        price = normalize_text(price_tag.text).replace(",", "") if price_tag else "0"
    except:
        price = "0"

    try:
        category_tag = driver.find_elements(By.XPATH, '//*[@id="product-743013"]/div/div[1]/div/div[2]/div[3]/span[2]/a')
        category = normalize_text(category_tag.text) if category_tag else "General"
    except:
        category = "General"

    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": int(float(price)) if price.replace(".", "").isdigit() else 0,
        "category": category,
        "url": driver.current_url,  # ลิงก์หน้ารายละเอียด
        "source": "amarin"
    }

def scrape_amarin_cards(driver):
    products = []
    main_window = driver.current_window_handle

    # ตัวอย่าง: หากต้อง scroll เพื่อให้โหลดการ์ดครบ
    # for _ in range(3):
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     time.sleep(2)

    # บันทึกหน้าเพื่อตรวจสอบโครงสร้าง
    with open("debug_amarin.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    card_elements = driver.find_elements(By.XPATH, '//*[@class="shop-container"]//p[contains(@class,"name product-title woocommerce-loop-product__title")]/a')
    print(f"[amarin] พบ {len(card_elements)} การ์ดหนังสือในหน้านี้")

    book_urls = []
    for elem in card_elements:
        url = elem.get_attribute("href")
        if url and url not in book_urls:
            book_urls.append(url)

    # เปิดแท็บใหม่ทีละลิงก์ เพื่อดึงรายละเอียด
    for index, book_url in enumerate(book_urls):
        try:
            print(f"[amarin] เปิดแท็บใหม่เพื่อดึงข้อมูลเล่มที่ {index+1}/{len(book_urls)}: {book_url}")
            driver.execute_script("window.open(arguments[0]);", book_url)
            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
            new_window = [w for w in driver.window_handles if w != main_window][0]
            driver.switch_to.window(new_window)

            # เรียกฟังก์ชันดึงข้อมูลจากหน้ารายละเอียด
            detail = scrape_amarin_detail_page(driver)
            products.append(detail)

            # ปิดแท็บใหม่ แล้วกลับมาหน้าหลัก
            driver.close()
            driver.switch_to.window(main_window)
        except Exception as e:
            print(f"[amarin] Error processing card {index+1}: {e}")
            # หากมีแท็บใหม่เปิดค้าง ให้ปิด
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            continue

    return products, driver

def scrape_amarin_all_pages(driver):
    all_products = []
    page = 1

    while page <= 100:  # กำหนดหน้าสูงสุดตามต้องการ
        print(f"[amarin] Scraping page {page} ...")

        try:
            products, driver = scrape_amarin_cards(driver)
            if not products:
                print(f"[amarin] ไม่พบข้อมูลในหน้า {page}, หยุดทำงาน")
                break
            all_products.extend(products)
        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page}: {e}")
            break

        # คลิกปุ่มถัดไป
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[3]/nav/ul/li[9]/a'))
            )
            driver.execute_script("arguments[0].click();", next_button)
            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (ไปหน้า {page+1})")
            time.sleep(3)
            page += 1
        except Exception as e:
            print("[ERROR] ไม่สามารถคลิกปุ่มถัดไป:", e)
            break

    return all_products
