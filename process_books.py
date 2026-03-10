import mysql.connector
from db_service import create_connection


def process_books(conn):

    cursor = conn.cursor(dictionary=True)

    print("เริ่มแยกข้อมูลจาก raw_books")

    cursor.execute("SELECT * FROM raw_books")

    rows = cursor.fetchall()

    for row in rows:

        isbn = row["isbn"]

        if not isbn or isbn == "Unknown":
            continue

        # หาใน books
        cursor.execute(
            "SELECT id FROM books WHERE isbn=%s",
            (isbn,)
        )

        book = cursor.fetchone()

        if book:
            book_id = book["id"]

        else:
            cursor.execute(
                """
                INSERT INTO books
                (isbn,title,author,publisher,image_url)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    row["isbn"],
                    row["title"],
                    row["author"],
                    row["publisher"],
                    row["image_url"]
                )
            )

            book_id = cursor.lastrowid

        # insert price
        cursor.execute(
            """
            INSERT INTO book_prices
            (book_id,store,price,url)
            VALUES (%s,%s,%s,%s)

            ON DUPLICATE KEY UPDATE
            price=VALUES(price),
            url=VALUES(url)
            """,
            (
                book_id,
                row["source"],
                row["price"],
                row["url"]
            )
        )

    conn.commit()

    print("แยกข้อมูลเสร็จแล้ว")

    cursor.close()


if __name__ == "__main__":
    conn = create_connection()

    if conn:
        process_books(conn)