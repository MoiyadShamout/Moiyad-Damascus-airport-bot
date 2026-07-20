import time
import requests
from flask import Flask
from bs4 import BeautifulSoup

# --- الإعدادات ---
TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'
URL = 'https://damairport.gov.sy/'
last_status = {'dummy': 'data'} 

app = Flask(__name__)

@app.route('/')
def home():
    # هنا نقوم بتشغيل فحص الرحلات عند زيارة الرابط
    check_flights()
    return "Bot is checking flights now!"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'})

def check_flights():
    print("DEBUG: Starting check_flights...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.flight-row')
        
        for row in rows:
            info = row.get('aria-label', '')
            flight_id = row.get('data-id', '')
            
            if flight_id and info:
                if last_status.get(flight_id) != info:
                    send_telegram(f"✈️ <b>تحديث:</b>\n{info}")
                    last_status[flight_id] = info
        print("DEBUG: Check completed.")
    except Exception as e:
        print(f"DEBUG: Error: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
