#!/bin/bash

echo "🔹 อัปเดตและติดตั้ง Google Chrome & Chromedriver..."
apt-get update && apt-get install -y wget unzip curl \
    && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i /tmp/chrome.deb || apt-get -fy install \
    && rm /tmp/chrome.deb \
    && wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# ตรวจสอบว่า Chrome และ Chromedriver ติดตั้งสำเร็จหรือไม่
echo "✅ ตรวจสอบ Google Chrome & Chromedriver"
google-chrome --version
chromedriver --version

echo "🚀 เริ่มรันโปรแกรม Python"
python main.py
