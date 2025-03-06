# db_service.py
import sqlite3

def create_connection(db_file="books.db"):
    conn = sqlite3.connect(db_file)
    return conn

def create_table(conn):
    sql_create_books_table = """
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT,
        title TEXT,
        author TEXT,
        publisher TEXT,
        price TEXT,
        category TEXT,
        source TEXT
    )
    """
    cursor = conn.cursor()
    cursor.execute(sql_create_books_table)
    conn.commit()

def insert_book(conn, book):
    sql = """
    INSERT INTO books(image, title, author, publisher, price, category, source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(sql, (
        book['image'],
        book['title'],
        book['author'],
        book['publisher'],
        book['price'],
        book['category'],
        book['source']
    ))
    conn.commit()
