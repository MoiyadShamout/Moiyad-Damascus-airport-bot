from flask import Flask
import requests
import sqlite3
import os
import threading
import time

app = Flask(__name__)

# إعداد قاعدة البيانات الدائمة على القرص لمنع التكرار حتى بعد إعادة تنشيط البوت
def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    # جدول لتخزين آخر حالة لكل رحلة مع تاريخها لمنع تكرار الإشعارات المطلق
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_last_status (
            flight_key TEXT PRIMARY KEY,
            flight_number TEXT,
            flight_date TEXT,
            last_status TEXT,
            last_update_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def send_telegram_message(text):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    channel_id = os.environ.get('TELEGRAM_CHANNEL_ID')
    if bot_token and channel_id:
        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            requests.post(telegram_url, json={
                'chat_id': channel_id,
                'text': text,
                'parse_mode': 'Markdown'
            }, timeout=10)
        except Exception as e:
            print(f"Telegram error: {e}")

# دالة فحص الرحلات مع منع التكرار المطلق وحفظ الحالة بشكل دائم
def check_flights_loop():
    while True:
        try:
            # بيانات تجريبية للرحلة (يمكنك ربطها بسحب البيانات الفعلي لاحقاً)
            flight_number = "VF341"
            flight_date = "22-07-2026"
            current_status = "في الجو"  # أو "في موعدها"
            update_time = "09:22"
            
            # مفتاح فريد يدمج رقم الرحلة مع تاريخها لمنع أي تداخل
            flight_key = f"{flight_number}_{flight_date}"
            
            conn = sqlite3.connect('bot_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            # التحقق مما إذا كانت هذه الرحلة وتاريخها قد أرسلت مسبقاً
            cursor.execute("SELECT last_status FROM flight_last_status WHERE flight_key = ?", (flight_key,))
            row = cursor.fetchone()
            
            if row is None:
                # إذا كانت المرة الأولى للرحلة بهذا التاريخ، يتم تخزينها وإرسال الإشعار
                cursor.execute("""
                    INSERT INTO flight_last_status (flight_key, flight_number, flight_date, last_status, last_update_time) 
                    VALUES (?, ?, ?, ?, ?)
                """, (flight_key, flight_number, flight_date, current_status, update_time))
                conn.commit()
                
                message = f"⚠️ *تحديث حالة الرحلة (مطار حلب الدولي)*\n\n✈️ رحلة مغادرة من مطار حلب الدولي\n📅 التاريخ: {flight_date}\n✈️ رقم الرحلة: {flight_number}\n🏢 الناقل: AJet\n🛫 مغادرة من: مطار حلب الدولي\n🛬 متجهة إلى: مطار Istanbul\n⏰ موعد المغادرة المحدد: 09:10\n⌚ وقت الإقلاع: {update_time}\n📊 الحالة: {current_status}"
                send_telegram_message(message)
                
            else:
                last_status = row[0]
                # الشرط الحاسم: لا يُرسل أي إشعار نهائياً إلا إذا تغيرت الحالة الفعلية مقارنة بآخر حالة مسجلة
                if last_status != current_status:
                    cursor.execute("""
                        UPDATE flight_last_status 
                        SET last_status = ?, last_update_time = ? 
                        WHERE flight_key = ?
                    """, (current_status, update_time, flight_key))
                    conn.commit()
                    
                    message = f"⚠️ *تحديث حالة الرحلة (مطار حلب الدولي)*\n\n✈️ رحلة مغادرة من مطار حلب الدولي\n📅 التاريخ: {flight_date}\n✈️ رقم الرحلة: {flight_number}\n🏢 الناقل: AJet\n🛫 مغادرة من: مطار حلب الدولي\n🛬 متجهة إلى: مطار Istanbul\n⏰ موعد المغادرة المحدد: 09:10\n⌚ وقت الإقلاع: {update_time}\n📊 الحالة: {current_status}"
                    send_telegram_message(message)
            
            conn.close()
            
        except Exception as e:
            print(f"Error in flight check loop: {e}")
            
        # فترة الانتظار بين عمليات الفحص (مثلاً كل 30 دقيقة)
        time.sleep(1800)

# تشغيل حلقة الفحص في الخلفية بشكل آمن ودائم
threading.Thread(target=check_flights_loop, daemon=True).start()

@app.route('/')
def home():
    return "Syrian Tourism & SANA Bot: Running with permanent duplicate-prevention!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
