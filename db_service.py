import mysql.connector
import json
import os

def create_connection():
    port_env = os.getenv("MYSQLPORT")
    port = int(port_env) if port_env and port_env.isdigit() else 55288

    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST", "ballast.proxy.rlwy.net"),
        user=os.getenv("MYSQLUSER", "root"),
        password=os.getenv("MYSQLPASSWORD", "FrmfJcaQNVQXdOsAtBuMQopdrwrqmPdF"),
        database=os.getenv("MYSQLDATABASE", "railway"),
        port=port
    )

# สร้างตาราง books ถ้ายังไม่มี
def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) DEFAULT 'Unknown',
        publisher VARCHAR(255) DEFAULT 'Unknown',
        price INT DEFAULT 0,
        category VARCHAR(255) DEFAULT 'General',
        url TEXT DEFAULT '',
        source VARCHAR(255) NOT NULL
    )
    """)
    conn.commit()
    cursor.close()


# บันทึกข้อมูลหนังสือลง MySQL
def insert_book(conn, book):
    cursor = conn.cursor()
    sql = """
    INSERT INTO books (title, author, publisher, price, category, url, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        book["title"], book["author"], book["publisher"],
        book["price"], book["category"], book["url"], book["source"]
    ))
    conn.commit()
    cursor.close()