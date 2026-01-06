import sqlite3
from datetime import datetime

def update_history(conn):
    """
    ดึงข้อมูลจาก raw_books มาอัปเดตใน book_history
    และจัดการข้อมูลซ้ำ
    """
    cursor = conn.cursor()
    
    # ดึงข้อมูลทั้งหมดจาก raw_books
    cursor.execute("SELECT isbn,title, author, publisher, price, url, source FROM raw_books")
    raw_books = cursor.fetchall()
    
    if not raw_books:
        print("ไม่มีข้อมูลใหม่ใน raw_books")
        # ใช้ cursor ในการล้างตาราง
        cursor.execute("DELETE FROM raw_books")
        conn.commit()
        return

    # สร้าง Dictionary เพื่อเก็บข้อมูลล่าสุดของหนังสือแต่ละเล่ม
    book_info = {}
    for book in raw_books:
        isbn, title, author, publisher, price, url, source = book
        # ใช้ (title, publisher) เป็น key เพื่อหาหนังสือซ้ำ
        key = (isbn, title)
        if key not in book_info:
            book_info[key] = {
                'isbn': isbn,
                'title': title,
                'author': author,
                'publisher': publisher,
                'price': price,
                'url': url,
                'source': source
            }
    
    # นำข้อมูลที่ผ่านการกรองแล้วไปอัปเดตใน book_history
    for key, book in book_info.items():
        isbn = book['isbn']
        title = book['title']
        publisher = book['publisher']
        price = book['price']
        url = book['url']
        source = book['source']
        author = book['author']

        cursor.execute("""
            SELECT id, price FROM book_history
            WHERE title = %s AND publisher = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (isbn, title))
        
        existing_book = cursor.fetchone()
        
        if existing_book:
            book_id, existing_price = existing_book
            if existing_price != price:
                cursor.execute("""
                    INSERT INTO book_history (isbn, title, author, publisher, price, url, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (isbn, title, author, publisher, price, url, source))
                conn.commit()
                print(f"✅ อัปเดตราคาหนังสือ: {title} จาก {existing_price} เป็น {price}")
        else:
            cursor.execute("""
                INSERT INTO book_history (isbn, title, author, publisher, price, url, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (isbn, title, author, publisher, price, url, source))
            book_id = cursor.lastrowid
            conn.commit()
            cursor.execute("UPDATE book_history SET book_id = %s WHERE id = %s", (book_id, book_id))
            conn.commit()
            print(f"✅ เพิ่มหนังสือใหม่: {title}")
