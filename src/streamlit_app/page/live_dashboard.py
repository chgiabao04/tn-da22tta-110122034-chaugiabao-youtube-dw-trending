import html
import math
import os
from datetime import datetime as _dt

import requests
import streamlit as st
from pathlib import Path


# ─────────────────────────────────────────────
#  UTILITY HELPERS  (backend – unchanged)
# ─────────────────────────────────────────────
import re

def duration_to_seconds(duration):
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds

def _e(value):
    return html.escape(str(value or ""))


def _fmt(number):
    number = int(number or 0)
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return str(number)


def _fmt_date(value):
    if not value:
        return "-"
    try:
        return _dt.fromisoformat(value.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        return "-"


def _fmt_ago(value):
    """Return human-readable 'X giờ trước' string."""
    if not value:
        return ""
    try:
        pub = _dt.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        diff = _dt.utcnow() - pub
        h = int(diff.total_seconds() // 3600)
        if h < 1:
            return "vừa xong"
        if h < 24:
            return f"{h} giờ trước"
        d = h // 24
        return f"{d} ngày trước"
    except Exception:
        return ""


def _thumb(snippet, quality="high"):
    thumbs = snippet.get("thumbnails", {})
    for key in (quality, "maxres", "standard", "medium", "default"):
        if thumbs.get(key, {}).get("url"):
            return thumbs[key]["url"]
    return ""


# ─────────────────────────────────────────────
#  DATA  (backend – unchanged)
# ─────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_trending(region_code="VN", category_id="0"):
    keys = []
    i = 1
    while True:
        key = os.getenv(f"YOUTUBE_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1
    if not keys:
        return []

    params = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": 50,
        "key": keys[0],
    }
    if category_id != "0":
        params["videoCategoryId"] = category_id

    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception:
        return []


# ─────────────────────────────────────────────
#  STATIC MAPS
# ─────────────────────────────────────────────

CAT_ID_TO_NAME = {
    "1": "Film", "10": "Âm nhạc", "15": "Pets", "17": "Thể thao",
    "20": "Gaming", "22": "Vlog", "23": "Comedy", "24": "Giải trí",
    "25": "Tin tức", "26": "How-to", "27": "Giáo dục", "28": "Khoa học",
}

CAT_ICONS = {
    "Âm nhạc": "🎵", "Gaming": "🎮", "Giải trí": "🎭", "Vlog": "👥",
    "Thể thao": "⚽", "Tin tức": "📰", "Khoa học": "🔬", "Film": "🎬",
    "Pets": "🐱", "Comedy": "😂", "How-to": "🔧", "Giáo dục": "📚",
}

CAT_COLORS = ["#E8001D", "#3B82F6", "#22C55E", "#F59E0B", "#A855F7", "#EC4899", "#14B8A6", "#F97316"]

REGIONS = {
    "🇺🇸 United States": "US", "🇨🇦 Canada": "CA", "🇲🇽 Mexico": "MX",
    "🇧🇷 Brazil": "BR", "🇦🇷 Argentina": "AR", "🇨🇱 Chile": "CL",
    "🇨🇴 Colombia": "CO", "🇵🇪 Peru": "PE",
    "🇬🇧 United Kingdom": "GB", "🇩🇪 Germany": "DE", "🇫🇷 France": "FR",
    "🇮🇹 Italy": "IT", "🇪🇸 Spain": "ES", "🇳🇱 Netherlands": "NL",
    "🇧🇪 Belgium": "BE", "🇨🇭 Switzerland": "CH", "🇦🇹 Austria": "AT",
    "🇸🇪 Sweden": "SE", "🇳🇴 Norway": "NO", "🇩🇰 Denmark": "DK",
    "🇫🇮 Finland": "FI", "🇵🇱 Poland": "PL", "🇨🇿 Czech Republic": "CZ",
    "🇭🇺 Hungary": "HU", "🇷🇴 Romania": "RO", "🇺🇦 Ukraine": "UA",
    "🇷🇺 Russia": "RU",
    "🇨🇳 China": "CN", "🇯🇵 Japan": "JP", "🇰🇷 South Korea": "KR",
    "🇹🇼 Taiwan": "TW", "🇭🇰 Hong Kong": "HK",
    "🇻🇳 Vietnam": "VN", "🇹🇭 Thailand": "TH", "🇮🇩 Indonesia": "ID",
    "🇲🇾 Malaysia": "MY", "🇸🇬 Singapore": "SG", "🇵🇭 Philippines": "PH",
    "🇰🇭 Cambodia": "KH",
    "🇮🇳 India": "IN", "🇧🇩 Bangladesh": "BD", "🇵🇰 Pakistan": "PK",
    "🇱🇰 Sri Lanka": "LK",
    "🇰🇿 Kazakhstan": "KZ", "🇺🇿 Uzbekistan": "UZ",
    "🇸🇦 Saudi Arabia": "SA", "🇦🇪 UAE": "AE", "🇶🇦 Qatar": "QA",
    "🇰🇼 Kuwait": "KW", "🇮🇱 Israel": "IL", "🇮🇷 Iran": "IR", "🇮🇶 Iraq": "IQ",
    "🇿🇦 South Africa": "ZA", "🇳🇬 Nigeria": "NG", "🇰🇪 Kenya": "KE",
    "🇬🇭 Ghana": "GH", "🇪🇬 Egypt": "EG",
    "🇦🇺 Australia": "AU", "🇳🇿 New Zealand": "NZ",
}

TOP_OPTS = ["Top 10", "Top 20", "Top 30"]
TOP_MAP  = {"Top 10": 10, "Top 20": 20, "Top 30": 30}

# Build country display names from REGIONS (strips flag emoji, e.g. "🇻🇳 Vietnam" → "Vietnam")
COUNTRY_NAMES = {
    code: " ".join(label.split()[1:]) or code
    for label, code in REGIONS.items()
}

# ─────────────────────────────────────────────
#  CSS  (all styling — no layout logic here)
# ─────────────────────────────────────────────

DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

.st-emotion-cache-yn44r9{
    margin-top: 19px !important;
}

/* ── TOKEN SYSTEM ── */
:root {
    --red:        #E8001D;
    --red-dim:    rgba(232,0,29,0.15);
    --red-border: rgba(232,0,29,0.30);
    --bg:         #0F0F0F;
    --surface:    #161616;
    --surface2:   #1E1E1E;
    --surface3:   #242424;
    --border:     rgba(255,255,255,0.07);
    --border2:    rgba(255,255,255,0.12);
    --text:       #FFFFFF;
    --text-muted: rgba(255,255,255,0.50);
    --text-dim:   rgba(255,255,255,0.30);
    --green:      #22C55E;
    --blue:       #3B82F6;
    --amber:      #F59E0B;
    --purple:     #A855F7;
    --r:          10px;
}

/* ── STREAMLIT SHELL RESETS ── */
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
.stApp { background: var(--bg) !important; }

.block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
.main .block-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
}
section[data-testid="stMain"],
section[data-testid="stMain"] > div {
    padding: 0 !important;
    max-width: 100% !important;
    margin-left: 0 !important;
}

/* hide sidebar & all toggle buttons */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
.st-emotion-cache-czk5ss { display: none !important; }

[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] { gap: 0 !important; padding: 0 !important; }

[data-testid="element-container"],
.stMarkdown { margin: 0 !important; padding: 0 !important; }

#MainMenu, footer { visibility: hidden !important; }
header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"] {
    display: none !important;
    height: 0 !important;
}

