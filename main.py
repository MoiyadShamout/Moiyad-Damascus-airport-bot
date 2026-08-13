import os
import requests
import sqlite3
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

# --- أوزان الحالات الصارمة (لمنع تكرار أو عودة الرحلة لحالة سابقة) ---
STATUS_WEIGHTS = {
    'scheduled': 1,
    'on time': 1,
    'estimated': 2,
    'delayed': 3,
    'departed': 4,
    'in_flight': 5,
    'landed': 6,
    'arrived': 6,
    'diverted': 7,
    'cancelled': 7
}

# --- إعداد قاعدة البيانات المحلية ---
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

# --- إعدادات التلغرام ---
TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def send_telegram_full_details(flight, note_type):
    airport_name = flight.get('_airport_name', 'مطار دمشق الدولي')
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
    
    raw_status = str(flight.get('status', 'scheduled')).strip().lower()
    
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
    
    status_text = status_mapping.get(raw_status, raw_status)
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
        f"📊 الحالة: <b>{status_text}</b>\n"
    )
    
    country_code = flight.get('countryCode')
    if country_code:
        msg += f"🌐 رمز الدولة: {country_code.upper()}\n"

    send_telegram(msg)

# --- جلب البيانات من الموقع الرسمي الجديد لمطار دمشق ---
def fetch_damascus_official_flights():
    base_url = "https://damairport.gov.sy/api/flights.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    all_flights = []
    directions = ['arrival', 'departure']
    
    for direction in directions:
        try:
            # نطلب الصفحة الأولى بـ 20 رحلة لكل اتجاه
            params = {
                "paged": 1,
                "page": 1,
                "pageSize": 20,
                "dir": direction
            }
            res = requests.get(base_url, headers=headers, params=params, timeout=15)
            if res.status_code == 200:
                json_data = res.json()
                raw_flights = json_data.get('flights', [])
                
                for item in raw_flights:
                    # تحويل الهيكلية الجديدة لـ JSON إلى الصيغة المعتمدة للسكربت
                    f_num = item.get('flightNumber', 'UNKNOWN')
                    airline_data = item.get('airlineInfo', {})
                    airline_name = airline_data.get('nameAr') or item.get('airline', 'غير متوفر')
                    
                    if direction == 'arrival':
                        route_data = item.get('originAirport', {})
                        route_city = route_data.get('city_ar') or route_data.get('name_ar', 'غير متوفر')
                        country_code = route_data.get('country_code', '')
                    else:
                        route_data = item.get('destinationAirport', {})
                        route_city = route_data.get('city_ar') or route_data.get('name_ar', 'غير متوفر')
                        country_code = route_data.get('country_code', '')

                    flight_obj = {
                        "_airport_name": "مطار دمشق الدولي",
                        "flightNumber": f_num,
                        "airline": airline_name,
                        "type": direction,
                        "flightDate": item.get('date', ''),
                        "scheduledTime": item.get('time', ''),
                        "status": item.get('status', 'scheduled'),
                        "route": route_city,
                        "countryCode": country_code,
                        "aircraft": item.get('aircraft', 'غير متوفر')
                    }
                    all_flights.append(flight_obj)
        except Exception as e:
            print(f"Damascus Fetch Error ({direction}): {e}")
            
    return all_flights

# --- جلب بيانات مطار حلب (من المصدر السابق) ---
def fetch_aleppo_flights():
    url = "https://ttqpvffxbouowufwbfze.supabase.co/rest/v1/flight_cache?select=payload%2Cupdated_at%2Ctotal_arrivals%2Ctotal_departures&id=eq.main"
    headers = {
        "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0cXB2ZmZ4Ym91b3d1ZndiZnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3ODU3NDMsImV4cCI6MjA4MjM2MTc0M30.A3j9iny8RusFtUt8J5mAyaj33cKEQJW9EPJw8iLtVWc",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0cXB2ZmZ4Ym91b3d1ZndiZnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3ODU3NDMsImV4cCI6MjA4MjM2MTc0M30.A3j9iny8RusFtUt8J5mAyaj33cKEQJW9EPJw8iLtVWc",
        "accept": "application/vnd.pgrst.object+json"
    }
    all_flights = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list): 
                data = data[0] if data else {}
            flights = data.get('payload', [])
            for flight in flights:
                flight['_airport_name'] = "مطار حلب الدولي"
                all_flights.append(flight)
    except Exception as e:
        print(f"Aleppo Fetch Error: {e}")
    return all_flights

