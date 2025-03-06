from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
<<<<<<< HEAD
from webdriver_manager.chrome import ChromeDriverManager
import time
=======
#from webdriver_manager.chrome import ChromeDriverManager  # ต้องเพิ่มส่วนนี้สำหรับ WebDriverManager
>>>>>>> a47718275b27b68f191a1fcd967733c1f0f50585

NAIIN_URL = "https://www.naiin.com/"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
<<<<<<< HEAD
    chrome_options.add_argument('--headless')  # ทำงานแบบไม่แสดง UI
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def scrape_detail_page(driver):
    """
    ฟังก์ชันนี้จะดึงข้อมูลจากหน้ารายละเอียดของหนังสือ
    เช่น รูป, ชื่อหนังสือ, ผู้แต่ง, สำนักพิมพ์, ราคา, หมวดหมู่ ฯลฯ
    ต้องปรับตามโครงสร้างจริงของหน้า Naiin
    """
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # ตัวอย่างโครงสร้างสมมุติ (ปรับให้ตรงกับหน้า Naiin)
    # รูปหนังสือ (img)
    img_tag = soup.find("img", {"class": "img-relative"})
    image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

    # ชื่อหนังสือ
    title_tag = soup.find("h1", {"class": "title-topic"})
    title = title_tag.get_text(strip=True) if title_tag else ""

    # ผู้แต่ง
    author_tag = soup.find("span", {"class": "inline-block link-book-detail"})
    author = author_tag.get_text(strip=True) if author_tag else ""

    # สำนักพิมพ์
    pub_tag = soup.find("span", {"class": "inline-block link-book-detail"})
    publisher = pub_tag.get_text(strip=True) if pub_tag else ""

    # ราคา
    price_tag = soup.find("span", {"class": "price"})
    price = price_tag.get_text(strip=True) if price_tag else ""

    # หมวดหมู่
    category_tag = soup.find("span", {"class": "inline-block link-book-detail"})
    category = category_tag.get_text(strip=True) if category_tag else ""

    # หรือถ้ามีรายละเอียดอื่น ๆ ก็เพิ่มการดึงข้อมูลได้

    return {
        "image": image_url,
        "title": title,
        "author": author,
        "publisher": publisher,
        "price": price,
        "category": category
    }

def get_all_books(driver):

    all_data = []
    page_number = 1

    while True:
        print(f"กำลังดึงข้อมูลจากหน้าที่ {page_number}...")
        time.sleep(3)  # รอให้หน้าปัจจุบันโหลดเสร็จ

        # หา element ของ "การ์ดหนังสือ" แต่ละเล่ม
        # สมมุติว่าแต่ละเล่มอยู่ใน div ที่มี class 'product-item'
        product_items = driver.find_elements(By.CLASS_NAME, "productitem item")
        if not product_items:
            print("ไม่พบรายการหนังสือในหน้านี้ หรือดึงข้อมูลไม่สำเร็จ")
            break

        for index, item in enumerate(product_items, start=1):
            try:
                # คลิกเพื่อเข้าไปดูรายละเอียดเล่ม
                print(f"  -> คลิกเล่มที่ {index}")
                item.click()
                time.sleep(3)  # รอให้หน้าโหลด

                # ดึงข้อมูลจากหน้ารายละเอียด
                detail_data = scrape_detail_page(driver)
                all_data.append(detail_data)

                # กลับมาหน้ารายการ
                driver.back()
                time.sleep(3)  # รอให้หน้ารายการโหลด
            except Exception as e:
                print(f"    [!] เกิดข้อผิดพลาดขณะคลิกเล่มที่ {index}: {e}")
                # พยายามกลับหน้ารายการ (ป้องกันไม่ให้ค้าง)
                driver.back()
                time.sleep(3)
                continue

        # เมื่อคลิกครบทุกเล่มในหน้านี้แล้ว ลองกดปุ่มถัดไป
        try:
            print("  -> กำลังคลิกปุ่มถัดไป...")
            # ปรับ XPATH ของปุ่มถัดไปให้ตรงกับเว็บจริง เช่น:
            # "//a[contains(text(),'ถัดไป')]"
            # หรือ "/html/body/div[1]/div[2]/div/div/div/div[3]/div[2]/div[1]/div/div[3]/ul/li[7]/a"
            next_button = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[3]/ul/li[15]/a")
            next_button.click()
            page_number += 1
        except Exception as e:
            print("ไม่มีหน้าถัดไปหรือเกิดข้อผิดพลาด:", e)
            break

    # สร้าง DataFrame จาก all_data
    df = pd.DataFrame(all_data)
    return df
=======
    chrome_options.add_argument('--headless')  # ใช้งานในโหมด Headless
    chrome_options.add_argument('--disable-dev-shm-usage')  # แก้ปัญหา Shared Memory
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ดึงข้อมูลหนังสือจากเว็บไซต์ Naiin
def get_books(driver):
    try:
        driver.get(NAIIN_URL)

        # ค้นหาช่องค้นหาและป้อนข้อความ
        search = driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/form/div[1]/input'
        )
        search.send_keys('หนังสือ')
        search.send_keys(Keys.ENTER)

        # รอให้หน้าโหลดข้อมูล
        driver.implicitly_wait(10)

        # ดึงข้อมูล HTML จากหน้าเว็บ
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ดึงชื่อหนังสือ
        all_book = soup.find_all('p', {'class': 'txt-normal'})
        all_book_list = [book.text.strip() for book in all_book]

        # ดึงราคาหนังสือ
        all_price = soup.find_all('p', {'class': 'txt-price'})
        all_price_list = [price.text.strip() for price in all_price]

        # ดึงชื่อผู้แต่ง
        all_author = soup.find_all('a', {'class': 'inline-block tw-whitespace-normal tw-block'})
        all_author_list = [author.text.strip() for author in all_author]
>>>>>>> a47718275b27b68f191a1fcd967733c1f0f50585

def save_to_csv(data, filename="naiin_books.csv"):
    try:
        data.to_csv(filename, index=False, encoding='utf-8')
        print(f"บันทึกข้อมูลลงไฟล์ {filename} สำเร็จ")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดระหว่างการบันทึกไฟล์: {e}")

if __name__ == "__main__":
    print("กำลังสร้าง driver")
    driver = get_driver()

    try:
        print("เปิดเว็บไซต์ Naiin")
        driver.get(NAIIN_URL)
        time.sleep(3)  # รอให้หน้าเว็บโหลด

        # ค้นหาช่องค้นหาและป้อนข้อความ "นิยาย" (หรือ "หนังสือ" ตามต้องการ)
        search = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/form/div[1]/input')
        search.send_keys('นิยาย')
        search.send_keys(Keys.ENTER)
        time.sleep(3)  # รอให้หน้าผลลัพธ์โหลด

        print("กำลังดึงข้อมูลหนังสือจากทุกหน้า (คลิกเข้าทีละเล่ม)")
        books_data = get_all_books(driver)

        if not books_data.empty:
            print("กำลังบันทึกข้อมูลลง CSV")
            save_to_csv(books_data, "naiin_books_detail.csv")
        else:
            print("ไม่มีข้อมูลที่จะบันทึก")

    except Exception as ex:
        print("เกิดข้อผิดพลาดในโปรแกรมหลัก:", ex)

    finally:
        print("จบการทำงาน")
        driver.quit()
