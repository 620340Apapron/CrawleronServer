import mysql.connector
import os

def create_connection():
    
    host = os.getenv("MYSQLHOST") 
    user = os.getenv("MYSQLUSER")
    password = os.getenv("MYSQLPASSWORD") 
    database = os.getenv("MYSQLDATABASE") 
    port = os.getenv("MYSQLPORT") 

    try:
        connection = mysql.connector.connect(
            host="mysql.railway.internal",
            user="root",
            password="Morigan3003",
            database="railway",
            port=int(3306),
            auth_plugin='mysql_native_password',
            connect_timeout=15
        )
        if connection.is_connected():
            print("✅ บอทเชื่อมต่อฐานข้อมูลสำเร็จ!")
            return connection
    except Exception as e:
        print(f"❌ บอทเชื่อมต่อไม่ได้: {e}")
        return None