import os
import requests
import sqlite3
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

# --- إعداد قاعدة البيانات مع حماية القفل (Timeout) ---
def get_db_connection():
    conn = sqlite3.connect('bot_database.db', timeout=30.0, check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_last_status (
            flight_id TEXT PRIMARY KEY,
            last_status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def send_telegram_full_details(flight, note_type, airport_name):
    f_type = flight.get('type')
    route_info = flight.get('route', 'غير متوفر')
    
    if f_type == 'arrival':
        direction = f"🛬 رحلة وصول إلى {airport_name}"
        from_airport = f"مطار {route_info}"
        to_airport = airport_name
        time_label = "موعد الوصول المحدد"
    else:
        direction = f"🛫 رحلة مغادرة من {airport_name}"
        from_airport = airport_name
        to_airport = f"مطار {route_info}"
        time_label = "موعد المغادرة المحدد"
    
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
        'estimated': 'متوقع',
        'arrived': 'وصلت'
    }
    
    status_text = status_mapping.get(str(raw_status).lower(), raw_status)
    header_title = "✅ رحلة جديدة" if note_type == "new" else "⚠️ تحديث حالة الرحلة"

    msg = (
        f"<b>{header_title} ({airport_name})</b>\n\n"
        f"<b>{direction}</b>\n"
        f"📅 التاريخ: {flight.get('flightDate', 'غير متوفر')}\n"
        f"✈️ رقم الرحلة: {flight.get('flightNumber', 'غير متوفر')}\n"
        f"🏢 الناقل: {flight.get('airline', 'غير متوفر')}\n"
        f"🛩️ طراز الطائرة: {flight.get('aircraft', 'غير متوفر')}\n"
        f"🛫 مغادرة من: {from_airport}\n"
        f"🛬 متجهة إلى: {to_airport}\n"
        f"⏰ {time_label}: {flight.get('scheduledTime', 'غير متوفر')}\n"
    )
    
    actual_time = flight.get('actualTime')
    if actual_time:
        msg += f"⌚ الوقت الفعلي: <b>{actual_time}</b>\n"
        
    estimated_time = flight.get('estimatedTime')
    if estimated_time and not actual_time:
        msg += f"⌚ الوقت المتوقع: <b>{estimated_time}</b>\n"
        
    msg += f"📊 الحالة: <b>{status_text}</b>\n"
    
    delay_info = flight.get('delay')
    if delay_info:
        msg += f"⏱️ مدة التأخير: <b>{delay_info} دقيقة</b>\n"
        
    remark_info = flight.get('remark')
    if remark_info:
        msg += f"📝 ملاحظات: <b>{remark_info}</b>\n"
        
    country_code = flight.get('countryCode')
    if country_code:
        msg += f"🌐 رمز الدولة: {country_code.upper()}\n"

    send_telegram(msg)

def check_flights():
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
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

    conn = get_db_connection()
    cursor = conn.cursor()

    for flight in all_fetched_flights:
        airport_name = flight.get('_airport_name')
        f_num = flight.get('flightNumber')
        if not f_num or f_num == 'Unknown':
            f_num = flight.get('route', 'UNKNOWN')
            
        f_date = flight.get('flightDate', '')
        f_time = flight.get('scheduledTime', '')
        f_type = flight.get('type', '')
        
        try:
            flight_datetime = datetime.strptime(f"{f_date} {f_time}", "%Y-%m-%d %H:%M")
            if now > flight_datetime + timedelta(hours=15):
                continue
        except:
            pass

        # استخدام معرف فريد ثابت لمنع التكرار عند تغير الوقت البسيط
        f_id = f"{airport_name}_{f_num}_{f_type}_{f_date}"
        
        raw_status = flight.get('status', 'scheduled')
        actual_time = flight.get('actualTime', '')
        current_state = f"{raw_status}_{actual_time}"
        
        cursor.execute("SELECT last_status FROM flight_last_status WHERE flight_id = ?", (f_id,))
        row = cursor.fetchone()
        
        if row is None:
            send_telegram_full_details(flight, "new", airport_name)
            cursor.execute("INSERT OR REPLACE INTO flight_last_status (flight_id, last_status) VALUES (?, ?)", (f_id, current_state))
            conn.commit()
        elif row[0] != current_state:
            send_telegram_full_details(flight, "update", airport_name)
            cursor.execute("UPDATE flight_last_status SET last_status = ? WHERE flight_id = ?", (current_state, f_id))
            conn.commit()

    conn.close()

scheduler = BackgroundScheduler(job_defaults={'max_instances': 1})
scheduler.add_job(func=check_flights, trigger="interval", minutes=2)
scheduler.start()

@app.route('/')
def home():
    return "Multi-Airport Flight Bot is running successfully!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
