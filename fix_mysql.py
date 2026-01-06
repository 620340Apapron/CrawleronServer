import mysql.connector
import os
import time

def run_emergency_fix():
    # ดึงค่าจาก Variables ใน Railway
    host = os.getenv("MYSQLHOST", "mysql.railway.internal")
    user = "root"
    password = os.getenv("MYSQLPASSWORD")
    database = os.getenv("MYSQLDATABASE", "railway")
    port = int(os.getenv("MYSQLPORT", 3306))

    print(f"🚀 เริ่มกระบวนการปลดล็อก MySQL 9 (Host: {host})")

    # รายการ Plugin ที่จะทดลองใช้ล็อกอิน
    plugins = ['caching_sha2_password', 'mysql_native_password']
    
    for plugin in plugins:
        try:
            print(f"🔄 กำลังลองเชื่อมต่อด้วยระบบ: {plugin}...")
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                auth_plugin=plugin,
                connect_timeout=15
            )
            
            if conn.is_connected():
                print(f"🔓 เชื่อมต่อสำเร็จด้วย {plugin}! กำลังปรับสิทธิ์...")
                cursor = conn.cursor()
                
                # คำสั่งเปลี่ยนให้ root ใช้ระบบที่ Python เข้าถึงง่ายที่สุด
                sql = f"ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '{password}';"
                cursor.execute(sql)
                cursor.execute("FLUSH PRIVILEGES;")
                
                conn.commit()
                print("✅ [SUCCESS] ปลดล็อกสิทธิ์ root เรียบร้อยแล้ว!")
                conn.close()
                return True
        except Exception as e:
            print(f"❌ ระบบ {plugin} ล้มเหลว: {e}")
    
    return False

if __name__ == "__main__":
    # รอให้ DB พร้อมใช้งานแป๊บหนึ่ง
    time.sleep(5)
    run_emergency_fix()