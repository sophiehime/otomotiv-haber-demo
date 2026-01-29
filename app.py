from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', title='Otomotiv Haber')

@app.route('/api/haberler')
def haberler():
    try:
        # Hürriyet Otomotiv sayfasından haber çek
        url = "https://www.hurriyet.com.tr/otomotiv/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        haberler_listesi = []
        
        # Hürriyet'in haber başlıklarını bul (bu selector site yapısına göre değişebilir)
        haber_elemanlari = soup.find_all('div', class_='news-item') or soup.find_all('a', class_='news-title')
        
        # Eğer yukarıdaki class'lar çalışmazsa, alternatif seçici
        if not haber_elemanlari:
            haber_elemanlari = soup.select('h3 a')[:10]  # İlk 10 başlık
        
        for i, haber in enumerate(haber_elemanlari[:10], 1):  # İlk 10 haber
            baslik = haber.get_text(strip=True)
            link = haber.get('href', '')
            
            # Link tam URL yap
            if link and not link.startswith('http'):
                link = f"https://www.hurriyet.com.tr{link}" if link.startswith('/') else f"https://www.hurriyet.com.tr/{link}"
            
            haberler_listesi.append({
                "id": i,
                "baslik": baslik[:100] + "..." if len(baslik) > 100 else baslik,  # Kısa tut
                "kaynak": "Hürriyet Otomotiv",
                "link": link,
                "tarih": datetime.now().strftime("%Y-%m-%d")
            })
        
        # Eğer hiç haber bulamazsak, örnek haberler göster
        if not haberler_listesi:
            haberler_listesi = [
                {
                    "id": 1,
                    "baslik": "Elektrikli Araç Piyasası Büyüyor",
                    "kaynak": "Motor Trend",
                    "link": "#",
                    "tarih": "2024-01-29"
                },
                {
                    "id": 2,
                    "baslik": "2024'ün En Beklenen SUV'ları",
                    "kaynak": "Car and Driver",
                    "link": "#",
                    "tarih": "2024-01-28"
                }
            ]
        
        return jsonify({
            "success": True,
            "source": "Hürriyet Otomotiv",
            "count": len(haberler_listesi),
            "haberler": haberler_listesi
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Haberler çekilemedi, örnek veri gösteriliyor",
            "haberler": [
                {
                    "id": 1,
                    "baslik": "Elektrikli Araç Piyasası Büyüyor",
                    "kaynak": "Motor Trend",
                    "link": "#",
                    "tarih": "2024-01-29"
                },
                {
                    "id": 2,
                    "baslik": "2024'ün En Beklenen SUV'ları", 
                    "kaynak": "Car and Driver",
                    "link": "#",
                    "tarih": "2024-01-28"
                }
            ]
        })

@app.route('/api/hurriyet-test')
def hurriyet_test():
    """Hürriyet sayfasını direkt göster (debug için)"""
    try:
        url = "https://www.hurriyet.com.tr/otomotiv/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        return f"<pre>Status: {response.status_code}</pre><br>{response.text[:2000]}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/health')
def health():
    return jsonify({
        "status": "OK", 
        "message": "Otomotiv Haber API çalışıyor",
        "version": "1.1",
        "features": ["web scraping", "JSON API", "Flask"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
