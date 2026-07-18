import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os

# --- الإعدادات الفنية الخاصة بك ---
TOKEN = "8975492791:AAEzDgBx2ZIPrScyLvqTHO-rquRgB_crKFm"
CHAT_ID = "@Moiyad_update_Dam_Airport_Flight" 

# استخدام واجهة طيران بديلة ومفتوحة للسيرفرات لتجنب حظر موقع المطار الجغرافي
URL = "https://aviationstack.com"
# هذا المفتاح مجاني ومفتوح لجلب رحلات مطار دمشق الدولي بدقة
API_KEY = "3b00085a6764516d2ca858066c6bbf85" 

class DummyWebhookServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive and monitoring flights!")
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
    def log_message(self, format, *args):
        return

def send_telegram(message):
    telegram_url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        print("استجابة تليجرام:", response.status_code, response.text)
    except Exception as e:
        print("خطأ في إرسال التليجرام:", e)

def check_flights():
    print("جاري فحص الرحلات القادمة إلى مطار دمشق عبر الرادار العالمي...")
    params = {
        'access_key': API_KEY,
        'arr_iata': 'DAM', # كود مطار دمشق الدولي عالمياً
        'flight_status': 'landed'
    }
    try:
        response = requests.get(URL, params=params, timeout=15)
        if response.status_code != 200:
            return []
        
        data = response.json()
        flights = []
        for flight in data.get('data', []):
            flight_info = {
                "number": flight.get('flight', {}).get('iata', 'غير محدد'),
                "origin": flight.get('departure', {}).get('airport', 'غير محدد'),
                "time": flight.get('arrival', {}).get('scheduled', 'غير محدد')[:16].replace('T', ' '),
                "status": "وصلت",
                "airline": flight.get('airline', {}).get('name', 'غير محدد')
            }
            flights.append(flight_info)
        return flights
    except Exception as e:
        print("خطأ أثناء جلب البيانات من الرادار:", e)
        return []

def airport_monitor():
    flight_registry = {}
    print("إرسال رسالة انطلاق النظام الفورية...")
    send_telegram("🚀 تم تشغيل نظام أتمتة إشعارات مطار دمشق الدولي بنجاح! المنظومة تعتمد الآن على الرادار العالمي لتفادي الحجب وتعمل بكفاءة.")
    
    while True:
        current_flights = check_flights()
        for flight in current_flights:
            f_num = flight["number"]
            f_status = flight["status"]
            f_origin = flight["origin"]
            f_time = flight["time"]
            f_airline = flight["airline"]
            
            if not f_num or f_num == "غير محدد":
                continue
                
            if f_num not in flight_registry:
                flight_registry[f_num] = f_status
                msg = (
                    f"🛬 **إشعار وصول رحلة الآن**\n\n"
                    f"🔢 **رقم الرحلة:** **{f_num}**\n"
                    f"✈️ **شركة الطيران:** *{f_airline}*\n"
                    f"📍 **القادمة من:** **{f_origin}**\n"
                    f"🏛️ **إلى:** **مطار دمشق الدولي**\n"
                    f"📊 **الحالة:** `{f_status}`\n"
                    f"⏰ **التوقيت:** {f_time}"
                )
                send_telegram(msg)
                
        time.sleep(300)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: HTTPServer(("0.0.0.0", port), DummyWebhookServer).serve_forever(), daemon=True).start()
    airport_monitor()
