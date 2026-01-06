import os
import io
import requests
from PIL import Image
from supabase import create_client

# ค่าเหล่านี้เอามาจากหน้า Settings > API ใน Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_book_cover(raw_image_url, isbn):
    """
    ดาวน์โหลดรูป ย่อขนาด และอัปโหลดขึ้น Supabase Storage
    """
    try:
        # 1. ดาวน์โหลดรูปจากเว็บต้นทาง (นายอินทร์/แจ่มใส)
        resp = requests.get(raw_image_url, timeout=10)
        if resp.status_code != 200: return None
        
        # 2. ใช้ Pillow ย่อขนาดและบีบอัด
        img = Image.open(io.BytesIO(resp.content))
        img = img.convert("RGB") # ป้องกัน Error กรณีรูปเป็น PNG โปร่งแสง
        
        # ย่อให้กว้างสูงสุด 400px (ประหยัดพื้นที่และชัดพอสำหรับ Mobile App)
        img.thumbnail((400, 600)) 
        
        # แปลงเป็น WebP (เล็กกว่า JPG 3-5 เท่า)
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=80) # คุณภาพ 80%
        image_bytes = buffer.getvalue()

        # 3. อัปโหลดขึ้น Supabase Bucket 'book-images'
        file_path = f"covers/{isbn}.webp"
        
        # พยายามอัปโหลด (ถ้ามีไฟล์เดิมอยู่แล้วจะเขียนทับ)
        # หมายเหตุ: ใน supabase-py version ใหม่ใช้ upsert=True ได้
        res = supabase.storage.from_("book-images").upload(
            path=file_path,
            file=image_bytes,
            file_options={"content-type": "image/webp", "x-upsert": "true"}
        )

        # 4. สร้าง Public URL สำหรับเอาไปเก็บใน Database
        public_url = supabase.storage.from_("book-images").get_public_url(file_path)
        return public_url

    except Exception as e:
        print(f"❌ Error uploading image for ISBN {isbn}: {e}")
        return raw_image_url # ถ้าพลาด ให้ส่ง URL เดิมกลับไปแทน