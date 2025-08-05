from db_service import create_connection
from mysql.connector import Error
import datetime


def create_history_table(conn):
    """
    สร้างตาราง book_history สำหรับเก็บประวัติหนังสือ
    เก็บ title, author, publisher, url, price, และ timestamp ของการ crawl แต่ละครั้ง
    """
    sql = '''
    CREATE TABLE IF NOT EXISTS book_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(500),
        author VARCHAR(255),
        publisher VARCHAR(255),
        url TEXT,
        price DECIMAL(10,2),
        crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    '''
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()


def update_history(conn):
    """
    เปรียบเทียบข้อมูลจากตาราง rawbooks กับ book_history
    ถ้าเจอหนังสือใหม่ (url ใหม่) หรือราคาต่างจากล่าสุด ให้ insert ใหม่ใน book_history
    """
    select_raw = '''
    SELECT title, author, publisher, url, price
    FROM rawbooks
    '''
    insert_sql = '''
    INSERT INTO book_history (title, author, publisher, url, price, crawled_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    '''
    lookup_sql = '''
    SELECT price
    FROM book_history
    WHERE url = %s
    ORDER BY crawled_at DESC
    LIMIT 1
    '''

    cur = conn.cursor()
    cur.execute(select_raw)
    raw_rows = cur.fetchall()

    for title, author, publisher, url, price in raw_rows:
        try:
            # ดึงราคาล่าสุดจาก history
            cur.execute(lookup_sql, (url,))
            last = cur.fetchone()
            # ตรวจสอบถ้าไม่มี record หรือราคาต่างกัน
            if last is None or float(last[0]) != float(price):
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                params = (title, author, publisher, url, price, timestamp)
                cur.execute(insert_sql, params)
        except Error as e:
            print(f"[history] Error processing {url}: {e}")
            continue

    conn.commit()
    cur.close()
    print(f"✅ Updated history: processed {len(raw_rows)} raw records")


if __name__ == '__main__':
    # ตัวอย่างวิธีใช้งาน
    conn = create_connection()
    create_history_table(conn)
    update_history(conn)
    conn.close()
