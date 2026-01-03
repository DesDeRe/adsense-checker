import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai  # <--- Hatanın sebebi bu satırın eksik olması
import time

from fpdf import FPDF

def pdf_olustur(veriler, ai_tavsiyesi):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="AdSense Onay Analiz Raporu", ln=1, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Skor: %{veriler['puan']}\n\nAI Tavsiyeleri:\n{ai_tavsiyesi}")
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# Streamlit butonunun altına:
if st.button("Raporu PDF Olarak İndir"):
    pdf_data = pdf_olustur(sonuc, response.text)
    st.download_button(label="📥 Dosyayı Kaydet", data=pdf_data, file_name="adsense_rapor.pdf", mime="application/pdf")


# --- GEMINI AYARI ---
# Kendi API anahtarını buraya eklemelisin: https://aistudio.google.com/app/apikey
genai.configure(api_key="")

class AdSensePro:
    def __init__(self, url):
        self.url = url if url.startswith("http") else "https://" + url
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.data = {"puan": 0, "hatalar": [], "hiz": 0, "yazi_sayisi": 0}

    def analiz_motoru(self):
        try:
            # 1. Hız ve Bağlantı
            start = time.time()
            res = requests.get(self.url, headers=self.headers, timeout=10)
            self.data["hiz"] = round(time.time() - start, 2)
            soup = BeautifulSoup(res.text, 'html.parser')

            # 2. Politika Sayfaları Tarama
            found_pages = []
            keywords = {"Gizlilik": "privacy", "İletişim": "contact", "Hakkımızda": "about"}
            links = [a.get('href', '').lower() for a in soup.find_all('a', href=True)]
            
            for name, key in keywords.items():
                if any(key in link for link in links):
                    self.data["puan"] += 15
                    found_pages.append(name)
                else:
                    self.data["hatalar"].append(f"{name} sayfası bulunamadı.")

            # 3. WordPress API Analizi
            try:
                wp_res = requests.get(f"{self.url}/wp-json/wp/v2/posts", timeout=5).json()
                self.data["yazi_sayisi"] = len(wp_res)
                if len(wp_res) >= 20: self.data["puan"] += 40
                else: self.data["hatalar"].append(f"Yazı sayısı yetersiz (Şu an: {len(wp_res)})")
            except:
                self.data["hatalar"].append("WordPress API erişimi kapalı.")

            # 4. SEO & UX
            if soup.find('title'): self.data["puan"] += 5
            if self.data["hiz"] < 2: self.data["puan"] += 10

            return self.data
        except:
            return None

# --- WEB ARAYÜZÜ ---
st.set_page_config(page_title="AI AdSense Expert", layout="wide")

st.title("🤖 AI Destekli AdSense Onay Uzmanı")
st.sidebar.header("Ayarlar")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

url_input = st.text_input("Analiz edilecek siteyi girin:", placeholder="kolaykredim.com.tr")

if st.button("Kapsamlı Analizi Başlat"):
    if not url_input or not api_key:
        st.error("Lütfen hem URL hem de API Key girin kanka!")
    else:
        with st.spinner('Yapay zeka sitenizi didik didik ediyor...'):
            bot = AdSensePro(url_input)
            sonuc = bot.analiz_motoru()
            
            if sonuc:
                # Üst Paneller
                c1, c2, c3 = st.columns(3)
                c1.metric("Genel Skor", f"%{sonuc['puan']}")
                c2.metric("Açılış Hızı", f"{sonuc['hiz']} sn")
                c3.metric("İçerik Sayısı", sonuc['yazi_sayisi'])

                # AI Tavsiyeleri Bölümü
                st.divider()
                st.subheader("📝 Yapay Zeka Özel İyileştirme Planı")
                
                # Gemini'ye raporu gönderiyoruz
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"""
                Bir AdSense uzmanı gibi davran. Site: {url_input}. 
                Bulunan hatalar: {sonuc['hatalar']}. 
                Skor: %{sonuc['puan']}. 
                Bu siteye onay alması için neler yapması gerektiğini madde madde, profesyonel ama samimi bir dille anlat.
                """
                
                try:
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except:
                    st.error("AI raporu oluşturulurken bir hata oluştu.")
                
                # Teknik Detay Listesi
                with st.expander("Teknik Detayları Gör"):
                    for hata in sonuc['hatalar']:
                        st.write(f"❌ {hata}")
            else:

                st.error("Siteye ulaşılamadı. Lütfen URL'yi kontrol et.")



