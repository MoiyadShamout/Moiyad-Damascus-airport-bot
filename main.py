import os
import requests
from flask import Flask

app = Flask(__name__)

# تأكد من وضع التوكن الخاص بك هنا بدقة
TELEGRAM_TOKEN = "8975492791:AAEzDgBx2ZIPrSCylVqTHO-rquRgB_crKfM"
TELEGRAM_CHAT_ID = "-1004481182341"

def get_flights():
    # نص بسيط بدون تنسيق Markdown معقد لتجنب أخطاء الـ parsing
    message = "✈️ جدول رحلات مطار دمشق الدولي:\n\n"
    message += "رقم الرحلة | شركة الطيران | الحالة\n"
    message += "----------------------------------\n"
    message += "F3741 | طيران أديل | وصلت\n"
    message += "G9363 | العربية | وصلت\n"
    message += "J9173 | طيران الجزيرة | متوقع\n"
    return message

@app.route('/')
def home():
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    flight_data = get_flights()
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": flight_data
    }
    
    response = requests.post(telegram_url, json=payload)
    if response.status_code == 200:
        return "✅ تم الإرسال بنجاح إلى القناة!"
    else:
        return f"❌ فشل الإرسال: {response.text}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
