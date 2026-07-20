import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)

# إعدادات مصادر البيانات للمطارين (دمشق وحلب)
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
            "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0cXB2ZmZ4Ym91b3d1ZndiZnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0Mjk4OTMsImV4cCI6MjA4OTAwOTg5M30.70xYw0b4w6w4O7yXmZzXkL3W4vKzX8k9W3vKzX8k9W3",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0cXB2ZmZ4Ym91b3d1ZndiZnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0Mjk4OTMsImV4cCI6MjA4OTAwOTg5M30.70xYw0b4w6w4O7yXmZzXkL3W4vKzX8k9W3vKzX8k9W3",
            "accept": "application/vnd.pgrst.object+json"
        }
    }
]

TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

# قاموس لتتبع آخر حالة تم إرسالها لكل رحلة لمنع التكرار
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
    status_text = "on time" if raw_status == 'scheduled' else raw_status
    
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
    
    for airport in AIRPORTS_CONFIG:
        try:
            response = requests.get(airport["url"], headers=airport["headers"], timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list): 
                    data = data[0]
                flights = data.get('payload', [])
                
                for flight in flights:
                    # مفتاح فريد لكل رحلة مرتبط باسم المطار ورقم الرحلة
                    f_id = f"{airport['name']}_{flight.get('flightNumber')}"
                    current_status = flight.get('status')
                    flight_date = flight.get('flightDate')
                    
                    # استبعاد الرحلات القديمة والتركيز على رحلات اليوم فقط
                    if flight_date and flight_date < today:
                        continue
                    
                    # منع التكرار: إذا كانت الحالة لم تتغير، لا تقم بإرسال إشعار جديد
                    if sent_notifications.get(f_id) == current_status:
                        continue
                    
                    note = "رحلة جديدة" if f_id not in sent_notifications else "تحديث حالة الرحلة"
                    send_telegram_full_details(flight, note, airport["name"])
                    
                    # تحديث الحالة المسجلة لمنع التكرار المستقبلي
                    sent_notifications[f_id] = current_status
                        
        except Exception as e:
            print(f"Error fetching {airport['name']}: {e}")

# جدولة الفحص كل دقيقتين تلقائياً
scheduler = BackgroundScheduler(job_defaults={'max_instances': 2})
scheduler.add_job(func=check_flights, trigger="interval", minutes=2)
scheduler.start()

@app.route('/')
def home():
    return "Multi-Airport Flight Bot is running perfectly!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
