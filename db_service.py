import mysql.connector
import os
from mysql.connector import Error

def create_connection():
    host = os.getenv("MYSQLHOST", "mysql.railway.internal")
    user = os.getenv("MYSQLUSER", "root")
    password = os.getenv("MYSQLPASSWORD", "ZosyTwKSPBYUrmmTcUfgPRFhqNwaIzNF")
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
    """สร้างตารางที่จำเป็น (ฟังก์ชันที่ Error แจ้งว่าหายไป)"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_books (
            id INT AUTO_INCREMENT ,
            isbn VARCHAR(255) PRIMARY KEY,
            title TEXT,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10, 2),
            image_url TEXT,
            url TEXT,
            source TEXT,
        );""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS book_history (
            id INT AUTO_INCREMENT ,
            isbn VARCHAR(255) PRIMARY KEY,
            title TEXT,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10, 2),
            image_url TEXT,
            url TEXT,
            source TEXT,
        );""")
        conn.commit()
        print("✅ สร้าง/ตรวจสอบตารางเรียบร้อย")
    except Error as e:
        print(f"❌ Error สร้างตาราง: {e}")
    finally:
        cursor.close()

def insert_book(conn, book):
    """บันทึกข้อมูลลง raw_books"""
    if conn is None:
        print("❌ [DB Error] ไม่มี Object การเชื่อมต่อ (Connection is None)")
        return

    cursor = conn.cursor()
    sql = """
    INSERT INTO raw_books (isbn, title, author, publisher, price, image_url, url, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        # มั่นใจว่าข้อมูลทุกตัวเป็นชนิดที่ถูกต้อง
        data_tuple = (
            str(book.get('isbn', 'Unknown')),
            str(book.get('title', 'Unknown')),
            str(book.get('author', 'Unknown')),
            str(book.get('publisher', 'Unknown')),
            float(book.get('price', 0) or 0), 
            str(book.get('image_url', '')),
            str(book.get('url', '')),
            str(book.get('source', 'Unknown'))
        )
        
        cursor.execute(sql, data_tuple)
        conn.commit() # ยืนยันการบันทึก
        print(f"   💾 บันทึกสำเร็จ: {book.get('title')[:30]}")
    except Error as e:
        print(f"❌ [MySQL Error] บันทึกไม่สำเร็จ: {e}")
        conn.rollback() # ย้อนกลับกรณีพัง
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