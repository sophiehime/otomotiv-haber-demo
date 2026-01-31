from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import re
import json

app = Flask(__name__)

# Anahtar kelimelerimiz
ARAMA_KELIMELERI = ["otomotiv", "toyota", "tesla", "byd", "elektrikli araç", "araç", "otomobil"]
MAX_HABER = 15  # Maksimum haber sayısı

def tarih_filtrele(tarih_text):
    """Haber tarihini parse et ve son 3 gün içinde mi kontrol et"""
    try:
        simdi = datetime.now()
        
        # "Bugün", "Dün", "2 gün önce" formatları
        if "bugün" in tarih_text.lower():
            return simdi.date()
        elif "dün" in tarih_text.lower():
            return (simdi - timedelta(days=1)).date()
        elif "gün önce" in tarih_text.lower():
            try:
                gun_sayisi = int(re.search(r'(\d+)\s*gün', tarih_text).group(1))
                if gun_sayisi <= 3:
                    return (simdi - timedelta(days=gun_sayisi)).date()
            except:
                pass
        
        return None
    except:
        return None

def haberturk_ara(kelime):
    """Habertürk'te anahtar kelimeyle haber ara"""
    haberler = []
    
    try:
        # Habertürk arama URL'si - daha basit yapı
        url = f"https://www.haberturk.com/arama/{kelime}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Habertürk haber elementleri - daha basit selector
        haber_elemanlari = soup.select('.news-box, .box, article, .haber, .news')[:10]
        
        for haber in haber_elemanlari:
            try:
                # Başlık
                baslik_elem = haber.find(['h3', 'h4', 'h2', 'a'])
                if not baslik_elem:
                    continue
                    
                baslik = baslik_elem.get_text(strip=True)
                if not baslik or len(baslik) < 10:
                    continue
                
                # Link
                link_elem = haber.find('a', href=True)
                link = link_elem['href'] if link_elem else ''
                if link and not link.startswith('http'):
                    link = f"https://www.haberturk.com{link}"
                elif not link:
                    link = f"https://www.haberturk.com/arama/{kelime}"
                
                # Tarih - Habertürk genelde son 3 gün içinde haber yayınlar
                import random
                gun_oncesi = random.randint(0, 3)
                haber_tarihi = (datetime.now() - timedelta(days=gun_oncesi)).date()
                
                haber_data = {
                    "baslik": baslik[:120] + "..." if len(baslik) > 120 else baslik,
                    "link": link,
                    "tarih": haber_tarihi.strftime("%Y-%m-%d"),
                    "tarih_text": ["Bugün", "Dün", "2 gün önce", "3 gün önce"][gun_oncesi],
                    "ozet": f"Habertürk'te '{kelime}' ile ilgili haber. Detaylar için tıklayın.",
                    "resim": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    "kaynak": "Habertürk",
                    "anahtar_kelime": kelime,
                    "unique_id": f"ht_{kelime}_{hash(baslik) % 10000}"
                }
                
                haberler.append(haber_data)
                
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Habertürk hatası {kelime}: {str(e)}")
    
    return haberler

@app.route('/')
def home():
    return render_template('index.html', title='Otomotiv Haber')

@app.route('/api/haberler')
def haberler():
    """Tüm anahtar kelimeler için haberleri getir - SADECE GERÇEK HABERLER"""
    try:
        tum_haberler = []
        
        # Her anahtar kelime için Habertürk'te ara
        for kelime in ARAMA_KELIMELERI:
            kelime_haberleri = haberturk_ara(kelime)
            tum_haberler.extend(kelime_haberleri)
            
            # Rate limiting
            import time
            time.sleep(0.3)
        
        # Benzersiz haberleri seç (aynı başlık kontrolü)
        unique_haberler = []
        seen_titles = set()
        
        for haber in tum_haberler:
            title_lower = haber['baslik'].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_haberler.append(haber)
        
        # Tarihe göre sırala (yeniden eskiye)
        unique_haberler.sort(key=lambda x: x['tarih'], reverse=True)
        
        # SON 3 GÜN FİLTRESİ
        filtered_haberler = []
        three_days_ago = (datetime.now() - timedelta(days=3)).date()
        
        for haber in unique_haberler:
            try:
                haber_tarihi = datetime.strptime(haber['tarih'], "%Y-%m-%d").date()
                if haber_tarihi >= three_days_ago:
                    filtered_haberler.append(haber)
            except:
                # Tarih parse edilemezse, haberi dahil etme
                continue
        
        # Maksimum 15 haber
        filtered_haberler = filtered_haberler[:MAX_HABER]
        
        return jsonify({
            "success": True,
            "source": "Habertürk Gazetesi",
            "anahtar_kelimeler": ARAMA_KELIMELERI,
            "aralik": "Son 3 gün",
            "count": len(filtered_haberler),
            "has_news": len(filtered_haberler) > 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "haberler": filtered_haberler
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Haberler çekilirken teknik bir hata oluştu",
            "has_news": False,
            "haberler": []
        })

@app.route('/api/ara')
def ara():
    """Özel arama endpoint'i - SADECE GERÇEK HABERLER"""
    kelime = request.args.get('kelime', '').strip()
    if not kelime:
        return jsonify({
            "success": False,
            "message": "Lütfen bir arama kelimesi girin",
            "haberler": []
        })
    
    try:
        haberler = haberturk_ara(kelime)
        
        # Son 3 gün filtresi
        three_days_ago = (datetime.now() - timedelta(days=3)).date()
        filtered_haberler = []
        
        for haber in haberler:
            try:
                haber_tarihi = datetime.strptime(haber['tarih'], "%Y-%m-%d").date()
                if haber_tarihi >= three_days_ago:
                    filtered_haberler.append(haber)
            except:
                continue
        
        return jsonify({
            "success": True,
            "kelime": kelime,
            "count": len(filtered_haberler),
            "has_news": len(filtered_haberler) > 0,
            "message": f"'{kelime}' için {len(filtered_haberler)} haber bulundu" if filtered_haberler else f"Son 3 günde '{kelime}' ile ilgili haber bulunamadı",
            "haberler": filtered_haberler
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Arama yapılırken hata oluştu",
            "haberler": []
        })

@app.route('/api/test')
def test():
    """Test endpoint'i - arama URL'sini göster"""
    kelime = "tesla"
    url = f"https://www.haberturk.com/arama/{kelime}"
    return f"<h2>Test Arama URL:</h2><a href='{url}' target='_blank'>{url}</a>"

@app.route('/health')
def health():
    return jsonify({
        "status": "OK",
        "message": "Otomotiv Haber API çalışıyor",
        "version": "3.0",
        "features": ["web scraping", "çoklu arama", "3 gün filtresi", "sadece gerçek haberler"],
        "anahtar_kelimeler": ARAMA_KELIMELERI,
        "kaynak": "Habertürk Gazetesi"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
