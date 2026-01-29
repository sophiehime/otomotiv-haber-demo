import streamlit as st
from fpdf import FPDF
import base64
import os
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

# Render için port ayarı
PORT = int(os.environ.get("PORT", 8501))

# Sayfa ayarları
st.set_page_config(
    page_title="Otomotiv Haber Küratörü",
    page_icon="🚗",
    layout="wide"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #F0F9FF;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin: 1rem 0;
    }
    .news-card {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        transition: transform 0.2s;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .language-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.2rem;
    }
    .tr-badge { background: #10B981; color: white; }
    .en-badge { background: #3B82F6; color: white; }
    .jp-badge { background: #EF4444; color: white; }
</style>
""", unsafe_allow_html=True)

# Başlık
st.markdown('<h1 class="main-header">🚗 Otomotiv Üretim Haber Küratörü</h1>', unsafe_allow_html=True)
st.markdown("**Demo Version 2.0** | *Günlük iş yükünü 6 saatten 30 dakikaya düşürür*")

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2267/2267911.png", width=80)
    st.header("⚙️ Filtre Ayarları")
    
    # Tarih seçimi
    selected_date = st.date_input("📅 Tarih", datetime.now())
    
    # Kaynak seçimi
    sources = st.multiselect(
        "📰 Haber Kaynakları",
        ["Interpress", "Reuters", "Bloomberg", "Nikkei", "Automotive News", "Financial Times"],
        default=["Interpress", "Reuters", "Nikkei"]
    )
    
    # Kategori seçimi
    categories = st.multiselect(
        "🏷️ Kategoriler",
        ["Üretim", "Gümrük", "Teknoloji", "Pazar Analizi", "Arz Zinciri", "Yatırım"],
        default=["Üretim", "Gümrük"]
    )
    
    # Önem seviyesi
    importance = st.slider("⭐ Önem Seviyesi", 1, 5, 3)
    
    st.markdown("---")
    st.markdown("### 📊 İstatistikler")
    st.metric("Zaman Tasarrufu", "5.5 saat", "92%")
    st.metric("Günlük Haber", "15-20", "ortalama")

# Bilgi kutusu
st.markdown("""
<div class="info-box">
<strong>🎯 Sistem Amacı:</strong> Günlük otomotiv haberlerini otomatik toplar, filtreler, çevirir ve yöneticilere PDF olarak gönderir.
<br><strong>⏱️ Mevcut Süre:</strong> 6 saat → <strong>Yeni Süre:</strong> 30 dakika
</div>
""", unsafe_allow_html=True)

# Haber verileri
def get_sample_news():
    return [
        {
            "id": 1,
            "title": "Toyota Japonya'da üretimi %15 artırdı",
            "source": "Nikkei",
            "category": "Üretim",
            "country": "Japonya",
            "date": "29.01.2026",
            "importance": "Yüksek",
            "summary": "Toyota, yeni fabrika yatırımları ile üretim kapasitesini artırdı. Yatırımlar özellikle hibrit ve elektrikli araç üretimine odaklanıyor.",
            "keywords": ["Toyota", "üretim", "fabrika", "hibrit", "Japonya"]
        },
        {
            "id": 2,
            "title": "AB otomotiv gümrük vergilerinde reform",
            "source": "Reuters",
            "category": "Gümrük",
            "country": "AB",
            "date": "28.01.2026",
            "importance": "Orta",
            "summary": "Avrupa Birliği, elektrikli araçlar için gümrük vergilerini gözden geçiriyor. Yeni düzenlemeler 2026 sonunda yürürlüğe girecek.",
            "keywords": ["AB", "gümrük", "elektrikli", "vergi", "reform"]
        },
        {
            "id": 3,
            "title": "Türkiye otomotiv ihracatında rekor",
            "source": "Interpress",
            "category": "Pazar Analizi",
            "country": "Türkiye",
            "date": "27.01.2026",
            "importance": "Yüksek",
            "summary": "2024 yılı ilk çeyreğinde otomotiv ihracatı %25 arttı. Avrupa pazarında Türk otomotiv ürünlerine talep rekor seviyede.",
            "keywords": ["Türkiye", "ihracat", "rekor", "Avrupa", "pazar"]
        },
        {
            "id": 4,
            "title": "Tesla Berlin fabrikasında kapasite artışı",
            "source": "Bloomberg",
            "category": "Üretim",
            "country": "Almanya",
            "date": "26.01.2026",
            "importance": "Orta",
            "summary": "Tesla, Berlin fabrikasında üretim kapasitesini ikiye katladı. Yeni Model Y üretim hattı devreye alındı.",
            "keywords": ["Tesla", "Berlin", "fabrika", "Model Y", "kapasite"]
        },
        {
            "id": 5,
            "title": "Honda yeni hibrit teknolojisini açıkladı",
            "source": "Automotive News",
            "category": "Teknoloji",
            "country": "Japonya",
            "date": "25.01.2026",
            "importance": "Yüksek",
            "summary": "Honda, yeni nesil hibrit motor teknolojisini tanıttı. Sistem %30 daha az yakıt tüketimi vaat ediyor.",
            "keywords": ["Honda", "hibrit", "teknoloji", "motor", "yakıt"]
        },
        {
            "id": 6,
            "title": "Çin'de otomotiv batarya üretimi artıyor",
            "source": "Financial Times",
            "category": "Teknoloji",
            "country": "Çin",
            "date": "24.01.2026",
            "importance": "Orta",
            "summary": "Çin, elektrikli araç bataryası üretiminde dünya liderliğini pekiştiriyor. Yıllık üretim kapasitesi 1000 GWh'ı aştı.",
            "keywords": ["Çin", "batarya", "elektrikli", "üretim", "kapasite"]
        }
    ]

# Sekmeler
tab1, tab2, tab3, tab4 = st.tabs(["📰 Haber Seçimi", "🌐 Çoklu Dil", "📊 Analiz", "🚀 Otomasyon"])

with tab1:
    st.header("Haber Seçimi ve Filtreleme")
    
    news_data = get_sample_news()
    selected_news = []
    
    # Filtreleme
    filtered_news = [
        news for news in news_data 
        if (not sources or news['source'] in sources) and 
           (not categories or news['category'] in categories)
    ]
    
    # Toplu seçim
    col_select, col_counter = st.columns([0.2, 0.8])
    with col_select:
        select_all = st.checkbox("Tümünü Seç")
    with col_counter:
        st.caption(f"Toplam {len(filtered_news)} haber bulundu")
    
    # Haber listesi
    for news in filtered_news:
        st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([0.05, 0.75, 0.2])
        
        with col1:
            selected = st.checkbox("", key=f"select_{news['id']}", value=select_all)
        
        with col2:
            # Başlık ve etiketler
            st.markdown(f"**{news['title']}**")
            
            # Etiketler
            col_tags = st.columns(5)
            with col_tags[0]:
                st.markdown(f'<span class="language-badge tr-badge">🇹🇷</span>', unsafe_allow_html=True)
            with col_tags[1]:
                st.caption(f"📰 {news['source']}")
            with col_tags[2]:
                st.caption(f"🏷️ {news['category']}")
            with col_tags[3]:
                st.caption(f"🌍 {news['country']}")
            with col_tags[4]:
                importance_stars = "⭐" * (3 if news['importance'] == 'Yüksek' else 2)
                st.caption(importance_stars)
            
            # Anahtar kelimeler
            if news.get('keywords'):
                keywords_html = " ".join([f"`{kw}`" for kw in news['keywords'][:3]])
                st.markdown(keywords_html)
        
        with col3:
            if st.button("👁️ Detay", key=f"detail_{news['id']}"):
                st.info(f"**Detaylı Özet:** {news['summary']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if selected:
            selected_news.append(news)
    
    # PDF oluşturma fonksiyonu
    def create_pdf(news_list, language='tr'):
        pdf = FPDF()
        pdf.add_page()
        
        # Logo/başlık
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(200, 15, txt="OTOMOTİV HABER RAPORU", ln=True, align='C')
        
        pdf.set_font("Helvetica", 'I', 12)
        pdf.cell(200, 10, txt="Günlük Üretim Sektörü Takibi", ln=True, align='C')
        pdf.ln(10)
        
        # Tarih ve bilgiler
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(100, 8, txt=f"Tarih: {datetime.now().strftime('%d.%m.%Y')}", ln=0)
        pdf.cell(100, 8, txt=f"Haber Sayısı: {len(news_list)}", ln=1)
        pdf.cell(100, 8, txt=f"Hazırlayan: Otomatik Sistem", ln=0)
        pdf.cell(100, 8, txt=f"Sürüm: Demo 2.0", ln=1)
        pdf.ln(15)
        
        # Haberler
        for i, news in enumerate(news_list, 1):
            pdf.set_font("Helvetica", 'B', 14)
            pdf.set_text_color(0, 51, 102)  # Koyu mavi
            pdf.multi_cell(0, 8, txt=f"{i}. {news['title']}")
            
            pdf.set_font("Helvetica", '', 10)
            pdf.set_text_color(100, 100, 100)  # Gri
            pdf.multi_cell(0, 6, txt=f"📰 {news['source']} | 🏷️ {news['category']} | 🌍 {news['country']} | 📅 {news['date']} | {news['importance']}")
            
            pdf.set_font("Helvetica", '', 11)
            pdf.set_text_color(0, 0, 0)  # Siyah
            pdf.multi_cell(0, 7, txt=f"Özet: {news['summary']}")
            
            # Anahtar kelimeler
            if news.get('keywords'):
                pdf.set_font("Helvetica", 'I', 9)
                keywords_text = "Anahtar kelimeler: " + ", ".join(news['keywords'])
                pdf.multi_cell(0, 6, txt=keywords_text)
            
            pdf.ln(10)
        
        # Footer
        pdf.set_y(-30)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, txt="Bu rapor otomatik olarak oluşturulmuştur. © 2026 Otomotiv Haber Küratörü", ln=True, align='C')
        
        return base64.b64encode(pdf.output()).decode('latin-1')
    
    # Butonlar
    if selected_news:
        st.success(f"✅ {len(selected_news)} haber seçildi")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📄 Türkçe PDF", type="primary", use_container_width=True):
                with st.spinner("PDF oluşturuluyor..."):
                    pdf_b64 = create_pdf(selected_news, 'tr')
                    href = f'''
                    <a href="data:application/pdf;base64,{pdf_b64}" 
                       download="otomotiv_raporu_tr_{datetime.now().strftime("%Y%m%d")}.pdf"
                       style="display:inline-block;width:100%;text-align:center;background:#4CAF50;color:white;padding:12px;border-radius:5px;text-decoration:none;margin-top:10px;">
                       📥 Türkçe PDF İndir
                    </a>
                    '''
                    st.markdown(href, unsafe_allow_html=True)
                    st.balloons()
        
        with col2:
            if st.button("🇬🇧 İngilizce", use_container_width=True):
                st.info("İngilizce özetler aktif değil. Gerçek sistemde ChatGPT API ile otomatik çevrilecek.")
        
        with col3:
            if st.button("🇯🇵 Japonca", use_container_width=True):
                st.info("Japonca özetler aktif değil. Gerçek sistemde ChatGPT API ile otomatik çevrilecek.")
        
        with col4:
            if st.button("💾 Excel Kaydet", use_container_width=True):
                df = pd.DataFrame(selected_news)
                df.to_excel("secilen_haberler.xlsx", index=False)
                st.success("Excel dosyası kaydedildi!")
    else:
        st.warning("Lütfen en az bir haber seçin.")

with tab2:
    st.header("Çoklu Dil Özetleri")
    
    if selected_news:
        st.subheader(f"Seçilen {len(selected_news)} Haberin Özetleri")
        
        for i, news in enumerate(selected_news, 1):
            with st.expander(f"{i}. {news['title'][:50]}...", expanded=(i == 1)):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🇹🇷 Türkçe Özet**")
                    st.markdown(f'<div style="background:#F0F9FF; padding:1rem; border-radius:8px;">{news["summary"]}</div>', unsafe_allow_html=True)
                    st.caption("Kaynak: " + news['source'])
                
                with col2:
                    st.markdown("**🇬🇧 İngilizce**")
                    english_summary = f"""
                    **{news['title']}** (English Translation)
                    
                    Toyota has increased production in Japan by 15% through new factory investments. 
                    The investments focus particularly on hybrid and electric vehicle production, 
                    responding to growing global demand for eco-friendly vehicles.
                    
                    **Source:** {news['source']}
                    **Category:** {news['category']}
                    """
                    st.markdown(f'<div style="background:#EFF6FF; padding:1rem; border-radius:8px;">{english_summary}</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown("**🇯🇵 日本語**")
                    japanese_summary = f"""
                    **{news['title']}** (日本語翻訳)
                    
                    トヨタは新工場への投資により、日本での生産を15％増加させました。
                    投資は特にハイブリッド車と電気自動車の生産に焦点を当てており、
                    環境に優しい車両に対する世界的な需要の高まりに対応しています。
                    
                    **ソース:** {news['source']}
                    **カテゴリ:** {news['category']}
                    """
                    st.markdown(f'<div style="background:#FEF2F2; padding:1rem; border-radius:8px;">{japanese_summary}</div>', unsafe_allow_html=True)
        
        # Toplu dil butonları
        st.markdown("---")
        st.subheader("Toplu Dil İşlemleri")
        
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            if st.button("📄 Tüm Haberleri İngilizceleştir", use_container_width=True):
                st.info("Gerçek sistemde: Tüm seçilen haberler ChatGPT API ile İngilizce'ye çevrilecek.")
        with col_l2:
            if st.button("📄 Tüm Haberleri Japoncalaştır", use_container_width=True):
                st.info("Gerçek sistemde: Tüm seçilen haberler ChatGPT API ile Japonca'ya çevrilecek.")
        with col_l3:
            if st.button("🌐 Çoklu Dil PDF Oluştur", use_container_width=True):
                st.info("Gerçek sistemde: TR/EN/JP tüm dilleri içeren tek PDF oluşturulacak.")
    else:
        st.info("👈 Lütfen önce 'Haber Seçimi' sekmesinden haber seçin.")

with tab3:
    st.header("Analitik ve Raporlama")
    
    # Grafikler
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Kategori dağılımı
        category_counts = {}
        for news in news_data:
            cat = news['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        fig1 = go.Figure(data=[
            go.Pie(
                labels=list(category_counts.keys()),
                values=list(category_counts.values()),
                hole=.3,
                marker_colors=['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444']
            )
        ])
        
        fig1.update_layout(
            title="Haber Kategori Dağılımı",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        # Ülke bazlı haber sayısı
        country_counts = {}
        for news in news_data:
            country = news['country']
            country_counts[country] = country_counts.get(country, 0) + 1
        
        fig2 = go.Figure(data=[
            go.Bar(
                x=list(country_counts.keys()),
                y=list(country_counts.values()),
                marker_color='#8B5CF6',
                text=list(country_counts.values()),
                textposition='auto'
            )
        ])
        
        fig2.update_layout(
            title="Ülkelere Göre Haber Sayısı",
            xaxis_title="Ülke",
            yaxis_title="Haber Sayısı",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # İstatistikler
    st.subheader("📈 Performans İstatistikleri")
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("Günlük Haber", "15-20", "ortalama")
    with col_stat2:
        st.metric("İşlem Süresi", "30 dk", "-5.5 saat")
    with col_stat3:
        st.metric("Doğruluk", "%98", "+%40")
    with col_stat4:
        st.metric("Maliyet", "%90", "azalma")
    
    # Kaynak analizi
    st.subheader("📰 Kaynak Analizi")
    
    source_data = pd.DataFrame(news_data)
    source_stats = source_data['source'].value_counts().reset_index()
    source_stats.columns = ['Kaynak', 'Haber Sayısı']
    
    st.dataframe(source_stats, use_container_width=True, hide_index=True)

with tab4:
    st.header("Otomasyon ve Entegrasyon")
    
    # Outlook simülasyonu
    st.subheader("📧 Outlook Otomatik Mail Sistemi")
    
    col_mail1, col_mail2 = st.columns([2, 1])
    
    with col_mail1:
        st.markdown("""
        <div style="border:1px solid #0072C6; border-radius:8px; padding:20px; background:#f0f8ff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        
        <div style="background:#0072C6; color:white; padding:10px; border-radius:5px; margin-bottom:15px;">
        <strong>📨 Yeni E-posta</strong>
        </div>
        
        <table style="width:100%; margin-bottom:15px;">
        <tr>
            <td style="width:60px; color:#666;"><strong>Kime:</strong></td>
            <td>yonetici1@sirket.com; yonetici2@sirket.com; japonya.ekibi@sirket.com</td>
        </tr>
        <tr>
            <td style="color:#666;"><strong>Konu:</strong></td>
            <td>Günlük Otomotiv Haber Özeti - {date} - [ÖNEMLİ]</td>
        </tr>
        <tr>
            <td style="color:#666;"><strong>Ek:</strong></td>
            <td>otomotiv_haberleri_{date}.pdf (📎 {size} MB)</td>
        </tr>
        </table>
        
        <hr style="border-color:#0072C6; opacity:0.3;">
        
        <div style="color:#333; line-height:1.6;">
        <p>Sayın Yöneticilerim,</p>
        
        <p>Bugünün otomotiv üretim sektörü haber özetleri ekteki PDF dosyasında sunulmuştur.</p>
        
        <div style="background:#e6f2ff; padding:10px; border-radius:5px; margin:10px 0;">
        <strong>📊 Özet Bilgiler:</strong><br>
        • Toplam Haber: <strong>{count}</strong> adet<br>
        • Kapsam: Üretim, gümrük, teknoloji, pazar analizi<br>
        • Önemli Gelişme: Toyota üretim artışı %15<br>
        • Kritik Haber: AB gümrük reformu
        </div>
        
        <p>PDF içinde her haberin Türkçe, İngilizce ve Japonca özetlerini bulabilirsiniz.</p>
        
        <p>Detaylı analiz ve geçmiş raporlar için sistem paneline giriş yapabilirsiniz.</p>
        
        <p>Saygılarımla,<br>
        <em style="color:#0072C6;">Otomatik Haber Küratörü Sistemi</em><br>
        <span style="font-size:0.9em; color:#666;">Bu mail otomatik olarak oluşturulmuştur.</span></p>
        </div>
        
        </div>
        """.format(
            date=datetime.now().strftime('%d.%m.%Y'),
            count=len(selected_news) if selected_news else 0,
            size=len(selected_news) * 0.5 + 0.5
        ), unsafe_allow_html=True)
    
    with col_mail2:
        st.markdown("### ⚙️ Ayarlar")
        
        # Mail zamanlama
        mail_time = st.time_input("Gönderim Saati", value=datetime.strptime("07:30", "%H:%M").time())
        
        # Alıcı listesi
        recipients = st.text_area("Alıcılar (noktalı virgülle ayırın)", 
                                "yonetici1@sirket.com; yonetici2@sirket.com; japonya.ekibi@sirket.com")
        
        # Öncelik
        priority = st.selectbox("Öncelik", ["Normal", "Yüksek", "Çok Yüksek"])
        
        # Butonlar
        if st.button("📨 Mail Taslağı Oluştur", type="primary", use_container_width=True):
            st.success(f"✅ Mail taslağı Outlook'ta hazırlandı! (Simülasyon)")
            st.info("Gerçek sistemde: Python win32com ile otomatik oluşturulup gönderilecek.")
        
        if st.button("🕐 Zamanlanmış Görev Ayarla", use_container_width=True):
            st.success(f"✅ Her gün {mail_time.strftime('%H:%M')}'da otomatik gönderim ayarlandı.")
    
    # Otomasyon planı
    st.markdown("---")
    st.subheader("🤖 Tam Otomasyon Planı")
    
    automation_steps = [
        {"step": 1, "title": "Haber Toplama", "desc": "RSS feed'lerinden otomatik çekme", "status": "✅ Demo"},
        {"step": 2, "title": "Filtreleme", "desc": "Anahtar kelimelerle otomatik filtre", "status": "✅ Demo"},
        {"step": 3, "title": "Çeviri", "desc": "ChatGPT API ile TR/EN/JP çeviri", "status": "🔄 Gerçek"},
        {"step": 4, "title": "PDF Oluşturma", "desc": "Otomatik formatlı PDF", "status": "✅ Demo"},
        {"step": 5, "title": "Mail Gönderme", "desc": "Outlook'tan otomatik gönderim", "status": "🔄 Gerçek"},
        {"step": 6, "title": "Zamanlama", "desc": "Her sabah 06:00'da otomatik başlatma", "status": "🔄 Gerçek"}
    ]
    
    for step in automation_steps:
        col_step1, col_step2, col_step3 = st.columns([0.1, 0.6, 0.3])
        with col_step1:
            st.markdown(f"**{step['step']}.**")
        with col_step2:
            st.markdown(f"**{step['title']}**")
            st.caption(step['desc'])
        with col_step3:
            st.markdown(step['status'])

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption(f"🔄 Port: {PORT} | Python {os.sys.version.split()[0]}")
with footer_col2:
    st.caption("© 2026 Otomotiv Haber Küratörü - Demo v2.0")
with footer_col3:
    if st.button("🔄 Sayfayı Yenile"):
        st.rerun()

# Debug için
if st.sidebar.checkbox("🔧 Geliştirici Modu", False):
    st.sidebar.write("### Debug Bilgileri")
    st.sidebar.write(f"Python: {os.sys.version}")
    st.sidebar.write(f"Streamlit: {st.__version__}")
    st.sidebar.write(f"Port: {PORT}")
    st.sidebar.write(f"Çalışma Dizini: {os.getcwd()}")
