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
            <div class="logo-icon">▶</div>
            VISION
        </a>
        <div class="nav-links">{links}</div>
        <div class="nav-right">
            <button class="theme-toggle" id="themeToggle" onclick="toggleTheme()" title="Chuyển chế độ sáng/tối">
                <span id="themeIcon">🌙</span>
            </button>
        </div>
    </div>

    <script>
    (function() {{
        var saved = localStorage.getItem('vision_theme');
        if (saved === 'dark') {{
            document.body.classList.add('dark-mode');
            var icon = document.getElementById('themeIcon');
            if (icon) icon.textContent = '☀️';
        }}
    }})();

    function toggleTheme() {{
        var isDark = document.body.classList.toggle('dark-mode');
        var icon = document.getElementById('themeIcon');
        if (icon) icon.textContent = isDark ? '☀️' : '🌙';
        localStorage.setItem('vision_theme', isDark ? 'dark' : 'light');
    }}
    </script>
    """, unsafe_allow_html=True)
