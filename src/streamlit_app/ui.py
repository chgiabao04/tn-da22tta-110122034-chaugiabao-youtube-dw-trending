from pathlib import Path

import streamlit as st


ASSETS_DIR = Path(__file__).parent / "assets"


def load_global_css() -> None:
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_navbar(active_tab: str = "home") -> None:
    nav_items = [
        ("home", "", "Home"),
        ("dashboard", "", "Dashboard"),
        ("trending", "", "Trending Analytics"),
        ("predict", "", "Predict"),
    ]
    links = "".join(
        f'<a class="nav-link {"active" if key == active_tab else ""}" href="?tab={key}" target="_self">{icon} {label}</a>'
        for key, icon, label in nav_items
    )
    st.markdown(f"""
    <div class="navbar">
        <a class="nav-logo" href="?tab=home" target="_self">
            <div style="display:inline-block; background: rgba(200,200,200,0.18); border-radius: 6px; padding: 4px 12px; letter-spacing: 2px;">VISION</div>
        </a>
        <div class="nav-links">{links}</div>
        <div class="nav-right" style="width: 120px;"></div>
    </div>
    """, unsafe_allow_html=True)