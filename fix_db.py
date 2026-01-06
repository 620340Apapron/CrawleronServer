import mysql.connector

def fix_mysql_9_login():
    config = {
        'host': 'shinkansen.proxy.rlwy.net', 
        'port': 14549,                        
        'user': 'root',
        'password': 'Morigan3003',
        'database': 'railway'
    }
    
    try:
        print("🔗 กำลังเชื่อมต่อเพื่อแก้ไขระบบล็อกอิน...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # คำสั่งนี้สำคัญมาก: เปลี่ยนระบบรหัสผ่านให้ Python เข้าใจได้ง่ายขึ้น
        print("🔧 กำลังเปลี่ยนระบบรหัสผ่านเป็น mysql_native_password...")
        cursor.execute("ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'Morigan3003';")
        cursor.execute("FLUSH PRIVILEGES;")
        
        conn.commit()
        print("✅ แก้ไขสำเร็จ! ตอนนี้บอทบน Railway จะเชื่อมต่อได้แล้ว")
        
    except mysql.connector.Error as err:
        print(f"❌ ล้มเหลว: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    fix_mysql_9_login()