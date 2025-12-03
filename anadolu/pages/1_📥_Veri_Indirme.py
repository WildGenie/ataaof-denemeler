import streamlit as st
import subprocess
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from anadolu.utils.ui_utils import load_courses, get_course_names, get_course_code, init_page_config, render_sidebar_header
from libs.anadolu_lib import (
    DEFAULT_UNIT_COUNT,
    DEFAULT_FETCH_ATTEMPTS,
    DEFAULT_LEARN_ATTEMPTS
)

# Page Config
init_page_config(page_title="Veri İndirme", page_icon="📥")

# Sidebar
render_sidebar_header()

st.title("📥 Veri İndirme Merkezi")
st.markdown("Ders materyallerini, soruları ve sınavları buradan indirebilirsiniz.")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETCH_SCRIPT = os.path.join(BASE_DIR, "fetch.py")

# Load Data
courses = load_courses()
course_names = get_course_names(courses)

# --- Sidebar Controls ---
st.sidebar.header("⚙️ İndirme Ayarları")

# Course Selection
selected_course_str = st.sidebar.selectbox(
    "Ders Seçin",
    ["Tüm Dersler"] + course_names,
    index=0
)
selected_course_code = get_course_code(selected_course_str)

# Unit Selection
use_specific_unit = st.sidebar.checkbox("Belirli Bir Ünite", value=False)
unit = None
if use_specific_unit:
    unit = st.sidebar.number_input("Ünite No", min_value=1, max_value=14, value=1)

# Actions
st.sidebar.subheader("İşlem Modu")
mode = st.sidebar.radio(
    "Çalışma Modu",
    ["Soru Bankası", "Çıkmış Sorular", "Sorularla Öğrenelim", "Özel (Gelişmiş)"]
)

# Logic for modes
if mode == "Soru Bankası":
    action_questions = True
    action_learn = False
    action_exams = False
    action_pdf = False
    action_chapters = False
    action_materials = False
    st.info("ℹ️ **Soru Bankası Modu:** Seçilen derslerin ünite soruları indirilecek.")
elif mode == "Çıkmış Sorular":
    action_questions = False
    action_learn = False
    action_exams = True
    action_pdf = False
    action_chapters = False
    action_materials = True
    st.info("ℹ️ **Çıkmış Sorular Modu:** Geçmiş dönem sınavları PDF olarak indirilecek.")
elif mode == "Sorularla Öğrenelim":
    action_questions = False
    action_learn = True
    action_exams = False
    action_pdf = False
    action_chapters = False
    action_materials = False
    st.info("ℹ️ **Öğrenme Modu:** 'Sorularla Öğrenelim' modülündeki sorular indirilecek.")
else: # Custom
    st.info("ℹ️ **Özel Mod:** İndirilecek içerikleri manuel olarak seçin.")
    col1, col2 = st.columns(2)
    with col1:
        action_questions = st.checkbox("Soru Bankası", value=True)
        action_learn = st.checkbox("Sorularla Öğrenelim", value=False)
        action_exams = st.checkbox("Çıkmış Sorular", value=False)
    with col2:
        action_pdf = st.checkbox("PDF İndir", value=False)
        action_chapters = st.checkbox("Ünite Bilgileri", value=False)
        action_materials = st.checkbox("Materyal Listesi", value=False)

# Advanced Options in Expander
with st.expander("Gelişmiş Ayarlar"):
    c1, c2, c3 = st.columns(3)
    with c1:
        parallel = st.number_input("Paralel İşlem", min_value=1, max_value=10, value=1)
    with c2:
        no_cache = st.checkbox("Önbelleği Yoksay", value=False)
    with c3:
        local_only = st.checkbox("Sadece Yerel", value=False)

    st.markdown("---")
    st.caption("Döngü Ayarları")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        fetch_attempts = st.number_input("Soru Denemesi", min_value=1, value=DEFAULT_FETCH_ATTEMPTS)
    with sc2:
        learn_attempts = st.number_input("Öğrenme Denemesi", min_value=1, value=DEFAULT_LEARN_ATTEMPTS)
    with sc3:
        unit_count = st.number_input("Ünite Sayısı", min_value=1, value=DEFAULT_UNIT_COUNT)

# Construct Command
command = [sys.executable, FETCH_SCRIPT]

if selected_course_code:
    command.extend(["--course", selected_course_code])

if use_specific_unit and unit:
    command.extend(["--unit", str(unit)])

if action_questions: command.append("--questions")
if action_learn: command.append("--learn-questions")
if action_exams: command.append("--download-exams")
if action_pdf: command.append("--pdf")
if action_chapters: command.append("--chapters")
if action_materials: command.append("--materials")

if parallel > 1: command.extend(["--parallel", str(parallel)])
if no_cache: command.append("--no-cache")
if local_only: command.append("--local-only")

if fetch_attempts != DEFAULT_FETCH_ATTEMPTS: command.extend(["--fetch-attempts", str(fetch_attempts)])
if learn_attempts != DEFAULT_LEARN_ATTEMPTS: command.extend(["--learn-attempts", str(learn_attempts)])
if unit_count != DEFAULT_UNIT_COUNT: command.extend(["--unit-count", str(unit_count)])

# Display Command
st.markdown("### 🚀 İşlem Başlat")
st.code(" ".join(command), language="bash")

if st.button("Çalıştır", type="primary", use_container_width=True):
    st.markdown("### 📝 İşlem Çıktısı")
    output_area = st.empty()

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        output_text = ""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_text += line
                output_area.code(output_text[-5000:], language="text")

        if process.returncode == 0:
            st.success("✅ İşlem başarıyla tamamlandı!")
            st.balloons()
        else:
            st.error(f"❌ İşlem hata ile sonlandı. Kod: {process.returncode}")

    except Exception as e:
        st.error(f"Hata oluştu: {e}")
