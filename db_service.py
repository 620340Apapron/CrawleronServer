import mysql.connector
import json
import os
from mysql.connector import Error

def create_connection():
    # ดึงค่าจาก environment variable (ทั้งสองแบบรองรับได้)
    host=os.getenv("DB_HOST", "hopper.proxy.rlwy.net"),
    port=os.getenv("DB_PORT", "22749"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "IjxcLAzTFgXxTnMDklQKTOghdAkvLRVb"),
    database=os.getenv("DB_DATABASE", "railway")

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
