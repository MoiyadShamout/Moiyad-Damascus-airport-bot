import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)

# الإعدادات الأساسية
API_URL = "https://ognrupehzbbckimkaikb.supabase.co/rest/v1/flight_cache?select=payload%2Cupdated_at%2Ctotal_arrivals%2Ctotal_departures&id=eq.main"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nbnJ1cGVoemJiY2tpbWthaWtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODc3NTIsImV4cCI6MjA4MDI2Mzc1Mn0.cBh06V2W7ocx8etUixo2lcdl1XH5RR4pTjXNOG59Xsg",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nbnJ1cGVoemJiY2tpbWthaWtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODc3NTIsImV4cCI6MjA4MDI2Mzc1Mn0.cBh06V2W7ocx8etUixo2lcdl1XH5RR4pTjXNOG59Xsg",
    "accept": "application/vnd.pgrst.object+json"
}

TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

sent_notifications = {}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'})

def send_telegram_full_details(flight, note):
    f_type = flight.get('type')
    route_info = flight.get('route', 'غير متوفر')
    
    # تحديد السطور بدقة لكل من رحلات الوصول والمغادرة
    if f_type == 'arrival':
        direction = "🛬 رحلة وصول"
        from_airport = f"مطار {route_info}"
        to_airport = "مطار دمشق الدولي"
    else:
        direction = "🛫 رحلة مغادرة"
        from_airport = "مطار دمشق الدولي"
        to_airport = f"مطار {route_info}"
    
    # تحويل الحالة المجدولة إلى "on time"
    raw_status = flight.get('status', 'scheduled')
    status_text = "on time" if raw_status == 'scheduled' else raw_status
    
    msg = (
        f"<b>⚠️ {note}</b>\n\n"
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
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list): data = data[0]
            flights = data.get('payload', [])
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            for flight in flights:
                f_id = flight.get('flightNumber')
                current_status = flight.get('status')
                flight_date = flight.get('flightDate')
                
                # تصفية الرحلات القديمة والتركيز على رحلات اليوم فقط
                if flight_date and flight_date < today:
                    continue
                
                if sent_notifications.get(f_id) == current_status:
                    continue
                
                note = "رحلة جديدة" if f_id not in sent_notifications else "تحديث حالة الرحلة"
                send_telegram_full_details(flight, note)
                
                sent_notifications[f_id] = current_status
                    
    except Exception as e:
        print(f"Update error: {e}")

scheduler = BackgroundScheduler(job_defaults={'max_instances': 2})
scheduler.add_job(func=check_flights, trigger="interval", minutes=2)
scheduler.start()

@app.route('/')
def home():
    return "Bot is running perfectly!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
