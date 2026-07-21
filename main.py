import os
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)

AIRPORTS_CONFIG = [
    {
        "name": "مطار دمشق الدولي",
        "url": "https://ognrupehzbbckimkaikb.supabase.co/rest/v1/flight_cache?select=payload%2Cupdated_at%2Ctotal_arrivals%2Ctotal_departures&id=eq.main",
        "headers": {
            "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nbnJ1cGVoemJiY2tpbWthaWtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODc3NTIsImV4cCI6MjA4MDI2Mzc1Mn0.cBh06V2W7ocx8etUixo2lcdl1XH5RR4pTjXNOG59Xsg",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nbnJ1cGVoemJiY2tpbWthaWtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODc3NTIsImV4cCI6MjA4MDI2Mzc1Mn0.cBh06V2W7ocx8etUixo2lcdl1XH5RR4pTjXNOG59Xsg",
            "accept": "application/vnd.pgrst.object+json"
        }
    },
    {
        "name": "مطار حلب الدولي",
        "url": "https://ttqpvffxbouowufwbfze.supabase.co/rest/v1/flight_cache?select=payload%2Cupdated_at%2Ctotal_arrivals%2Ctotal_departures&id=eq.main",
        "headers": {
            "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0cXB2ZmZ4Ym91b3d1ZndiZnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3ODU3NDMsImV4cCI6MjA4MjM2MTc0M30.A3j9iny8RusFtUt8J5mAyaj33cKEQJW9EPJw8iLtVWc",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0cXB2ZmZ4Ym91b3d1ZndiZnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3ODU3NDMsImV4cCI6MjA4MjM2MTc0M30.A3j9iny8RusFtUt8J5mAyaj33cKEQJW9EPJw8iLtVWc",
            "accept": "application/vnd.pgrst.object+json"
        }
    }
]

TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

sent_notifications = {}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'})

def send_telegram_full_details(flight, note, airport_name):
    f_type = flight.get('type')
    route_info = flight.get('route', 'غير متوفر')
    
    if f_type == 'arrival':
        direction = f"🛬 رحلة وصول إلى {airport_name}"
        from_airport = f"مطار {route_info}"
        to_airport = airport_name
    else:
        direction = f"🛫 رحلة مغادرة من {airport_name}"
        from_airport = airport_name
        to_airport = f"مطار {route_info}"
    
    raw_status = flight.get('status', 'scheduled')
    
    status_mapping = {
        'scheduled': 'في موعدها',
        'on time': 'في موعدها',
        'delayed': 'متأخرة',
        'cancelled': 'ملغاة',
        'diverted': 'تم تحويل مسارها',
        'landed': 'هبطت',
        'departed': 'أقلعت',
        'in_flight': 'في الجو',
        'estimated': 'متوقع'
    }
    
    status_text = status_mapping.get(str(raw_status).lower(), raw_status)
    
    msg = (
        f"<b>⚠️ {note} ({airport_name})</b>\n\n"
        f"<b>{direction}</b>\n"
        f"📅 التاريخ: {flight.get('flightDate', 'غير متوفر')}\n"
        f"✈️ رقم الرحلة: {flight.get('flightNumber', 'غير متوفر')}\n"
        f"🏢 الناقل: {flight.get('airline', 'غير متوفر')}\n"
        f"🛫 مغادرة من: {from_airport}\n"
        f"🛬 متجهة إلى: {to_airport}\n"
        f"⏰ الموعد: {flight.get('scheduledTime', 'غير متوفر')}\n"
    )
    
    actual_time = flight.get('actualTime')
    if actual_time:
        msg += f"⌚ الوقت الفعلي: {actual_time}\n"
        
    msg += f"📊 الحالة: <b>{status_text}</b>"
    
    send_telegram(msg)

def check_flights():
    global sent_notifications
    today = datetime.now().strftime('%Y-%m-%d')
    all_fetched_flights = []
    
    for airport in AIRPORTS_CONFIG:
        try:
            response = requests.get(airport["url"], headers=airport["headers"], timeout=15)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list): 
                    data = data[0] if data else {}
                flights = data.get('payload', [])
                
                for flight in flights:
                    flight_date = flight.get('flightDate')
                    if flight_date and flight_date < today:
                        continue
                    flight['_airport_name'] = airport["name"]
                    all_fetched_flights.append(flight)
        except Exception as e:
            print(f"خطأ في جلب البيانات: {e}")

    def parse_flight_time(f):
        d = f.get('flightDate', '9999-12-31')
        t = f.get('scheduledTime', '00:00')
        return f"{d} {t}"

    all_fetched_flights.sort(key=parse_flight_time)

    for flight in all_fetched_flights:
        airport_name = flight.get('_airport_name')
        f_num = flight.get('flightNumber')
        if not f_num or f_num == 'Unknown':
            f_num = flight.get('route', 'UNKNOWN')
            
        f_date = flight.get('flightDate', '')
        f_time = flight.get('scheduledTime', '')
        f_type = flight.get('type', '')
        
        # مفتاح فريد لكل رحلة
        f_id = f"{airport_name}_{f_num}_{f_type}_{f_date}_{f_time}"
        current_status = flight.get('status')
        
        # التحقق الذكي: هل هذه الرحلة جديدة كلياً أم تغيرت حالتها؟
        if f_id not in sent_notifications:
            # رحلة جديدة تماماً لم تُرسل أبداً
            send_telegram_full_details(flight, "رحلة جديدة", airport_name)
            sent_notifications[f_id] = current_status
        elif sent_notifications[f_id] != current_status:
            # الرحلة موجودة، لكن حالتها تغيرت (مثلاً من مجدولة إلى متأخرة)
            send_telegram_full_details(flight, "تحديث حالة الرحلة", airport_name)
            sent_notifications[f_id] = current_status

scheduler = BackgroundScheduler(job_defaults={'max_instances': 2})
scheduler.add_job(func=check_flights, trigger="interval", minutes=2)
scheduler.start()

check_flights()

@app.route('/')
def home():
    return "Multi-Airport Flight Bot is running perfectly!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
