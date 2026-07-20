import requests
from flask import Flask
from bs4 import BeautifulSoup

app = Flask(__name__)

# الإعدادات
URL = 'https://damairport.gov.sy/'

@app.route('/')
def home():
    try:
        # محاكاة التصفح
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن كل صفوف الجدول
        all_tr = soup.select('tr')
        
        # استخراج التصنيفات الموجودة في الصفحة
        classes_found = []
        for tag in all_tr:
            if tag.get('class'):
                classes_found.append(tag.get('class'))
        
        # عرض النتائج في المتصفح
        return f"Found {len(all_tr)} table rows. Classes found: {classes_found}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
