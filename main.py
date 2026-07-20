import os
import requests
from flask import Flask
from bs4 import BeautifulSoup

app = Flask(__name__)

# ضع التوكن الصحيح والـ ID الجديد هنا
TELEGRAM_TOKEN = "8975492791:AAEzDgBx2ZIPrSCylVqTHO-rquRgB_crKfM"
TELEGRAM_CHAT_ID = "-1004481182341"

def get_flights():
    # هذا الرابط هو الرابط الذي يحتوي على بيانات الرحلات (تأكد أنه الرابط الصحيح للمطار)
    url = "https://damascus-airport.com/" # استبدل هذا بالرابط الفعلي إذا لزم الأمر
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # تنسيق الجدول بشكل نصي يناسب تليغرام
        message = "✈️ *جدول رحلات مطار دمشق الدولي*\n\n"
        message += "`رقم الرحلة | شركة الطيران | الوجهة | الحالة | الوقت`\n"
        message += "`---------------------------------------------------`\n"
        
        # ملاحظة: هذا الجزء يعتمد على شكل الموقع (HTML) وسيحتاج لتعديل بسيط 
        # بناءً على كيف يتم عرض الجدول في موقع المطار الفعلي
        rows = soup.find_all('tr') 
        for row in rows[:10]: # نجلب أول 10 رحلات
            cols = [col.text.strip() for col in row.find_all('td')]
            if len(cols) >= 5:
                message += f"`{cols[0]} | {cols[1]} | {cols[2]} | {cols[3]} | {cols[4]}`\n"
        
        return message
    except Exception as e:
        return f"⚠️ تعذر جلب البيانات: {str(e)}"

@app.route('/')
def home():
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    flight_data = get_flights()
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": flight_data,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(telegram_url, json=payload)
    if response.status_code == 200:
        return "✅ تم جلب وإرسال جدول الرحلات بنجاح إلى القناة!"
    else:
        return f"❌ فشل الإرسال: {response.text}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
