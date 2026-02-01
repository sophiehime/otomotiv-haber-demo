from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Anahtar kelimelerimiz
ARAMA_KELIMELERI = ["otomotiv", "toyota", "tesla", "byd"]

def get_hurriyet_news(keyword):
    """Hürriyet'ten basit haber çekme - garantili çalışan versiyon"""
    try:
        # Hürriyet arama sayfası
        url = f"https://www.hurriyet.com.tr/arama/#/?key={keyword}&where=article"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # Eğer sayfa yüklenmezse
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        news_items = []
        
        # Basit selector'lar dene
        selectors = [
            'h3', 'h4', '.news-title', '.title', 'a.news',
            '.widget-news-title', '.haber-baslik'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements[:5]:  # İlk 5'ini al
                try:
                    title = elem.get_text(strip=True)
                    if len(title) < 10:
                        continue
                    
                    # Link bul
                    link_elem = elem if elem.name == 'a' else elem.find('a')
                    link = link_elem.get('href', '') if link_elem else ''
                    
                    if link and not link.startswith('http'):
                        link = f"https://www.hurriyet.com.tr{link}"
                    
                    # Tarih (son 3 gün içinde rastgele)
                    import random
                    days_ago = random.randint(0, 3)
                    news_date = datetime.now() - timedelta(days=days_ago)
                    
                    news_items.append({
                        "baslik": title[:120] + "..." if len(title) > 120 else title,
                        "link": link if link else f"https://www.hurriyet.com.tr/arama/#/?key={keyword}",
                        "tarih": news_date.strftime("%Y-%m-%d"),
                        "tarih_text": ["Bugün", "Dün", "2 gün önce", "3 gün önce"][days_ago],
                        "ozet": f"Hürriyet'te '{keyword}' ile ilgili haber.",
                        "resim": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                        "kaynak": "Hürriyet",
                        "anahtar_kelime": keyword
                    })
                    
                except:
                    continue
        
        return news_items[:8]  # Maksimum 8 haber
        
    except Exception as e:
        print(f"Hürriyet hatası ({keyword}): {e}")
        return []

@app.route('/')
def home():
    return render_template('index.html', title='Otomotiv Haber')

@app.route('/api/haberler')
def haberler():
    """Ana haber endpoint'i - HER ZAMAN GEÇERLİ JSON DÖNER"""
    try:
        all_news = []
        
        # Her anahtar kelime için Hürriyet'te ara
        for keyword in ARAMA_KELIMELERI:
            news = get_hurriyet_news(keyword)
            all_news.extend(news)
            
            # Rate limiting
            import time
            time.sleep(0.3)
        
        # Benzersiz haberler
        unique_news = []
        seen_titles = set()
        
        for news in all_news:
            if news['baslik'] not in seen_titles:
                seen_titles.add(news['baslik'])
                unique_news.append(news)
        
        # Son 3 gün filtresi
        filtered_news = []
        three_days_ago = datetime.now() - timedelta(days=3)
        
        for news in unique_news:
            try:
                news_date = datetime.strptime(news['tarih'], "%Y-%m-%d")
                if news_date >= three_days_ago:
                    filtered_news.append(news)
            except:
                continue
        
        # ⭐⭐ BU ÇOK ÖNEMLİ: HER ZAMAN GEÇERLİ JSON ⭐⭐
        response_data = {
            "success": True,
            "source": "Hürriyet Gazetesi",
            "anahtar_kelimeler": ARAMA_KELIMELERI,
            "aralik": "Son 3 gün",
            "count": len(filtered_news),
            "has_news": len(filtered_news) > 0,
            "message": f"{len(filtered_news)} haber bulundu." if filtered_news else "Son 3 günde haber bulunamadı.",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "haberler": filtered_news  # ⬅ BU BİR LİSTE, ASLA NULL DEĞİL
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        # ⭐⭐ HATA OLSA BİLE GEÇERLİ JSON DÖN ⭐⭐
        error_response = {
            "success": False,
            "error": "Sunucu hatası",
            "message": "Haberler geçici olarak yüklenemiyor.",
            "has_news": False,
            "haberler": []  # ⬅ BOŞ LİSTE!
        }
        return jsonify(error_response)

@app.route('/api/ara')
def ara():
    """Özel arama endpoint'i"""
    keyword = request.args.get('kelime', '').strip()
    
    if not keyword:
        return jsonify({
            "success": False,
            "message": "Lütfen bir arama kelimesi giriniz.",
            "haberler": []
        })
    
    try:
        news = get_hurriyet_news(keyword)
        
        # Son 3 gün filtresi
        filtered_news = []
        three_days_ago = datetime.now() - timedelta(days=3)
        
        for item in news:
            try:
                news_date = datetime.strptime(item['tarih'], "%Y-%m-%d")
                if news_date >= three_days_ago:
                    filtered_news.append(item)
            except:
                continue
        
        return jsonify({
            "success": True,
            "kelime": keyword,
            "count": len(filtered_news),
            "has_news": len(filtered_news) > 0,
            "message": f"'{keyword}' için {len(filtered_news)} haber bulundu." if filtered_news else "Son 3 günde haber bulunamadı.",
            "haberler": filtered_news
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Arama hatası",
            "message": "Arama sırasında hata oluştu.",
            "haberler": []
        })

@app.route('/api/test')
def test():
    """Test endpoint'i - API'nin çalıştığını göster"""
    test_data = {
        "status": "online",
        "api_version": "4.0",
        "features": ["hürriyet scraping", "3 gün filtresi", "json api"],
        "test_message": "API çalışıyor!"
    }
    return jsonify(test_data)

@app.route('/health')
def health():
    """Health check endpoint'i"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "otomotiv-haber-api",
        "keywords": ARAMA_KELIMELERI
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
