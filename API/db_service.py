import mysql.connector
import json
import os
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    # ดึงค่าจาก environment variable
    host     = os.getenv("MYSQL_HOST")
    port     = int(os.getenv("MYSQL_PORT"))
    user     = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

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
