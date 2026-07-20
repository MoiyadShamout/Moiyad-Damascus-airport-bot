import requests
from flask import Flask
from bs4 import BeautifulSoup

app = Flask(__name__)
TELEGRAM_TOKEN = '8975492791:AAGg_v5cRNnuo3gqdi9msdZrarzFcpO7ZzQ' # تأكد من وضعه الصحيح هنا
CHAT_ID = '-1004481182341'
URL = 'https://damairport.gov.sy/'

@app.route('/')
def home():
    # عملية سحب البيانات وإرسالها فوراً
    try:
        response = requests.get(URL, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.flight-row')
        
        if not rows:
            return "No flight data found on the page!"
            
        for row in rows:
            info = row.get('aria-label', '')
            if info:
                # إرسال مباشر لكل رحلة
                send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                requests.post(send_url, data={'chat_id': CHAT_ID, 'text': f"✈️ تجربة وصول: {info}"})
        
        return "Check initiated! Check your Telegram channel."
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