def fetch_all_flights_data():
    damascus_flights = fetch_damascus_official_flights()
    aleppo_flights = fetch_aleppo_flights()
    return damascus_flights + aleppo_flights

def silent_bootstrap():
    flights = fetch_all_flights_data()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for flight in flights:
        airport_name = flight.get('_airport_name')
        f_num = flight.get('flightNumber', 'UNKNOWN')
        f_date = flight.get('flightDate', '')
        f_type = flight.get('type', '')
        f_id = f"{airport_name}_{f_num}_{f_type}_{f_date}"
        
        raw_status = str(flight.get('status', 'scheduled')).strip().lower()
        cursor.execute("INSERT OR IGNORE INTO flight_last_status (flight_id, last_status) VALUES (?, ?)", (f_id, raw_status))
        
    conn.commit()
    conn.close()

def check_flights():
    raw_flights = fetch_all_flights_data()
    now = datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. فلترة البيانات وتطبيق أوزان الحالات
    unique_flights = {}
    for flight in raw_flights:
        airport_name = flight.get('_airport_name')
        f_num = flight.get('flightNumber', 'UNKNOWN')
        f_date = flight.get('flightDate', '')
        f_type = flight.get('type', '')

        f_id = f"{airport_name}_{f_num}_{f_type}_{f_date}"
        raw_status = str(flight.get('status', 'scheduled')).strip().lower()
        current_weight = STATUS_WEIGHTS.get(raw_status, 0)

        if f_id in unique_flights:
            existing_status = str(unique_flights[f_id].get('status', 'scheduled')).strip().lower()
            existing_weight = STATUS_WEIGHTS.get(existing_status, 0)
            if current_weight > existing_weight:
                unique_flights[f_id] = flight
        else:
            unique_flights[f_id] = flight

    # 2. معالجة التحديثات والإرسال
    for f_id, flight in unique_flights.items():
        f_date = flight.get('flightDate', '')
        f_time = flight.get('scheduledTime', '')
        
        try:
            flight_datetime = datetime.strptime(f"{f_date} {f_time}", "%Y-%m-%d %H:%M")
            if now > flight_datetime + timedelta(hours=15):
                continue
        except:
            pass

        raw_status = str(flight.get('status', 'scheduled')).strip().lower()
        current_state = raw_status
        current_weight = STATUS_WEIGHTS.get(raw_status, 0)
        
        cursor.execute("SELECT last_status FROM flight_last_status WHERE flight_id = ?", (f_id,))
        row = cursor.fetchone()
        
        if row is None:
            send_telegram_full_details(flight, "new")
            cursor.execute("INSERT INTO flight_last_status (flight_id, last_status) VALUES (?, ?)", (f_id, current_state))
            conn.commit()
            
        elif row[0] != current_state:
            last_weight = STATUS_WEIGHTS.get(row[0], 0)
            if current_weight > last_weight:
                send_telegram_full_details(flight, "update")
                cursor.execute("UPDATE flight_last_status SET last_status = ? WHERE flight_id = ?", (current_state, f_id))
                conn.commit()

    conn.close()

silent_bootstrap()

scheduler = BackgroundScheduler(job_defaults={'max_instances': 1})
scheduler.add_job(func=check_flights, trigger="interval", minutes=2)
scheduler.start()

@app.route('/')
def home():
    return "Bot is running with Official Damascus Airport API Integration!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
