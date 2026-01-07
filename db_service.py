import mysql.connector
import os
from mysql.connector import Error

def create_connection():
    host = os.getenv("MYSQLHOST", "mysql-k65u.railway.internal")
    user = os.getenv("MYSQLUSER", "root")
    password = os.getenv("MYSQLPASSWORD", "TpmaxCTXjtHqhDnvlUCXbNIhZlmjfnnn")
    database = os.getenv("MYSQLDATABASE", "railway")
    port = int(os.getenv("MYSQLPORT", "3306"))

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            connect_timeout=20
        )
        if connection.is_connected():
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
            return connection
    except mysql.connector.Error as err:
        if err.errno == 1045:
            try:
                print("🔄 พยายามเชื่อมต่อด้วย auth_plugin สำรอง...")
                connection = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    port=port,
                    connect_timeout=20
                )
                return connection
            except:
                pass
        print(f"❌ ไม่สามารถเชื่อมต่อ MySQL ได้: {err}")
        return None

def create_tables(conn):
    """สร้างตารางที่จำเป็น (ฟังก์ชันที่ Error แจ้งว่าหายไป)"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            isbn VARCHAR(255),
            title TEXT,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10, 2),
            image_url TEXT,
            url TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS book_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            isbn VARCHAR(255),
            title TEXT,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10, 2),
            image_url TEXT,
            url TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")
        conn.commit()
        print("✅ สร้าง/ตรวจสอบตารางเรียบร้อย")
    except Error as e:
        print(f"❌ Error สร้างตาราง: {e}")
    finally:
        cursor.close()

def insert_book(conn, book):
    """บันทึกข้อมูลลง raw_books"""
    cursor = conn.cursor()
    sql = """
    INSERT INTO raw_books (isbn, title, author, publisher, price, image_url, url, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(sql, (
            book.get('isbn'), book.get('title'), book.get('author'),
            book.get('publisher'), book.get('price'), book.get('image_url'),
            book.get('url'), book.get('source')
        ))
        conn.commit()
    except Error as e:
        print(f"❌ Error บันทึกหนังสือ: {e}")
    finally:
        cursor.close()

def clear_raw_books_table(conn):
    """ล้างตาราง raw_books"""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM raw_books")
        conn.commit()
        print("🧹 ล้างข้อมูลดิบเรียบร้อย")
    except Error as e:
        print(f"❌ Error ล้างตาราง: {e}")
    finally:
        cursor.close()