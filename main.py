import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

app = Flask(__name__)

TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'

flights_memory = {}
is_initialized = False 

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'})
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_all_flights():
    global is_initialized
    tz = pytz.timezone('Asia/Damascus')
    today = datetime.now(tz).strftime('%Y-%m-%d')
    api_url = f'https://damairport.gov.sy/api/flights.php?paged=1&page=1&dir=all&wfloor={today}&dexact={today}'
    
    try:
        response = requests.get(api_url, timeout=15)
        data = response.json()
        flights = data.get('flights', [])

        for flight in flights:
            unique_key = f"{flight.get('flightNumber')}_{flight.get('time')}"
            raw_status = str(flight.get('status', '')).lower()
            
            # تحديد نوع الرحلة (وصول أو مغادرة)
            direction = flight.get('direction', '').lower()
            direction_label = "رحلة وصول 🛬" if direction == 'arrival' else "رحلة مغادرة 🛫"
            
            display_status = raw_status.replace('scheduled', 'on time').replace('departed', 'takeoff time').replace('arrived', 'arrival time')
            
            info = (
                f"{direction_label}\n"
                f"📅 التاريخ: {flight.get('date')}\n"
                f"✈️ رقم الرحلة: {flight.get('flightNumber')}\n"
                f"🏢 الناقل: {flight.get('airline')}\n"
                f"📍 من: {flight.get('originText')} ({flight.get('origin')})\n"
                f"📍 إلى: {flight.get('destinationText')} ({flight.get('destination')})\n"
                f"⏰ الموعد: {flight.get('time')}\n"
                f"🏢 الصالة: {flight.get('terminal', 'غير محدد')}\n"
                f"🚪 البوابة: {flight.get('gate', 'غير محدد')}\n"
                f"📊 الحالة: <b>{display_status}</b>"
            )

            if not is_initialized:
                send_telegram(f"📋 <b>جدول الرحلات الحالي:</b>\n\n{info}")
                flights_memory[unique_key] = raw_status
            else:
                if unique_key in flights_memory:
                    if flights_memory[unique_key] != raw_status:
                        send_telegram(f"⚠️ <b>تحديث حالة الرحلة:</b>\n\n{info}")
                        flights_memory[unique_key] = raw_status
                else:
                    send_telegram(f"🆕 <b>رحلة جديدة في الجدول:</b>\n\n{info}")
                    flights_memory[unique_key] = raw_status
        
        is_initialized = True

    except Exception as e:
        print(f"Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_all_flights, trigger="interval", minutes=5)
scheduler.start()

@app.route('/')
def home():
    return "Bot is tracking ALL flights with direction!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
