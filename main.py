import crawler_naiin
import crawler_b2s
import crawler_jamsai
import crawler_amarin
import crawler_seed
import mysql.connector
import os

# ฟังก์ชันเชื่อมต่อกับ Database
def connect_to_database():
    return mysql.connector.connect(
        host=os.getenv("mysql.railway.internal"),
        user=os.getenv("root"),
        password=os.getenv("jfYnLvcFdUEEVzrvcfceFwTFuMdUBVOc"),
        database=os.getenv("jfYnLvcFdUEEVzrvcfceFwTFuMdUBVOc"),
        port=os.getenv("3306")
    )

# ฟังก์ชันบันทึกข้อมูลลง Database
def save_to_database(cursor, books_data, source):
    for _, row in books_data.iterrows():
        cursor.execute("""
            INSERT INTO books (name, price, author, source)
            VALUES (%s, %s, %s, %s)
        """, (row['name'], row['price'], row['author'], source))

# ฟังก์ชันเรียกใช้ Crawler และบันทึกข้อมูล
def run_crawler(crawler, source):
    print(f"Starting {source} Crawler")
    try:
        driver = crawler.get_driver()
        books_data = crawler.get_books(driver)
        if not books_data.empty:
            print(f"Saving data from {source} to database...")
            connection = connect_to_database()
            cursor = connection.cursor()
            save_to_database(cursor, books_data, source)
            connection.commit()
            cursor.close()
            connection.close()
            print(f"Data from {source} saved successfully.")
        else:
            print(f"No data found from {source}.")
    except Exception as e:
        print(f"Error in {source} Crawler: {e}")
    finally:
        driver.quit()

# ฟังก์ชันหลัก
def run_all_crawlers():
    run_crawler(crawler_naiin, "Naiin")
    run_crawler(crawler_b2s, "B2S")
    run_crawler(crawler_jamsai, "Jamsai")
    run_crawler(crawler_amarin, "Amarin")
    run_crawler(crawler_seed, "Seed")

if __name__ == "__main__":
    print("Running all crawlers...")
    run_all_crawlers()
    print("Finished all crawlers.")
