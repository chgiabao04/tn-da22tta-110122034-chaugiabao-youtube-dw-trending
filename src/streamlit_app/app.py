import streamlit as st
from dotenv import load_dotenv

from page.dashboard import render_dashboard
from page.home import render_home
from page.predict_page import render_predict
from page.live_dashboard import render_trending
from ui import load_global_css, render_navbar

load_dotenv()

st.set_page_config(
    page_title="VISION",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_global_css()

PAGES = {
    "home": render_home,
    "dashboard": render_dashboard,
    "trending": render_trending,
    "predict": render_predict,
}

current_tab = st.query_params.get("tab", "home")
if current_tab not in PAGES:
    current_tab = "home"

st.session_state.current_tab = current_tab
render_navbar(current_tab)
PAGES[current_tab]()