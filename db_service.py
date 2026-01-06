import mysql.connector
import os
from mysql.connector import Error

#supabase:https://sqkajhdscwdiszwliaqh.supabase.co:sb_publishable_jiEjxjKdtjfMZdxFdDiopg_M1wXa49G

def create_connection():
    try:
        # ดึงค่าจาก Variables ใน Railway (ถ้าไม่มีให้ใช้ค่า Default ที่คุณใส่ไว้)
        connection = mysql.connector.connect(
            host=os.getenv("MYSQLHOST", "mysql.railway.internal"),
            port=os.getenv("MYSQLPORT", "3306"),
            user=os.getenv("MYSQLUSER", "root"),
            password=os.getenv("MYSQLPASSWORD", "Morigan3003"),
            database=os.getenv("MYSQLDATABASE", "railway"),
            auth_plugin='mysql_native_password',
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
def create_tables(conn):
    cursor = conn.cursor()
    try:
        # raw_books: พักข้อมูลจากการสเกรปรายวัน
        sql_create_raw_books_table = """
        CREATE TABLE IF NOT EXISTS raw_books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            isbn VARCHAR(20),
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10, 2),
            image_url TEXT,
            url TEXT,
            source VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );"""
        
        # book_history: เก็บข้อมูลถาวรและประวัติราคา
        sql_create_history_table = """
        CREATE TABLE IF NOT EXISTS book_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            isbn VARCHAR(20),
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            price DECIMAL(10, 2),
            image_url TEXT,
            url TEXT,
            source VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );"""
        
        cursor.execute(sql_create_raw_books_table)
        cursor.execute(sql_create_history_table)
        conn.commit()
        print("✅ สร้าง/ตรวจสอบ ตารางเรียบร้อย")
    except Error as e:
        print(f"Error creating tables: {e}")

def insert_book(conn, book):
    """แทรกข้อมูลลงใน raw_books (เพิ่ม isbn และ image_url)"""
    cursor = conn.cursor()
    sql = """
    INSERT INTO raw_books (isbn, title, author, publisher, price, image_url, url, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        cursor.execute(sql, (
            book.get('isbn'), book.get('title'), book.get('author'), 
            book.get('publisher'), book.get('price'), book.get('image_url'),
            book.get('url'), book.get('source')
        ))
        conn.commit()
    except Error as e:
        print(f"Error inserting book: {e}")