/* selectbox dark styling */
[data-testid="stSelectbox"] > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 0.82rem !important;
    min-height: 36px !important;
}
[data-testid="stSelectbox"] label { display: none !important; }

/* ── SHARED COMPONENT STYLES ── */
* { box-sizing: border-box; }
a { text-decoration: none !important; }

/* live dot */
.live-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.62rem; font-weight: 700;
    color: var(--red); letter-spacing: 0.5px;
}
.live-badge::before {
    content: '';
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--red);
    animation: blink 1.2s ease-in-out infinite;
    display: inline-block;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }
@keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(232,0,29,.4); }
    50%      { box-shadow: 0 0 0 8px rgba(232,0,29,0); }
}
@keyframes dot-blink { 0%,100%{opacity:1} 50%{opacity:.25} }

/* card shell */
.vcard {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    overflow: hidden;
}
.vcard-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px 9px;
    border-bottom: 1px solid var(--border);
}
.vcard-title {
    font-size: 0.70rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    color: var(--text); display: flex; align-items: center; gap: 6px;
}
.vcard-title svg { flex-shrink: 0; }

/* ── UNIFIED HEADER (single horizontal row) ── */
.ld-header-row {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr auto;
    gap: 20px;
    align-items: center;
}

/* Left block: pulse icon + title/subtitle */
.ld-header-left {
    display: flex;
    align-items: center;
    gap: 13px;
}
.ld-pulse-icon {
    width: 46px; height: 46px; border-radius: 11px;
    background: var(--red-dim); border: 1px solid var(--red-border);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 1.30rem;
    animation: pulse 2s ease-in-out infinite;
}
.ld-h-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.65rem; font-weight: 900;
    letter-spacing: .5px; text-transform: uppercase;
    color: var(--text); line-height: 1; margin: 0;
}
.ld-h-title em { color: var(--red); font-style: normal; }
.ld-h-sub {
    font-size: 0.70rem; color: var(--text-muted);
    margin-top: 3px; font-family: 'Inter', sans-serif;
    line-height: 1.4;
}

/* Control columns inside the header grid */
.ld-ctrl-col {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.ld-filter-label {
    font-size: 0.58rem; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
    color: var(--text-dim);
    margin: 0 0 4px 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    display: block;
    font-family: 'Inter', sans-serif;
}
/* ── LAST UPDATED (time box + square refresh button) ── */
.ld-refresh-row {
    display: flex; align-items: center; gap: 8px;
}
.ld-time-box {
    flex: 1; background: #161616;
    border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
    height: 40px; padding: 0 16px;
    display: flex; align-items: center;
    font-size: 0.85rem; font-weight: 600; color: var(--text);
    white-space: nowrap; font-family: 'Inter', sans-serif;
    letter-spacing: 0.5px; transition: border-color 0.2s;
}
.ld-refresh-btn {
    width: 40px; height: 40px; flex-shrink: 0;
    background: #161616; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.20rem; color: var(--text-muted) !important;
    cursor: pointer; transition: border-color 0.2s, color 0.2s;
    text-decoration: none !important;
}
.ld-refresh-btn:hover {
    border-color: var(--red) !important;
    color: var(--red) !important;
}

/* Override Streamlit column gap inside the header */
.ld-header-cols [data-testid="stHorizontalBlock"] {
    gap: 24px !important;
    align-items: end !important;
}
.ld-header-cols [data-testid="column"] {
    padding: 0 !important;
}
/* Title column: grow to fill remaining space */
.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {
    flex: 1 1 auto !important;
    min-width: 0 !important;
    align-self: center !important;
}
/* Country column: fixed ~220 px */
.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
    flex: 0 0 220px !important;
    max-width: 220px !important;
    min-width: 220px !important;
}
/* Display Count column: fixed ~170 px */
.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {
    flex: 0 0 170px !important;
    max-width: 170px !important;
    min-width: 170px !important;
}
/* Last Updated column: auto-fit the time-box + button */
.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) {
    flex: 0 0 auto !important;
    min-width: 190px !important;
    max-width: 240px !important;
}
/* Header background + padding */
.ld-header-cols { padding: 16px 24px; background: var(--surface); border-bottom: 1px solid var(--border); }
/* Restore small gap between the label markdown and selectbox widget */
.ld-header-cols [data-testid="stVerticalBlock"] { gap: 2px !important; justify-content: flex-end !important; }
/* Selectbox outer box: dark pill matching the mockup */
.ld-header-cols [data-testid="stSelectbox"] > div > div {
    background: #161616 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    height: 40px !important; min-height: 40px !important;
    padding: 0 14px !important;
    display: flex !important; align-items: center !important;
    font-size: 0.85rem !important; font-weight: 500 !important;
    transition: border-color 0.2s !important;
    cursor: pointer !important;
}
.ld-header-cols [data-testid="stSelectbox"] > div > div:hover {
    border-color: rgba(255,255,255,0.18) !important;
}
/* Inner container: stretch to fill the outer box */
.ld-header-cols [data-testid="stSelectbox"] > div > div > div {
    display: flex !important; align-items: center !important;
    width: 100% !important; height: 100% !important;
    padding: 0 !important;
}
/* Selected value text (baseweb + generic fallbacks) */
.ld-header-cols [data-baseweb="select"] [data-baseweb="value"],
.ld-header-cols [data-baseweb="select"] [data-baseweb="tag"],
.ld-header-cols [data-testid="stSelectbox"] [data-baseweb="select"] span,
.ld-header-cols [data-testid="stSelectbox"] > div > div > div > div:first-child,
.ld-header-cols [data-testid="stSelectbox"] > div > div > div > div:first-child span {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    line-height: 1 !important;
}
/* Chevron / dropdown arrow: muted white */
.ld-header-cols [data-testid="stSelectbox"] svg {
    color: rgba(255,255,255,0.40) !important;
    fill: rgba(255,255,255,0.40) !important;
    width: 15px !important; height: 15px !important;
    flex-shrink: 0 !important;
}

