import os
import threading
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running and monitoring!", 200

# بياناتك
TELEGRAM_TOKEN = "8975492791:AAEzDgBx2ZIPrSCylVqTHO-rquRgB_crKfM"
TELEGRAM_CHAT_ID = "-1002237894561"
URL = "https://damairport.gov.sy"

def run_bot():
    print("[BOT] عملية الرصد بدأت...")
    while True:
        try:
            print("[BOT] جاري محاولة الاتصال بالمطار...")
            response = requests.get(URL, timeout=15)
            print(f"[BOT] تم الاتصال، كود الحالة: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # تجربة بحث عامة
                rows = soup.find_all('tr')
                print(f"[BOT] تم العثور على {len(rows)} صف في الجدول.")
                
                # اختبار إرسال بسيط
                telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                msg = {"chat_id": TELEGRAM_CHAT_ID, "text": "البوت يعمل ويقوم بالفحص حالياً"}
                requests.post(telegram_url, json=msg)
                print("[BOT] تم إرسال رسالة تجريبية لتليغرام.")
            else:
                print(f"[BOT] فشل الوصول للموقع: {response.status_code}")
                
        except Exception as e:
            print(f"[BOT] خطأ أثناء الرصد: {e}")
            
        time.sleep(300) # فحص كل 5 دقائق

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
