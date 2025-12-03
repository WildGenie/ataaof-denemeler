import streamlit as st
import json
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

DERSLER_FILE = os.path.join(PROJECT_ROOT, "anadolu", "dersler.json")

@st.cache_data
def load_courses():
    """Load courses from dersler.json"""
    try:
        with open(DERSLER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"{DERSLER_FILE} bulunamadı!")
        return []

def get_course_names(courses):
    """Get list of formatted course names"""
    return [f"{c.get('CourseName')} ({c.get('DersKodu')})" for c in courses]

def get_course_code(course_str):
    """Extract course code from formatted string 'Name (Code)'"""
    if not course_str or course_str == "Tüm Dersler":
        return None
    return course_str.split("(")[-1].strip(")")

def init_page_config(page_title="Anadolu AÖF", page_icon="📚"):
    """Initialize standard page configuration"""
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )

def render_sidebar_header():
    """Render standard sidebar header"""
    st.sidebar.title("📚 Anadolu AÖF")
    st.sidebar.markdown("---")
