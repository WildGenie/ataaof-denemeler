import streamlit as st
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from anadolu.utils.ui_utils import init_page_config, render_sidebar_header

init_page_config(page_title="Materyal Yönetimi", page_icon="📁")
render_sidebar_header()

st.title("📁 Materyal Yönetimi")
st.info("Bu özellik yapım aşamasındadır.")
st.markdown("Yerel materyallerin eşleştirilmesi ve yönetimi arayüzü buraya gelecek.")
