import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ'
CHAT_ID = '-1004481182341'
# الرابط الذي حصلنا عليه
API_URL = 'https://damairport.gov.sy/api/flights.php?paged=1&page=1&dir=all&wfloor=2026-07-17&dexact=2026-07-20'
last_flight_ids = set()

@app.route('/')
def home():
    check_flights()
    return "Bot is active and checking flights!"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'})

def check_flights():
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()
        flights = data.get('flights', [])

        for flight in flights:
            flight_id = flight.get('id')
            
            # معالجة النصوص حسب طلبك
            status = flight.get('status', '').replace('scheduled', 'on time')
            
            # بناء نص الرسالة
            info = (
                f"✈️ <b>رحلة جديدة</b>\n"
                f"رقم الرحلة: {flight.get('flightNumber')}\n"
                f"من: {flight.get('origin')} إلى: {flight.get('destination')}\n"
                f"موعد الإقلاع: {flight.get('time')}\n"
                f"الحالة: {status}"
            )

            if flight_id and flight_id not in last_flight_ids:
                send_telegram(info)
                last_flight_ids.add(flight_id)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
