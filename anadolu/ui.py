import streamlit as st
import os
import sys
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anadolu.utils.ui_utils import load_courses, init_page_config, render_sidebar_header

# Initialize Page
init_page_config(page_title="Anadolu AÖF - Dashboard", page_icon="🏠")

# Sidebar
render_sidebar_header()
st.sidebar.success("Lütfen yukarıdaki menüden bir işlem seçin.")

# Main Content
st.title("🏠 Anadolu AÖF Asistanı")
st.markdown("### Hoş Geldiniz!")

st.markdown("""
Bu uygulama, Anadolu Üniversitesi AÖF ders materyallerini yönetmenize, soruları indirmenize ve yapay zeka ile zenginleştirmenize yardımcı olur.

Sol taraftaki menüyü kullanarak aşağıdaki işlemleri yapabilirsiniz:
""")

# Dashboard Cards
col1, col2, col3 = st.columns(3)

courses = load_courses()
total_courses = len(courses)

with col1:
    st.info(f"📚 **{total_courses}**\n\nToplam Ders")

with col2:
    st.success("🤖 **AI Destekli**\n\nSoru Çözümleri")

with col3:
    st.warning("📝 **Markdown**\n\nNot Dönüştürme")

st.markdown("---")

# Quick Actions / Descriptions
c1, c2 = st.columns(2)

with c1:
    st.subheader("📥 Veri İndirme")
    st.markdown("""
    * **Soru Bankası:** Ünite bazlı soruları indirin.
    * **Çıkmış Sorular:** Geçmiş sınavları PDF olarak alın.
    * **Sorularla Öğrenelim:** Öğrenme modülü sorularını çekin.
    """)

with c2:
    st.subheader("🤖 AI Zenginleştirme")
    st.markdown("""
    * **Akıllı Açıklamalar:** Sorulara detaylı çözümler ekleyin.
    * **Konu Analizi:** Soruların hangi konudan olduğunu öğrenin.
    * **Toplu İşlem:** Tüm dersleri tek tıkla zenginleştirin.
    """)

st.markdown("---")
st.caption("v2.0.0 - Gelişmiş Arayüz")
