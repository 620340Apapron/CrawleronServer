import mysql.connector
import sqlite3
import os
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "hopper.proxy.rlwy.net"),
        port=os.getenv("DB_PORT", "22749"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "IjxcLAzTFgXxTnMDklQKTOghdAkvLRVb"),
        database=os.getenv("DB_DATABASE", "railway")
        )
        return connection

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
def create_tables(conn):
    """สร้างตาราง raw_books และ book_history หากยังไม่มี"""
    try:
        sql_create_raw_books_table = """
        CREATE TABLE IF NOT EXISTS raw_books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            price REAL,
            url TEXT,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );"""
        
        sql_create_history_table = """
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
        );"""
        
        conn.execute(sql_create_raw_books_table)
        conn.execute(sql_create_history_table)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

def insert_book(conn, book):
    """แทรกข้อมูลหนังสือใหม่ลงในตาราง raw_books"""
    sql = """
    INSERT INTO raw_books (title, author, publisher, price, url, source)
    VALUES (?, ?, ?, ?, ?, ?);
    """
    try:
        conn.execute(sql, (book['title'], book['author'], book['publisher'], book['price'], book['url'], book['source']))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting book: {e}")

def get_all_books(conn):
    """ดึงข้อมูลหนังสือทั้งหมดจาก raw_books"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM raw_books")
    return cursor.fetchall()

def clear_raw_books_table(conn):
    """ล้างข้อมูลในตาราง raw_books"""
    try:
        conn.execute("DELETE FROM raw_books")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error clearing table: {e}")