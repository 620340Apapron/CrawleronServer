import os
import io
import requests
from PIL import Image
from supabase import create_client

# 1. ดึงค่าจาก Environment Variable
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 2. ตรวจสอบเงื่อนไข: ถ้าไม่มีค่า หรือค่าไม่ใช่ URL ให้ข้ามการต่อ Supabase
if not SUPABASE_URL or not SUPABASE_URL.startswith("http"):
    print("⚠️ [Warning] SUPABASE_URL ไม่ถูกต้องหรือว่างเปล่า! ระบบจะข้ามการอัปโหลดรูปภาพ")
    supabase = None
else:
    try:
        # สร้าง Client เฉพาะเมื่อค่า URL ถูกต้องเท่านั้น
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ เชื่อมต่อ Supabase Storage สำเร็จ")
    except Exception as e:
        print(f"❌ ไม่สามารถสร้าง Supabase Client ได้: {e}")
        supabase = None

def upload_book_cover(raw_image_url, isbn):
    # ถ้าไม่มี Supabase ให้ส่งลิงก์เดิมกลับไปเลย บอทจะได้ไม่พัง
    if supabase is None or not raw_image_url:
        return raw_image_url

    try:
        # ... (โค้ดโหลดรูปและบีบอัดรูปภาพเหมือนเดิม) ...
        # [ย่อส่วนโค้ดเพื่อความกระชับ]
        resp = requests.get(raw_image_url, timeout=10)
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img.thumbnail((400, 600))
        
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=80)
        
        file_path = f"covers/{isbn}.webp"
        supabase.storage.from_("book-images").upload(
            path=file_path,
            file=buffer.getvalue(),
            file_options={"content-type": "image/webp", "x-upsert": "true"}
        )
        return supabase.storage.from_("book-images").get_public_url(file_path)
    except Exception as e:
        print(f"❌ Image Upload Error: {e}")
        return raw_image_url