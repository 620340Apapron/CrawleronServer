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
    
    # Railway/Nixpacks typically installs to these locations
    chrome_path = "/usr/bin/google-chrome-stable"
    driver_path = "/usr/bin/chromedriver"
    
    # Check if they exist, if not, try alternative chromium path
    if not os.path.exists(chrome_path):
        chrome_path = "/usr/bin/chromium"

    options.binary_location = chrome_path
    service = Service(executable_path=driver_path)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Failed to start Chrome. Error: {e}")
        # Last resort: Try without explicit paths and let Selenium Manager find it
        return webdriver.Chrome(options=options)


def main():
    print("เริ่มระบบ crawler")

    conn = create_connection() #
    create_tables(conn) #
    limit = 50

    if conn is None:
        print("เชื่อมต่อ database ไม่ได้")
        return

    create_tables(conn)

    try:
        driver = get_driver() #
        scrape_naiin_all_pages(driver, conn, max_books=limit)
        scrape_b2s_all_pages(driver, conn, max_books=limit)
        scrape_jamsai_all_pages(driver, conn, max_books=limit)
        scrape_seed_all_pages(driver, conn, max_books=limit)
        scrape_amarin_all_pages(driver, conn, max_books=limit)
        driver.quit()

        # Run normalization and history update
        process_books(conn)
        update_history(conn)

    finally:
        conn.close()

if __name__ == "__main__":
    main()