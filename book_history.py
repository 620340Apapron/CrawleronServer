from datetime import datetime
from mysql.connector import Error

def update_history(conn):
    """
    ย้ายข้อมูลจาก raw_books ไปยัง book_history 
    ถ้า ISBN เดิมมีอยู่แล้วและราคาเปลี่ยน จะเก็บเป็น Record ใหม่ (History)
    """
    cursor = conn.cursor()
    
    # 1. ดึงข้อมูลจาก raw_books
    cursor.execute("SELECT isbn, title, author, publisher, price, image_url, url, source FROM raw_books")
    raw_books = cursor.fetchall()
    
    if not raw_books:
        print("ไม่มีข้อมูลใหม่ใน raw_books")
        return

    # 2. จัดการข้อมูลซ้ำในก้อนที่เพิ่งสเกรปมา (เผื่อสเกรปซ้ำในวันเดียวกัน)
    unique_books = {}
    for b in raw_books:
        isbn = b[0]
        if isbn not in unique_books:
            unique_books[isbn] = b

    # 3. ตรวจสอบและอัปเดตลง book_history
    for isbn, book in unique_books.items():
        isbn, title, author, publisher, price, image_url, url, source = book

        # หาข้อมูลล่าสุดของเล่มนี้ใน history
        cursor.execute("""
            SELECT price FROM book_history 
            WHERE isbn = %s 
            ORDER BY created_at DESC LIMIT 1
        """, (isbn,))
        
        existing = cursor.fetchone()
        
        if existing:
            last_price = existing[0]
            # ถ้าราคาเปลี่ยน ถึงจะบันทึก record ใหม่เข้าไป
            if float(last_price) != float(price):
                insert_history(cursor, book)
                print(f"📈 ราคาเปลี่ยน [{title}]: {last_price} -> {price}")
        else:
            # ถ้าเป็นหนังสือใหม่ ไม่เคยมีในระบบเลย
            insert_history(cursor, book)
            print(f"🆕 เพิ่มหนังสือใหม่: {title}")
    
    conn.commit()
    
    # 4. ล้างตารางพักข้อมูล (raw_books) เพื่อรอการสเกรปรอบถัดไป
    cursor.execute("DELETE FROM raw_books")
    conn.commit()
    print("🧹 ล้างข้อมูลใน raw_books เรียบร้อย")

def insert_history(cursor, b):
    sql = """
    INSERT INTO book_history (isbn, title, author, publisher, price, image_url, url, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, b)