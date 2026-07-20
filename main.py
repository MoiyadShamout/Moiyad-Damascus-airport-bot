import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

API_URL = "https://ognrupehzbbckimkaikb.supabase.co/rest/v1/flight_cache?select=payload%2Cupdated_at%2Ctotal_arrivals%2Ctotal_departures&id=eq.main"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nbnJ1cGVoemJiY2tpbWthaWtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODc3NTIsImV4cCI6MjA4MDI2Mzc1Mn0.cBh06V2W7ocx8etUixo2lcdl1XH5RR4pTjXNOG59Xsg",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nbnJ1cGVoemJiY2tpbWthaWtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODc3NTIsImV4cCI6MjA4MDI2Mzc1Mn0.cBh06V2W7ocx8etUixo2lcdl1XH5RR4pTjXNOG59Xsg",
    "accept": "application/vnd.pgrst.object+json"
}

TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

last_flights_data = {}
is_initialized = False

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'})

def send_telegram_full_details(flight, note):
    direction = "🛬 رحلة وصول" if flight.get('direction') == 'arrival' else "🛫 رحلة مغادرة"
    msg = (
        f"<b>⚠️ {note}</b>\n\n"
        f"<b>{direction}</b>\n"
        f"📅 التاريخ: {flight.get('date', 'غير متوفر')}\n"
        f"✈️ رقم الرحلة: {flight.get('flight_number', 'غير متوفر')}\n"
        f"🏢 الناقل: {flight.get('airline', 'غير متوفر')}\n"
        f"📍 من: {flight.get('origin', 'غير متوفر')}\n"
        f"📍 إلى: {flight.get('destination', 'غير متوفر')}\n"
        f"⏰ الموعد: {flight.get('time', 'غير متوفر')}\n"
    )
    terminal = flight.get('terminal')
    if terminal and str(terminal).strip(): msg += f"🏢 الصالة: {terminal}\n"
    gate = flight.get('gate')
    if gate and str(gate).strip(): msg += f"🚪 البوابة: {gate}\n"
    msg += f"📊 الحالة: <b>{flight.get('status', 'غير متوفر')}</b>"
    send_telegram(msg)

def check_flights():
    global last_flights_data, is_initialized
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list): data = data[0]
            flights = data.get('payload', [])
            
            for flight in flights:
                f_id = flight.get('flight_number')
                current_status = flight.get('status')
                
                if not is_initialized:
                    send_telegram_full_details(flight, "رحلة حالية في الجدول")
                elif f_id in last_flights_data and last_flights_data[f_id].get('status') != current_status:
                    send_telegram_full_details(flight, "تحديث حالة الرحلة")
                
                last_flights_data[f_id] = flight
            
            is_initialized = True
    except Exception as e:
        print(f"Update error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_flights, trigger="interval", minutes=2)
scheduler.start()

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
