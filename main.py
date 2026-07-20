import time
import requests
import threading
from flask import Flask
from bs4 import BeautifulSoup

# --- الإعدادات ---
TELEGRAM_TOKEN = '8975492791:AAEzDgBx2ZIPrSCylVqTH0-rquRgB_crKfM'
CHAT_ID = '-1004481182341'
URL = 'https://damairport.gov.sy/'
last_status = {'dummy': 'data'} 

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
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(URL, headers=headers, timeout=20)
        
        # أداة الفحص (DEBUG)
        print(f"DEBUG: Response status code: {response.status_code}")
        print(f"DEBUG: Page content sample: {response.text[:200]}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.flight-row')
        
        if not rows:
            print("DEBUG: No rows found! Check class names.")
            
        for row in rows:
            info = row.get('aria-label', '')
            flight_id = row.get('data-id', '')
            
            if flight_id and info:
                if last_status.get(flight_id) != info:
                    send_telegram(f"✈️ <b>تحديث:</b>\n{info}")
                    last_status[flight_id] = info
            
    except Exception as e:
        print(f"Check error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    while True:
        check_flights()
        time.sleep(300)
