import mysql.connector
import os


def create_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306)),
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
                   
        UNIQUE(isbn,source)
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
        book_id INT,
        source VARCHAR(50),
        price DECIMAL(10,2),
        url TEXT,
                   
        UNIQUE(book_id,source)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        isbn VARCHAR(50),
        price DECIMAL(10,2),
        source VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()


def insert_book(conn, book):

    cursor = conn.cursor()

    sql = """
    INSERT INTO raw_books
    (isbn,title,author,publisher,price,image_url,url,source)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)

    ON DUPLICATE KEY UPDATE
        price = VALUES(price),
        image_url = VALUES(image_url),
        url = VALUES(url)
    """

    cursor.execute(sql, (
        book["isbn"],
        book["title"],
        book["author"],
        book["publisher"],
        book["price"],
        book["image_url"],
        book["url"],
        book["source"]
    ))

    conn.commit()