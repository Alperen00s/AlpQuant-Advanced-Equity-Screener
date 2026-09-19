import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import io
import concurrent.futures
import plotly.graph_objects as go
import numpy as np
import os
import tempfile
import matplotlib.pyplot as plt
from fpdf import FPDF

# --- 1. SAYFA AYARLARI VE CSS ---
st.set_page_config(page_title="AlpQuant | Financial Terminal", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #131722; color: #D1D4DC; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    [data-testid="stSidebar"] { background-color: #1E222D !important; border-right: 1px solid #2A2E39; }
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 600 !important; }
    p, span, div { color: #D1D4DC; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; font-weight: 600; }
    [data-testid="stMetricLabel"] { color: #787B86 !important; font-size: 0.9rem !important; text-transform: uppercase; letter-spacing: 0.5px; }
    .stButton > button {
        background-color: #2962FF !important; color: #FFFFFF !important;
        border: none !important; border-radius: 4px !important;
        transition: background-color 0.2s ease !important; font-weight: 500 !important;
    }
    .stButton > button:hover { background-color: #1E53E5 !important; }
    hr { border-color: #2A2E39 !important; margin-top: 1rem; margin-bottom: 1rem; }
    .streamlit-expanderHeader { background-color: #1E222D !important; border-bottom: 1px solid #2A2E39 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='margin-bottom: 0px;'>AlpQuant <span style='color: #787B86; font-size: 18px; font-weight: 400;'>| Advanced Equity Screener</span></h2>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 5px;'>", unsafe_allow_html=True)

# --- UYGULAMA HAFIZASI VE TETİKLEYİCİLER ---
if "tarama_yapildi" not in st.session_state: st.session_state.tarama_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = pd.DataFrame()
if "ham_veri" not in st.session_state: st.session_state.ham_veri = pd.DataFrame()
if "son_aranan_hisseler" not in st.session_state: st.session_state.son_aranan_hisseler = []
if "menu_kapat" not in st.session_state: st.session_state.menu_kapat = False

def taramayi_baslat(): 
    st.session_state.tarama_yapildi = True
    st.session_state.menu_kapat = True

def ana_ekrana_don():
    st.session_state.tarama_yapildi = False
    st.session_state.analiz_sonucu = pd.DataFrame()

# Javascript ile sol menüyü otomatik daraltma
if st.session_state.menu_kapat:
    st.markdown("""
        <script>
            var elements = window.parent.document.querySelectorAll('[data-testid="stSidebarCollapseButton"]');
            if (elements.length > 0) {
                elements[0].click();
            }
        </script>
    """, unsafe_allow_html=True)
    st.session_state.menu_kapat = False

# --- 1. PDF ÜRETİM FONKSİYONU (GRAFİKLİ VERSİYON) ---
def generate_pdf_file(hisse, veri_dict):
    pdf = FPDF()
    pdf.add_page()
    
    def tr2eng(text):
        t = str(text).replace('ı','i').replace('ğ','g').replace('ü','u').replace('ş','s').replace('ö','o').replace('ç','c').replace('İ','I').replace('Ğ','G').replace('Ü','U').replace('Ş','S').replace('Ö','O').replace('Ç','C')
        return t.encode('latin-1', 'ignore').decode('latin-1')

    # Başlık ve Şirket Bilgileri
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(41, 98, 255)
    pdf.cell(0, 12, tr2eng("AlpQuant - EQUITY RESEARCH REPORT"), ln=1, align='C')
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(120, 123, 134)
    pdf.cell(0, 8, tr2eng(f"Ticker: {hisse}  |  Sector: {veri_dict.get('Sector', '')}  |  Date: {datetime.date.today()}"), ln=1, align='C')
    pdf.line(10, 32, 200, 32)
    pdf.ln(8)
    
    # 1. Finansal Metrikler
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Financial & Technical Analysis Profile", ln=1)
    pdf.ln(2)
    
    metrics_list = [(k, v) for k, v in veri_dict.items() if k not in ["Ticker", "Sector", "SMA50", "SMA200"]]
    
    for i in range(0, len(metrics_list), 2):
        k1, v1 = metrics_list[i]
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(35, 6, tr2eng(f"{k1}:"), ln=0)
        
        v_str1 = str(v1)
        if "Bull" in v_str1 or "Up" in v_str1: pdf.set_text_color(8, 153, 129)
        elif "Bear" in v_str1 or "Down" in v_str1 or v_str1 == "N/A": pdf.set_text_color(242, 54, 69)
        else: pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(55, 6, tr2eng(v_str1), ln=0)
        
        if i+1 < len(metrics_list):
            k2, v2 = metrics_list[i+1]
            pdf.set_font("Arial", 'B', 11)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(35, 6, tr2eng(f"{k2}:"), ln=0)
            
            v_str2 = str(v2)
            if "Bull" in v_str2 or "Up" in v_str2: pdf.set_text_color(8, 153, 129)
            elif "Bear" in v_str2 or "Down" in v_str2 or v_str2 == "N/A": pdf.set_text_color(242, 54, 69)
            else: pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(55, 6, tr2eng(v_str2), ln=1)
        else:
            pdf.ln(6)
            
    pdf.ln(5)
    
    # --- YENİ: MATPLOTLIB İLE BULUT-DOSTU GRAFİK ÇİZİMİ ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Algorithmic Price Action (6 Months)", ln=1)
    
    img_path = None
    try:
        hist_data = yf.Ticker(f"{hisse}.IS").history(period="6mo")
        if not hist_data.empty:
            plt.figure(figsize=(10, 4))
            plt.plot(hist_data.index, hist_data['Close'], color='#2962FF', linewidth=1.5)
            plt.fill_between(hist_data.index, hist_data['Close'], hist_data['Close'].min(), color='#2962FF', alpha=0.1)
            plt.grid(axis='y', linestyle='--', alpha=0.5)
            plt.gca().spines['top'].set_visible(False)
            plt.gca().spines['right'].set_visible(False)
            plt.xticks(rotation=45, fontsize=8)
            plt.yticks(fontsize=8)
            plt.tight_layout()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img: 
                img_path = tmp_img.name
            plt.savefig(img_path, dpi=150)
            plt.close()
            
            pdf.image(img_path, x=10, w=190)
    except:
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "(Chart data currently unavailable)", ln=1)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf: 
        pdf_path = tmp_pdf.name
        
    pdf.output(pdf_path)
    with open(pdf_path, "rb") as f: 
        pdf_bytes = f.read()
        
    try: 
        os.remove(pdf_path)
        if img_path: os.remove(img_path)
    except: 
        pass
        
    return pdf_bytes

# --- 2. LİSTELER VE SÖZLÜKLER ---
bist_30 = ["AKBNK", "ALARK", "ARCLK", "ASELS", "ASTOR", "BIMAS", "DOAS", "EKGYO", "ENKAI", "EREGL", "FROTO", "GARAN", "GUBRF", "HEKTS", "ISCTR", "KCHOL", "KOZAA", "KOZAL", "KRDMD", "ODAS", "PETKM", "PGSUS", "SAHOL", "SASA", "SISE", "TCELL", "THYAO", "TOASO", "TUPRS", "YKBNK"]
bankalar = ["AKBNK", "GARAN", "YKBNK", "ISCTR", "ALBRK", "VAKBN", "HALKB", "TSKB", "SKBNK"]
holdingler = ["KCHOL", "SAHOL", "AGHOL", "ALARK", "DOHOL", "TKFEN", "ENKAI", "GOHOL"]
otomotiv = ["FROTO", "TOASO", "DOAS", "TTRAK", "ASUZU", "KARSAN", "TMSN"]
ulastirma_havacilik = ["THYAO", "PGSUS", "TAVHL", "CLEBI"]
enerji = ["TUPRS", "ENJSA", "GWIND", "GESAN", "SMRTG", "CWENE", "NATEN", "MAGEN", "KARYE", "ZOREN", "ODAS", "CANTE", "ASTOR", "EUPWR", "ALFAS"]
perakende_ticaret = ["BIMAS", "SOKM", "MGROS", "MAVI", "BIZIM", "VAKKO", "TKNSA"]
teknoloji_bilisim = ["LOGO", "MIATK", "ARDYZ", "VBTYZ", "MOBTL", "PAPIL", "FONET", "KFEIN", "LINK", "ASELS", "KONTR"]
gida_tarim = ["HEKTS", "GUBRF", "TATGD", "TUKAS", "YYLGD", "ELITE", "FADEL", "ULKER", "AEFES", "CCOLA", "PNLSN"]
demir_celik_maden = ["EREGL", "KRDMD", "KCAER", "BRSAN", "KOZAA", "KOZAL", "KMPUR", "CEMAS"]
cimento_insaat = ["CIMSA", "AKCNS", "BUCIM", "OYAKC", "NUHCM", "KLSER", "KAYSE"]
kimya_plastik_ilac = ["SASA", "PETKM", "AKSA", "DEVA", "TRILC", "GENIL", "RTALB"]
gyolar = ["EKGYO", "SRVGY", "ISGYO", "AKFGY", "TSGYO", "PAGYO", "DMLKT", "TRGYO", "HLGYO", "VKGYO", "ZGYO", "OZKGY", "KZBGY"]
sigorta_araci_kurumlar = ["AKGRT", "ANSGR", "TURSG", "ISMEN", "INFO", "OSMEN"]
dayanikli_tuketim = ["ARCLK", "VESBE", "VESTL"]
telekom = ["TCELL", "TTKOM"]

sektor_sozlugu = {
    "Banking": bankalar, "Holdings & Investments": holdingler, "Automotive": otomotiv,
    "Transportation": ulastirma_havacilik, "Energy": enerji, "Retail": perakende_ticaret,
    "Technology": teknoloji_bilisim, "Food & Agriculture": gida_tarim, "Mining & Steel": demir_celik_maden,
    "Construction": cimento_insaat, "Chemicals & Pharma": kimya_plastik_ilac, "Real Estate (REIT)": gyolar,
    "Insurance & Brokerage": sigorta_araci_kurumlar, "Durables": dayanikli_tuketim, "Telecommunications": telekom
}
bist_100_ham = []
for liste in sektor_sozlugu.values(): bist_100_ham.extend(liste)
bist_100 = list(set(bist_100_ham + bist_30))

katilim_30 = ["BIMAS", "THYAO", "ASELS", "FROTO", "TUPRS", "DOAS", "ENJSA", "ALBRK", "OYAKC", "EREGL", "ASTOR", "GESAN", "MIATK", "CWENE", "EUPWR", "ALFAS", "KCAER", "BRSAN", "CIMSA", "ARCLK", "LOGO", "SOKM", "HEKTS", "GWIND", "YUNSA", "TTRAK", "YEOTK", "SDTTR", "CVKMD", "KORDS"]
katilim_tum = list(set(katilim_30 + ["KTLEV", "ALTNY", "SRVGY", "LKMNH", "DMLKT", "KAYSE", "FMIZP", "BRYAT", "BRLSM", "BUCIM", "TUKAS", "TATGD", "ARDYZ", "MOBTL", "VBTYZ", "BIZIM", "FADEL", "ELITE", "RTALB", "TRILC", "GENIL", "DEVA", "SASA", "GUBRF", "VAKFN", "KZBGY", "KLNMA", "INFO", "OSMEN", "TRGYO", "HLGYO", "VKGYO", "KMPUR", "SUWEN", "MTRKS", "PCILT", "KARYE", "NATEN", "MAGEN", "ESEN", "AGROT", "REEDR", "EBEBK", "OBAMS"]))

# --- 3. PROFESYONEL SOL MENÜ ---
st.sidebar.markdown("<h3 style='text-align: center; color: #FFFFFF;'>Filters & Options</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

with st.sidebar.expander("📌 Market & Sector", expanded=True):
    endeks_secimi = st.radio("Index", ("BIST 100", "BIST 30", "BIST Islamic"))
    sektor_secimi = st.multiselect("Sector", options=list(sektor_sozlugu.keys()), placeholder="All Sectors")
    sadece_katilim = st.checkbox("Islamic Compliant Only")

with st.sidebar.expander("📊 Fundamental Analysis", expanded=True):
    fk_max = st.number_input("Max P/E", min_value=0.0, max_value=200.0, value=25.0, step=1.0)
    pddd_max = st.number_input("Max P/B", min_value=0.0, max_value=50.0, value=5.0, step=0.5)
    peg_max = st.number_input("Max PEG Ratio", min_value=0.0, max_value=20.0, value=5.0, step=0.1)
    roe_min = st.number_input("Min ROE (%)", min_value=-50, max_value=100, value=5, step=1)
    temettu_min = st.number_input("Min Div Yield (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)

with st.sidebar.expander("📈 Technical & Risk", expanded=True):
    rsi_max = st.slider("Max RSI", 10, 90, 80)
    beta_max = st.slider("Max Beta (Volatility)", 0.0, 3.0, 1.5, 0.1)
    sadece_macd_al = st.checkbox("MACD 'Bull' Signal")
    sadece_trend = st.checkbox("Uptrend (SMA50 > 200)")

st.sidebar.markdown("<br>", unsafe_allow_html=True)
eksik_verileri_goster = st.sidebar.checkbox("Allow Missing Data (N/A)", value=True)

with st.sidebar.form(key='screener_form'):
    st.form_submit_button(label='🚀 RUN SCREENER', use_container_width=True, on_click=taramayi_baslat)

# --- YASAL UYARI (DISCLAIMER) ---
st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style='font-size: 0.75rem; color: #787B86; text-align: justify; padding: 10px; background-color: #131722; border-radius: 5px;'>
    <b>Disclaimer:</b> The data and insights provided by AlpQuant are for informational and educational purposes only. They do not constitute financial, investment, or trading advice. Data may be delayed or inaccurate. Always conduct your own research before making investment decisions.
    </div>
""", unsafe_allow_html=True) 

# --- 4. VERİ MOTORU ---
def verileri_hazirla_paralel(hisseler):
    if not hisseler: return pd.DataFrame()
    progress_bar = st.progress(0)
    hesaplanan_veriler, tamamlanan, toplam_hisse = [], 0, len(hisseler)
    
    def guvenli_deger_al(deger):
        try:
            if deger is None or deger == 999.0 or deger == "" or pd.isna(deger): return "N/A"
            return round(float(deger), 2)
        except: return "N/A"

    def tek_hisse_isle(hisse):
        guncel_fiyat, fk_orani, pddd_orani, roe_orani = 0, 999.0, 999.0, 0.0
        sma_50, sma_200, rsi_14, temettu_verimi, peg_rasyosu, beta_katsayisi = 999.0, 999.0, 999.0, 0.0, 999.0, 999.0
        macd_sinyal, bb_genislik = "N/A", 999.0
        
        grup = "Other"
        for sek_isim, sek_list in sektor_sozlugu.items():
            if hisse in sek_list: grup = sek_isim; break
            
        try:
            ticker_obj = yf.Ticker(f"{hisse}.IS")
            info_full = ticker_obj.info
            guncel_fiyat = info_full.get('currentPrice', info_full.get('regularMarketPrice', 0))
            if guncel_fiyat == 0:
                try: guncel_fiyat = ticker_obj.fast_info.last_price
                except: pass
            
            fk_orani = info_full.get('trailingPE', 999.0)
            pddd_orani = info_full.get('priceToBook', 999.0)
            raw_roe = info_full.get('returnOnEquity', None)
            roe_orani = raw_roe * 100 if raw_roe is not None else 0.0
            raw_div = info_full.get('dividendYield', None)
            temettu_verimi = raw_div * 100 if raw_div is not None else 0.0
            peg_rasyosu = info_full.get('pegRatio', info_full.get('trailingPegRatio', 999.0))
            beta_katsayisi = info_full.get('beta', 999.0) 
            sma_50 = info_full.get('fiftyDayAverage', 999.0)
            sma_200 = info_full.get('twoHundredDayAverage', 999.0)

            try:
                hist = ticker_obj.history(period="6mo")
                if not hist.empty:
                    close_px = hist['Close'].dropna() 
                    if len(close_px) > 30:
                        delta = close_px.diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi_series = 100 - (100 / (1 + rs))
                        if not rsi_series.dropna().empty: rsi_14 = rsi_series.dropna().iloc[-1]

                        ema12 = close_px.ewm(span=12, adjust=False).mean()
                        ema26 = close_px.ewm(span=26, adjust=False).mean()
                        macd_line = ema12 - ema26
                        signal_line = macd_line.ewm(span=9, adjust=False).mean()
                        macd_hist = macd_line - signal_line
                        if not macd_hist.dropna().empty: macd_sinyal = "🟢 Bull" if macd_hist.dropna().iloc[-1] > 0 else "🔴 Bear"

                        sma20 = close_px.rolling(window=20).mean()
                        std20 = close_px.rolling(window=20).std()
                        bb_width_series = (((sma20 + (std20 * 2)) - (sma20 - (std20 * 2))) / sma20) * 100
                        if not bb_width_series.dropna().empty: bb_genislik = bb_width_series.dropna().iloc[-1]
            except: pass
        except: pass 
        
        trend_durumu = "🚀 Up" if (sma_50 != 999.0 and sma_200 != 999.0 and sma_50 > sma_200) else "📉 Down"
        
        return {
            "Ticker": hisse, "Sector": grup, "Price": guvenli_deger_al(guncel_fiyat),
            "P/E": guvenli_deger_al(fk_orani), "P/B": guvenli_deger_al(pddd_orani), "PEG": guvenli_deger_al(peg_rasyosu),
            "ROE%": guvenli_deger_al(roe_orani), "Div Yield%": guvenli_deger_al(temettu_verimi) if temettu_verimi != 0.0 else 0.0,
            "Beta": guvenli_deger_al(beta_katsayisi),
            "RSI": guvenli_deger_al(rsi_14), "BBW%": guvenli_deger_al(bb_genislik), "MACD": macd_sinyal, 
            "Trend": trend_durumu, "SMA50": guvenli_deger_al(sma_50), "SMA200": guvenli_deger_al(sma_200)
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        gelecek_sonuclar = {executor.submit(tek_hisse_isle, h): h for h in hisseler}
        for future in concurrent.futures.as_completed(gelecek_sonuclar):
            tamamlanan += 1
            progress_bar.progress(tamamlanan / toplam_hisse)
            try:
                if (sonuc := future.result()) is not None: hesaplanan_veriler.append(sonuc)
            except: pass

    progress_bar.empty()
    return pd.DataFrame(hesaplanan_veriler) if hesaplanan_veriler else pd.DataFrame()

# --- ANA EKRAN AKIŞI ---
if not st.session_state.tarama_yapildi:
    st.markdown("<h3 style='color: #D1D4DC;'>Market Overview</h3>", unsafe_allow_html=True)
    st.info("👈 Set your filters on the left panel and click 'RUN SCREENER' to start analysis.")
    
    def render_dashboard(df, title):
        if df is None or df.empty or len(df) < 2:
            st.warning(f"⚠️ Yahoo Finance API currently does not provide stable data for '{title}'. Data provider limitation.")
            return
        
        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        pct_change = ((last_price - prev_price) / prev_price) * 100
        high_6m = df['High'].max()
        low_6m = df['Low'].min()
        sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"{title} Index", f"{last_price:,.2f}", f"{pct_change:.2f}%")
        c2.metric("6M High", f"{high_6m:,.2f}")
        c3.metric("6M Low", f"{low_6m:,.2f}")
        
        trend_status = "🟢 Bullish" if not pd.isna(sma50) and last_price > sma50 else "🔴 Bearish"
        dist_to_high = ((high_6m - last_price) / high_6m) * 100
        
        commentary = f"**Market Insight:** The index is currently showing a **{trend_status}** short-term trend based on the 50-day SMA. "
        if dist_to_high < 2:
            commentary += "It is trading very close to its 6-month high, indicating strong upside momentum."
        elif dist_to_high > 10:
            commentary += f"It has corrected by **{dist_to_high:.1f}%** from its 6-month peak, suggesting a consolidation phase."
        else:
            commentary += f"It is currently trading **{dist_to_high:.1f}%** below its 6-month peak."
        
        st.markdown(f"<div style='background-color:#1E222D; padding:15px; border-radius:8px; border-left: 4px solid #2962FF; margin-bottom: 20px; color: #D1D4DC; font-size: 15px;'>{commentary}</div>", unsafe_allow_html=True)

        fig_idx = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            increasing_line_color='#089981', decreasing_line_color='#F23645'
        )])
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722",
            margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=True, gridcolor="#2A2E39"), yaxis=dict(showgrid=True, gridcolor="#2A2E39", side="right"),
            height=450
        )
        st.plotly_chart(fig_idx, use_container_width=True)

    with st.spinner("Loading live market data..."):
        def safe_get_data(ticker):
            try:
                df = yf.Ticker(ticker).history(period="6mo")
                return df
            except:
                return pd.DataFrame()

        xu100 = safe_get_data("XU100.IS")
        xu030 = safe_get_data("XU030.IS")
            
        tab1, tab2 = st.tabs(["XU100 (BIST 100)", "XU030 (BIST 30)"])
        
        with tab1:
            render_dashboard(xu100, "XU100")
        with tab2:
            render_dashboard(xu030, "XU030")
  
else:
    if endeks_secimi == "BIST 100": evren = bist_100
    elif endeks_secimi == "BIST 30": evren = bist_30
    else: evren = katilim_tum
    
    sektor_havuzu = evren if not sektor_secimi else []
    if sektor_secimi:
        for s in sektor_secimi: sektor_havuzu.extend(sektor_sozlugu[s])
        
    aktif_hisseler = list(set(evren) & set(sektor_havuzu))
    if sadece_katilim: aktif_hisseler = [h for h in aktif_hisseler if h in katilim_tum]
    aktif_hisseler.sort()
    
    if len(aktif_hisseler) == 0:
        st.warning("No matches found. Please loosen your criteria.")
        st.button("⬅️ Back to Market", on_click=ana_ekrana_don)
    else:
        if aktif_hisseler != st.session_state.son_aranan_hisseler or st.session_state.ham_veri.empty:
            with st.spinner("Downloading Market Data..."):
                st.session_state.ham_veri = verileri_hazirla_paralel(aktif_hisseler)
                st.session_state.son_aranan_hisseler = aktif_hisseler
        
        df_b = st.session_state.ham_veri.copy()
        if not df_b.empty:
            for col in ['P/E', 'P/B', 'ROE%', 'Div Yield%', 'PEG', 'Beta', 'RSI', 'BBW%']:
                df_b[col] = pd.to_numeric(df_b[col], errors='coerce')
            
            fk_muaf_sektorler = ["Banking", "Real Estate (REIT)", "Insurance & Brokerage", "Holdings & Investments"]
            
            if eksik_verileri_goster:
                kural_pddd = (df_b["P/B"] <= pddd_max) | (df_b["P/B"].isna())
                kural_roe = (df_b["ROE%"] >= roe_min) | (df_b["ROE%"].isna())
                kural_rsi = (df_b["RSI"] <= rsi_max) | (df_b["RSI"].isna())
                kural_fk = (df_b["P/E"] <= fk_max) | (df_b["Sector"].isin(fk_muaf_sektorler)) | (df_b["P/E"].isna())
                kural_temettu = (df_b["Div Yield%"] >= temettu_min) | (df_b["Div Yield%"].isna())
                kural_peg = (df_b["PEG"] <= peg_max) | (df_b["PEG"].isna())
                kural_beta = (df_b["Beta"] <= beta_max) | (df_b["Beta"].isna())
            else:
                kural_pddd = df_b["P/B"] <= pddd_max
                kural_roe = df_b["ROE%"] >= roe_min
                kural_rsi = df_b["RSI"] <= rsi_max
                kural_fk = (df_b["P/E"] <= fk_max) | (df_b["Sector"].isin(fk_muaf_sektorler))
                kural_temettu = df_b["Div Yield%"] >= temettu_min
                kural_peg = df_b["PEG"] <= peg_max
                kural_beta = df_b["Beta"] <= beta_max
            
            filtrelenmis_df = df_b[kural_pddd & kural_roe & kural_rsi & kural_fk & kural_temettu & kural_peg & kural_beta]
            if sadece_trend: filtrelenmis_df = filtrelenmis_df[filtrelenmis_df["Trend"] == "🚀 Up"]
            if sadece_macd_al: filtrelenmis_df = filtrelenmis_df[filtrelenmis_df["MACD"] == "🟢 Bull"]
            
            st.session_state.analiz_sonucu = filtrelenmis_df
            
    if not st.session_state.analiz_sonucu.empty:
        df_show = st.session_state.analiz_sonucu
        
        col_back, col_title = st.columns([1, 9])
        with col_back:
            st.button("⬅️ Back to Market", on_click=ana_ekrana_don)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Matches", f"{len(df_show)}")
        fk_s = pd.to_numeric(df_show['P/E'], errors='coerce').dropna()
        c2.metric("Avg P/E", f"{round(fk_s.mean(), 2)}" if not fk_s.empty else "N/A")
        roe_s = pd.to_numeric(df_show['ROE%'], errors='coerce').dropna()
        c3.metric("Max ROE", f"{round(roe_s.max(), 1)}%" if not roe_s.empty else "N/A")
        c4.metric("Bullish MACD", f"{len(df_show[df_show['MACD'] == '🟢 Bull'])}")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.dataframe(df_show.drop(columns=["SMA50", "SMA200"]), use_container_width=True, hide_index=True)
        
        st.markdown("<br><h4 style='color: #D1D4DC;'>Advanced Chart & Research</h4>", unsafe_allow_html=True)
        secilen_grafik_hissesi = st.selectbox("Select Ticker for Research", df_show["Ticker"].tolist())
        
        if secilen_grafik_hissesi:
            try:
                hist_data = yf.Ticker(f"{secilen_grafik_hissesi}.IS").history(period="6mo")
                if not hist_data.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=hist_data.index, open=hist_data['Open'], high=hist_data['High'],
                        low=hist_data['Low'], close=hist_data['Close'],
                        increasing_line_color='#089981', decreasing_line_color='#F23645' 
                    )])
                    fig.update_layout(
                        title=f"{secilen_grafik_hissesi} | 1D",
                        xaxis_title="", yaxis_title="", template="plotly_dark",
                        paper_bgcolor="#131722", plot_bgcolor="#131722",
                        margin=dict(l=10, r=10, t=40, b=10), xaxis_rangeslider_visible=False,
                        xaxis=dict(showgrid=True, gridcolor="#2A2E39"), yaxis=dict(showgrid=True, gridcolor="#2A2E39", side="right"),
                        height=550
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    hisse_verisi = df_show[df_show["Ticker"] == secilen_grafik_hissesi].iloc[0].to_dict()
                    pdf_bytes = generate_pdf_file(secilen_grafik_hissesi, hisse_verisi)
                    st.download_button(
                        label=f"📥 Download Research Report ({secilen_grafik_hissesi})", data=pdf_bytes,
                        file_name=f"{secilen_grafik_hissesi}_Report.pdf", mime="application/pdf", type="primary"
                    )
            except:
                st.error("Chart loading error.")
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.warning("⚠️ No stocks matched your strict criteria (e.g., Bullish MACD + Uptrend). Please loosen your filters and try again.")
        col_center = st.columns([4, 2, 4])
        with col_center[1]:
            st.button("⬅️ Back to Market", on_click=ana_ekrana_don, use_container_width=True)