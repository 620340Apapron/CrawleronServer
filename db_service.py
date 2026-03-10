import mysql.connector
import os
from mysql.connector import Error


def create_connection():
    host = os.getenv("MYSQLHOST", "mysql.railway.internal")
    user = os.getenv("MYSQLUSER", "root")
    password = os.getenv("MYSQLPASSWORD")
    database = os.getenv("MYSQLDATABASE", "railway")
    port = int(os.getenv("MYSQLPORT", "3306"))

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            connect_timeout=20,
        )

        if connection.is_connected():
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
            return connection

    except mysql.connector.Error as err:
        print(f"❌ ไม่สามารถเชื่อมต่อ MySQL ได้: {err}")
        return None


def create_tables(conn):
    cursor = conn.cursor()

    try:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            isbn VARCHAR(50),
            title TEXT,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10,2),
            image_url TEXT,
            url TEXT,
            source VARCHAR(50)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS book_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            isbn VARCHAR(50),
            title TEXT,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10,2),
            image_url TEXT,
            url TEXT,
            source VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("✅ สร้าง/ตรวจสอบตารางเรียบร้อย")

    except Error as e:
        print(f"❌ Error สร้างตาราง: {e}")

    finally:
        cursor.close()


def insert_book(conn, book):

    if conn is None:
        print("❌ ไม่มีการเชื่อมต่อ DB")
        return

    cursor = conn.cursor()

    sql = """
    INSERT INTO raw_books
    (isbn,title,author,publisher,price,image_url,url,source)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """

    try:

        data = (
            str(book.get("isbn", "Unknown")),
            str(book.get("title", "Unknown")),
            str(book.get("author", "Unknown")),
            str(book.get("publisher", "Unknown")),
            float(book.get("price", 0) or 0),
            str(book.get("image_url", "")),
            str(book.get("url", "")),
            str(book.get("source", "Unknown")),
        )

        cursor.execute(sql, data)
        conn.commit()

        print(f"💾 บันทึก: {book.get('title')[:40]}")

    except Error as e:

        print(f"❌ MySQL Error: {e}")
        conn.rollback()

    finally:
        cursor.close()


def clear_raw_books_table(conn):

    cursor = conn.cursor()

    try:

        cursor.execute("DELETE FROM raw_books")
        conn.commit()

        print("🧹 ล้าง raw_books แล้ว")

    except Error as e:

        print(f"❌ Error: {e}")

    finally:
        cursor.close()