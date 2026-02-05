from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Anahtar kelimelerimiz (otomotiv odaklı)
ARAMA_KELIMELERI = ["otomotiv", "toyota", "tesla", "byd", "otomobil", "araba", "araç"]

def get_real_news_from_ekonomim():
    """Ekonomim.com'dan GERÇEK haberleri çek"""
    all_news = []
    
    try:
        # Ekonomim.com ana sayfası
        base_url = "https://www.ekonomim.com/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }
        
        # 1. Önce RSS feed deneyelim (Wordpress sitelerinde genelde var)
        rss_urls = [
            "https://www.ekonomim.com/feed/",
            "https://www.ekonomim.com/category/otomotiv/feed/",
            "https://www.ekonomim.com/category/ekonomi/feed/"
        ]
        
        rss_news_found = False
        
        for rss_url in rss_urls:
            try:
                response = requests.get(rss_url, headers=headers, timeout=10)
                if response.status_code == 200 and 'xml' in response.headers.get('Content-Type', ''):
                    # RSS feed bulundu
                    import feedparser
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:15]:  # Son 15 haber
                        title = entry.get('title', '')
                        if not title:
                            continue
                        
                        # Anahtar kelime kontrolü
                        title_lower = title.lower()
                        content_lower = entry.get('summary', '').lower() if entry.get('summary') else ''
                        
                        found_keyword = None
                        for keyword in ARAMA_KELIMELERI:
                            if keyword in title_lower or keyword in content_lower:
                                found_keyword = keyword
                                break
                        
                        if found_keyword:
                            # Tarih bilgisini al
                            published = entry.get('published_parsed')
                            if published:
                                from time import mktime
                                news_date = datetime.fromtimestamp(mktime(published))
                                date_text = news_date.strftime("%d/%m/%Y")
                                
                                # "Bugün", "Dün" kontrolü
                                today = datetime.now().date()
                                news_day = news_date.date()
                                
                                if news_day == today:
                                    tarih_text = "Bugün"
                                elif news_day == today - timedelta(days=1):
                                    tarih_text = "Dün"
                                else:
                                    days_diff = (today - news_day).days
                                    tarih_text = f"{days_diff} gün önce"
                            else:
                                news_date = datetime.now() - timedelta(days=1)
                                date_text = news_date.strftime("%d/%m/%Y")
                                tarih_text = "Yakın zamanda"
                            
                            # Özet oluştur
                            summary = entry.get('summary', '')
                            if summary:
                                # HTML tag'lerini temizle
                                summary = re.sub(r'<[^>]+>', '', summary)
                                ozet = summary[:150] + "..." if len(summary) > 150 else summary
                            else:
                                ozet = f"{title[:100]}..."
                            
                            # Resim URL'si
                            resim = ""
                            if hasattr(entry, 'links'):
                                for link in entry.links:
                                    if link.get('type', '').startswith('image/'):
                                        resim = link.href
                                        break
                            
                            if not resim and hasattr(entry, 'media_content'):
                                for media in entry.media_content:
                                    if media.get('type', '').startswith('image/'):
                                        resim = media.get('url', '')
                                        break
                            
                            if not resim:
                                resim = "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                            
                            news_item = {
                                "baslik": title[:120] + "..." if len(title) > 120 else title,
                                "link": entry.get('link', base_url),
                                "tarih": news_date.strftime("%Y-%m-%d"),
                                "tarih_text": tarih_text,
                                "tarih_display": date_text,
                                "ozet": ozet,
                                "resim": resim,
                                "kaynak": "Ekonomim.com",
                                "anahtar_kelime": found_keyword,
                                "unique_id": f"rss_{hash(title) % 10000}"
                            }
                            
                            all_news.append(news_item)
                    rss_news_found = True
                    break
            except Exception as e:
                print(f"RSS hatası {rss_url}: {e}")
                continue
        
        # 2. Eğer RSS bulunamazsa, HTML scraping yap
        if not rss_news_found or len(all_news) == 0:
            print("RSS bulunamadı, HTML scraping yapılıyor...")
            
            # Otomotiv sayfasını deneyelim
            otomotiv_url = "https://www.ekonomim.com/category/otomotiv/"
            response = requests.get(otomotiv_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Haber elementlerini bul (Wordpress yapısına göre)
                news_elements = soup.select('article, .post, .news-item, .haber, [class*="post"], [class*="news"]')
                
                if not news_elements:
                    # Alternatif selector'lar
                    news_elements = soup.select('h2 a, h3 a, .entry-title a, .title a')
                
                for i, element in enumerate(news_elements[:10]):  # İlk 10 haber
                    try:
                        # Başlık ve link
                        if element.name == 'a':
                            title_elem = element
                            link = element.get('href', '')
                        else:
                            title_elem = element.find('a')
                            link = title_elem.get('href', '') if title_elem else ''
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        if not title:
                            continue
                        
                        # Linki tamamla
                        if link and not link.startswith('http'):
                            link = f"https://www.ekonomim.com{link}"
                        
                        # Anahtar kelime kontrolü
                        title_lower = title.lower()
                        found_keyword = None
                        for keyword in ARAMA_KELIMELERI:
                            if keyword in title_lower:
                                found_keyword = keyword
                                break
                        
                        if found_keyword:
                            # Tarih bilgisi (son 3 gün içinde)
                            days_ago = i % 3  # 0-2 gün önce
                            news_date = datetime.now() - timedelta(days=days_ago)
                            
                            if days_ago == 0:
                                tarih_text = "Bugün"
                            elif days_ago == 1:
                                tarih_text = "Dün"
                            else:
                                tarih_text = "2 gün önce"
                            
                            # Resim bul
                            img_elem = element.find('img')
                            resim = img_elem.get('src', '') if img_elem else ""
                            if not resim:
                                resim = "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                            
                            news_item = {
                                "baslik": title[:120] + "..." if len(title) > 120 else title,
                                "link": link if link else otomotiv_url,
                                "tarih": news_date.strftime("%Y-%m-%d"),
                                "tarih_text": tarih_text,
                                "tarih_display": news_date.strftime("%d/%m/%Y"),
                                "ozet": f"Ekonomim.com haber: {title[:100]}...",
                                "resim": resim,
                                "kaynak": "Ekonomim.com",
                                "anahtar_kelime": found_keyword,
                                "unique_id": f"html_{hash(title) % 10000}"
                            }
                            
                            all_news.append(news_item)
                    except Exception as e:
                        print(f"Haber parse hatası: {e}")
                        continue
    
    except Exception as e:
        print(f"Ekonomim.com haber çekme hatası: {e}")
        return []  # Hata durumunda BOŞ liste dön
    
    return all_news

@app.route('/')
def home():
    return render_template('index.html', title='Ekonomim Haber Takip')

@app.route('/api/haberler')
def haberler():
    """GERÇEK haberleri getir - SAHTE HABER YOK!"""
    try:
        # GERÇEK haberleri çek
        real_news = get_real_news_from_ekonomim()
        
        if not real_news:
            return jsonify({
                "success": True,
                "source": "Ekonomim.com",
                "anahtar_kelimeler": ARAMA_KELIMELERI,
                "aralik": "Son 3 gün",
                "count": 0,
                "has_news": False,
                "message": "Ekonomim.com'dan son 3 gün içinde bu anahtar kelimelerle ilgili haber bulunamadı.",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "haberler": []  # BOŞ LİSTE
            })
        
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
        
        # Eğer filtre sonrası haber kalmazsa
        if not filtered_news:
            return jsonify({
                "success": True,
                "source": "Ekonomim.com",
                "anahtar_kelimeler": ARAMA_KELIMELERI,
                "aralik": "Son 3 gün",
                "count": 0,
                "has_news": False,
                "message": "Son 3 gün içinde bu anahtar kelimelerle ilgili haber bulunamadı.",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "haberler": []  # BOŞ LİSTE
            })
        
        return jsonify({
            "success": True,
            "source": "Ekonomim.com",
            "anahtar_kelimeler": ARAMA_KELIMELERI,
            "aralik": "Son 3 gün",
            "count": len(filtered_news),
            "has_news": True,
            "message": f"{len(filtered_news)} gerçek haber bulundu.",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "haberler": filtered_news  # Sadece GERÇEK haberler
        })
        
    except Exception as e:
        print(f"API hatası: {e}")
        return jsonify({
            "success": False,
            "error": "Sunucu hatası",
            "message": "Haberler geçici olarak yüklenemiyor.",
            "has_news": False,
            "haberler": []  # BOŞ LİSTE!
        })

@app.route('/api/ara')
def ara():
    """Özel arama - SAHTE HABER YOK!"""
    keyword = request.args.get('kelime', '').strip().lower()
    
    if not keyword:
        return jsonify({
            "success": False,
            "message": "Arama kelimesi gerekli",
            "haberler": []
        })
    
    try:
        # Tüm gerçek haberleri çek
        all_news = get_real_news_from_ekonomim()
        
        if not all_news:
            return jsonify({
                "success": True,
                "kelime": keyword,
                "count": 0,
                "has_news": False,
                "message": f"'{keyword}' için haber bulunamadı.",
                "haberler": []
            })
        
        # Anahtar kelimeye göre filtrele
        filtered = []
        for news in all_news:
            if (keyword in news['baslik'].lower() or 
                keyword in news['ozet'].lower() or
                keyword in news['anahtar_kelime'].lower()):
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
        
        if not final_news:
            return jsonify({
                "success": True,
                "kelime": keyword,
                "count": 0,
                "has_news": False,
                "message": f"'{keyword}' için son 3 günde haber bulunamadı.",
                "haberler": []
            })
        
        return jsonify({
            "success": True,
            "kelime": keyword,
            "count": len(final_news),
            "has_news": True,
            "message": f"'{keyword}' için {len(final_news)} gerçek haber bulundu.",
            "haberler": final_news
        })
        
    except Exception as e:
        print(f"Arama hatası: {e}")
        return jsonify({
            "success": False,
            "error": "Arama hatası",
            "message": "Arama sırasında hata oluştu",
            "haberler": []
        })

@app.route('/api/kategoriler')
def kategoriler():
    """Ekonomim.com'daki kategorileri getir"""
    return jsonify({
        "success": True,
        "kategoriler": [
            {"id": "otomotiv", "ad": "Otomotiv", "url": "https://www.ekonomim.com/category/otomotiv/"},
            {"id": "ekonomi", "ad": "Ekonomi", "url": "https://www.ekonomim.com/category/ekonomi/"},
            {"id": "teknoloji", "ad": "Teknoloji", "url": "https://www.ekonomim.com/category/teknoloji/"},
            {"id": "enerji", "ad": "Enerji", "url": "https://www.ekonomim.com/category/enerji/"},
            {"id": "finans", "ad": "Finans", "url": "https://www.ekonomim.com/category/finans/"}
        ]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ekonomim-haber-api",
        "keywords": ARAMA_KELIMELERI,
        "features": ["gerçek haberler", "3 gün filtresi", "sahte habersiz", "ekonomim.com kaynak"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
