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
    
    # 1. Find Chrome Binary
    # Try multiple common paths for Railway/Nixpacks
    chrome_locations = [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        shutil.which("google-chrome-stable"),
        shutil.which("chromium")
    ]
    
    chrome_path = next((loc for loc in chrome_locations if loc and os.path.exists(loc)), None)
    
    if chrome_path:
        print(f"Found Chrome at: {chrome_path}")
        options.binary_location = chrome_path
    else:
        print("Warning: Could not find Chrome binary path. Selenium might fail.")

    # 2. Find Chromedriver
    driver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    
    if os.path.exists(driver_path):
        print(f"Found Chromedriver at: {driver_path}")
        service = Service(executable_path=driver_path)
    else:
        print(f"Error: Chromedriver not found at {driver_path}")
        # If not found, we let Selenium try to find it in PATH automatically
        service = Service()

    return webdriver.Chrome(service=service, options=options)


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