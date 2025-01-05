import schedule
import time
import crawler_naiin
import crawler_b2s
import crawler_jamsai
import crawler_amarin
import crawler_seed

def run_all_crawlers():
    # เรียกใช้ Naiin
    print("Starting Naiin Crawler")
    try:
        driver = crawler_naiin.get_driver()
        books_data = crawler_naiin.get_books(driver)
        crawler_naiin.save_to_csv(books_data, "naiin_books.csv")
    except Exception as e:
        print(f"Error in Naiin Crawler: {e}")
    finally:
        driver.quit()

    # เรียกใช้ B2S
    print("Starting B2S Crawler")
    try:
        driver = crawler_b2s.get_driver()
        books_data = crawler_b2s.get_books(driver)
        crawler_b2s.save_to_csv(books_data, "b2s_books.csv")
    except Exception as e:
        print(f"Error in B2S Crawler: {e}")
    finally:
        driver.quit()

    # เรียกใช้ Jamsai
    print("Starting Jamsai Crawler")
    try:
        driver = crawler_jamsai.get_driver()
        books_data = crawler_jamsai.get_books(driver)
        crawler_jamsai.save_to_csv(books_data, "jamsai_books.csv")
    except Exception as e:
        print(f"Error in Jamsai Crawler: {e}")
    finally:
        driver.quit()

    # เรียกใช้ Amarin
    print("Starting Amarin Crawler")
    try:
        driver = crawler_amarin.get_driver()
        books_data = crawler_amarin.get_books(driver)
        crawler_amarin.save_to_csv(books_data, "amarin_books.csv")
    except Exception as e:
        print(f"Error in Amarin Crawler: {e}")
    finally:
        driver.quit()

    # เรียกใช้ Seed
    print("Starting Seed Crawler")
    try:
        driver = crawler_seed.get_driver()
        books_data = crawler_seed.get_books(driver)
        crawler_seed.save_to_csv(books_data, "seed_books.csv")
    except Exception as e:
        print(f"Error in Seed Crawler: {e}")
    finally:
        driver.quit()

# กำหนด Schedule
schedule.every().sunday.at("10:00").do(run_all_crawlers)

print("Scheduler started. Waiting for Sunday at 10:00...")
while True:
    schedule.run_pending()
    time.sleep(1)
