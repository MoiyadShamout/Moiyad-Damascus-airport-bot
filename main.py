import os
import threading
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask

# إعداد خادم الويب ليوافق شروط Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!", 200

# بيانات البوت
TELEGRAM_TOKEN = "8975492791:AAEzDgBx2ZIPrSCylVqTHO-rquRgB_crKfM"
TELEGRAM_CHAT_ID = "-1002237894561"
URL = "https://damairport.gov.sy"
STATE_FILE = "flights_advanced_state.json"

def clean_text(text):
    return " ".join(text.split()).strip()

def fetch_live_flights():
    flights_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        if response.status_code != 200: return flights_list
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all(['tr', 'div'])
        for row in rows:
            text = clean_text(row.get_text(separator=" "))
            if any(k in text for k in ["وصول", "مغادرة", "XH", "RB", "فلاي شام", "السورية"]):
                parts = text.split()
                if len(parts) >= 4:
                    f_num = parts[0]
                    f_airline = "فلاي شام" if "فلاي" in text or "شام" in text else "السورية للطيران"
                    f_airport = "مطار حلب الدولي" if "حلب" in text else "مطار دمشق الدولي"
                    f_origin = "وجهة إقليمية"
                    f_status = "🛬 وصلت" if "وصول" in text else "🛫 أقلعت" if "مغادرة" in text else "⏰ مجدولة"
                    time_parts = [p for p in parts if ":" in p and len(p) == 5]
                    f_scheduled_time = time_parts[0] if time_parts else "04:30"
                    
                    flights_list.append({
                        "num": f_num, "airline": f_airline, "airport": f_airport, 
                        "origin": f_origin, "status": f_status, 
                        "scheduled_time": f_scheduled_time, "estimated_time": f_scheduled_time,
                        "type": "رحلة وصول" if "وصول" in text else "رحلة مغادرة",
                        "direction_label": "القادمة من" if "وصول" in text else "المتجهة إلى"
                    })
    except: pass
    return flights_list

def broadcast_telegram_alert(flight):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    message = f"✅ تحديث حالة الرحلة {flight['num']}\nالحالة: {flight['status']}\nالموعد: {flight['scheduled_time']}"
    requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})

def run_bot():
    """وظيفة الرصد التي تعمل في الخلفية"""
    past_state = {}
    while True:
        live_flights = fetch_live_flights()
        for flight in live_flights:
            f_num = flight["num"]
            if f_num not in past_state or past_state[f_num] != flight["status"]:
                broadcast_telegram_alert(flight)
                past_state[f_num] = flight["status"]
        time.sleep(600) # فحص كل 10 دقائق

if __name__ == "__main__":
    # تشغيل الرصد في Thread منفصل
    threading.Thread(target=run_bot, daemon=True).start()
    # تشغيل الخادم
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
