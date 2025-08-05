import sqlite3
from datetime import datetime

def create_history_table(conn):
    """สร้างตาราง book_history หากยังไม่มี"""
    try:
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS book_history (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            price REAL,
            url TEXT,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(sql_create_table)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating history table: {e}")

def update_history(conn):
    """
    ดึงข้อมูลจาก raw_books มาอัปเดตใน book_history
    และจัดการข้อมูลซ้ำ
    """
    cursor = conn.cursor()
    
    # ดึงข้อมูลทั้งหมดจาก raw_books
    cursor.execute("SELECT title, author, publisher, price, url, source FROM raw_books")
    raw_books = cursor.fetchall()
    
    # ล้างข้อมูลเดิมใน raw_books
    conn.execute("DELETE FROM raw_books")
    conn.commit()
    
    if not raw_books:
        print("ไม่มีข้อมูลใหม่ใน raw_books")
        return

    for book in raw_books:
        title, author, publisher, price, url, source = book
        
        # ตรวจสอบว่าหนังสือเล่มนี้มีอยู่แล้วใน book_history หรือไม่
        cursor.execute("""
            SELECT id, price FROM book_history
            WHERE title = ? AND publisher = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (title, publisher))
        
        existing_book = cursor.fetchone()
        
        if existing_book:
            existing_id, existing_price = existing_book
            # ถ้ามีอยู่แล้วและราคามีการเปลี่ยนแปลง ให้เพิ่มรายการใหม่
            if existing_price != price:
                cursor.execute("""
                    INSERT INTO book_history (book_id, title, author, publisher, price, url, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (existing_id, title, author, publisher, price, url, source, datetime.now()))
                conn.commit()
                print(f"✅ อัปเดตราคาหนังสือ: {title} จาก {existing_price} เป็น {price}")
        else:
            # ถ้าเป็นหนังสือใหม่ ให้เพิ่มเป็นรายการแรก
            cursor.execute("""
                INSERT INTO book_history (book_id, title, author, publisher, price, url, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (None, title, author, publisher, price, url, source, datetime.now()))
            conn.commit()
            print(f"✅ เพิ่มหนังสือใหม่: {title}")