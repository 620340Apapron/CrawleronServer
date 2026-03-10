import ssl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from db_service import create_connection, create_tables
from book_history import update_history

from crawlers.amarin import scrape_amarin_all_pages
from crawlers.b2s import scrape_b2s_all_pages
from crawlers.jamsai import scrape_jamsai_all_pages
from crawlers.niin import scrape_naiin_all_pages
from crawlers.seed import scrape_seed_all_pages


ssl._create_default_https_context = ssl._create_unverified_context


def get_driver():

    options = Options()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    return driver


def main():

    conn = create_connection()

    if conn is None:
        print("DB connection failed")
        return

    create_tables(conn)

    driver = get_driver()

    sites = [

        {"name": "jamsai", "scraper": scrape_jamsai_all_pages},

        {"name": "naiin", "scraper": scrape_naiin_all_pages},

        {"name": "seed", "scraper": scrape_seed_all_pages},

        {"name": "b2s", "scraper": scrape_b2s_all_pages},

        {"name": "amarin", "scraper": scrape_amarin_all_pages},

    ]

    max_pages_to_scrape = 10

    for site in sites:

        source = site["name"]

        scraper = site["scraper"]

        print(f"\n🚀 เริ่ม crawl {source}")

        try:

            scraper(driver, conn, max_pages=max_pages_to_scrape)

        except Exception as e:

            print(f"❌ error {source}: {e}")

    print("\n📊 update price history")

    update_history(conn)

    print("\n✅ เสร็จสิ้น")

    driver.quit()

    conn.close()


if __name__ == "__main__":
    main()