import os
import io
import requests
from PIL import Image
from supabase import create_client

# ดึงค่า Config จาก Environment Variables (ตั้งค่าใน Railway)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ตรวจสอบว่ามีค่าครบไหมก่อนเริ่มทำงาน
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("⚠️ Warning: ไม่พบ SUPABASE_URL หรือ SUPABASE_KEY บอทจะเก็บแค่ลิงก์รูปเดิม")

def upload_book_cover(raw_image_url, isbn):
    """
    หน้าที่: ดาวน์โหลดรูป -> ย่อขนาด -> แปลงเป็น WebP -> อัปโหลดขึ้น Supabase
    """
    if not supabase or not raw_image_url:
        return raw_image_url # คืนค่าเดิมถ้าไม่ได้ตั้งค่า Supabase

    try:
        # 1. ดาวน์โหลดรูปภาพจากต้นทาง (นายอินทร์/แจ่มใส/SE-ED)
        response = requests.get(raw_image_url, timeout=10)
        if response.status_code != 200:
            return raw_image_url

        # 2. ใช้ Pillow เปิดรูปภาพ
        img = Image.open(io.BytesIO(response.content))
        
        # แปลงเป็น RGB (กัน Error กรณีไฟล์เป็น PNG หรือมี Alpha channel)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 3. ย่อขนาด (Resize) 
        # หน้าปกหนังสือใน App กว้างแค่ 300-400px ก็ชัดมากแล้ว
        img.thumbnail((400, 600)) 

        # 4. บีบอัดและแปลงเป็นไฟล์ WebP (ประหยัดพื้นที่ที่สุด)
        output_buffer = io.BytesIO()
        # quality=80 คือจุดที่สมดุลระหว่างความชัดและขนาดไฟล์
        img.save(output_buffer, format="WEBP", quality=80)
        image_bytes = output_buffer.getvalue()

        # 5. อัปโหลดไปที่ Supabase Storage
        # ตั้งชื่อไฟล์ตาม ISBN (เช่น 9786161885700.webp)
        file_path = f"covers/{isbn}.webp"
        bucket_name = "book-images" # ชื่อ Bucket ที่คุณสร้างใน Supabase

        # อัปโหลดไฟล์ (ถ้ามีไฟล์เดิมอยู่แล้วจะเขียนทับด้วย upsert)
        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=image_bytes,
            file_options={"content-type": "image/webp", "x-upsert": "true"}
        )

        # 6. รับ Public URL เพื่อส่งกลับไปเก็บใน MySQL
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        return public_url

    except Exception as e:
        print(f"❌ Image Service Error: {e}")
        return raw_image_url # ถ้าผิดพลาด ให้ใช้ลิงก์เดิมไปก่อน