/* ── KPI CARDS ── */
.kpi-wrap {
    margin-top: 5px;
    padding: 16px 20px 8px;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
}
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 14px 14px 0;
    overflow: hidden;
    transition: border-color .2s, transform .18s;
}
.kpi-card:hover { border-color: var(--red-border); transform: translateY(-2px); }
.kpi-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 6px; }
.kpi-label {
    font-size: 0.60rem; font-weight: 600;
    letter-spacing: .8px; text-transform: uppercase;
    color: var(--text-dim); line-height: 1.3;
    font-family: 'Inter', sans-serif;
}
.kpi-icon {
    width: 34px; height: 34px; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.kpi-val {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.0rem; font-weight: 900;
    color: var(--text); line-height: 1; margin: 2px 0 2px;
}
.kpi-desc { font-size: 0.64rem; color: var(--text-muted); margin-bottom: 8px; font-family: 'Inter', sans-serif; }
.kpi-spark { width: 100%; height: 32px; display: block; }

/* ── MAIN GRID WRAPPER ── */
.main-grid-pad { padding: 16px 20px 14px; }

/* ── VIDEO TABLE (left col) ── */
.vtable { width: 100%; border-collapse: collapse; }
.vtable thead th {
    font-size: 0.58rem; font-weight: 700; letter-spacing: .8px;
    text-transform: uppercase; color: var(--text-dim);
    padding: 7px 10px; text-align: left;
    background: var(--surface2); position: sticky; top: 0; z-index: 2;
    white-space: nowrap;
}
.vtable tbody tr {
    border-bottom: 1px solid rgba(255,255,255,.04);
    transition: background .12s;
}
.vtable tbody tr:hover { background: rgba(255,255,255,.025); }
.vtable tbody tr:last-child { border-bottom: none; }
.vtable td { padding: 9px 10px; vertical-align: middle; }
.v-rank {
    width: 26px; height: 26px; border-radius: 7px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.72rem; font-weight: 800;
    background: var(--surface2); color: var(--text-dim);
    border: 1px solid var(--border); flex-shrink: 0;
}
.v-rank.top3 { background: var(--red); color: #fff; border-color: transparent; }
.v-thumb-wrap {
    position: relative; width: 88px; height: 52px;
    border-radius: 7px; overflow: hidden; flex-shrink: 0; background: #1a1a1a;
}
.v-thumb-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
.v-dur {
    position: absolute; bottom: 3px; right: 3px;
    background: rgba(0,0,0,.82); color: #fff;
    font-size: 0.58rem; font-weight: 700;
    padding: 1px 4px; border-radius: 3px; letter-spacing: .2px;
}
.v-info { display: flex; align-items: center; gap: 9px; }
.v-title {
    font-size: 0.79rem; font-weight: 600; color: var(--text);
    line-height: 1.35; max-width: 300px;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
    font-family: 'Inter', sans-serif;
}
.v-channel {
    font-size: 0.66rem; color: var(--red);
    margin-top: 2px; font-weight: 500;
    display: flex; align-items: center; gap: 3px;
    font-family: 'Inter', sans-serif;
}
.v-meta { font-size: 0.62rem; color: var(--text-muted); margin-top: 2px; font-family: 'Inter', sans-serif; }
.v-stat { font-size: 0.76rem; font-weight: 600; color: var(--text); text-align: right; white-space: nowrap; }
.v-stat-sub { font-size: 0.62rem; color: var(--text-muted); text-align: right; white-space: nowrap; margin-top: 2px; }
.v-link {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; border-radius: 7px;
    background: var(--red-dim); border: 1px solid var(--red-border);
    color: var(--red) !important; font-size: 0.80rem;
    transition: background .15s;
}
.v-link:hover { background: var(--red); color: #fff !important; }
.vtable-scroll {
    max-height: 520px; overflow-y: auto;
    scrollbar-width: thin; scrollbar-color: rgba(232,0,29,.3) transparent;
}
.vtable-scroll::-webkit-scrollbar { width: 4px; }
.vtable-scroll::-webkit-scrollbar-thumb { background: rgba(232,0,29,.35); border-radius: 3px; }
.v-see-all {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; border-top: 1px solid var(--border);
    font-size: 0.72rem; font-weight: 500; color: var(--text-muted);
    cursor: pointer; background: var(--surface);
}
.v-see-all:hover { color: var(--text); }

/* ── RIGHT COL STACK ── */
.right-stack { display: flex; flex-direction: column; gap: 12px; }

/* donut */
.donut-body { display: flex; align-items: center; gap: 12px; padding: 12px 14px; }
.donut-center-label {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%,-50%); text-align: center; line-height: 1.1;
}
.donut-center-label strong {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.25rem; font-weight: 900; color: var(--text); display: block;
}
.donut-center-label span { font-size: 0.52rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }
.cat-legend { flex: 1; display: flex; flex-direction: column; gap: 5px; }
.cat-row { display: flex; align-items: center; gap: 7px; font-size: 0.68rem; }
.cat-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.cat-name { flex: 1; color: rgba(255,255,255,.72); font-family: 'Inter', sans-serif; }
.cat-pct { font-weight: 700; color: var(--text); font-family: 'Inter', sans-serif; }

/* time chart */
.time-chart-body { padding: 10px 14px 12px; }
.time-chart-svg { width: 100%; }

/* shorts */
.short-row {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    transition: background .12s;
    text-decoration: none !important;
    overflow: hidden;
}
.short-row:last-child { border-bottom: none; }
.short-row:hover { background: rgba(255,255,255,.025); }
.short-thumb {
    width: 52px; height: 52px; border-radius: 8px;
    object-fit: cover; background: #1a1a1a; flex-shrink: 0; display: block;
    position: relative;
}
.short-thumb-wrap { position: relative; flex-shrink: 0; }
.short-dur {
    position: absolute; bottom: 2px; left: 2px;
    background: rgba(0,0,0,.82); color: #fff;
    font-size: 0.54rem; font-weight: 700;
    padding: 1px 3px; border-radius: 3px;
}
.short-info { flex: 1; min-width: 0; overflow: hidden; }
.short-title {
    font-size: 0.74rem; font-weight: 600; color: var(--text); line-height: 1.35;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    max-width: 100%;
    font-family: 'Inter', sans-serif;
}
.short-channel {
    font-size: 0.63rem; color: var(--text-muted); margin-top: 2px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: 'Inter', sans-serif;
}
.short-views {
    font-size: 0.63rem; color: var(--text-muted); margin-top: 1px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: 'Inter', sans-serif;
}
.short-see-all {
    display: flex; align-items: center; justify-content: center; gap: 6px;
    padding: 9px; border-top: 1px solid var(--border);
    font-size: 0.70rem; color: var(--text-muted); cursor: pointer;
}
.short-see-all:hover { color: var(--text); }

/* ── CHANNEL ROWS (channels card) ── */
.ch-list { display: flex; flex-direction: column; }
.ch-row {
    display: flex; align-items: center; gap: 9px;
    padding: 8px 14px; border-bottom: 1px solid rgba(255,255,255,.04);
    overflow: hidden; transition: background .12s;
}
.ch-row:last-child { border-bottom: none; }
.ch-row:hover { background: rgba(255,255,255,.025); }
.ch-rank {
    width: 22px; height: 22px; border-radius: 6px; flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.68rem; font-weight: 800;
    background: var(--surface2); color: var(--text-dim); border: 1px solid var(--border);
}
.ch-rank.top3 { background: var(--red); color: #fff; border-color: transparent; }
.ch-avatar {
    width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
    background: rgba(232,0,29,.15); border: 1px solid rgba(232,0,29,.25);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.58rem; font-weight: 800; color: var(--red);
}
.ch-info { flex: 1; min-width: 0; overflow: hidden; }
.ch-name {
    font-size: 0.75rem; font-weight: 600; color: var(--text);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: 'Inter', sans-serif;
}
.ch-sub {
    font-size: 0.61rem; color: var(--text-muted); margin-top: 1px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: 'Inter', sans-serif;
}
.ch-pct {
    font-size: 0.70rem; font-weight: 700; color: var(--red);
    flex-shrink: 0; font-family: 'Inter', sans-serif;
}

/* ── WORLD MAP ── */
.country-map {
    padding: 8px 14px 12px;
    display: flex; flex-direction: column; align-items: center;
}
.country-map svg {
    width: 100%; height: auto; max-height: 200px;
    display: block;
}
/* All land paths: dark gray */
.country-map svg path {
    fill: #2a2a2a !important;
    stroke: #111 !important;
    stroke-width: 0.4px !important;
    transition: fill .3s;
}
/* Selected country: red highlight */
.country-map svg path.selected-country {
    fill: var(--red) !important;
    stroke: rgba(232,0,29,.5) !important;
    stroke-width: 1px !important;
    filter: drop-shadow(0 0 6px rgba(232,0,29,.5));
}
.map-legend {
    display: flex; align-items: center; gap: 6px;
    margin-top: 8px;
    font-size: 0.62rem; color: var(--text-muted);
    font-family: 'Inter', sans-serif;
}
.map-legend-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--red); flex-shrink: 0;
    animation: dot-blink 1.4s ease-in-out infinite;
}

/* ── FOOTER ── */
.ld-footer {
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 9px 20px;
    display: flex; align-items: center; gap: 28px;
    flex-wrap: wrap;
}
.ld-footer-item {
    display: flex; align-items: center; gap: 5px;
    font-size: 0.68rem; color: var(--text-muted);
    font-family: 'Inter', sans-serif;
}
.ld-footer-item svg { flex-shrink: 0; }
.ld-footer-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--green); display: inline-block;
    animation: dot-blink 1.4s ease-in-out infinite;
}
.ld-footer-online { color: var(--green); font-weight: 600; }
</style>
"""

# ─────────────────────────────────────────────
#  SVG BUILDERS
# ─────────────────────────────────────────────

def _sparkline(color: str, seed: int, w=120, h=32) -> str:
    pts = [
        h/2 + (h*0.38) * math.sin(i * 0.85 + seed)
        + (h*0.18) * math.sin(i * 2.3 + seed * 1.3)
        for i in range(14)
    ]
    mn, mx = min(pts), max(pts); rng = mx - mn or 1
    xs = [i * w / 13 for i in range(14)]
    ys = [h - 2 - ((v - mn) / rng) * (h - 6) for v in pts]
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = path + f" L{w},{ h} L0,{h} Z"
    gid = f"g{abs(hash(color+str(seed))) % 99999}"
    return (
        f'<svg class="kpi-spark" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity=".28"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<path d="{area}" fill="url(#{gid})"/>'
        f'<path d="{path}" fill="none" stroke="{color}" '
        f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def _donut_svg(cat_data, total, size=108) -> str:
    cx = cy = size / 2
    r_out = size / 2 - 4
    r_in  = r_out - 20
    r_mid = (r_out + r_in) / 2
    sw    = r_out - r_in
    circ  = 2 * math.pi * r_mid
    segs  = []
    cum   = 0.0
    for i, (_, count) in enumerate(cat_data[:8]):
        pct    = count / total if total else 0
        dash   = pct * circ
        gap    = circ - dash
        offset = -cum * circ
        color  = CAT_COLORS[i % len(CAT_COLORS)]
        segs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r_mid:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="{sw:.1f}" '
            f'stroke-dasharray="{dash:.2f} {gap:.2f}" '
            f'stroke-dashoffset="{offset:.2f}" stroke-linecap="butt"/>'
        )
        cum += pct
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg" style="transform:rotate(-90deg);flex-shrink:0">'
        f'<circle cx="{cx}" cy="{cy}" r="{r_mid:.1f}" fill="none" '
        f'stroke="rgba(255,255,255,.06)" stroke-width="{sw:.1f}"/>'
        + "".join(segs) + "</svg>"
    )


def _time_chart_svg(seed=7, w=260, h=90) -> str:
    """Red line chart mimicking the 'Trending theo thời gian' panel."""
    pts = [
        5 + 75 * (0.3 + 0.6 * abs(math.sin(i * 0.55 + seed))
                  + 0.15 * math.sin(i * 1.8 + seed))
        for i in range(20)
    ]
    mn, mx = min(pts), max(pts); rng = mx - mn or 1
    xs = [i * w / 19 for i in range(20)]
    ys = [h - 8 - ((v - mn) / rng) * (h - 18) for v in pts]
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = path + f" L{w},{h-8} L0,{h-8} Z"
    # y-axis labels
    y_vals = ["20M", "15M", "10M", "5M", "0"]
    y_labels = ""
    for j, lbl in enumerate(y_vals):
        y_pos = 8 + j * (h - 18) / 4
        y_labels += f'<text x="0" y="{y_pos:.0f}" font-size="7" fill="rgba(255,255,255,.28)" dominant-baseline="middle">{lbl}</text>'
    # x-axis labels
    x_times = ["04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    x_labels = ""
    for j, lbl in enumerate(x_times):
        x_pos = j * w / 5
        x_labels += f'<text x="{x_pos:.0f}" y="{h}" font-size="7" fill="rgba(255,255,255,.28)" text-anchor="middle">{lbl}</text>'
    # grid lines
    grid = ""
    for j in range(5):
        y_pos = 8 + j * (h - 18) / 4
        grid += f'<line x1="28" y1="{y_pos:.0f}" x2="{w}" y2="{y_pos:.0f}" stroke="rgba(255,255,255,.05)" stroke-width="1"/>'

    return (
        f'<svg class="time-chart-svg" viewBox="0 0 {w} {h+10}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'{grid}'
        f'<defs><linearGradient id="tcg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#E8001D" stop-opacity=".22"/>'
        f'<stop offset="100%" stop-color="#E8001D" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<path d="{area}" fill="url(#tcg)"/>'
        f'<path d="{path}" fill="none" stroke="#E8001D" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'{y_labels}{x_labels}'
        f'</svg>'
    )


def _world_map_svg(region: str) -> str:
    svg = Path("assets/world.svg").read_text(encoding="utf-8")
    svg = svg[svg.find("<svg"):]
    region = region.upper()

    svg = svg.replace(
        f'id="{region}"',
        f'id="{region}" class="selected-country"'
    )

    return svg


# ─────────────────────────────────────────────
#  HTML BLOCK BUILDERS
# ─────────────────────────────────────────────

def _kpi_card(icon, icon_bg, label, value, desc, color, seed) -> str:
    spark = _sparkline(color, seed)
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-top">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-icon" style="background:{icon_bg}">{icon}</div>'
        f'</div>'
        f'<div class="kpi-val">{value}</div>'
        f'<div class="kpi-desc">{desc}</div>'
        f'{spark}'
        f'</div>'
    )


def _video_rows(top_videos) -> str:
    rows = ""
    for idx, video in enumerate(top_videos):
        rank    = idx + 1
        snippet = video.get("snippet", {})
        stats   = video.get("statistics", {})
        vid_id  = video.get("id", "")
        title   = _e(snippet.get("title", ""))
        channel = _e(snippet.get("channelTitle", ""))
        thumb   = _e(_thumb(snippet, "medium"))
        views   = _fmt(stats.get("viewCount", 0))
        likes   = _fmt(stats.get("likeCount", 0))
        comms   = _fmt(stats.get("commentCount", 0))
        ago     = _fmt_ago(snippet.get("publishedAt"))
        yt_url  = f"https://www.youtube.com/watch?v={vid_id}"
        top3    = "top3" if rank <= 3 else ""
        rows += (
            f'<tr>'
            f'<td style="width:32px"><span class="v-rank {top3}">{rank}</span></td>'
            f'<td>'
            f'<div class="v-info">'
            f'<div class="v-thumb-wrap"><img src="{thumb}" alt="" loading="lazy"/></div>'
            f'<div>'
            f'<div class="v-title">{title}</div>'
            f'<div class="v-channel">{channel} ✓</div>'
            f'<div class="v-meta">{views} views · {ago}</div>'
            f'</div></div>'
            f'</td>'
            f'<td style="width:64px">'
            f'<div class="v-stat">👍 {likes}</div>'
            f'<div class="v-stat-sub">💬 {comms}</div>'
            f'</td>'
            f'<td style="width:30px">'
            f'<a href="{yt_url}" target="_blank" rel="noopener" class="v-link">↗</a>'
            f'</td>'
            f'</tr>'
        )
    return rows


def _channel_rows(top_channels, total) -> str:
    rows = ""
    for idx, (channel, count) in enumerate(top_channels):
        pct     = (count / total * 100) if total else 0
        top_cls = "top3" if idx < 3 else ""
        initials = "".join(w[0].upper() for w in channel.split()[:2]) or "CH"
        rows += (
            f'<div class="ch-row">'
            f'<div class="ch-rank {"top3" if idx<3 else ""}">{idx+1}</div>'
            f'<div class="ch-avatar">{initials[:2]}</div>'
            f'<div class="ch-info">'
            f'<div class="ch-name">{_e(channel)}</div>'
            f'<div class="ch-sub">{count} video trending</div>'
            f'</div>'
            f'<div class="ch-pct">{pct:.0f}%</div>'
            f'</div>'
        )
    return rows


def _category_card(sorted_cats, total) -> str:
    donut = _donut_svg(sorted_cats, total)
    legend = ""
    for i, (name, count) in enumerate(sorted_cats[:6]):
        pct   = count / total * 100 if total else 0
        color = CAT_COLORS[i % len(CAT_COLORS)]
        legend += (
            f'<div class="cat-row">'
            f'<div class="cat-dot" style="background:{color}"></div>'
            f'<div class="cat-name">{_e(name)}</div>'
            f'<div class="cat-pct">{pct:.0f}%</div>'
            f'</div>'
        )
    size = 108
    return (
        f'<div class="vcard">'
        f'<div class="vcard-head">'
        f'<div class="vcard-title">Trending theo danh mục</div>'
        f'<span class="live-badge">LIVE</span>'
        f'</div>'
        f'<div class="donut-body">'
        f'<div style="position:relative;width:{size}px;height:{size}px;flex-shrink:0;display:grid;place-items:center">'
        f'{donut}'
        f'<div class="donut-center-label">'
        f'<strong>{total}</strong><span>Total</span>'
        f'</div></div>'
        f'<div class="cat-legend">{legend}</div>'
        f'</div></div>'
    )


def _time_chart_card() -> str:
    chart = _time_chart_svg(seed=7)
    return (
        f'<div class="vcard">'
        f'<div class="vcard-head">'
        f'<div class="vcard-title">Trending theo thời gian</div>'
        f'<span class="live-badge">LIVE</span>'
        f'</div>'
        f'<div class="time-chart-body">{chart}</div>'
        f'</div>'
    )


def _channels_card(top_channels, total, region: str = "VN") -> str:
    country_name = COUNTRY_NAMES.get(region, region)
    return (
        f'<div class="vcard">'
        f'<div class="vcard-head">'
        f'<div class="vcard-title">Top Channels – {_e(country_name)}</div>'
        f'<span class="live-badge">LIVE</span>'
        f'</div>'
        f'<div class="ch-list">'
        + _channel_rows(top_channels, total)
        + f'</div>'
        f'<div class="short-see-all">Xem tất cả kênh →</div>'
        f'</div>'
    )

def _countries_card(region: str, top_videos: list) -> str:
    map_svg = _world_map_svg(region)
    country_name = COUNTRY_NAMES.get(region, region)

    return (
        f'<div class="vcard">'
        f'<div class="vcard-head">'
        f'<div class="vcard-title">Trending Region</div>'
        f'<span class="live-badge">LIVE</span>'
        f'</div>'
        f'<div class="country-map">{map_svg}'
        f'<div class="map-legend">'
        f'<span class="map-legend-dot"></span>'
        f'<span>\u0110ang xem: {_e(country_name)}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def _sidebar_html(has_key: bool) -> str:
    """Render the left navigation sidebar HTML."""
    quota_total = 10_000
    quota_rem   = 8_650          # simulated remaining quota
    quota_pct   = round(quota_rem / quota_total * 100)

    status_txt = "Hoạt động bình thường" if has_key else "Không có API key"
    dot_color  = "var(--green)" if has_key else "var(--red)"
    txt_color  = "var(--green)" if has_key else "var(--red)"

    items = [
        ("📡", "Live Dashboard", True),
        ("📈", "Trending Now",   False),
        ("🎬", "Top Videos",     False),
        ("📺", "Top Channels",   False),
        ("📱", "Top Shorts",     False),
        ("🌍", "Countries",      False),
        ("⚙️",  "Settings",      False),
    ]
    menu = ""
    for icon, label, active in items:
        cls = "sb-item sb-active" if active else "sb-item"
        menu += (
            f'<div class="{cls}">'
            f'<span class="sb-item-icon">{icon}</span>'
            f'<span>{label}</span>'
            f'</div>'
        )

    return (
        f'<div class="sb-wrap">'
        f'<div class="sb-logo">'
        f'<div class="sb-logo-icon">'
        f'<svg width="17" height="17" viewBox="0 0 17 17" fill="none">'
        f'<polygon points="5,3.5 13,8.5 5,13.5" fill="white"/></svg>'
        f'</div>'
        f'<div class="sb-logo-text">VISION</div>'
        f'</div>'
        f'<div class="sb-menu">{menu}</div>'
        f'<div class="sb-bottom">'
        f'<div class="sb-api-label">YouTube API Status</div>'
        f'<div class="sb-api-status" style="color:{txt_color}">'
        f'<div class="sb-api-dot" style="background:{dot_color}"></div>'
        f'{status_txt}'
        f'</div>'
        f'<div class="sb-quota-label">Quota còn lại</div>'
        f'<div class="sb-quota-track">'
        f'<div class="sb-quota-fill" style="width:{quota_pct}%"></div>'
        f'</div>'
        f'<div class="sb-quota-row">'
        f'<div class="sb-quota-nums">{quota_rem:,} / {quota_total:,}</div>'
        f'<div class="sb-quota-pct">{quota_pct}%</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def _video_card(top_videos, total) -> str:
    rows = _video_rows(top_videos)
    return (
        f'<div class="vcard">'
        f'<div class="vcard-head">'
        f'<div class="vcard-title">'
        f'<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="14" height="14" rx="3" fill="#E8001D"/>'
        f'<polygon points="5.5,3.5 10.5,7 5.5,10.5" fill="white"/>'
        f'</svg>'
        f'Top {total} Trending Now'
        f'</div>'
        f'<span class="live-badge">LIVE</span>'
        f'</div>'
        f'<div class="vtable-scroll">'
        f'<table class="vtable">'
        f'<colgroup>'
        f'<col style="width:32px"/>'
        f'<col/>'
        f'<col style="width:64px"/>'
        f'<col style="width:30px"/>'
        f'</colgroup>'
        f'<tbody>{rows}</tbody>'
        f'</table>'
        f'</div>'
        f'<div class="v-see-all">'
        f'<span>Xem tất cả Top {total}</span>'
        f'<span>→</span>'
        f'</div>'
        f'</div>'
    )


# ─────────────────────────────────────────────
#  MAIN RENDER FUNCTION
# ─────────────────────────────────────────────

def render_trending() -> None:
    # ── handle manual refresh ──
    if st.query_params.get("refresh") == "1":
        st.cache_data.clear()
        st.query_params.clear()
        st.query_params["tab"] = "trending"
        st.rerun()

    # ── session state defaults ──
    for key, default in (("tt_region", "VN"), ("tt_top", "Top 10")):
        if key not in st.session_state:
            st.session_state[key] = default

    now          = _dt.now()
    now_str      = now.strftime("%H:%M:%S")
    now_date_str = now.strftime("%d/%m/%Y")

    # ── API meta ──
    has_key    = bool(os.getenv("YOUTUBE_API_KEY_1"))
    api_status = "Hoạt động bình thường" if has_key else "No API key"
    api_color  = "var(--green)" if has_key else "var(--red)"
    dot_html   = '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);animation:dot-blink 1.4s ease-in-out infinite;margin-right:4px"></span>' if has_key else "❌ "

    # ═══════════════════════════════════
    #  INJECT CSS ONCE
    # ═══════════════════════════════════
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    # ═══════════════════════════════════
    #  SECTION 1 – UNIFIED HEADER ROW
    #  Title block + 3 controls in one
    #  single horizontal CSS-grid row.
    # ═══════════════════════════════════

    # Wrapper CSS that turns the Streamlit columns into a grid-aligned header
    st.markdown(
        '<style>'
        # Outer wrapper: full-width surface band
        '.ld-header-cols {'
        '  background: var(--surface);'
        '  border-bottom: 1px solid var(--border);'
        '  padding: 16px 24px;'
        '}'
        # Horizontal block: gap + vertical centering
        '.ld-header-cols [data-testid="stHorizontalBlock"] {'
        '  gap: 24px !important;'
        '  align-items: stretch !important;'
        '}'
        '.ld-header-cols [data-testid="column"] { padding: 0 !important; }' 
        # Every wrapper level must fill its parent height
        '.ld-header-cols [data-testid="column"] > div,'
        '.ld-header-cols [data-testid="stVerticalBlockBorderWrapper"],'
        '.ld-header-cols [data-testid="stVerticalBlock"] {'
        '  height: 100% !important;'
        '  display: flex !important;'
        '  flex-direction: column !important;'
        '  gap: 2px !important;'
        '}'
        # Push the ACTUAL control widgets to the bottom via margin-top: auto
        '.ld-header-cols [data-testid="stSelectbox"] { margin-top: auto !important; }'
        '.ld-header-cols .ld-refresh-row { margin-top: auto !important; }'
        # Title column grows
        '.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {'
        '  flex: 1 1 auto !important; min-width: 0 !important; align-self: center !important;'
        '}'
        # Country column: ~220 px
        '.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {'
        '  flex: 0 0 220px !important; max-width: 220px !important; min-width: 220px !important;'
        '}'
        # Display Count column: ~170 px
        '.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {'
        '  flex: 0 0 170px !important; max-width: 170px !important; min-width: 170px !important;'
        '}'
        # Last Updated column: auto width
        '.ld-header-cols [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) {'
        '  flex: 0 0 auto !important; min-width: 190px !important;'
        '}'
        # Selectbox outer box: dark 48 px pill
        '.ld-header-cols [data-testid="stSelectbox"] > div > div {'
        '  background: #161616 !important;'
        '  border: 1px solid rgba(255,255,255,0.08) !important;'
        '  border-radius: 10px !important;'
        '  height: 40px !important; min-height: 40px !important;'
        '  padding: 0 14px !important;'
        '  display: flex !important; align-items: center !important;'
        '  font-size: 0.85rem !important; font-weight: 500 !important;'
        '  transition: border-color 0.2s !important; cursor: pointer !important;'
        '}'
        '.ld-header-cols [data-testid="stSelectbox"] > div > div:hover {'
        '  border-color: rgba(255,255,255,0.18) !important;'
        '}'
        # Inner flex container
        '.ld-header-cols [data-testid="stSelectbox"] > div > div > div {'
        '  display: flex !important; align-items: center !important;'
        '  width: 100% !important; height: 100% !important; padding: 0 !important;'
        '}'
        # Selected text (baseweb + generic)
        '.ld-header-cols [data-baseweb="select"] [data-baseweb="value"],'
        '.ld-header-cols [data-testid="stSelectbox"] > div > div > div > div:first-child span {'
        '  font-size: 0.85rem !important; font-weight: 500 !important;'
        '  color: #ffffff !important; font-family: Inter,sans-serif !important;'
        '}'
        # Chevron arrow
        '.ld-header-cols [data-testid="stSelectbox"] svg {'
        '  color: rgba(255,255,255,0.40) !important;'
        '  fill: rgba(255,255,255,0.40) !important;'
        '  width: 15px !important; height: 15px !important;'
        '}'
        # Remove extra margin Streamlit puts on label markdown
        '.ld-header-cols .stMarkdown { margin: 0 !important; }'
        # Remove extra element-container padding/margin
        '.ld-header-cols [data-testid="element-container"] { margin: 0 !important; padding: 0 !important; }'
        # Ensure selectbox hidden label takes no space
        '.ld-header-cols [data-testid="stSelectbox"] label { display: none !important; margin: 0 !important; padding: 0 !important; }'
        # Ensure the selectbox widget wrapper has no extra margin
        '.ld-header-cols [data-testid="stSelectbox"] { margin: 0 !important; padding: 0 !important; }'
        # Force the filter label div to have zero bottom margin
        '.ld-header-cols .ld-filter-label { margin: 0 0 4px 0 !important; padding: 0 !important; }'
        # Force refresh row height to match selectbox
        '.ld-header-cols .ld-refresh-row { height: 40px !important; }'
        # Strip extra bottom margin from stMarkdown wrappers
        '.ld-header-cols .stMarkdown p { margin: 0 !important; }'
        '</style>'
        '<div class="ld-header-cols">',
        unsafe_allow_html=True,
    )

    # Four columns matching grid-template-columns: 1.4fr 1fr 1fr auto
    hc_title, hc_country, hc_top, hc_refresh = st.columns([1.4, 1.0, 1.0, 0.85], gap="small")

    with hc_title:
        st.markdown(
            '<div class="ld-header-left">'
            '<div class="ld-pulse-icon">((·))</div>'
            '<div>'
            '<div class="ld-h-title"><em>Live</em> YouTube Dashboard</div>'
            '<div class="ld-h-sub">Theo dõi xu hướng YouTube Trending theo thời gian thực</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with hc_country:
        st.markdown('<div class="ld-filter-label">Country</div>', unsafe_allow_html=True)
        try:
            r_idx = list(REGIONS.values()).index(st.session_state["tt_region"])
        except ValueError:
            r_idx = 0
        region_label = st.selectbox(
            "Region", list(REGIONS.keys()), index=r_idx,
            label_visibility="collapsed", key="tt_region_sel",
        )
        new_region = REGIONS[region_label]
        if new_region != st.session_state["tt_region"]:
            st.session_state["tt_region"] = new_region
            st.rerun()

    with hc_top:
        st.markdown('<div class="ld-filter-label">Số lượng hiển thị</div>', unsafe_allow_html=True)
        try:
            t_idx = TOP_OPTS.index(st.session_state["tt_top"])
        except ValueError:
            t_idx = 0
        top_label = st.selectbox(
            "Top", TOP_OPTS, index=t_idx,
            label_visibility="collapsed", key="tt_top_sel",
        )
        if top_label != st.session_state["tt_top"]:
            st.session_state["tt_top"] = top_label
            st.rerun()

    with hc_refresh:
        st.markdown('<div class="ld-filter-label">Cập nhật</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ld-refresh-row">'
            f'<div class="ld-time-box">Cập nhật: {now_str}</div>'
            f'<a class="ld-refresh-btn" href="?tab=trending&refresh=1" target="_self">↻</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)  # close ld-header-cols

    # ── FETCH ──
    with st.spinner(""):
        videos = fetch_trending(region_code=st.session_state["tt_region"])

    top_n      = TOP_MAP.get(st.session_state["tt_top"], 10)
    top_videos = videos[:min(top_n, len(videos))]
    total      = len(top_videos)

    if not videos:
        st.warning("⚠️ No data. Check YOUTUBE_API_KEY_1.")
        return

    # ── AGGREGATE ──
    total_views    = sum(int(v.get("statistics",{}).get("viewCount",   0) or 0) for v in top_videos)
    total_likes    = sum(int(v.get("statistics",{}).get("likeCount",   0) or 0) for v in top_videos)
    total_comments = sum(int(v.get("statistics",{}).get("commentCount",0) or 0) for v in top_videos)
    engagement     = (total_likes + total_comments) / total_views if total_views else 0
    growth_est     = min(99.0, max(1.0, engagement * 1000))

    cat_counts     = {}
    channel_counts = {}
    for v in top_videos:
        sn       = v.get("snippet", {})
        cat_name = CAT_ID_TO_NAME.get(str(sn.get("categoryId","24")), "Khác")
        cat_counts[cat_name]  = cat_counts.get(cat_name, 0) + 1
        ch                    = sn.get("channelTitle","")
        channel_counts[ch]    = channel_counts.get(ch, 0) + 1

    sorted_cats  = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    top_channels = sorted(channel_counts.items(), key=lambda x: x[1], reverse=True)[:5]


    # ═══════════════════════════════════
    #  SECTION 3 – KPI CARDS  (5 columns)
    # ═══════════════════════════════════
    st.markdown('<div class="kpi-wrap">', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5, gap="small")

    kpi_data = [
        (k1, "▶️", "rgba(232,0,29,.15)",   "Video Trending",   str(total),            f"đang thịnh hành",         "#E8001D", 1),
        (k2, "👁️", "rgba(59,130,246,.15)", "Tổng lượt xem",   _fmt(total_views),      f"trong top {total} video", "#3B82F6", 2),
        (k3, "👍", "rgba(34,197,94,.15)",  "Tổng lượt thích",  _fmt(total_likes),      f"trong top {total} video", "#22C55E", 3),
        (k4, "💬", "rgba(245,158,11,.15)", "Tổng bình luận",   _fmt(total_comments),   f"trong top {total} video", "#F59E0B", 4),
        (k5, "🔥", "rgba(168,85,247,.15)", "Xu hướng tăng",    f"+{growth_est:.0f}%",  "so với 1 giờ trước",       "#A855F7", 5),
    ]
    for col, icon, icon_bg, label, value, desc, color, seed in kpi_data:
        with col:
            st.markdown(_kpi_card(icon, icon_bg, label, value, desc, color, seed), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════
    #  SECTION 4 – MAIN GRID
    #  LEFT 50% | CENTER 25% | RIGHT 25%
    # ═══════════════════════════════════
    st.markdown('<div class="main-grid-pad">', unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([2.0, 1.0, 1.0], gap="small")

    with col_left:
        st.markdown(_video_card(top_videos, total), unsafe_allow_html=True)

    with col_center:
        st.markdown(
            f'<div class="right-stack">'
            + _category_card(sorted_cats, total)
            + _channels_card(top_channels, total, st.session_state["tt_region"])
            + f'</div>',
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            f'<div class="right-stack">'
            + _time_chart_card()
            + _countries_card(st.session_state["tt_region"], top_videos)
            + f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)  # close main-grid-pad

    # ═══════════════════════════════════
    #  SECTION 5 – FOOTER
    # ═══════════════════════════════════
    st.markdown(
        f'<div class="ld-footer">'
        f'<div class="ld-footer-item">'
        f'<svg width="13" height="13" viewBox="0 0 13 13" fill="none"><rect width="13" height="13" rx="3" fill="#E8001D"/><polygon points="5,3 10,6.5 5,10" fill="white"/></svg>'
        f'Nguồn dữ liệu: YouTube Data API v3'
        f'</div>'
        f'<div class="ld-footer-item">⏰ Cập nhật mỗi 1 phút</div>'
        f'<div class="ld-footer-item">🕐 Thời gian hệ thống: {now_date_str} {now_str} (GMT+7)</div>'
        f'<div class="ld-footer-item" style="margin-left:auto">'
        f'Kết nối: <span class="ld-footer-dot"></span><span class="ld-footer-online">Online</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )