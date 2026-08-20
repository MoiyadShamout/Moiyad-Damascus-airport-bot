import requests
import sqlite3
from datetime import datetime

# --- إعدادات الاتصال ---
TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

def get_db_connection():
    return sqlite3.connect('bot_database.db', timeout=30.0)

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
    
    status_mapping = {
        'scheduled': 'في موعدها', 'on time': 'في موعدها', 'on-time': 'في موعدها',
        'delayed': 'متأخرة ⚠️', 'cancelled': 'ملغاة ❌', 'diverted': 'تم تحويل مسارها 🔄',
        'landed': 'هبطت 🛬', 'departed': 'أقلعت 🛫', 'in_flight': 'في الجو ✈️',
        'estimated': 'متوقع ⏰', 'arrived': 'وصلت 🛬'
    }
    
    raw_status = str(flight.get('status', 'scheduled')).strip().lower()
    status_text = status_mapping.get(raw_status, raw_status)
    header_title = "✅ رحلة جديدة" if note_type == "new" else "⚠️ تحديث حالة الرحلة"

    msg = (
        f"<b>{header_title} ({airport_name})</b>\n\n"
        f"<b>{direction}</b>\n"
        f"📅 التاريخ: {flight.get('flightDate')}\n"
        f"✈️ رقم الرحلة: {flight.get('flightNumber')}\n"
        f"🏢 الناقل: {flight.get('airline')}\n"
        f"🛫 مغادرة من: {from_airport}\n"
        f"🛬 متجهة إلى: {to_airport}\n"
        f"⏰ {time_label}: {flight.get('scheduledTime')}\n"
        f"📊 الحالة: <b>{status_text}</b>"
    )
    send_telegram(msg)

def fetch_official_flights(base_url, airport_name):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    all_flights = []
    
    # الحصول على تاريخ اليوم الحالي فقط بدقة
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_city = airport_name.replace("مطار ", "").replace(" الدولي", "").strip()
    
    for direction in ['arrival', 'departure']:
        try:
            params = {"dir": direction, "date": today_str}
            res = requests.get(base_url, headers=headers, params=params, timeout=15)
            if res.status_code == 200:
                raw_flights = res.json().get('flights', [])
                for item in raw_flights:
                    flight_date = item.get('date', '')
                    
                    # جلب رحلات اليوم الحالي فقط وتجاهل أي شيء آخر
                    if flight_date != today_str:
                        continue
                        
                    airline_data = item.get('airlineInfo', {})
                    route_data = (item.get('originAirport') if direction == 'arrival' else item.get('destinationAirport')) or {}
                    route_city = route_data.get('city_ar') or route_data.get('name_ar', 'غير متوفر')
                    
                    # فلترة الرحلات الوهمية (التي تكون نفس مدينة المطار)
                    if base_city in route_city or route_city in base_city:
                        continue
                    
                    all_flights.append({
                        "_airport_name": airport_name,
                        "flightNumber": item.get('flightNumber', 'غير متوفر'),
                        "airline": airline_data.get('nameAr') or item.get('airline', 'غير متوفر'),
                        "type": direction,
                        "flightDate": flight_date,
                        "scheduledTime": item.get('time', '00:00'),
                        "status": item.get('status', 'scheduled'),
                        "route": route_city
                    })
        except Exception as e:
            continue
                
    all_flights.sort(key=lambda x: x['scheduledTime'])
    return all_flights

def run_check():
    init_db()
    all_raw_flights = []
    airports = [
        {"url": "https://damairport.gov.sy/api/flights.php", "name": "مطار دمشق الدولي"},
        {"url": "https://alpairport.gov.sy/api/flights.php", "name": "مطار حلب الدولي"},
        {"url": "https://deirezzorairport.gov.sy/api/flights.php", "name": "مطار دير الزور الدولي"}
    ]
    
    for ap in airports:
        all_raw_flights.extend(fetch_official_flights(ap["url"], ap["name"]))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for flight in all_raw_flights:
        f_id = f"{flight['_airport_name']}_{flight['flightNumber']}_{flight['type']}_{flight['flightDate']}"
        current_status = str(flight.get('status', 'scheduled')).strip().lower()
        
        cursor.execute("SELECT last_status FROM flight_last_status WHERE flight_id = ?", (f_id,))
        row = cursor.fetchone()
        
        if row is None:
            send_telegram_full_details(flight, "new")
            cursor.execute("INSERT INTO flight_last_status (flight_id, last_status) VALUES (?, ?)", (f_id, current_status))
        elif row[0] != current_status:
            send_telegram_full_details(flight, "update")
            cursor.execute("UPDATE flight_last_status SET last_status = ? WHERE flight_id = ?", (current_status, f_id))
            
        conn.commit()
    conn.close()

if __name__ == "__main__":
    run_check()
