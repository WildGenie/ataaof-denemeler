import streamlit as st
import subprocess
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from anadolu.utils.ui_utils import load_courses, get_course_names, get_course_code, init_page_config, render_sidebar_header

# Page Config
init_page_config(page_title="AI Zenginleştirme", page_icon="🤖")

# Sidebar
render_sidebar_header()

st.title("🤖 AI Soru Zenginleştirme")
st.markdown("""
Google Gemini AI kullanarak sorulara detaylı açıklamalar, konu etiketleri ve ünite özetleri ekleyin.
""")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENRICH_SCRIPT = os.path.join(BASE_DIR, "scripts", "enrich_questions.py")
BATCH_SCRIPT = os.path.join(BASE_DIR, "scripts", "process_all_enrichments.py")

# Tabs
tab1, tab2 = st.tabs(["Tek Ders İşlemi", "Toplu İşlem (Batch)"])

# --- Single Course Tab ---
with tab1:
    st.header("Tek Ders Zenginleştirme")

    courses = load_courses()
    course_names = get_course_names(courses)

    col1, col2 = st.columns(2)

    with col1:
        selected_course_str = st.selectbox(
            "Ders Seçin",
            course_names,
            index=0,
            key="single_course_select"
        )
        selected_course_code = get_course_code(selected_course_str)

        # Find selected course object to get semester
        selected_course_obj = next((c for c in courses if c.get("DersKodu") == selected_course_code), None)
        default_donem = int(selected_course_obj.get("Donem", 1)) if selected_course_obj else 1

    with col2:
        donem = st.number_input("Dönem", min_value=1, max_value=8, value=default_donem, key="single_donem")
        no_cache_single = st.checkbox("Önbelleği Yoksay (Yeniden Oluştur)", key="single_no_cache")

    if st.button("Seçili Dersi Zenginleştir", type="primary"):
        cmd = [sys.executable, ENRICH_SCRIPT, "--course", selected_course_obj.get("CourseName"), "--donem", str(donem)]
        if no_cache_single:
            cmd.append("--no-cache")

        st.code(" ".join(cmd), language="bash")

        with st.status("İşlem yapılıyor...", expanded=True) as status:
            st.write("AI Modeli başlatılıyor...")
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                output_area = st.empty()
                output_text = ""

                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        output_text += line
                        output_area.code(output_text[-5000:], language="text")

                if process.returncode == 0:
                    status.update(label="İşlem Başarılı!", state="complete", expanded=False)
                    st.success("Zenginleştirme tamamlandı!")
                else:
                    status.update(label="Hata Oluştu", state="error")
                    st.error("İşlem başarısız oldu.")
            except Exception as e:
                st.error(f"Hata: {e}")

# --- Batch Tab ---
with tab2:
    st.header("Toplu Zenginleştirme")
    st.info("Birden fazla dersi sırayla işlemek için bu modu kullanın.")

    col1, col2 = st.columns(2)

    with col1:
        filter_type = st.radio(
            "Filtreleme Yöntemi",
            ["Tüm Dersler", "Kayıtlı Dersler (--enrolled)", "Dönem Bazlı", "Yarıyıl Bazlı (Güz/Bahar)"]
        )

    with col2:
        batch_donem = None
        batch_semester = None

        if filter_type == "Dönem Bazlı":
            batch_donem = st.number_input("Dönem Seçin", 1, 8, 1)
        elif filter_type == "Yarıyıl Bazlı (Güz/Bahar)":
            batch_semester = st.selectbox("Yarıyıl Seçin", ["guz", "bahar"])

        batch_no_cache = st.checkbox("Önbelleği Yoksay", key="batch_no_cache")

    if st.button("Toplu İşlemi Başlat", type="primary"):
        cmd = [sys.executable, BATCH_SCRIPT]

        if filter_type == "Kayıtlı Dersler (--enrolled)":
            cmd.append("--enrolled")
        elif filter_type == "Dönem Bazlı":
            cmd.extend(["--donem", str(batch_donem)])
        elif filter_type == "Yarıyıl Bazlı (Güz/Bahar)":
            cmd.extend(["--semester", batch_semester])

        if batch_no_cache:
            cmd.append("--no-cache")

        st.code(" ".join(cmd), language="bash")

        output_area = st.empty()

        try:
            process = subprocess.Popen(
                cmd,
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
                st.success("Toplu işlem tamamlandı!")
            else:
                st.error("Bazı işlemlerde hata oluştu.")

        except Exception as e:
            st.error(f"Hata: {e}")
