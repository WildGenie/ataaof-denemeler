import streamlit as st
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from anadolu.utils.ui_utils import init_page_config, render_sidebar_header

init_page_config(page_title="Ayarlar", page_icon="⚙️")
render_sidebar_header()

st.title("⚙️ Ayarlar")
st.info("Bu özellik yapım aşamasındadır.")
st.markdown("Uygulama ayarları ve yapılandırma seçenekleri buraya gelecek.")
