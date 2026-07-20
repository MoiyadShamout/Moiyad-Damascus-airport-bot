import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# الإعدادات
TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'
API_URL = 'https://damairport.gov.sy/api/flights.php?paged=1&page=1&dir=all&wfloor=2026-07-17&dexact=2026-07-20'

flights_memory = {}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'})

def check_flights():
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()
        flights = data.get('flights', [])

        for flight in flights:
            unique_id = flight.get('id')
            raw_status = flight.get('status', '')
            
            # جلب معلومات الصالة والبوابة
            terminal = flight.get('terminal', '')
            gate = flight.get('gate', '')
            
            # معالجة المصطلحات
            display_status = raw_status.replace('scheduled', 'on time').replace('departed', 'takeoff time').replace('arrived', 'arrival time')
            
            origin_display = f"{flight.get('originText') or flight.get('origin')} ({flight.get('origin')})"
            dest_display = f"{flight.get('destinationText') or flight.get('destination')} ({flight.get('destination')})"
            location_info = f"📍 من مطار: {origin_display}\n📍 إلى مطار: {dest_display}"
            
            extra_info = ""
            if terminal: extra_info += f"🏢 الصالة: {terminal}\n"
            if gate: extra_info += f"🚪 البوابة: {gate}\n"

            # منطق التوقيت
            is_arrival = flight.get('direction') == 'arrival'
            time_label = "الوصول" if is_arrival else "الإقلاع"
            
            if raw_status == 'delayed':
                revised_time = flight.get('expectedTime')
                if revised_time:
                    time_info = f"⏰ الموعد المجدول: {flight.get('time')}\n⏱️ التوقيت الجديد: {revised_time}"
                else:
                    time_info = f"⏰ الموعد المجدول: {flight.get('time')}\n⏱️ التوقيت الجديد المتوقع: (يرجى مراجعة وكيل سفرك)"
            else:
                time_info = f"⏰ موعد {time_label}: {flight.get('time')}"

            # تحديد الإيموجي للرحلة
            direction_label = "رحلة وصول 🛬" if is_arrival else "رحلة مغادرة 🛫"

            info = (
                f"📅 التاريخ: {flight.get('date')}\n"
                f"✈️ رقم الرحلة: {flight.get('flightNumber')}\n"
                f"🏢 الناقل: {flight.get('airline')}\n"
                f"{location_info}\n"
                f"{extra_info}"
                f"{direction_label}\n"
                f"{time_info}\n"
                f"📊 الحالة: <b>{display_status}</b>\n"
                f"🔗 حالة المطار: {raw_status}"
            )

            # المنطق البرمجي لإرسال الإشعار
            if unique_id not in flights_memory or flights_memory[unique_id] != raw_status:
                if raw_status == 'boarding':
                    send_telegram(f"📢 <b>إعلان صعود الركاب (Boarding):</b>\n\n{info}")
                else:
                    send_telegram(f"⚠️ <b>تحديث حالة الرحلة:</b>\n\n{info}")
                flights_memory[unique_id] = raw_status

    except Exception as e:
        print(f"Error: {e}")

# ضبط المؤقت
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_flights, trigger="interval", minutes=5)
scheduler.start()

@app.route('/')
def home():
    return "Bot is running automatically!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
