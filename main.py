import time
import requests
import threading
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# --- الإعدادات ---
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'
URL_MONITOR = 'https://damairport.gov.sy/'
last_status = {}

# إعداد Flask لإبقاء الخدمة نشطة
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- إعداد المتصفح ---
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # توجيه المتصفح للمسار الصحيح في السيرفر
    chrome_options.binary_location = "/usr/bin/chromium" 
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# --- وظائف البوت ---
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error: {e}")

def check_flights():
    driver = get_driver()
    try:
        driver.get(URL_MONITOR)
        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.select('tr.flight-row')
        
        for row in rows:
            info = row.get('aria-label', '')
            flight_id = row.get('data-id', '')
            
            if flight_id and info and last_status.get(flight_id) != info:
                message = f"✈️ <b>تحديث حالة الرحلة</b>\n\n{info}"
                send_telegram_message(message)
                last_status[flight_id] = info
    finally:
        driver.quit()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    while True:
        try:
            check_flights()
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(300)
