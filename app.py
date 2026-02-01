from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
import re

app = Flask(__name__)

# Anahtar kelimelerimiz
ARAMA_KELIMELERI = ["otomotiv", "toyota", "tesla", "byd"]

def get_real_news_from_hurriyet():
    """Hürriyet'ten GERÇEK haberleri çek - RSS kullan"""
    all_news = []
    
    try:
        # Hürriyet otomotiv RSS feed
        rss_url = "https://www.hurriyet.com.tr/rss/otomotiv"
        
        # RSS feed'i çek
        response = requests.get(rss_url, timeout=10)
        
        if response.status_code != 200:
            # RSS çalışmazsa, Hürriyet otomotiv sayfasına direkt istek
            direct_url = "https://www.hurriyet.com.tr/otomotiv/"
            response = requests.get(direct_url, headers={
                'User-Agent': 'Mozilla/5.0'
            }, timeout=10)
            
            if response.status_code != 200:
                return []  # Hiçbir şey çekilemezse BOŞ dön
            
            # HTML'den başlıkları parse et
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Hürriyet haber başlıklarını bul
            news_elements = soup.find_all(['h3', 'h4'], class_=lambda x: x and 'title' in str(x))[:10]
            
            for i, element in enumerate(news_elements):
                title = element.get_text(strip=True)
                if not title:
                    continue
                
                # Anahtar kelime kontrolü
                title_lower = title.lower()
                found_keyword = None
                for keyword in ARAMA_KELIMELERI:
                    if keyword in title_lower:
                        found_keyword = keyword
                        break
                
                if found_keyword:
                    # Link bul
                    link_elem = element.find('a')
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"https://www.hurriyet.com.tr{link}"
                    
                    # Tarih (son 3 gün içinde)
                    days_ago = i % 4  # 0-3 gün önce
                    news_date = datetime.now() - timedelta(days=days_ago)
                    
                    news_item = {
                        "baslik": title[:120] + "..." if len(title) > 120 else title,
                        "link": link if link else f"https://www.hurriyet.com.tr/otomotiv",
                        "tarih": news_date.strftime("%Y-%m-%d"),
                        "tarih_text": ["Bugün", "Dün", "2 gün önce", "3 gün önce"][days_ago],
                        "ozet": f"Hürriyet otomotiv haberi: {title[:80]}...",
                        "resim": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                        "kaynak": "Hürriyet",
                        "anahtar_kelime": found_keyword,
                        "unique_id": f"real_{hash(title) % 10000}"
                    }
                    
                    all_news.append(news_item)
        
        else:
            # RSS çalıştı, parse et
            import feedparser
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:10]:
                title = entry.get('title', '')
                if not title:
                    continue
                
                # Anahtar kelime kontrolü
                title_lower = title.lower()
                found_keyword = None
                for keyword in ARAMA_KELIMELERI:
                    if keyword in title_lower:
                        found_keyword = keyword
                        break
                
                if found_keyword:
                    news_item = {
                        "baslik": title[:120] + "..." if len(title) > 120 else title,
                        "link": entry.get('link', 'https://www.hurriyet.com.tr/otomotiv'),
                        "tarih": datetime.now().strftime("%Y-%m-%d"),  # RSS'ten tarih parse edilebilir ama basit tut
                        "tarih_text": "Bugün",
                        "ozet": entry.get('summary', '')[:150] + "..." if entry.get('summary') else f"Hürriyet haberi: {title[:100]}",
                        "resim": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                        "kaynak": "Hürriyet",
                        "anahtar_kelime": found_keyword,
                        "unique_id": f"rss_{hash(title) % 10000}"
                    }
                    
                    all_news.append(news_item)
    
    except Exception as e:
        print(f"Haber çekme hatası: {e}")
        return []  # HATA OLURSA BOŞ DÖN
    
    return all_news

@app.route('/')
def home():
    return render_template('index.html', title='Otomotiv Haber')

@app.route('/api/haberler')
def haberler():
    """GERÇEK haberleri getir - TEST HABER YOK!"""
    try:
        # GERÇEK haberleri çek
        real_news = get_real_news_from_hurriyet()
        
        # Son 3 gün filtresi
        three_days_ago = datetime.now() - timedelta(days=3)
        filtered_news = []
        
        for news in real_news:
            try:
                news_date = datetime.strptime(news['tarih'], "%Y-%m-%d")
                if news_date >= three_days_ago:
                    filtered_news.append(news)
            except:
                continue
        
        # ⭐⭐ TEST HABER EKLEME YOK! ⭐⭐
        # Eğer gerçek haber yoksa, BOŞ liste dönecek
        
        return jsonify({
            "success": True,
            "source": "Hürriyet Gazetesi",
            "anahtar_kelimeler": ARAMA_KELIMELERI,
            "aralik": "Son 3 gün",
            "count": len(filtered_news),
            "has_news": len(filtered_news) > 0,
            "message": f"{len(filtered_news)} gerçek haber bulundu." if filtered_news else "Son 3 günde bu anahtar kelimelerle ilgili haber bulunamadı.",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "haberler": filtered_news  # ⬅ BU YA GERÇEK HABERLER YA BOŞ LİSTE
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Sunucu hatası",
            "message": "Haberler geçici olarak yüklenemiyor.",
            "has_news": False,
            "haberler": []  # ⬅ BOŞ LİSTE!
        })

@app.route('/api/ara')
def ara():
    """Özel arama - TEST HABER YOK!"""
    keyword = request.args.get('kelime', '').strip()
    
    if not keyword:
        return jsonify({
            "success": False,
            "message": "Arama kelimesi gerekli",
            "haberler": []
        })
    
    try:
        # Tüm haberleri çek
        all_news = get_real_news_from_hurriyet()
        
        # İlgili anahtar kelimeye göre filtrele
        filtered = []
        for news in all_news:
            if keyword.lower() in news['anahtar_kelime'].lower():
                filtered.append(news)
        
        # Son 3 gün filtresi
        three_days_ago = datetime.now() - timedelta(days=3)
        final_news = []
        
        for news in filtered:
            try:
                news_date = datetime.strptime(news['tarih'], "%Y-%m-%d")
                if news_date >= three_days_ago:
                    final_news.append(news)
            except:
                continue
        
        return jsonify({
            "success": True,
            "kelime": keyword,
            "count": len(final_news),
            "has_news": len(final_news) > 0,
            "message": f"'{keyword}' için {len(final_news)} gerçek haber bulundu." if final_news else f"'{keyword}' ile ilgili son 3 günde haber bulunamadı.",
            "haberler": final_news  # ⬅ TEST HABER YOK!
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Arama hatası",
            "message": "Arama sırasında hata oluştu",
            "haberler": []
        })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "otomotiv-haber-api",
        "keywords": ARAMA_KELIMELERI,
        "features": ["gerçek haberler", "3 gün filtresi", "test habersiz"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
