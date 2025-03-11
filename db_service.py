import sqlite3
import json

def create_connection(db_file="books.db"):
    """สร้างการเชื่อมต่อฐานข้อมูล SQLite"""
    conn = sqlite3.connect(db_file)
    return conn

def create_table(conn):
    sql_create_books_table = """
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT DEFAULT 'Unknown',
        publisher TEXT DEFAULT 'Unknown',
        price INTEGER DEFAULT 0,
        category TEXT DEFAULT 'General',
        url TEXT DEFAULT '',
        source TEXT NOT NULL
    );
    """
    cursor = conn.cursor()
    cursor.execute(sql_create_books_table)
    conn.commit()


def insert_book(conn, book):
    """บันทึกข้อมูลหนังสือลงฐานข้อมูล"""
    
    if isinstance(book, str):  # ถ้า book เป็น string ให้แปลงกลับเป็น dictionary
        try:
            book = json.loads(book)
        except json.JSONDecodeError:
            print("[ERROR] ไม่สามารถแปลง JSON:", book)
            return  # ข้ามไปยังข้อมูลถัดไป

    required_keys = ["title", "author", "publisher", "price", "category", "url", "source"]
    for key in required_keys:
        if key not in book or book[key] is None:
            print(f"[ERROR] Key '{key}' หายไปหรือเป็น None ในข้อมูล: {book}")
            return  # ข้ามการบันทึกถ้าข้อมูลไม่ครบ

    # แปลงข้อมูลให้มีประเภทที่ถูกต้อง
    title = str(book["title"]) if book["title"] else "Unknown"
    author = str(book["author"]) if book["author"] else "Unknown"
    publisher = str(book["publisher"]) if book["publisher"] else "Unknown"
    category = str(book["category"]) if book["category"] else "General"
    url = str(book["url"]) if book["url"] else ""
    source = str(book["source"]) if book["source"] else "Unknown"

    # แปลง price เป็น int (ถ้าแปลงไม่ได้ให้กำหนดเป็น 0)
    try:
        if isinstance(book["price"], (int, float)):
            price = int(book["price"])
        elif isinstance(book["price"], str):
            price = int(float(book["price"].replace(",", "").replace("฿", "")))  # ลบ "," และ "฿"
        else:
            price = 0
    except (ValueError, TypeError, AttributeError):
        price = 0  # ถ้าผิดพลาด ให้กำหนดค่าเป็น 0

    sql = """
    INSERT INTO books(title, author, publisher, price, category, url, source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (title, author, publisher, price, category, url, source))
        conn.commit()
        print("[SUCCESS] บันทึกข้อมูลสำเร็จ:", title)
    except Exception as e:
        print("[ERROR] ไม่สามารถบันทึกข้อมูล:", e)
