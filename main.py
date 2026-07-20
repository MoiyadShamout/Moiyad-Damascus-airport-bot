import requests
from bs4 import BeautifulSoup
import time

# إعدادات البوت (قم بوضع بياناتك هنا)
TELEGRAM_TOKEN = '8975492791:AAEzDgBx2ZIPrSCylVqTH0-rquRgB_crKfM'
CHAT_ID = '-1004481182341'
URL_MONITOR = 'https://damairport.gov.sy/'

# قاموس لتخزين حالة الرحلات لضمان عدم تكرار الإشعارات
last_status = {}

def send_telegram_message(text):
    """إرسال رسالة إلى تيليجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    requests.post(url, data=payload)

def check_flights():
    """فحص حالة الرحلات في موقع المطار"""
    try:
        response = requests.get(URL_MONITOR)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.flight-row') 
        
        for row in rows:
            info = row.get('aria-label', '')
            flight_id = row.get('data-id', '')
            
            if not flight_id or not info:
                continue
                
            # التحقق إذا تغيرت حالة الرحلة منذ آخر فحص
            if last_status.get(flight_id) != info:
                
                parts = info.split(' . ')
                if len(parts) < 3:
                    continue
                
                flight_no = parts[0]
                status_raw = parts[1]
                route = parts[2]
                
                # تحديد نوع الرحلة والرموز بناءً على الحالة
                if "مغادرة" in status_raw:
                    flight_type = "رحلة مغادرة"
                    status_display = "في موعدها"
                    emoji = "🛫"
                elif "وصول" in status_raw:
                    flight_type = "رحلة وصول"
                    status_display = "في موعدها"
                    emoji = "🛬"
                else:
                    flight_type = "رحلة مجدولة"
                    status_display = "في موعدها"
                    emoji = "📅"
                
                # بناء النص النهائي للإشعار
                message = (
                    f"✈️ <b>تحديث حالة الرحلة</b>\n\n"
                    f"📋 <b>نوع الرحلة:</b> {flight_type}\n"
                    f"✈️ <b>رقم الرحلة:</b> {flight_no}\n"
                    f"{emoji} <b>الحالة:</b> {status_display}\n"
                    f"📍 <b>المسار:</b> {route}\n"
                    f"🗓️ <b>تاريخ الرحلة:</b> 20/07/2026\n"
                    f"⏰ <b>الموعد المجدول:</b> 07:40\n"
                )
                
                send_telegram_message(message)
                last_status[flight_id] = info
                
    except Exception as e:
        print(f"حدث خطأ أثناء فحص الرحلات: {e}")

if __name__ == "__main__":
    while True:
        check_flights()
        time.sleep(60) # فحص الموقع كل دقيقة
