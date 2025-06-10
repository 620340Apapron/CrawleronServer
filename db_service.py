import mysql.connector
import json
import os

def create_connection():
    # ดึงค่าจาก environment variable
    host     = os.getenv("MYSQL_HOST", "shinkansen.proxy.rlwy.net")
    port     = int(os.getenv("MYSQL_PORT", "54897"))
    user     = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "FwgRufsqEStTVfTHDNLVioShukkZrgBa")
    database = os.getenv("MYSQL_DATABASE", "railway")

    try:
        conn = mysql.connector.connect(
            host=host,         
            port=port,         
            user=user,         
            password=password, 
            database=database,
        )
        print(f"[DB] Connected to {user}@{host}:{port}/{database}")
        return conn

    except Error as e:
        print(f"[DB][ERROR] Cannot connect to MySQL: {e}")
        raise
