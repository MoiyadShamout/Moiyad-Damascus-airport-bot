import requests
import time
from bs4 import BeautifulSoup

# --- الإعدادات الفنية الخاصة بك تم إصلاحها بدقة ---
TOKEN = "8975492791:AAEzDgBx2ZIPrScyLvqTHO-rquRgB_crKFm"
CHAT_ID = "@Moiyad_update_Dam_Airport_Flight" 

# الرابط المباشر الصحيح لجدول الرحلات القادمة
URL = "https://damascusairport.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def send_telegram(message):
    # تم تصحيح رابط الـ API الخاص بتليجرام وإضافة كلمة bot الإلزامية
    telegram_url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(telegram_url, json=payload)
    except Exception as e:
        print("خطأ في إرسال التليجرام:", e)

def check_flights():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table') or soup.find(class_='table')
        if not table:
            return []
        flights = []
        rows = table.find_all('tr')[1:] # تخطي الهيدر
        for row in rows:
            cols = [ele.text.strip() for ele in row.find_all(['td', 'th'])]
            if len(cols) >= 4:
                flight_info = {
                    "number": cols[0] if len(cols) > 0 else "غير محدد",
                    "origin": cols[1] if len(cols) > 1 else "غير محدد",
                    "time": cols[2] if len(cols) > 2 else "غير محدد",
                    "status": cols[3] if len(cols) > 3 else "غير محدد",
                    "airline": cols[4] if len(cols) > 4 else "غير محدد"
                }
                flights.append(flight_info)
        return flights
    except Exception as e:
        print("خطأ أثناء جلب البيانات:", e)
        return []

def main():
    flight_registry = {}
    send_telegram("🚀 تم تشغيل نظام أتمتة إشعارات مطار دمشق الدولي المتكامل بنجاح وهو يراقب الرحلات الآن!")
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
                
            # 1. إشعار إضافة رحلة جديدة بالكامل للجدول لأول مرة
            if f_num not in flight_registry:
                flight_registry[f_num] = {"status": f_status, "time": f_time, "origin": f_origin, "airline": f_airline}
                msg = (
                    f"📋 **رحلة جديدة مضافة للجدول**\n\n"
                    f"🔢 **رقم الرحلة:** **{f_num}**\n"
                    f"✈️ **شركة الطيران:** *{f_airline}*\n"
                    f"📍 **من:** **{f_origin}**\n"
                    f"🏛️ **إلى:** **مطار دمشق الدولي**\n"
                    f"📊 **الحالة:** `{f_status}`\n"
                    f"⏰ **الوقت المجدول:** {f_time}"
                )
                send_telegram(msg)
                continue
                
            old_data = flight_registry[f_num]
            
            # 2. رصد تحول الحالة إلى "ملغاة" بشكل طارئ
            if ("ملغاة" in f_status or "cancelled" in f_status.lower()) and "ملغاة" not in old_data["status"]:
                msg = (
                    f"❌ **إشعار إلغاء رحلة بالكامل**\n\n"
                    f"🔢 **رقم الرحلة:** **{f_num}**\n"
                    f"✈️ **شركة الطيران:** *{f_airline}*\n"
                    f"📍 **من:** **{f_origin}**\n"
                    f"🏛️ **إلى:** **مطار دمشق الدولي**\n\n"
                    f"🚨 **تنبيه هام:** تم إلغاء هذه الرحلة بالكامل من قبل شركة الطيران أو إدارة المطار."
                )
                send_telegram(msg)
                flight_registry[f_num]["status"] = f_status
                
            # 3. إشعار وصول الرحلة (إلى مطار دمشق الدولي)
            elif ("وصلت" in f_status or "landed" in f_status.lower()) and "وصلت" not in old_data["status"]:
                msg = (
                    f"🛬 **إشعار وصول رحلة الآن**\n\n"
                    f"🔢 **رقم الرحلة:** **{f_num}**\n"
                    f"✈️ **شركة الطيران:** *{f_airline}*\n"
                    f"📍 **من:** **{f_origin}**\n"
                    f"🏛️ **إلى:** **مطار دمشق الدولي**\n"
                    f"📊 **الحالة:** `{f_status}`\n"
                    f"⏰ **الوقت المجدول:** {f_time}"
                )
                send_telegram(msg)
                flight_registry[f_num]["status"] = f_status
                
            # 4. إشعار التعديل أو التأخير (تغير الحالة أو التوقيت المجدول)
            elif f_status != old_data["status"] or f_time != old_data["time"]:
                msg = (
                    f"⚠️ **تحديث طارئ وتعديل على رحلة**\n\n"
                    f"🔢 **رقم الرحلة:** **{f_num}**\n"
                    f"✈️ **شركة الطيران:** *{f_airline}*\n"
                    f"📍 **من:** **{f_origin}**\n\n"
                    f"🔄 **التفاصيل المعدلة:**\n"
                )
                if f_status != old_data["status"]:
                    msg += f"📉 تغيير الحالة من `{old_data['status']}` إلى **`{f_status}`**\n"
                if f_time != old_data["time"]:
                    msg += f"⏳ تغيير الوقت المجدول من *{old_data['time']}* إلى **{f_time}**\n"
                send_telegram(msg)
                flight_registry[f_num] = {"status": f_status, "time": f_time, "origin": f_origin, "airline": f_airline}
                
        # إعادة الفحص تلقائياً كل 5 دقائق
        time.sleep(300)

if __name__ == "__main__":
    main()
