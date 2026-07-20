import time
import requests
import threading
from flask import Flask
from bs4 import BeautifulSoup

# --- الإعدادات ---
TELEGRAM_TOKEN = '8975492791:AAEzDgBx2ZIPrSCylVqTH0-rquRgB_crKfM'
CHAT_ID = '-1004481182341'
URL = 'https://damairport.gov.sy/'
last_status = {'dummy': 'data'} # تغيير هذا السطر مؤقتاً
is_first_run = True  # متغير للتأكد من أنها المرة الأولى

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'})
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_flights():
    global is_first_run
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.flight-row')
        
        # ترتيب الصفوف حسب الترتيب في الموقع
        for row in rows:
            info = row.get('aria-label', '')
            flight_id = row.get('data-id', '')
            
            if flight_id and info:
                # إذا كانت المرة الأولى، أرسل كل الرحلات بالتسلسل
                if is_first_run:
                    send_telegram(f"✈️ <b>رحلة مجدولة:</b>\n{info}")
                    last_status[flight_id] = info
                    time.sleep(1) # تأخير بسيط بين كل رسالة لتصل بالترتيب
                
                # إذا كانت رحلة سابقة وتغيرت حالتها
                elif flight_id in last_status and last_status[flight_id] != info:
                    send_telegram(f"✈️ <b>تحديث حالة الرحلة:</b>\n{info}")
                    last_status[flight_id] = info
        
        is_first_run = False # بعد الانتهاء من أول دورة، نغلق خيار الإرسال الجماعي
            
    except Exception as e:
        print(f"Check error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    while True:
        check_flights()
        time.sleep(300)
