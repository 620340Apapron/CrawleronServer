import mysql.connector
import json
import os
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    # ดึงค่าจาก environment variable
    host     = os.getenv("MYSQLHOST")
    port     = int(os.getenv("MYSQLPORT"))
    user     = os.getenv("MYSQLUSER")
    password = os.getenv("MYSQLPASSWORD")
    database = os.getenv("MYSQLDATABASE")

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
