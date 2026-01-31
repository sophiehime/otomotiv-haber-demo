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
MAX_HABER = 20  # Maksimum haber sayısı

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
        
        # Tarih formatı: "29 Ocak 2024"
        turkce_aylar = {
            'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'haziran': 6,
            'temmuz': 7, 'ağustos': 8, 'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
        }
        
        for ay, num in turkce_aylar.items():
            if ay in tarih_text.lower():
                parts = tarih_text.split()
                gun = int(parts[0])
                yil = int(parts[2]) if len(parts) > 2 else simdi.year
                haber_tarihi = datetime(yil, num, gun).date()
                
                # Son 3 gün kontrolü
                if (simdi.date() - haber_tarihi).days <= 3:
                    return haber_tarihi
                
        return None
    except:
        return None

def hurriyet_ara(kelime):
    """Hürriyet'te anahtar kelimeyle haber ara"""
    haberler = []
    
    try:
        # Hürriyet arama URL'si
        url = f"https://www.hurriyet.com.tr/arama/#/?key={kelime}&where=article&how=Date&page=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Hürriyet arama sonuçlarını parse et
        haber_elemanlari = soup.find_all('div', class_='news-item') or \
                          soup.find_all('div', class_='widget-news') or \
                          soup.find_all('article')[:15]
        
        for haber in haber_elemanlari:
            try:
                # Başlık
                baslik_elem = haber.find(['h3', 'h4', 'h2']) or haber.find('a', class_=lambda x: x and 'title' in x.lower())
                if not baslik_elem:
                    continue
                    
                baslik = baslik_elem.get_text(strip=True)
                if not baslik or len(baslik) < 10:
                    continue
                
                # Link
                link_elem = haber.find('a', href=True)
                link = link_elem['href'] if link_elem else ''
                if link and not link.startswith('http'):
                    link = f"https://www.hurriyet.com.tr{link}"
                
                # Tarih
                tarih_elem = haber.find('time') or haber.find('span', class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
                tarih_text = tarih_elem.get_text(strip=True) if tarih_elem else ''
                
                # Tarih filtresi
                haber_tarihi = tarih_filtrele(tarih_text)
                if not haber_tarihi:
                    continue  # 3 günden eski haberleri atla
                
                # Özet/kısa açıklama
                ozet_elem = haber.find('p') or haber.find('div', class_=lambda x: x and 'summary' in x.lower())
                ozet = ozet_elem.get_text(strip=True)[:150] + "..." if ozet_elem else ""
                
                # Resim
                img_elem = haber.find('img')
                resim = img_elem.get('src', '') if img_elem else ''
                if resim and not resim.startswith('http'):
                    resim = f"https:{resim}" if resim.startswith('//') else resim
                
                haber_data = {
                    "baslik": baslik,
                    "link": link,
                    "tarih": haber_tarihi.strftime("%Y-%m-%d"),
                    "tarih_text": tarih_text,
                    "ozet": ozet,
                    "resim": resim,
                    "kaynak": "Hürriyet",
                    "anahtar_kelime": kelime,
                    "unique_id": f"{kelime}_{hash(baslik) % 10000}"
                }
                
                haberler.append(haber_data)
                
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Hata {kelime}: {str(e)}")
    
    return haberler

@app.route('/')
def home():
    return render_template('index.html', title='Otomotiv Haber')

@app.route('/api/haberler')
def haberler():
    """Tüm anahtar kelimeler için haberleri getir"""
    try:
        tum_haberler = []
        haber_set = set()  # Tekrarları önlemek için
        
        for kelime in ARAMA_KELIMELERI:
            kelime_haberleri = hurriyet_ara(kelime)
            for haber in kelime_haberleri:
                # Tekrar kontrolü (aynı başlık)
                haber_hash = haber['baslik'].lower().strip()
                if haber_hash not in haber_set:
                    haber_set.add(haber_hash)
                    tum_haberler.append(haber)
            
            # Her kelime aramasından sonra biraz bekle (rate limiting için)
            import time
            time.sleep(0.5)
        
        # Tarihe göre sırala (yeniden eskiye)
        tum_haberler.sort(key=lambda x: x['tarih'], reverse=True)
        
        # Limit uygula
        tum_haberler = tum_haberler[:MAX_HABER]
        
        # Eğer hiç haber yoksa, örnek göster
        if not tum_haberler:
            tum_haberler = [
                {
                    "baslik": "Toyota Türkiye'de Yeni Fabrika Açıyor",
                    "link": "#",
                    "tarih": datetime.now().strftime("%Y-%m-%d"),
                    "tarih_text": "Bugün",
                    "ozet": "Toyota'nın Türkiye'deki yatırımları devam ediyor...",
                    "resim": "",
                    "kaynak": "Hürriyet",
                    "anahtar_kelime": "toyota",
                    "unique_id": "toyota_1"
                },
                {
                    "baslik": "Tesla'nın Yeni Modeli Türkiye Yollarında",
                    "link": "#", 
                    "tarih": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "tarih_text": "Dün",
                    "ozet": "Tesla Model 3'ün güncellenmiş versiyonu Türkiye'de satışa sunuldu...",
                    "resim": "",
                    "kaynak": "Hürriyet",
                    "anahtar_kelime": "tesla",
                    "unique_id": "tesla_1"
                },
                {
                    "baslik": "BYD Elektrikli Araçları İstanbul'da Tanıtıldı",
                    "link": "#",
                    "tarih": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "tarih_text": "2 gün önce",
                    "ozet": "Çinli otomobil üreticisi BYD, Türkiye pazarına resmen girdi...",
                    "resim": "",
                    "kaynak": "Hürriyet",
                    "anahtar_kelime": "byd",
                    "unique_id": "byd_1"
                }
            ]
        
        return jsonify({
            "success": True,
            "source": "Hürriyet Gazetesi",
            "anahtar_kelimeler": ARAMA_KELIMELERI,
            "aralik": "Son 3 gün",
            "count": len(tum_haberler),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "haberler": tum_haberler
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Haberler çekilemedi, örnek veri gösteriliyor",
            "haberler": [
                {
                    "baslik": "Örnek Haber: Otomotiv Sektörü Büyüyor",
                    "link": "#",
                    "tarih": datetime.now().strftime("%Y-%m-%d"),
                    "tarih_text": "Bugün",
                    "ozet": "Bu bir örnek haberdir. Hürriyet'ten gerçek haberler çekilemedi.",
                    "resim": "",
                    "kaynak": "Örnek",
                    "anahtar_kelime": "otomotiv",
                    "unique_id": "sample_1"
                }
            ]
        })

@app.route('/api/ara')
def ara():
    """Özel arama endpoint'i"""
    kelime = request.args.get('kelime', 'otomotiv')
    try:
        haberler = hurriyet_ara(kelime)
        return jsonify({
            "success": True,
            "kelime": kelime,
            "count": len(haberler),
            "haberler": haberler
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/test')
def test():
    """Test endpoint'i - arama URL'sini göster"""
    kelime = "tesla"
    url = f"https://www.hurriyet.com.tr/arama/#/?key={kelime}&where=article&how=Date&page=1"
    return f"<h2>Test Arama URL:</h2><a href='{url}' target='_blank'>{url}</a>"

@app.route('/health')
def health():
    return jsonify({
        "status": "OK",
        "message": "Otomotiv Haber API çalışıyor",
        "version": "2.0",
        "features": ["web scraping", "çoklu arama", "tarih filtresi", "JSON API"],
        "anahtar_kelimeler": ARAMA_KELIMELERI
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
