import mysql.connector
import json
import os
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    # ดึงค่าจาก environment variable (ทั้งสองแบบรองรับได้)
    host     = os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST")
    port_str = os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT", "3306")
    user     = os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER")
    password = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD")
    database = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE")

    print(f"[DEBUG] env values: host={host}, port={port_str}, user={user}, database={database}")

    try:
        port = int(port_str)
    except (TypeError, ValueError):
        print(f"[DB][ERROR] invalid port value: {port_str}")
        raise

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
