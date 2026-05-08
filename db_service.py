import time
import mysql.connector
import os
from dotenv import load_dotenv

import time
import mysql.connector

load_dotenv()
def create_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=os.getenv("MYSQLPORT")
    )
def create_tables(conn):
    cursor = conn.cursor()
    
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
        source VARCHAR(50),
        UNIQUE(isbn, source)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY, 
        isbn VARCHAR(50) UNIQUE,
        title TEXT,
        author TEXT,
        publisher TEXT,
        image_url TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_prices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        isbn VARCHAR(50),
        source VARCHAR(50),
        price DECIMAL(10,2),
        url TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (isbn) REFERENCES books(isbn),
        UNIQUE(isbn, source)
    )
    """)
    conn.commit()

def insert_book(conn, book):
    cursor = conn.cursor()
    sql = """
    INSERT INTO raw_books (isbn, title, author, publisher, price, image_url, url, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        price = VALUES(price),
        image_url = VALUES(image_url),
        url = VALUES(url)
    """

    print(f"DEBUG DB: กำลังจะบันทึกเล่ม {book['title']} (ISBN: {book['isbn']})")
    cursor.execute(sql, (
        book["isbn"], book["title"], book["author"], book["publisher"],
        book["price"], book["image_url"], book["url"], book["source"]
    ))
    try:
        cursor.execute(sql, (...))
        conn.commit()
        print(f"บันทึกสำเร็จ: {book['isbn']}")
    except Exception as e:
        print(f"DB Error: {e}")
    
    conn.commit()
def get_books():
    conn = create_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        return books
    finally:
        conn.close()
