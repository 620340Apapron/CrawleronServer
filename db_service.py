import mysql.connector
import json
import os

def create_connection():
    # ดึงค่าจาก environment variable
    host     = os.getenv("MYSQL_HOST", "localhost")
    port     = int(os.getenv("MYSQL_PORT", "3306"))        # ← เปลี่ยนตรงนี้
    user     = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "")

    try:
        conn = mysql.connector.connect(
            host="shinkansen.proxy.rlwy.net",
            port=54897,                                  # ← และตรงนี้
            user="root",
            password="FwgRufsqEStTVfTHDNLVioShukkZrgBa",
            database=railway,
        )
        print(f"[DB] Connected to {user}@{host}:{port}/{database}")
        return conn

    except Error as e:
        print(f"[DB][ERROR] Cannot connect to MySQL: {e}")
        raise
