import streamlit as st
import subprocess
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.anadolu_lib import (
    DEFAULT_UNIT_COUNT,
    DEFAULT_FETCH_ATTEMPTS,
    DEFAULT_LEARN_ATTEMPTS
)

# Page configuration
st.set_page_config(
    page_title="Anadolu AÖF Soru Getirici",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Anadolu AÖF Soru Getirici")
st.markdown("Bu uygulama `anadolu/fetch.py` betiğini çalıştırmak için bir arayüz sağlar.")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FETCH_SCRIPT = os.path.join(BASE_DIR, "fetch.py")
DERSLER_FILE = os.path.join(BASE_DIR, "dersler.json")

# Load courses
@st.cache_data
def load_courses():
    try:
        with open(DERSLER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"{DERSLER_FILE} bulunamadı!")
        return []

courses = load_courses()
course_names = [f"{c.get('CourseName')} ({c.get('DersKodu')})" for c in courses]

# Sidebar Configuration
st.sidebar.header("⚙️ Ayarlar")

# Course Selection
selected_course_str = st.sidebar.selectbox(
    "Ders Seçin (İsteğe Bağlı)",
    ["Tüm Dersler"] + course_names,
    index=0
)

selected_course_code = None
if selected_course_str != "Tüm Dersler":
    # Extract code from string "Name (Code)"
    selected_course_code = selected_course_str.split("(")[-1].strip(")")

# Unit Selection
use_specific_unit = st.sidebar.checkbox("Belirli Bir Ünite", value=False)
unit = None
if use_specific_unit:
    unit = st.sidebar.number_input("Ünite No", min_value=1, max_value=14, value=1)

# Actions
st.sidebar.subheader("İşlem Modu")
mode = st.sidebar.radio(
    "Çalışma Modu Seçin",
    ["Soru Bankası", "Çıkmış Sorular", "Sorularla Öğrenelim", "Özel (Gelişmiş)"]
)

st.sidebar.subheader("Seçili İşlemler")
if mode == "Soru Bankası":
    action_questions = True
    action_learn = False
    action_exams = False
    action_pdf = False
    action_chapters = False
    action_materials = False
    st.sidebar.info("Sadece Soru Bankası indirilecek.")
elif mode == "Çıkmış Sorular":
    action_questions = False
    action_learn = False
    action_exams = True
    action_pdf = False
    action_chapters = False
    action_materials = True # Usually needed for exams
    st.sidebar.info("Çıkmış Sorular ve Materyal Listesi indirilecek.")
elif mode == "Sorularla Öğrenelim":
    action_questions = False
    action_learn = True
    action_exams = False
    action_pdf = False
    action_chapters = False
    action_materials = False
    st.sidebar.info("Sorularla Öğrenelim modülü indirilecek.")
else: # Custom
    action_questions = st.sidebar.checkbox("Soru Bankası (--questions)", value=True)
    action_learn = st.sidebar.checkbox("Sorularla Öğrenelim (--learn-questions)", value=False)
    action_exams = st.sidebar.checkbox("Çıkmış Sorular (--download-exams)", value=False)
    action_pdf = st.sidebar.checkbox("PDF İndir (--pdf)", value=False)
    action_chapters = st.sidebar.checkbox("Ünite Bilgileri (--chapters)", value=False)
    action_materials = st.sidebar.checkbox("Materyal Listesi (--materials)", value=False)

# Advanced Options
st.sidebar.subheader("Gelişmiş Seçenekler")
parallel = st.sidebar.number_input("Paralel İşlem Sayısı", min_value=1, max_value=10, value=1)
no_cache = st.sidebar.checkbox("Önbelleği Yoksay (--no-cache)", value=False)
local_only = st.sidebar.checkbox("Sadece Yerel (--local-only)", value=False)

with st.sidebar.expander("Döngü Ayarları"):
    fetch_attempts = st.number_input("Soru Çekme Denemesi", min_value=1, value=DEFAULT_FETCH_ATTEMPTS)
    learn_attempts = st.number_input("Öğrenelim Denemesi", min_value=1, value=DEFAULT_LEARN_ATTEMPTS)
    unit_count = st.number_input("Ünite Sayısı", min_value=1, value=DEFAULT_UNIT_COUNT)

# Construct Command
command = [sys.executable, FETCH_SCRIPT]

if selected_course_code:
    command.extend(["--course", selected_course_code])

if use_specific_unit and unit:
    command.extend(["--unit", str(unit)])

if action_questions:
    command.append("--questions")
if action_learn:
    command.append("--learn-questions")
if action_exams:
    command.append("--download-exams")
if action_pdf:
    command.append("--pdf")
if action_chapters:
    command.append("--chapters")
if action_materials:
    command.append("--materials")

if parallel > 1:
    command.extend(["--parallel", str(parallel)])
if no_cache:
    command.append("--no-cache")
if local_only:
    command.append("--local-only")

# Add loop configs if changed from default
if fetch_attempts != DEFAULT_FETCH_ATTEMPTS:
    command.extend(["--fetch-attempts", str(fetch_attempts)])
if learn_attempts != DEFAULT_LEARN_ATTEMPTS:
    command.extend(["--learn-attempts", str(learn_attempts)])
if unit_count != DEFAULT_UNIT_COUNT:
    command.extend(["--unit-count", str(unit_count)])

# Display Command
st.subheader("Çalıştırılacak Komut")
st.code(" ".join(command), language="bash")

# Run Button
if st.button("🚀 Çalıştır", type="primary"):
    st.subheader("Çıktı")
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
                # Update output area (limit length to avoid UI lag if too long)
                output_area.code(output_text[-5000:], language="text")

        if process.returncode == 0:
            st.success("İşlem tamamlandı!")
        else:
            st.error(f"İşlem hata ile sonlandı. Kod: {process.returncode}")

    except Exception as e:
        st.error(f"Hata oluştu: {e}")

st.markdown("---")
st.caption("Not: Bu arayüz `anadolu/fetch.py` betiğini çalıştırır. Betiğin çıktıları yukarıdaki alanda görüntülenir.")
