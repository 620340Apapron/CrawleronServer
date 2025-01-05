from bs4 import BeautifulSoup
#import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
#from webdriver_manager.chrome import ChromeDriverManager  # ต้องเพิ่มส่วนนี้สำหรับ WebDriverManager

# URL สำหรับเว็บไซต์ B2S
B2S_URL = 'https://www.b2s.co.th/'

# ตั้งค่า Chrome Options สำหรับโหมด Headless
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')  # ใช้งานในโหมด Headless
    chrome_options.add_argument('--disable-dev-shm-usage')  # แก้ปัญหา Shared Memory
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ดึงข้อมูลหนังสือจากเว็บไซต์ B2S
def get_books(driver):
    try:
        driver.get(B2S_URL)

        # ค้นหาช่องค้นหาและป้อนข้อความ
        search = driver.find_element(By.XPATH,'/html/body/div[1]/div/div/nav/div[3]/div/div/input'
        )
        search.send_keys('หนังสือ')
        search.send_keys(Keys.ENTER)

        # รอให้หน้าโหลดข้อมูล
        driver.implicitly_wait(10)

        # ดึงข้อมูล HTML จากหน้าเว็บ
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ดึงชื่อหนังสือ
        all_book = soup.find_all('h3', {'class': 'pointer'})
        all_book_list = [book.text.strip() for book in all_book]

        # ดึงราคาหนังสือ
        all_price = soup.find_all('div', {'class': 'product-price'})
        all_price_list = [price.text.strip() for price in all_price]

        # ดึงชื่อผู้แต่ง
        all_author = soup.find_all('a', {'class': 'inline-block tw-whitespace-normal tw-block'})
        all_author_list = [author.text.strip() for author in all_author]

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
def save_to_csv(data, filename="B2S_books.csv"):
    try:
        data.to_csv(filename, index=False, encoding='utf-8')
        print(f"บันทึกข้อมูลลงไฟล์ {filename} สำเร็จ")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดระหว่างการบันทึกไฟล์: {e}")

if __name__ == "__main__":
    print("Creating driver")
    driver = get_driver()

    print("Fetching books from B2S")
    books_data = get_books(driver)

    if not books_data.empty:
        print("Saving data to CSV")
        save_to_csv(books_data)
    else:
        print("ไม่มีข้อมูลที่จะบันทึก")

    print("Finished.")
    driver.quit()
