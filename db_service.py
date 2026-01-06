import mysql.connector
import os

def create_connection():
    # ดึงค่าจาก Variables ที่คุณตั้งไว้ใน Web
    host = os.getenv("MYSQLHOST") # จะได้ mysql.railway.internal
    user = os.getenv("MYSQLUSER") # จะได้ root
    password = os.getenv("MYSQLPASSWORD") # จะได้ Morigan3003
    database = os.getenv("MYSQLDATABASE") # จะได้ railway
    port = os.getenv("MYSQLPORT") # จะได้ 3306

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=int(port),
            # ระบุ Plugin ให้ตรงกับที่เราไปแก้ในข้อ 1
            auth_plugin='mysql_native_password',
            connect_timeout=15
        )
        if connection.is_connected():
            print("✅ บอทเชื่อมต่อฐานข้อมูลสำเร็จ!")
            return connection
    except Exception as e:
        print(f"❌ บอทเชื่อมต่อไม่ได้: {e}")
        return None