from datetime import datetime


def update_history(conn):

    cursor = conn.cursor()

    cursor.execute("""
    SELECT isbn, price, source, created_at
    FROM raw_books
    """)

    raw_books = cursor.fetchall()

    if not raw_books:
        print("ไม่มีข้อมูลใหม่")
        return

    unique_books = {}

    for b in raw_books:
        isbn = b[0]

        if isbn not in unique_books:
            unique_books[isbn] = b

    for isbn, book in unique_books.items():

        isbn, price, source, created_at = book

        cursor.execute("""
        SELECT price FROM book_history
        WHERE isbn=%s
        ORDER BY source DESC
        LIMIT 1
        """, (isbn,))

        result = cursor.fetchone()

        if result:

            last_price = result[0]

            if float(last_price) != float(price):

                insert_history(cursor, book)

                print(f"ราคาเปลี่ยน {isbn} : {last_price} -> {price}")

        else:

            insert_history(cursor, book)

            print(f"เพิ่มหนังสือใหม่ {isbn}")

    conn.commit()

    cursor.execute("DELETE FROM raw_books")

    conn.commit()

    print("🧹 ล้าง raw_books เรียบร้อย")


def insert_history(cursor, book):

    sql = """
    INSERT INTO book_history
    (isbn, price, source, created_at)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql, book)