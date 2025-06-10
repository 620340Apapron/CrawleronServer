import mysql.connector
import json
import os

def create_connection():
    # ดึงค่าจาก environment variable
    host = os.getenv("MYSQLHOST")
    if not host:
        host = "shinkansen.proxy.rlwy.net"
    
    user = os.getenv("MYSQLUSER")
    if not user:
        user = "root"
    
    password = os.getenv("MYSQLPASSWORD")
    if not password:
        password = "FwgRufsqEStTVfTHDNLVioShukkZrgBa"
    
    database = os.getenv("MYSQLDATABASE")
    if not database:
        database = "railway"
    
    port_env = os.getenv("MYSQLPORT")
    port = int(port_env) if port_env and port_env.isdigit() else 554897

    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )
