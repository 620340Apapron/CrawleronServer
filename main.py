import ssl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from db_service import create_connection, create_tables
from book_history import update_history
from process_books import process_books

from amarin import scrape_amarin_all_pages
from b2s import scrape_b2s_all_pages
from jamsai import scrape_jamsai_all_pages
from niin import scrape_naiin_all_pages
from seed import scrape_seed_all_pages


ssl._create_default_https_context = ssl._create_unverified_context


def get_driver():

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=options)


def main():

    print("เริ่มระบบ crawler")

    conn = create_connection()

    if conn is None:
        print("เชื่อมต่อ database ไม่ได้")
        return

    create_tables(conn)

    driver = get_driver()

    try:

        print("เริ่ม crawl Naiin")
        scrape_naiin_all_pages(driver, conn)

        print("เริ่ม crawl B2S")
        scrape_b2s_all_pages(driver, conn)

        print("เริ่ม crawl Jamsai")
        scrape_jamsai_all_pages(driver, conn)

        print("เริ่ม crawl SE-ED")
        scrape_seed_all_pages(driver, conn)

        print("เริ่ม crawl Amarin")
        scrape_amarin_all_pages(driver, conn)

        print("เริ่มแยกข้อมูลหนังสือ")
        process_books(conn)

        print("บันทึกประวัติราคา")
        update_history(conn)

        print("ระบบทำงานเสร็จแล้ว")

    finally:

        driver.quit()
        conn.close()


if __name__ == "__main__":
    main()