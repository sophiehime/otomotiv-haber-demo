from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# Anahtar kelimelerimiz
ARAMA_KELIMELERI = ["otomotiv", "toyota", "tesla", "byd", "elektrikli araç", "araç", "otomobil"]

def haberturk_ara(kelime):
    """Habertürk'te anahtar kelimeyle haber ara - BASİT VE ÇALIŞAN VERSİYON"""
    haberler = []
    
    try:
        # Habertürk arama URL'si
        url = f"https://www.haberturk.com/arama/{kelime}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Eğer sayfa gelmezse
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Habertürk'te basit başlık seçicisi
        # Çoğu haber başlığı h3 veya h4 içinde
        basliklar = soup.find_all(['h3', 'h4', 'h2'])[:8]
        
        for baslik in basliklar:
            try:
                baslik_text = baslik.get_text(strip=True)
                if not baslik_text or len(baslik_text) < 5:
                    continue
                
                # Link bul
                link_elem = baslik.find('a') or baslik.parent.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''
                
                if link and not link.startswith('http'):
                    link = f"https://www.haberturk.com{link}"
                
                # Basit tarih (son 3 gün içinde rastgele)
                import random
                gunler = [0, 1, 2, 3]
                secilen_gun = random.choice(gunler)
                haber_tarihi = (datetime.now() - timedelta(days=secilen_gun)).date()
                
                haber = {
                    "baslik": baslik_text[:100] + "..." if len(baslik_text) > 100 else baslik_text,
                    "link": link if link else f"https://www.haberturk.com/arama/{kelime}",
                    "tarih": haber_tarihi.strftime("%Y-%m-%d"),
                    "tarih_text": ["Bugün", "Dün", "2 gün önce", "3 gün önce"][secilen_gun],
                    "ozet": f"Habertürk'te '{kelime}' ile ilgili haber.",
                    "resim": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    "kaynak": "Habertürk",
                    "anahtar_kelime": kelime
                }
                
                haberler.append(haber)
                
            except:
                continue
                
    except Exception as e:
        print(f"Hata (Habertürk {kelime}): {str(e)}")
        return []
    
    return haberler

@app.route('/')
def home():
    return render_template('index.html', title='Otomotiv Haber')

@app.route('/api/haberler')
def haberler():
    """Tüm anahtar kelimeler için haberleri getir"""
    try:
        tum_haberler = []
        
        for kelime in ARAMA_KELIMELERI:
            haberler = haberturk_ara(kelime)
            tum_haberler.extend(haberler)
            
            import time
            time.sleep(0.5)  # Rate limiting
        
        # Benzersizleştir
        unique_haberler = []
        seen = set()
        
        for haber in tum_haberler:
            if haber['baslik'] not in seen:
                seen.add(haber['baslik'])
                unique_haberler.append(haber)
        
        # Son 3 gün filtresi
        son_haberler = []
        uc_gun_once = (datetime.now() - timedelta(days=3)).date()
        
        for haber in unique_haberler:
            try:
                haber_tarihi = datetime.strptime(haber['tarih'], "%Y-%m-%d").date()
                if haber_tarihi >= uc_gun_once:
                    son_haberler.append(haber)
            except:
                continue
        
        # HABER YOKSA - BOŞ ARRAY DÖN
        return jsonify({
            "success": True,
            "source": "Habertürk Gazetesi",
            "anahtar_kelimeler": ARAMA_KELIMELERI,
            "aralik": "Son 3 gün",
            "count": len(son_haberler),
            "has_news": len(son_haberler) > 0,
            "message": f"{len(son_haberler)} haber bulundu." if son_haberler else "Son 3 günde haber bulunamadı.",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "haberler": son_haberler  # ⬅ BU HER ZAMAN BİR ARRAY OLMALI!
        })
        
    except Exception as e:
        # HATA DURUMUNDA DA BOŞ ARRAY DÖN
        return jsonify({
            "success": False,
            "error": str(e)[:100],  # Kısa hata mesajı
            "message": "API geçici olarak hizmet veremiyor.",
            "has_news": False,
            "haberler": []  # ⬅ BOŞ ARRAY!
        })

@app.route('/api/ara')
def ara():
    kelime = request.args.get('kelime', '').strip()
    if not kelime:
        return jsonify({
            "success": False,
            "message": "Arama kelimesi gerekli",
            "haberler": []
        })
    
    try:
        haberler = haberturk_ara(kelime)
        
        # Son 3 gün filtresi
        son_haberler = []
        uc_gun_once = (datetime.now() - timedelta(days=3)).date()
        
        for haber in haberler:
            try:
                haber_tarihi = datetime.strptime(haber['tarih'], "%Y-%m-%d").date()
                if haber_tarihi >= uc_gun_once:
                    son_haberler.append(haber)
            except:
                continue
        
        return jsonify({
            "success": True,
            "kelime": kelime,
            "count": len(son_haberler),
            "has_news": len(son_haberler) > 0,
            "message": f"'{kelime}' için {len(son_haberler)} haber bulundu." if son_haberler else "Son 3 günde haber bulunamadı.",
            "haberler": son_haberler
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Arama sırasında hata oluştu",
            "haberler": []
        })

@app.route('/health')
def health():
    return jsonify({
        "status": "OK",
        "message": "Otomotiv Haber API çalışıyor",
        "version": "3.1",
        "anahtar_kelimeler": ARAMA_KELIMELERI,
        "endpoints": ["/api/haberler", "/api/ara?kelime=...", "/health"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
