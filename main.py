import requests
import time
import os
from flask import Flask
import threading

# --- الإعدادات الفنية الخاصة بك ---
TOKEN = "8975492791:AAEzDgBx2ZIPrScyLvqTHO-rquRgB_crKFm"
CHAT_ID = "@Moiyad_update_Dam_Airport_Flight" 

URL = "https://aviationstack.com"
API_KEY = "3b00085a6764516d2ca858066c6bbf85" 

# --- استخدام إطار عمل Flask لتوليد ويب حقيقي متوافق مع Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and tracking Damascus airport!", 200

def send_telegram(message):
    telegram_url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        print(f"استجابة تليجرام الفورية: {response.status_code}")
    except Exception as e:
        print("خطأ في إرسال التليجرام:", e)

def check_flights():
    print("جاري سحب بيانات الرحلات من الرادار الدولي...")
    params = {
        'access_key': API_KEY,
        'arr_iata': 'DAM',
        'flight_status': 'landed'
    }
    try:
        response = requests.get(URL, params=params, timeout=15)
        if response.status_code == 200:
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
        return []
    except Exception as e:
        print("خطأ في الرادار:", e)
        return []

def airport_monitor():
    # الفحص الدوري في الخلفية
    flight_registry = {}
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

# تشغيل الفحص والترحيب فوراً عند إقلاع السيرفر
print("إرسال إشعار تشغيل النظام...")
send_telegram("🚀 تم تشغيل نظام أتمتة إشعارات مطار دمشق الدولي بنجاح! المنظومة تعتمد الآن على الرادار العالمي لتفادي الحجب وتعمل بكفاءة 100%.")

if __name__ == "__main__":
    # تشغيل الفحص في خيط منفصل
    threading.Thread(target=airport_monitor, daemon=True).start()
    # تشغيل Flask لتلبية متطلبات البورت في Render المجاني
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
