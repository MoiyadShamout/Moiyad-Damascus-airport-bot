import os
import requests
import sqlite3
from datetime import datetime, timedelta

# --- أوزان الحالات للتدرج المنطقي ---
STATUS_WEIGHTS = {
    'scheduled': 1,
    'on time': 1,
    'on-time': 1,
    'estimated': 2,
    'delayed': 3,
    'departed': 4,
    'in_flight': 5,
    'landed': 6,
    'arrived': 6,
    'diverted': 7,
    'cancelled': 7
}

def get_db_connection():
    conn = sqlite3.connect('bot_database.db', timeout=30.0)
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

TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def send_telegram_full_details(flight, note_type):
    airport_name = flight.get('_airport_name', 'المطار')
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
        'on-time': 'في موعدها',
        'delayed': 'متأخرة ⚠️',
        'cancelled': 'ملغاة ❌',
        'diverted': 'تم تحويل مسارها 🔄',
        'landed': 'هبطت 🛬',
        'departed': 'أقلعت 🛫',
        'in_flight': 'في الجو ✈️',
        'estimated': 'متوقع ⏰',
        'arrived': 'وصلت 🛬'
    }
    
    status_text = status_mapping.get(raw_status, raw_status)
    header_title = "✅ رحلة جديدة" if note_type == "new" else "⚠️ تحديث حالة الرحلة"

    aircraft = flight.get('aircraft')
    aircraft_line = ""
    if aircraft and str(aircraft).strip() and str(aircraft).strip() != 'غير متوفر':
        aircraft_line = f"🛩️ طراز الطائرة: {str(aircraft).strip()}\n"

    msg = (
        f"<b>{header_title} ({airport_name})</b>\n\n"
        f"<b>{direction}</b>\n"
        f"📅 التاريخ: {flight.get('flightDate', 'غير متوفر')}\n"
        f"✈️ رقم الرحلة: {flight.get('flightNumber', 'غير متوفر')}\n"
        f"🏢 الناقل: {flight.get('airline', 'غير متوفر')}\n"
        f"{aircraft_line}"
        f"🛫 مغادرة من: {from_airport}\n"
        f"🛬 متجهة إلى: {to_airport}\n"
        f"⏰ {time_label}: {flight.get('scheduledTime', 'غير متوفر')}\n"
        f"📊 الحالة الجديدة: <b>{status_text}</b>\n"
    )
    
    country_code = flight.get('countryCode')
    if country_code:
        msg += f"🌐 رمز الدولة: {country_code.upper()}\n"

    send_telegram(msg)

def fetch_official_flights(base_url, airport_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    all_flights = []
    directions = ['arrival', 'departure']
    
    for direction in directions:
        try:
            params = {"paged": 1, "page": 1, "pageSize": 50, "dir": direction}
            res = requests.get(base_url, headers=headers, params=params, timeout=15)
            if res.status_code == 200:
                raw_flights = res.json().get('flights', [])
                for item in raw_flights:
                    airline_data = item.get('airlineInfo', {})
                    airline_name = airline_data.get('nameAr') or item.get('airline', 'غير متوفر')
                    
                    if direction == 'arrival':
                        route_data = item.get('originAirport', {})
                    else:
                        route_data = item.get('destinationAirport', {})
                        
                    route_city = route_data.get('city_ar') or route_data.get('name_ar', 'غير متوفر')

                    all_flights.append({
                        "_airport_name": airport_name,
                        "flightNumber": item.get('flightNumber', 'UNKNOWN'),
                        "airline": airline_name,
                        "type": direction,
                        "flightDate": item.get('date', ''),
                        "scheduledTime": item.get('time', ''),
                        "status": item.get('status', 'scheduled'),
                        "route": route_city,
                        "countryCode": route_data.get('country_code', ''),
                        "aircraft": item.get('aircraft', '')
                    })
        except Exception as e:
            print(f"Error fetching {airport_name} flights ({direction}): {e}")
            
    return all_flights

def fetch_all_airports_flights():
    airports = [
        {"url": "https://damairport.gov.sy/api/flights.php", "name": "مطار دمشق الدولي"},
        {"url": "https://alpairport.gov.sy/api/flights.php", "name": "مطار حلب الدولي"},
        {"url": "https://deirezzorairport.gov.sy/api/flights.php", "name": "مطار دير الزور الدولي"}
    ]
    
    all_flights = []
    for ap in airports:
        all_flights.extend(fetch_official_flights(ap["url"], ap["name"]))
        
    return all_flights

def run_check():
    init_db()
    raw_flights = fetch_all_airports_flights()
    now = datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()

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
            if current_weight > STATUS_WEIGHTS.get(existing_status, 0):
                unique_flights[f_id] = flight
        else:
            unique_flights[f_id] = flight

    for f_id, flight in unique_flights.items():
        f_date = flight.get('flightDate', '')
        f_time = flight.get('scheduledTime', '')
        
        # تجاوز الرحلات التي مضى عليها أكثر من 15 ساعة
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
        
        # 1. إذا كانت رحلة جديدة تماماً لم تُسجّل سابقاً
        if row is None:
            send_telegram_full_details(flight, "new")
            cursor.execute("INSERT INTO flight_last_status (flight_id, last_status) VALUES (?, ?)", (f_id, current_state))
            conn.commit()
            
        # 2. إذا تبيّن أن حالة الرحلة تغيّرت (مثل الانتقال من on-time إلى departed أو landed)
        elif row[0] != current_state:
            last_weight = STATUS_WEIGHTS.get(row[0], 0)
            if current_weight > last_weight:
                send_telegram_full_details(flight, "update")
                cursor.execute("UPDATE flight_last_status SET last_status = ? WHERE flight_id = ?", (current_state, f_id))
                conn.commit()

    conn.close()

if __name__ == "__main__":
    run_check()
