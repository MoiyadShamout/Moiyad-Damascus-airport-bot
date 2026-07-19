import os
import time
import json
import requests
from bs4 import BeautifulSoup

# بيانات الربط الصارمة والنهائية الخاصة ببوتك وقناتك لضمان التشغيل الفوري
TELEGRAM_TOKEN = "8975492791:AAEzDgBx2ZIPrSCylVqTHO-rquRgB_crKfM"
TELEGRAM_CHAT_ID = "-1002237894561"

URL = "https://damairport.gov.sy"
STATE_FILE = "flights_advanced_state.json"

def clean_text(text):
    """تنظيف النصوص وإزالة الفراغات الزائدة لمنع أخطاء القراءة"""
    return " ".join(text.split()).strip()

def fetch_live_flights():
    """سحب الجداول الحية للقادمين والمغادرين من الموقع الحكومي الموحد"""
    flights_list = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"[-] فشل الاتصال بالموقع الحكومي الموحد. كود الحالة: {response.status_code}")
            return flights_list
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # قراءة الأسطر البرمجية للجداول ديناميكياً لتخطي جدار الحماية الحكومي الجديد
        rows = soup.find_all(['tr', 'div'], class_=lambda c: c and any(w in c.lower() for w in ['flight', 'row', 'auto', 'table']))
        if not rows:
            rows = soup.find_all('tr')
            
        for row in rows:
            text = clean_text(row.get_text(separator=" "))
            
            # فلترة ذكية لالتقاط أسطر الرحلات السورية والإقليمية النشطة فقط
            if any(k in text for k in ["وصول", "مغادرة", "XH", "فلاي شام", "السورية"]):
                parts = text.split()
                if len(parts) >= 4:
                    # تفكيك النص وتوزيع البيانات بدقة على مصفوفة الرحلة
                    f_num = parts[1] if len(parts) > 1 else parts[0]
                    f_airline = "فلاي شام" if "فلاي" in text or "شام" in text else "السورية للطيران"
                    
                    # استخراج وتحديد مكان المطار ونوع الاتجاه
                    f_airport = "مطار حلب الدولي" if "حلب" in text else "مطار دمشق الدولي"
                    f_origin = "طرابلس - MJI" if "طرابلس" in text else ("دبي - DXB" if "دبي" in text else "وجهة إقليمية")
                    
                    # محرك ذكي لتصنيف الحالة الحالية المتغيرة من شاشة المطار
                    if "ملغاة" in text or "إلغاء" in text or "ملغاه" in text:
                        f_status = "ملغاة"
                    elif "متأخرة" in text or "تأخير" in text or "تأخرت" in text:
                        f_status = "تأخرت"
                    elif "تعديل" in text or "تعدلت" in text:
                        f_status = "تعدلت"
                    elif "وصول" in text or "وصلت" in text:
                        f_status = "وصلت"
                    elif "مغادرة" in text or "أقلعت" in text:
                        f_status = "أقلعت"
                    else:
                        f_status = "مجدولة"
                    
                    # قراءة نمط التوقيت المحدث للرحلة
                    time_parts = [p for p in parts if ":" in p and len(p) == 5]
                    f_time = time_parts[0] if time_parts else "00:15"
                    
                    # تحديد اتجاه الرحلة (مغادرة أو قادمة) لصياغة نص دقيق تسويقياً للشركات
                    f_type = "DEPARTURE" if "مغادرة" in text or "أقلعت" in text else "ARRIVAL"
                    
                    flights_list.append({
                        "num": f_num,
                        "airline": f_airline,
                        "airport": f_airport,
                        "origin": f_origin,
                        "status": f_status,
                        "time": f_time,
                        "type": f_type
                    })
    except Exception as e:
        print(f"[-] حدث خطأ أثناء معالجة البيانات الحية: {e}")
        
    return flights_list

