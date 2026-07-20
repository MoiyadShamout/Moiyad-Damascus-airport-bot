import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- الإعدادات ---
TELEGRAM_TOKEN = '8975492791:AAEzDgBx2ZIPrSCylVqTH0-rquRgB_crKfM'
CHAT_ID = '-1004481182341'
URL_MONITOR = 'https://damairport.gov.sy/'
last_status = {}

def send_telegram_message(text):
    """إرسال إشعار إلى تيليجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def get_driver():
    """إعداد المتصفح للعمل في الخلفية"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def check_flights():
    """فحص الرحلات واستخراج البيانات"""
    driver = get_driver()
    try:
        driver.get(URL_MONITOR)
        time.sleep(10)  # انتظار تحميل الصفحة والبيانات
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.select('tr.flight-row')
        
        for row in rows:
            info = row.get('aria-label', '')
            flight_id = row.get('data-id', '')
            
            if flight_id and info and last_status.get(flight_id) != info:
                parts = info.split(' . ')
                if len(parts) >= 3:
                    flight_no, status_raw, route = parts[0], parts[1], parts[2]
                    
                    # تحديد النوع بناءً على التنسيق المطلوب
                    flight_type = "رحلة مغادرة" if "مغادرة" in status_raw else "رحلة وصول"
                    emoji = "🛫" if "مغادرة" in status_raw else "🛬"
                    
                    message = (
                        f"✈️ <b>تحديث حالة الرحلة</b>\n\n"
                        f"📋 <b>نوع الرحلة:</b> {flight_type}\n"
                        f"✈️ <b>رقم الرحلة:</b> {flight_no}\n"
                        f"{emoji} <b>الحالة:</b> في موعدها\n"
                        f"📍 <b>المسار:</b> {route}\n"
                        f"🗓️ <b>تاريخ الرحلة:</b> {time.strftime('%d/%m/%Y')}\n"
                        f"⏰ <b>الموعد المجدول:</b> {time.strftime('%H:%M')}\n"
                    )
                    
                    send_telegram_message(message)
                    last_status[flight_id] = info
                    
    finally:
        driver.quit()

if __name__ == "__main__":
    while True:
        check_flights()
        time.sleep(300) # فحص كل 5 دقائق لتقليل استهلاك السيرفر
