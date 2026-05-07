import ssl
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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
    
    # This line automatically finds where 'chromium' is installed in the kitchen
    path = shutil.which("chromium") or shutil.which("chromium-browser")
    if path:
        options.binary_location = path
    
    # Just start it up
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