def load_previous_state():
    """تحميل ذاكرة السيرفر للرحلات السابقة"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_current_state(state):
    """تثبيت الذاكرة المؤقتة الحالية للدورة القادمة"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def broadcast_telegram_alert(flight, alert_type):
    """بناء الإشعارات بالأسطر المنفصلة والإيموجي المخصص لكل حالة وبثها فوراً"""
    
    # صياغة ترويية الرسالة والحالة بناءً على نوع التغير المكتشف في الجدول
    if alert_type == "CANCELLED":
        header = "❌ **إشعار إلغاء رحلة جوية عاجل**\n\n"
        status_display = "`ملغاة بالكامل من المصدر` ⚠️"
    elif alert_type == "DELAYED":
        header = "⏳ **إشعار تأخر رحلة جوية الآن**\n\n"
        status_display = "`متأخرة عن موعدها المحدد` ⏰"
    elif alert_type == "MODIFIED":
        header = "🔄 **إشعار تعديل وقت الرحلة الجوية**\n\n"
        status_display = "`تم تعديل توقيت الإقلاع/الهبوط المجدول` ⏱️"
    elif alert_type == "ARRIVED":
        header = "🛬 **إشعار وصول رحلة الآن**\n\n"
        status_display = "`وصلت بسلام وأمان` ✅"
    else:
        header = "🛫 **إشعار إقلاع رحلة الآن**\n\n"
        status_display = "`أقلعت بحفظ الله` ✈️"

    # صياغة السطور المنفصلة وتحديد جهة الطيران (قادمة من أو متجهة إلى) بناءً على نوع الجدول
    direction_label = "المتجهة إلى" if flight['type'] == "DEPARTURE" else "القادمة من"
    location_label = "من" if flight['type'] == "DEPARTURE" else "إلى"
    
    message = (
        f"{header}"
        f"🔢 **رقم الرحلة:** **{flight['num']}**\n"
        f"✈️ **شركة الطيران:** *{flight['airline']}*\n"
        f"📍 **{direction_label}:** **{flight['origin']}**\n"
        f"🏛️ **{location_label}:** **{flight['airport']}**\n"
        f"📊 **الحالة:** {status_display}\n"
        f"⏰ **التوقيت:** {flight['time']}"
    )
    
    telegram_url = f"https://telegram.com{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(telegram_url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"[+] تم بث الإشعار المنفصل للرحلة: {flight['num']}")
        else:
            print(f"[-] خطأ تليغرام: {res.text}")
    except Exception as e:
        print(f"[-] فشل الاتصال بتليغرام: {e}")

def main():
    print("[+] انطلاق نظام تتبع الطيران السوري الموحد في السحاب (دمشق وحلب)...")
    
    while True:
        live_flights = fetch_live_flights()
        past_state = load_previous_state()
        current_state = {}
        
        for flight in live_flights:
            f_num = flight["num"]
            live_status = flight["status"]
            live_time = flight["time"]
            
            # حفظ الحالة والتوقيت الحالي في مصفوفة المقارنة العميقة
            current_state[f_num] = {"status": live_status, "time": live_time}
            
            # رصد الفروقات البرمجية وإطلاق التنبيهات المستقلة فوراً عند التعديل
            if f_num in past_state:
                old_status = past_state[f_num]["status"]
                old_time = past_state[f_num]["time"]
                
                if live_status != old_status:
                    if live_status == "ملغاة":
                        broadcast_telegram_alert(flight, "CANCELLED")
                    elif live_status == "تأخرت":
                        broadcast_telegram_alert(flight, "DELAYED")
                    elif live_status == "تعدلت":
                        broadcast_telegram_alert(flight, "MODIFIED")
                    elif live_status == "وصلت":
                        broadcast_telegram_alert(flight, "ARRIVED")
                    elif live_status == "أقلعت":
                        broadcast_telegram_alert(flight, "DEPARTED")
                elif live_time != old_time:
                    broadcast_telegram_alert(flight, "MODIFIED")
            else:
                # رصد بث الرحلات المحدثة لأول مرة على شاشات المطارات
                if live_status in ["وصلت", "أقلعت", "تأخرت", "ملغاة"]:
                    broadcast_telegram_alert(flight, live_status.upper())
                    
        save_current_state(current_state)
        
        # فحص دوري مستقر وآمن للموقع كل 15 دقيقة (900 ثانية) في السحاب
        print("[+] انتهت دورة الرصد الحالية بنجاح، السيرفر سينتظر 15 دقيقة قبل التحديث القادم...")
        time.sleep(900)

if __name__ == "__main__":
    main()
