from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def normalize_text(text):
    if not text:
        return ""
    return text.replace('"', '').strip()

def scrape_seed_detail_page(driver):

    time.sleep(2)  # รอให้หน้ารายละเอียดโหลด (ปรับตามความเหมาะสม)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ตัวอย่างโครงสร้างการดึงข้อมูล
    # ต้องปรับ class/selector ให้ตรงกับหน้ารายละเอียด Se-Ed ปัจจุบัน
    try:
        title_tag = soup.find("h1", class_='MuiTypography-root MuiTypography-h4 css-18oprtn')
        title = normalize_text(title_tag.text) if title_tag else "Unknown"
    except Exception:
        title = "Unknown"

    try:
        author_tag = driver.find_element(By.XPATH, '//*[@id="mpe-editor"]/div/p[1]/span[2]')
        author = normalize_text(author_tag.text) if author_tag else "Unknown"
    except Exception:
        author = "Unknown"

    try:
        publisher_tag = driver.find_element(By.XPATH, '//*[@id="mpe-editor"]/div/p[15]/span')
        publisher = normalize_text(publisher_tag.text) if publisher_tag else "Se-Ed Publisher"
    except Exception:
        publisher = "Se-Ed Publisher"

    try:
        price_tag = soup.find("span", class_='MuiTypography-root MuiTypography-h3 truncate css-muszlw')
        price = normalize_text(price_tag.text).replace(",", "") if price_tag else "0"
    except Exception:
        price = "0"

    try:
        category_tag = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div/main/main/div/div[2]/div/div[1]/a/div/span[1]')
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
        "source": "se-ed"
    }

def scrape_seed_cards(driver):

    products = []
    main_window = driver.current_window_handle

    # ตัวอย่าง: หากต้อง scroll เพื่อให้โหลดการ์ดครบ
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # บันทึกหน้าเพื่อ debug โครงสร้าง DOM
    with open("debug_seed.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    card_elements = driver.find_elements(By.XPATH, '//*[@class="flex flex-col gap-12 relative"]//div[contains(@class,"h-full css-1g7jf02")]/a')
    print(f"[se-ed] พบ {len(card_elements)} ลิงก์หนังสือในหน้านี้ (หลัง scroll)")

    book_urls = []
    for elem in card_elements:
        url = elem.get_attribute("href")
        if url and url not in book_urls:
            book_urls.append(url)

    if len(book_urls) < 1:
        print("[se-ed] ไม่พบลิงก์หนังสือในหน้านี้ หรือมีน้อยเกินไป")
        return [], driver

    # เปิดแท็บใหม่เพื่อดึงรายละเอียดทีละเล่ม
    for index, book_url in enumerate(book_urls):
        try:
            print(f"[se-ed] Processing book {index+1}/{len(book_urls)}: {book_url}")
            driver.execute_script("window.open(arguments[0]);", book_url)
            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
            new_window = [w for w in driver.window_handles if w != main_window][0]
            driver.switch_to.window(new_window)

            # ดึงรายละเอียด
            detail = scrape_seed_detail_page(driver)
            products.append(detail)

            # ปิดแท็บแล้วกลับหน้าหลัก
            driver.close()
            driver.switch_to.window(main_window)

        except Exception as e:
            print(f"[se-ed] Error processing book {index+1}: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            continue

        # รีสตาร์ท WebDriver
        # if (index + 1) % 50 == 0:
        #     print("[se-ed] Restarting WebDriver to prevent session timeout...")
        #     driver.quit()
        #     driver = start_new_driver()
        #     driver.get("https://www.se-ed.com/book-cat.book?filter.productTypes=PRODUCT_TYPE_BOOK_PHYSICAL&sorter=PRODUCT_SORTER_POPULAR")
        #     main_window = driver.current_window_handle
        #     break

    return products, driver

def scrape_seed_all_pages(driver):

    all_products = []
    page = 1

    while page <= 150:
        print(f"[se-ed] Scraping page {page} ...")

        try:
            products, driver = scrape_seed_cards(driver)
            if not products:
                print(f"[se-ed] ไม่พบข้อมูลในหน้า {page}, หยุดทำงาน")
                break
            all_products.extend(products)

        except Exception as e:
            print(f"[ERROR] ไม่สามารถดึงข้อมูลจากหน้า {page}: {e}")
            break

        # คลิกปุ่มถัดไป
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/div/main/main/div[2]/div/div[2]/div[2]/nav/ul/li[9]/button'))
            )
            driver.execute_script("arguments[0].click();", next_button)
            print(f"✅ คลิกปุ่ม 'ถัดไป' สำเร็จ (ไปหน้า {page+1})")
            time.sleep(3)
            page += 1
        except Exception as e:
            print("[ERROR] ไม่สามารถคลิกปุ่มถัดไป:", e)
            break

    return all_products
