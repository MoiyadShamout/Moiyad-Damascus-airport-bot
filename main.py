import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from bs4 import BeautifulSoup

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
        "url": "https://lahifemguttthywckyml.supabase.co/rest/v1/flight_cache?select=payload%2Cupdated_at%2Ctotal_arrivals%2Ctotal_departures&id=eq.main",
        "update_url": "https://lahifemguttthywckyml.supabase.co/rest/v1/flight_cache?id=eq.main",
        "headers": {
            "apikey": "sb_publishable_RXLr7kUNGCfrqWaPqvnPbA_cycYi4Xx",
            "Authorization": "Bearer sb_publishable_RXLr7kUNGCfrqWaPqvnPbA_cycYi4Xx",
            "accept": "application/vnd.pgrst.object+json"
        },
        "scrape_url": "https://aleppoairport.net/?lang=ar"
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

def update_aleppo_cache():
    try:
        headers_site = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get("https://aleppoairport.net/?lang=ar", headers=headers_site, timeout=15)
        if resp.status_code != 200:
            print("فشل في جلب موقع مطار حلب")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        flights_list = []
        today_str = datetime.now().strftime('%Y-%m-%d')

        # استخراج صفوف جدول الرحلات من الموقع
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 6:
                flight_number = cols[0].text.strip()
                airline = cols[1].text.strip()
                route = cols[2].text.strip()
                status = cols[3].text.strip()
                scheduled_time = cols[4].text.strip()
                
                flight_data = {
                    "flightNumber": flight_number if flight_number else "UNKNOWN",
                    "airline": airline if airline else "غير متوفر",
                    "route": route if route else "غير متوفر",
                    "status": "scheduled" if "مجدولة" in status or "on time" in status else status,
                    "scheduledTime": scheduled_time if scheduled_time else "00:00",
                    "flightDate": today_str,
                    "type": "departure" # افتراضي أو يمكن استنتاجه من التبويب
                }
                flights_list.append(flight_data)

        # رفع البيانات المحدثة إلى Supabase الخاص بمطار حلب
        payload_data = {
            "payload": flights_list,
            "total_arrivals": 0,
            "total_departures": len(flights_list),
            "updated_at": datetime.utcnow().isoformat() + "+00:00"
        }
        
        for airport in AIRPORTS_CONFIG:
            if airport["name"] == "مطار حلب الدولي":
                up_headers = airport["headers"].copy()
                up_headers["Content-Type"] = "application/json"
                up_headers["Prefer"] = "return=minimal"
                requests.patch(airport["update_url"], json=payload_data, headers=up_headers, timeout=15)
                print(f"تم تحديث قاعدة بيانات مطار حلب بنجاح بـ {len(flights_list)} رحلة.")
                break
    except Exception as e:
        print(f"خطأ أثناء تحديث كاش مطار حلب: {e}")

def check_flights():
    global sent_notifications
    
    # تحديث بيانات حلب أولاً قبل الفحص
    update_aleppo_cache()
    
    today = datetime.now().strftime('%Y-%m-%d')
    all_fetched_flights = []
    
    for airport in AIRPORTS_CONFIG:
        try:
            print(f"جاري إرسال طلب إلى: {airport['name']} - الرابط: {airport['url']}")
            response = requests.get(airport["url"], headers=airport["headers"], timeout=15)
            print(f"استجابة {airport['name']}: رمز الحالة {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list): 
                    data = data[0] if data else {}
                flights = data.get('payload', [])
                print(f"تم جلب {len(flights)} رحلة بنجاح من {airport['name']}")
                
                for flight in flights:
                    flight_date = flight.get('flightDate')
                    if flight_date and flight_date < today:
                        continue
                    flight['_airport_name'] = airport["name"]
                    all_fetched_flights.append(flight)
            else:
                print(f"فشل جلب بيانات {airport['name']} برمز خطأ: {response.status_code}")
        except Exception as e:
            print(f"حدث خطأ استثنائي أثناء جلب بيانات {airport['name']}: {e}")

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
        
        f_id = f"{airport_name}_{f_num}_{f_type}_{f_date}_{f_time}"
        current_status = flight.get('status')
        
        if sent_notifications.get(f_id) == current_status:
            continue
        
        note = "رحلة جديدة" if f_id not in sent_notifications else "تحديث حالة الرحلة"
        send_telegram_full_details(flight, note, airport_name)
        
        sent_notifications[f_id] = current_status

scheduler = BackgroundScheduler(job_defaults={'max_instances': 2})
scheduler.add_job(func=check_flights, trigger="interval", minutes=2)
scheduler.start()

check_flights()

@app.route('/')
def home():
    return "Multi-Airport Flight Bot is running perfectly!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
