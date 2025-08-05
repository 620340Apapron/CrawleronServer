import mysql.connector
import json
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
