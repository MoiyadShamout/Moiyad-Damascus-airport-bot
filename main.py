import os
import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_TOKEN = "8975492791:AAEzDgBx2ZIPrSCylVqTHO-rquRgB_crKfM"
TELEGRAM_CHAT_ID = "-1002237894561"

@app.route('/')
def home():
    # عملية اتصال بسيطة جداً للتجربة فقط
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": "✅ البوت يعمل بنجاح من Render!"}
        requests.post(telegram_url, json=payload, timeout=10)
        return "تم إرسال الإشعار بنجاح إلى تليغرام!", 200
    except Exception as e:
        return f"حدث خطأ: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
