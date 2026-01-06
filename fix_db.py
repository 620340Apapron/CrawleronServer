import mysql.connector
import os

def fix_permissions():
    # ใช้ค่า TCP Proxy เพื่อเชื่อมต่อจากข้างนอกเข้าไปแก้
    config = {
        'host': 'shinkansen.proxy.rlwy.net',
        'port': 14549,
        'user': 'bookroot',
        'password': 'Morigan3003',
        'database': 'railway'
    }
    
    try:
        # พยายามเชื่อมต่อ
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("🔧 กำลังปรับปรุงระบบความปลอดภัยของ User...")
        # รันคำสั่งแก้ Plugin
        cursor.execute("ALTER USER 'bookroot'@'%' IDENTIFIED WITH mysql_native_password BY 'Morigan3003';")
        cursor.execute("FLUSH PRIVILEGES;")
        
        conn.commit()
        print("✅ แก้ไขเรียบร้อย! ตอนนี้บอทหลักควรจะเชื่อมต่อได้แล้ว")
        
    except Exception as e:
        print(f"❌ พลาด: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    fix_permissions()