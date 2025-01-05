from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# URL สำหรับเว็บไซต์ Naiin
NAIIN_URL = 'https://www.naiin.com/'

# ตั้งค่า Chrome Options สำหรับโหมด Headless
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')  # ใช้งานในโหมด Headless
    chrome_options.add_argument('--disable-dev-shm-usage')  # แก้ปัญหา Shared Memory
    chrome_options.add_argument('--ignore-certificate-errors')  # ปิดการตรวจสอบ SSL
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--disable-web-security')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# ดึงข้อมูลหนังสือจากเว็บไซต์ Naiin
def get_books(driver):

    all_book_list = []
    all_price_list = []
    all_author_list = []

    try:
        driver.get(NAIIN_URL)

        # ค้นหาช่องค้นหาและป้อนข้อความ
        search = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/form/div[1]/input')
        search.send_keys('หนังสือ')
        search.send_keys(Keys.ENTER)

        # รอให้หน้าโหลดข้อมูล
        time.sleep(5)

        while True:
            # ดึงข้อมูล HTML จากหน้าเว็บ
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # ดึงชื่อหนังสือ
            all_book = soup.find_all('p', {'class': 'txt-normal'})
            all_book_list.extend([book.text.strip() for book in all_book])

            # ดึงราคาหนังสือ
            all_price = soup.find_all('p', {'class': 'txt-price'})
            all_price_list.extend([price.text.strip() for price in all_price])

            # ดึงชื่อผู้แต่ง
            all_author = soup.find_all('a', {'class': 'inline-block tw-whitespace-normal tw-block'})
            all_author_list.extend([author.text.strip() for author in all_author])

            # ตรวจสอบว่ามีปุ่มหน้าถัดไปหรือไม่
            try:
                next_button = driver.find_element(By.XPATH, '//a[contains(@class, "page")]')
            #    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            #    driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
            except Exception as e:
            #    print("ไม่มีหน้าถัดไปหรือเกิดข้อผิดพลาด:", e)
                break

        # ตรวจสอบความยาวของข้อมูล

        min_length = min(len(all_book_list), len(all_price_list), len(all_author_list))
        all_book_list = all_book_list[:min_length]
        all_price_list = all_price_list[:min_length]
        all_author_list = all_author_list[:min_length]

        # สร้าง DataFrame
        shop_data = pd.DataFrame({
            'name': all_book_list,
            'price': all_price_list,
            'author': all_author_list
        })

        return shop_data

    except Exception as e:
        print(f"เกิดข้อผิดพลาดระหว่างการดึงข้อมูล: {e}")
        return pd.DataFrame()  # คืนค่า DataFrame ว่างในกรณีเกิดข้อผิดพลาด

# บันทึกข้อมูลลงไฟล์ CSV
def save_to_csv(data, filename="naiin_books.csv"):
    try:
        data.to_csv(filename, index=False, encoding='utf-8')
        print(f"บันทึกข้อมูลลงไฟล์ {filename} สำเร็จ")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดระหว่างการบันทึกไฟล์: {e}")

if __name__ == "__main__":
    print("Creating driver")
    driver = get_driver()

    print("Fetching books from Naiin")
    books_data = get_books(driver)

    if not books_data.empty:
        print("Saving data to CSV")
        save_to_csv(books_data)
    else:
        print("ไม่มีข้อมูลที่จะบันทึก")

    print("Finished.")
    driver.quit()
