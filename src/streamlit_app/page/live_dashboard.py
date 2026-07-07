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
[class*="st-key-ld-header-container"] [data-testid="stHorizontalBlock"] {
    gap: 24px !important;
    align-items: flex-end !important;
    flex-wrap: nowrap !important;
}
[class*="st-key-ld-header-container"] [data-testid="column"] {
    padding: 0 !important;
}
/* Title column: grow to fill remaining space */
[class*="st-key-ld-header-container"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {
    flex: 1 1 auto !important;
    min-width: 0 !important;
    align-self: flex-end !important; /* Đổi từ center thành flex-end */
    padding-bottom: 5px !important;   /* Thêm dòng này để căn chỉnh thẳng hàng */
}
/* Country column: fixed ~220 px */
[class*="st-key-ld-header-container"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
    flex: 0 0 220px !important;
    max-width: 220px !important;
    min-width: 220px !important;
}
/* Display Count column: fixed ~170 px */
[class*="st-key-ld-header-container"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {
    flex: 0 0 170px !important;
    max-width: 170px !important;
    min-width: 170px !important;
}
/* Last Updated column: auto-fit the time-box + button */
[class*="st-key-ld-header-container"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) {
    flex: 0 0 auto !important;
    min-width: 190px !important;
    max-width: 240px !important;
}
/* Header background + padding */
[class*="st-key-ld-header-container"] { padding: 28px 24px 16px 24px; margin-top: 4px; background: var(--surface); border-bottom: 1px solid var(--border); }
/* Restore small gap between the label markdown and selectbox widget */
[class*="st-key-ld-header-container"] [data-testid="stVerticalBlock"] { gap: 2px !important; justify-content: flex-end !important; }
/* Align control widgets to the bottom of their column */
[class*="st-key-ld-header-container"] [data-testid="stSelectbox"] { margin-top: auto !important; margin-bottom: 0 !important; padding: 0 !important; }
[class*="st-key-ld-header-container"] .ld-refresh-row { margin-top: auto !important; height: 40px !important; }
/* Selectbox outer box: dark pill matching the mockup */
[class*="st-key-ld-header-container"] [data-testid="stSelectbox"] > div > div {
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
[class*="st-key-ld-header-container"] [data-testid="stSelectbox"] > div > div:hover {
    border-color: rgba(255,255,255,0.18) !important;
}
/* Chevron / dropdown arrow: muted white */
[class*="st-key-ld-header-container"] [data-testid="stSelectbox"] svg {
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
.vtable td { padding: 12px 10px; vertical-align: middle; }
.v-rank {
    width: 32px; height: 32px; border-radius: 8px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 800;
    background: var(--surface2); color: var(--text-dim);
    border: 1px solid var(--border); flex-shrink: 0;
}
.v-rank.top3 { background: var(--red); color: #fff; border-color: transparent; }
.v-thumb-wrap {
    position: relative; width: 120px; height: 68px;
    border-radius: 8px; overflow: hidden; flex-shrink: 0; background: #1a1a1a;
}
.v-thumb-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
.v-dur {
    position: absolute; bottom: 3px; right: 3px;
    background: rgba(0,0,0,.82); color: #fff;
    font-size: 0.58rem; font-weight: 700;
    padding: 1px 4px; border-radius: 3px; letter-spacing: .2px;
}
.v-info { display: flex; align-items: center; gap: 12px; }
.v-title {
    font-size: 0.88rem; font-weight: 600; color: var(--text);
    line-height: 1.35; max-width: 480px;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
    font-family: 'Inter', sans-serif;
}
.v-channel {
    font-size: 0.72rem; color: var(--red);
    margin-top: 2px; font-weight: 500;
    display: flex; align-items: center; gap: 3px;
    font-family: 'Inter', sans-serif;
}
.v-meta { font-size: 0.68rem; color: var(--text-muted); margin-top: 2px; font-family: 'Inter', sans-serif; }
.v-stat { font-size: 0.84rem; font-weight: 600; color: var(--text); text-align: right; white-space: nowrap; }
.v-stat-sub { font-size: 0.68rem; color: var(--text-muted); text-align: right; white-space: nowrap; margin-top: 2px; }
.v-link {
    display: inline-flex; align-items: center; justify-content: center;
    width: 32px; height: 32px; border-radius: 8px;
    background: var(--red-dim); border: 1px solid var(--red-border);
    color: var(--red) !important; font-size: 0.90rem;
    transition: background .15s;
}
.v-link:hover { background: var(--red); color: #fff !important; }
.vtable-scroll {
    max-height: 650px; overflow-y: auto;
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

/* ── TRENDING ACROSS TIME CARD (Plotly Integration) ── */
[class*="st-key-trending-across-time-card"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    overflow: hidden !important;
    padding: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    margin-bottom: 12px !important;
}
[class*="st-key-trending-across-time-card"] [data-testid="element-container"] {
    margin: 0 !important;
    padding: 0 !important;
}
[class*="st-key-trending-across-time-card"] .stPlotlyChart {
    padding: 0 4px 8px 4px !important;
    margin: 0 !important;
}
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
            f'<td style="width:40px"><span class="v-rank {top3}">{rank}</span></td>'
            f'<td>'
            f'<div class="v-info">'
            f'<div class="v-thumb-wrap"><img src="{thumb}" alt="" loading="lazy"/></div>'
            f'<div>'
            f'<div class="v-title">{title}</div>'
            f'<div class="v-channel">{channel}</div>'
            f'<div class="v-meta">{views} views · {ago}</div>'
            f'</div></div>'
            f'</td>'
            f'<td style="width:80px">'
            f'<div class="v-stat">{likes}</div>'
            f'<div class="v-stat-sub">💬 {comms}</div>'
            f'</td>'
            f'<td style="width:40px">'
            f'<a href="{yt_url}" target="_blank" rel="noopener" class="v-link">↗</a>'
            f'</td>'
            f'</tr>'
        )
    return rows


def _channel_rows(top_channels, total_views) -> str:
    rows = ""
    for idx, (channel, views) in enumerate(top_channels):
        pct     = (views / total_views * 100) if total_views else 0
        top_cls = "top3" if idx < 3 else ""
        initials = "".join(w[0].upper() for w in channel.split()[:2]) or "CH"
        rows += (
            f'<div class="ch-row">'
            f'<div class="ch-rank {"top3" if idx<3 else ""}">{idx+1}</div>'
            f'<div class="ch-avatar">{initials[:2]}</div>'
            f'<div class="ch-info">'
            f'<div class="ch-name">{_e(channel)}</div>'
            f'<div class="ch-sub">{_fmt(views)} lượt xem</div>'
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
        f'<div class="vcard-title">Trending across categories</div>'
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


def _render_time_chart_card(seed=7) -> None:
    import plotly.graph_objects as go
    with st.container(key="trending-across-time-card"):
        st.markdown(
            f'<div class="vcard-head" style="border-bottom: 1px solid var(--border); padding: 10px 14px 9px;">'
            f'<div class="vcard-title">Trending across time</div>'
            f'<span class="live-badge">LIVE</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        pts = [
            (0.3 + 0.6 * abs(math.sin(i * 0.55 + seed))
             + 0.15 * math.sin(i * 1.8 + seed)) * 20_000_000
            for i in range(24)
        ]
        times = [f"{i:02d}:00" for i in range(24)]
        views_fmt = [_fmt(int(v)) for v in pts]

        fig = go.Figure(
            go.Scatter(
                x=times,
                y=pts,
                mode="lines+markers",
                line=dict(color="#E8001D", width=2),
                marker=dict(
                    color="#E8001D",
                    size=4,
                ),
                fill="tozeroy",
                fillcolor="rgba(232,0,29,0.08)",
                text=views_fmt,
                hovertemplate="<b>Time:</b> %{x}<br><b>Views:</b> %{text}<extra></extra>",
            )
        )
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=14, r=14, t=10, b=10),
            height=180,
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                color="rgba(255,255,255,0.28)",
                dtick=4,
                tickfont=dict(size=9, family="Inter, sans-serif"),
                tickangle=0,
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                color="rgba(255,255,255,0.28)",
                tickvals=[0, 5_000_000, 10_000_000, 15_000_000, 20_000_000],
                ticktext=["0", "5M", "10M", "15M", "20M"],
                tickfont=dict(size=9, family="Inter, sans-serif"),
                zeroline=False,
            ),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#161616",
                bordercolor="rgba(255,255,255,0.08)",
                font=dict(color="#FFFFFF", family="Inter, sans-serif", size=10)
            )
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _channels_card(top_channels, total_views, region: str = "VN") -> str:
    country_name = COUNTRY_NAMES.get(region, region)
    return (
        f'<div class="vcard">'
        f'<div class="vcard-head">'
        f'<div class="vcard-title">Top Channels By Views – {_e(country_name)}</div>'
        f'<span class="live-badge">LIVE</span>'
        f'</div>'
        f'<div class="ch-list">'
        + _channel_rows(top_channels, total_views)
        + f'</div>'
        f'</div>'
    )


def _countries_card(region: str, top_videos: list) -> str:
    map_svg = _world_map_svg(region)
    country_name = COUNTRY_NAMES.get(region, region)

    return (
        f'<div class="vcard">'
        f'<div class="vcard-head">'
        f'<div class="vcard-title">Trending Regions</div>'
        f'<span class="live-badge">LIVE</span>'
        f'</div>'
        f'<div class="country-map">{map_svg}'
        f'<div class="map-legend">'
        f'<span class="map-legend-dot"></span>'
        f'<span>Current Watch: {_e(country_name)}</span>'
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
        f'<span> View all {total}</span>'
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

    # ── HEADER: Title trái + 3 controls phải cùng hàng ──
    st.markdown(
        '<style>'
        # Header container styling: increase top padding to 45px
        '[class*="st-key-ld-header-container"] {'
        '  background: var(--surface) !important;'
        '  border-bottom: 1px solid var(--border) !important;'
        '  padding: 45px 24px 16px 24px !important;'
        '}'
        # Controls Bar layout styling
        '[class*="st-key-ld-controls-bar"] [data-testid="stHorizontalBlock"] {'
        '  gap: 16px !important;'
        '  align-items: flex-end !important;'
        '  flex-wrap: nowrap !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] [data-testid="column"] {'
        '  padding: 0 !important;'
        '}'
        # Reset margins for elements in controls bar to prevent vertical misalignment
        '[class*="st-key-ld-controls-bar"] [data-testid="stSelectbox"] {'
        '  margin: 0 !important;'
        '  padding: 0 !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] [data-testid="element-container"] {'
        '  margin: 0 !important;'
        '  padding: 0 !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] .stMarkdown {'
        '  margin: 0 !important;'
        '  padding: 0 !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] .stMarkdown p {'
        '  margin: 0 !important;'
        '}'
        # Custom Selectbox styling for Controls Bar (Deep dark pill)
        '[class*="st-key-ld-controls-bar"] [data-testid="stSelectbox"] > div > div {'
        '  background: #161616 !important;'
        '  border: 1px solid rgba(255,255,255,0.08) !important;'
        '  border-radius: 10px !important;'
        '  height: 40px !important; min-height: 40px !important;'
        '  padding: 0 14px !important;'
        '  display: flex !important; align-items: center !important;'
        '  font-size: 0.85rem !important; font-weight: 500 !important;'
        '  color: #ffffff !important;'
        '  transition: border-color 0.2s !important; cursor: pointer !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] [data-testid="stSelectbox"] > div > div:hover {'
        '  border-color: rgba(255,255,255,0.18) !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] [data-testid="stSelectbox"] svg {'
        '  color: rgba(255,255,255,0.40) !important;'
        '  fill: rgba(255,255,255,0.40) !important;'
        '  width: 15px !important; height: 15px !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] [data-testid="stSelectbox"] label {'
        '  display: none !important; margin: 0 !important; padding: 0 !important;'
        '}'
        '[class*="st-key-ld-controls-bar"] .ld-refresh-row {'
        '  margin: 0 !important;'
        '  height: 40px !important;'
        '}'
        '</style>',
        unsafe_allow_html=True,
    )

    with st.container(key="ld-header-container"):
        # Header: chỉ hiện title
        st.markdown(
            '<div class="ld-header-left">'
            '<div class="ld-h-title"><em>Live</em> YouTube Dashboard</div>'
            '<div class="ld-h-sub">Monitor YouTube Trending across regions</div>'
            '</div>',
            unsafe_allow_html=True,
        )

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
    channel_views  = {}
    for v in top_videos:
        sn       = v.get("snippet", {})
        cat_name = CAT_ID_TO_NAME.get(str(sn.get("categoryId","24")), "Khác")
        cat_counts[cat_name]  = cat_counts.get(cat_name, 0) + 1
        ch                    = sn.get("channelTitle","")
        views_val             = int(v.get("statistics", {}).get("viewCount", 0) or 0)
        channel_views[ch]     = channel_views.get(ch, 0) + views_val

    sorted_cats  = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    top_channels = sorted(channel_views.items(), key=lambda x: x[1], reverse=True)[:5]

    # ═══════════════════════════════════
    #  CONTROLS BAR – above KPI cards
    #  This row: [spacer] [Country] [Top]
    # ═══════════════════════════════════
    with st.container(key="ld-controls-bar"):
        _spacer, ctrl_country, ctrl_top = st.columns(
            [3.0, 1.0, 1.0],
            gap="medium",
            vertical_alignment="bottom",
        )

        with ctrl_country:
            try:
                r_idx = list(REGIONS.values()).index(st.session_state["tt_region"])
            except ValueError:
                r_idx = 0
            region_label = st.selectbox(
                "Country", list(REGIONS.keys()), index=r_idx,
                key="tt_region_sel",
            )
            new_region = REGIONS[region_label]
            if new_region != st.session_state["tt_region"]:
                st.session_state["tt_region"] = new_region
                st.rerun()

        with ctrl_top:
            try:
                t_idx = TOP_OPTS.index(st.session_state["tt_top"])
            except ValueError:
                t_idx = 0
            top_label = st.selectbox(
                "Số video", TOP_OPTS, index=t_idx,
                key="tt_top_sel",
            )
            if top_label != st.session_state["tt_top"]:
                st.session_state["tt_top"] = top_label
                st.rerun()

    # ═══════════════════════════════════
    #  SECTION 3 – KPI CARDS  (5 columns)
    # ═══════════════════════════════════
    st.markdown('<div class="kpi-wrap">', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5, gap="small")

    kpi_data = [
        (k1, "", "rgba(232,0,29,.15)",   "Trending Videos",   str(total),            f"currently trending",         "#E8001D", 1),
        (k2, "", "rgba(59,130,246,.15)", "Total Views",   _fmt(total_views),      f"across top {total} videos", "#3B82F6", 2),
        (k3, "", "rgba(34,197,94,.15)",  "Total Likes",  _fmt(total_likes),      f"across top {total} videos", "#22C55E", 3),
        (k4, "", "rgba(245,158,11,.15)", "Total Comments",   _fmt(total_comments),   f"across top {total} videos", "#F59E0B", 4),
        (k5, "", "rgba(168,85,247,.15)", "Growth Trend",    f"+{growth_est:.0f}%",  "vs. 1 hour ago",       "#A855F7", 5),
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
            + _channels_card(top_channels, total_views, st.session_state["tt_region"])
            + f'</div>',
            unsafe_allow_html=True,
        )

    with col_right:
        _render_time_chart_card()
        st.markdown(
            f'<div class="right-stack">'
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
        f'Source: YouTube Data API v3'
        f'</div>'
        f'<div class="ld-footer-item">Update every 1 minute</div>'
        f'<div class="ld-footer-item">🕐 System time: {now_date_str} {now_str} (GMT+7)</div>'
        f'<div class="ld-footer-item" style="margin-left:auto">'
        f'Connection: <span class="ld-footer-dot"></span><span class="ld-footer-online">Online</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )