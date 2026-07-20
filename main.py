import os
import requests
from flask import Flask

app = Flask(__name__)

# تأكد من أن هذه الأرقام هي التي حصلت عليها من BotFather ومن قناتك
TELEGRAM_TOKEN = "8975492791:AAEzDgBx2ZIPrSCylVqTH0-rquRgB_crKfM"
TELEGRAM_CHAT_ID = "-1002237894561"

@app.route('/')
def home():
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": "اختبار اتصال جديد"}
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=15)
        # هنا سنرى السبب الحقيقي للخطأ في المتصفح
        if response.status_code == 200:
            return "✅ تم الإرسال بنجاح!", 200
        else:
            return f"❌ فشل الإرسال. كود الخطأ: {response.status_code} | التفاصيل: {response.text}", 200
    except Exception as e:
        return f"❌ خطأ في الاتصال: {str(e)}", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
