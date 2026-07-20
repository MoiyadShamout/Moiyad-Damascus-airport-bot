import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

app = Flask(__name__)

# الإعدادات
TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

# الذاكرة لحفظ حالة الرحلات ومنع التكرار
flights_memory = {}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'})
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_flights():
    # الحصول على تاريخ اليوم بتوقيت دمشق
    tz = pytz.timezone('Asia/Damascus')
    today = datetime.now(tz).strftime('%Y-%m-%d')
    
    # رابط الـ API الديناميكي لرحلات اليوم
    api_url = f'https://damairport.gov.sy/api/flights.php?paged=1&page=1&dir=all&wfloor={today}&dexact={today}'
    
    try:
        response = requests.get(api_url, timeout=15)
        data = response.json()
        flights = data.get('flights', [])

        for flight in flights:
            unique_id = str(flight.get('id'))
            raw_status = flight.get('status', '').lower()
            
            # معالجة النصوص حسب طلباتك السابقة
            display_status = raw_status.replace('scheduled', 'on time').replace('departed', 'takeoff time').replace('arrived', 'arrival time')
            
            # البيانات الأساسية
            flight_num = flight.get('flightNumber', 'N/A')
            airline = flight.get('airline', 'N/A')
            origin = flight.get('origin', 'N/A')
            destination = flight.get('destination', 'N/A')
            time_val = flight.get('time', 'N/A')
            is_arrival = flight.get('direction') == 'arrival'
            
            # صياغة الرسالة
            info = (
                f"✈️ الرحلة: {flight_num} ({airline})\n"
                f"📍 من: {origin} | إلى: {destination}\n"
                f"⏰ الموعد: {time_val}\n"
                f"📊 الحالة: <b>{display_status}</b>"
            )

            # منطق المقارنة: الإرسال فقط عند وجود رحلة جديدة أو تغير الحالة
            if unique_id not in flights_memory or flights_memory[unique_id] != raw_status:
                prefix = "📢 <b>تحديث جديد للرحلة:</b>" if unique_id in flights_memory else "🆕 <b>رحلة مجدولة لهذا اليوم:</b>"
                send_telegram(f"{prefix}\n\n{info}")
                
                # تحديث الذاكرة
                flights_memory[unique_id] = raw_status

    except Exception as e:
        print(f"Scraping Error: {e}")

# ضبط المؤقت ليعمل كل 5 دقائق
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_flights, trigger="interval", minutes=5)
scheduler.start()

@app.route('/')
def home():
    return "Bot is running and monitoring flight statuses!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
