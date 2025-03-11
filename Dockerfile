# ใช้ Python 3.10-slim เป็น Base Image
FROM python:3.10-slim

# ตั้ง WORKDIR เป็น /app
WORKDIR /app

# ติดตั้งแพ็กเกจพื้นฐานสำหรับ apt-get
RUN apt-get update && apt-get install -y wget unzip curl gnupg

# ติดตั้ง Google Chrome
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i /tmp/chrome.deb || apt-get -fy install \
    && rm /tmp/chrome.deb

# ติดตั้ง Chromedriver (ปรับ URL ให้ตรงกับเวอร์ชันที่ต้องการ)
RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# คัดลอกไฟล์ทั้งหมดจาก repository ไปยัง WORKDIR
COPY . .

# ติดตั้ง Python dependencies จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คำสั่งเริ่มต้น เมื่อ container ถูก launch
CMD ["python", "main.py"]
