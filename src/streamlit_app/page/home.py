import os
import requests
from datetime import datetime, timezone

import streamlit as st


def _fetch_top1_trending():
    """Fetch #1 trending video from YouTube API (VN, all categories)."""
    keys = []
    i = 1
    while True:
        key = os.getenv(f"YOUTUBE_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1
    if not keys:
        return None
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": "VN",
                "maxResults": 1,
                "key": keys[0],
            },
            timeout=10,
        )
        items = resp.json().get("items", [])
        if not items:
            return None
        item    = items[0]
        snippet = item["snippet"]
        stats   = item.get("statistics", {})

        views = int(stats.get("viewCount", 0) or 0)
        if views >= 1_000_000:
            views_str = f"{views/1_000_000:.1f}M"
        elif views >= 1_000:
            views_str = f"{views/1_000:.1f}K"
        else:
            views_str = str(views)

        published_raw = snippet.get("publishedAt", "")
        try:
            pub_dt  = datetime.strptime(published_raw[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            now_utc = datetime.now(timezone.utc)
            delta   = now_utc - pub_dt
            days    = delta.days
            if days == 0:
                hours   = delta.seconds // 3600
                age_str = f"{hours} giờ trước" if hours > 0 else "Vừa đăng"
            elif days == 1:
                age_str = "1 ngày trước"
            else:
                age_str = f"{days} ngày trước"
        except Exception:
            age_str = ""

        thumbnail = (
            snippet.get("thumbnails", {}).get("maxres", {}).get("url")
            or snippet.get("thumbnails", {}).get("high", {}).get("url", "")
        )

        return {
            "title":     snippet.get("title", ""),
            "channel":   snippet.get("channelTitle", ""),
            "views_str": views_str,
            "age_str":   age_str,
            "thumbnail": thumbnail,
            "video_id":  item["id"],
        }
    except Exception:
        return None


def render_home() -> None:

    # Remove Streamlit default spacing
    st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    [data-testid="element-container"] { margin: 0 !important; padding: 0 !important; }
    .stMarkdown { margin: 0 !important; padding: 0 !important; }
    [data-testid="stMarkdownContainer"] p { margin: 0 !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Fetch #1 trending (cached 10 min) ────────────────────────
    @st.cache_data(ttl=600, show_spinner=False)
    def get_top1():
        return _fetch_top1_trending()

    top1 = get_top1()

    # Build hero card HTML depending on whether fetch succeeded
    if top1:
        if top1["thumbnail"]:
            thumb_html = (
                '<img src="' + top1["thumbnail"] + '" '
                'style="width:100%;height:100%;object-fit:cover;display:block;" '
                'alt="thumbnail">'
            )
        else:
            thumb_html = '<div class="hp-vcard-thumb-bg"></div>'

        hero_card_html = (
            '<div class="hp-vcard">'
            '<div class="hp-vcard-badge">#1 TRENDING</div>'
            '<div class="hp-vcard-thumb">'
            '<div class="hp-vcard-thumb-inner">'
            + thumb_html +
            '</div>'
            '</div>'
            '<div class="hp-vcard-info">'
            '<div class="hp-vcard-title">' + top1["title"] + '</div>'
            '<div class="hp-vcard-channel">' + top1["channel"] + '</div>'
            '<div class="hp-vcard-meta">' + top1["views_str"] + ' views &nbsp;&middot;&nbsp; ' + top1["age_str"] + '</div>'
            '<a class="hp-vcard-cta" href="?tab=trending" target="_self">Xem chi ti&#7871;t &#8599;</a>'
            '</div>'
            '</div>'
        )
    else:
        hero_card_html = (
            '<div class="hp-vcard">'
            '<div class="hp-vcard-badge">#1 TRENDING</div>'
            '<div class="hp-vcard-thumb">'
            '<div class="hp-vcard-thumb-inner">'
            '<div class="hp-vcard-thumb-bg"></div>'
            '</div>'
            '</div>'
            '<div class="hp-vcard-info">'
            '<div class="hp-vcard-title">&#272;ang t&#7843;i d&#7919; li&#7879;u...</div>'
            '<div class="hp-vcard-channel">YouTube Trending VN</div>'
            '<div class="hp-vcard-meta">&nbsp;</div>'
            '<a class="hp-vcard-cta" href="?tab=trending" target="_self">Xem Top Trending &#8599;</a>'
            '</div>'
            '</div>'
        )

    # ── 1. HERO ──────────────────────────────────────────────────
    st.markdown(
        """
    <section class="hp-hero">
      <div class="hp-hero-inner">
        <div class="hp-hero-left">
          <div class="hp-eyebrow">
            <span class="hp-eyebrow-line"></span>AI &middot; YOUTUBE ANALYTICS
          </div>
          <h1 class="hp-title">
            ANALYZE<br>
             <span class="hp-red">YOUTUBE</span> TRENDS<br>
            IN REAL TIME
          </h1>
          <p class="hp-desc">
            Analyze YouTube trends in real time using YouTube Data API v3<br>
             Data Warehouse technology and XGBoost prediction models.
          </p>
          <div class="hp-actions">
            <a class="hp-btn-primary" href="?tab=predict" target="_self">&#9654; Analyze Now</a>
            <a class="hp-btn-secondary" href="?tab=trending" target="_self">View Top Trending</a>
          </div>
        </div>
        <div class="hp-hero-right">
    """
        + hero_card_html +
        """
        </div>
      </div>
    </section>
    """,
        unsafe_allow_html=True,
    )

    # ── 2. KPI BAR ───────────────────────────────────────────────
    st.markdown("""
    <section class="hp-kpi">
      <div class="hp-kpi-inner">
        <div class="hp-kpi-card">
          <div class="hp-kpi-icon" style="background:rgba(232,0,29,0.15)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="#E8001D"><path d="M8 5v14l11-7z"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">150K+</div>
            <div class="hp-kpi-label">Videos Analyzed</div>
            <div class="hp-kpi-sub">Historical Dataset</div>
          </div>
        </div>
        <div class="hp-kpi-card">
          <div class="hp-kpi-icon" style="background:rgba(232,0,29,0.15)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">87.3%</div>
            <div class="hp-kpi-label">Model Accuracy</div>
            <div class="hp-kpi-sub">XGBoost Model</div>
          </div>
        </div>
        <div class="hp-kpi-card">
          <div class="hp-kpi-icon" style="background:rgba(232,0,29,0.15)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="#E8001D"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">30</div>
            <div class="hp-kpi-label">Popular Videos</div>
            <div class="hp-kpi-sub">By Region</div>
          </div>
        </div>
        <div class="hp-kpi-card">
          <div class="hp-kpi-icon" style="background:rgba(232,0,29,0.15)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">8</div>
            <div class="hp-kpi-label">Supported Regions</div>
            <div class="hp-kpi-sub">Globally</div>
          </div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # ── 3. TRENDING SNAPSHOT (dùng components.html để bypass SVG sanitizer) ──
    import streamlit.components.v1 as components
    components.html("""
    <style>
      * { margin:0; padding:0; box-sizing:border-box; }
      body { background:#0D0D0D; font-family:'DM Sans',sans-serif; overflow:hidden; }
      .hp-snap { background:#0D0D0D; padding:0; }
      .hp-snap-inner { max-width:1280px; margin:0 auto; padding:3rem 0 3.5rem; }
      .hp-snap-head { display:flex; align-items:center; gap:.6rem; font-size:.78rem; font-weight:800; letter-spacing:2px; text-transform:uppercase; color:#E8001D; margin-bottom:2rem; }
      .hp-snap-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; }
      .hp-snap-card { background:#131313; border:1px solid #222; border-radius:14px; padding:1.25rem; transition:border-color .2s; }
      .hp-snap-card:hover { border-color:#333; }
      .hp-snap-card-label { font-size:.6rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:rgba(255,255,255,.28); margin-bottom:.9rem; }
      .hp-snap-cat-row { display:flex; align-items:center; gap:.5rem; margin-bottom:.15rem; }
      .hp-snap-cat-ico { font-size:1rem; }
      .hp-snap-cat-name { font-size:1rem; font-weight:700; color:#fff; }
      .hp-snap-cat-pct { font-size:.72rem; color:rgba(255,255,255,.4); margin-bottom:.85rem; }
      .hp-snap-donut-flex { display:flex; align-items:center; gap:.85rem; }
      .hp-snap-donut-wrap { position:relative; width:96px; height:96px; flex:0 0 96px; display:grid; place-items:center; }
      .hp-snap-donut-label { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center; line-height:1.1; }
      .hp-snap-donut-label strong { display:block; font-size:1.3rem; font-weight:800; color:#fff; line-height:1; }
      .hp-snap-donut-label span { font-size:.6rem; color:rgba(255,255,255,.4); }
      .hp-snap-legend { flex:1; display:flex; flex-direction:column; gap:.28rem; }
      .hp-snap-leg-row { display:flex; align-items:center; gap:5px; font-size:.7rem; color:rgba(255,255,255,.6); }
      .hp-snap-leg-row i { width:8px; height:8px; border-radius:2px; flex-shrink:0; display:inline-block; }
      .hp-snap-leg-row b { margin-left:auto; color:#fff; font-weight:700; }
      .hp-snap-hero-row { display:flex; align-items:center; gap:.7rem; margin-bottom:.85rem; }
      .hp-snap-hero-name { font-size:1.05rem; font-weight:700; color:#fff; line-height:1.15; }
      .hp-snap-hero-sub { font-size:.7rem; color:rgba(255,255,255,.38); }
      .hp-snap-table { display:flex; flex-direction:column; gap:.42rem; }
      .hp-snap-tr { display:flex; align-items:center; gap:.55rem; font-size:.78rem; }
      .hp-snap-rank { width:16px; font-weight:800; color:rgba(255,255,255,.3); flex-shrink:0; font-size:.78rem; }
      .hp-snap-rank.r1 { color:#E8001D; }
      .hp-snap-tname { flex:1; color:rgba(255,255,255,.8); }
      .hp-snap-tval { font-weight:600; color:rgba(255,255,255,.55); font-size:.75rem; }
      .hp-snap-ch-list { display:flex; flex-direction:column; gap:.5rem; }
      .hp-snap-ch-row { display:flex; align-items:center; gap:.55rem; font-size:.76rem; }
      .hp-snap-av { width:26px; height:26px; border-radius:50%; background:rgba(232,0,29,.15); border:1px solid rgba(232,0,29,.25); display:flex; align-items:center; justify-content:center; font-size:.55rem; font-weight:700; color:#E8001D; flex-shrink:0; }
      .hp-snap-ch-name { flex:1; color:rgba(255,255,255,.75); }
      .hp-snap-growth { font-weight:700; color:#22C55E; font-size:.75rem; }
      .hp-snap-views-big { font-size:1.8rem; font-weight:800; color:#fff; line-height:1; }
      .hp-snap-views-delta { font-size:.7rem; color:#22C55E; font-weight:600; margin-top:2px; }
      .hp-snap-chart { display:flex; gap:6px; margin-top:.5rem; }
      .hp-snap-chart-y { display:flex; flex-direction:column; justify-content:space-between; height:80px; font-size:.55rem; color:rgba(255,255,255,.25); text-align:right; width:30px; flex-shrink:0; padding-top:2px; }
      .hp-snap-chart-svg { flex:1; }
      .hp-snap-chart-x { display:flex; justify-content:space-between; font-size:.58rem; color:rgba(255,255,255,.25); margin-top:4px; }
    </style>
    <div class="hp-snap">
      <div class="hp-snap-inner">
        <div class="hp-snap-head">
          <span>TRENDING SNAPSHOT</span>
        </div>
        <div class="hp-snap-grid">

          <div class="hp-snap-card">
            <div class="hp-snap-card-label">TOP DANH MỤC HÔM NAY</div>
            <div class="hp-snap-cat-row">
              <span class="hp-snap-cat-ico">🎵</span>
              <span class="hp-snap-cat-name">Âm nhạc</span>
            </div>
            <div class="hp-snap-cat-pct">42% tổng lượt xem</div>
            <div class="hp-snap-donut-flex">
              <div class="hp-snap-donut-wrap">
                <svg viewBox="0 0 100 100" width="96" height="96">
                  <circle cx="50" cy="50" r="38" fill="none" stroke="#1e1e1e" stroke-width="13"/>
                  <circle cx="50" cy="50" r="38" fill="none" stroke="#E8001D" stroke-width="13" stroke-dasharray="100.5 138.5" stroke-dashoffset="0" transform="rotate(-90 50 50)"/>
                  <circle cx="50" cy="50" r="38" fill="none" stroke="#FF6B35" stroke-width="13" stroke-dasharray="59.7 179.3" stroke-dashoffset="-100.5" transform="rotate(-90 50 50)"/>
                  <circle cx="50" cy="50" r="38" fill="none" stroke="#A855F7" stroke-width="13" stroke-dasharray="35.8 203.2" stroke-dashoffset="-160.2" transform="rotate(-90 50 50)"/>
                  <circle cx="50" cy="50" r="38" fill="none" stroke="#3B82F6" stroke-width="13" stroke-dasharray="23.9 215.1" stroke-dashoffset="-196.0" transform="rotate(-90 50 50)"/>
                  <circle cx="50" cy="50" r="38" fill="none" stroke="#6B7280" stroke-width="13" stroke-dasharray="19.1 219.9" stroke-dashoffset="-219.9" transform="rotate(-90 50 50)"/>
                </svg>
                <div class="hp-snap-donut-label">
                  <strong>42%</strong><span>Music</span>
                </div>
              </div>
              <div class="hp-snap-legend">
                <div class="hp-snap-leg-row"><i style="background:#E8001D"></i>Âm nhạc<b>42%</b></div>
                <div class="hp-snap-leg-row"><i style="background:#FF6B35"></i>Giải trí<b>25%</b></div>
                <div class="hp-snap-leg-row"><i style="background:#A855F7"></i>Gaming<b>15%</b></div>
                <div class="hp-snap-leg-row"><i style="background:#3B82F6"></i>Thể thao<b>10%</b></div>
                <div class="hp-snap-leg-row"><i style="background:#6B7280"></i>Khác<b>8%</b></div>
              </div>
            </div>
          </div>

          <div class="hp-snap-card">
            <div class="hp-snap-card-label">QUỐC GIA HOẠT ĐỘNG MẠNH NHẤT</div>
            <div class="hp-snap-hero-row">
              <span style="font-size:1.7rem">🌍</span>
              <div>
                <div class="hp-snap-hero-name">Vietnam</div>
                <div class="hp-snap-hero-sub">21.4% tổng lượt xem</div>
              </div>
            </div>
            <div class="hp-snap-table">
              <div class="hp-snap-tr"><span class="hp-snap-rank r1">1</span><span class="hp-snap-tname">Vietnam</span><span class="hp-snap-tval">21.4%</span></div>
              <div class="hp-snap-tr"><span class="hp-snap-rank">2</span><span class="hp-snap-tname">Indonesia</span><span class="hp-snap-tval">16.7%</span></div>
              <div class="hp-snap-tr"><span class="hp-snap-rank">3</span><span class="hp-snap-tname">United States</span><span class="hp-snap-tval">12.3%</span></div>
              <div class="hp-snap-tr"><span class="hp-snap-rank">4</span><span class="hp-snap-tname">India</span><span class="hp-snap-tval">8.9%</span></div>
              <div class="hp-snap-tr"><span class="hp-snap-rank">5</span><span class="hp-snap-tname">Japan</span><span class="hp-snap-tval">6.2%</span></div>
            </div>
          </div>

          <div class="hp-snap-card">
            <div class="hp-snap-card-label">KÊNH TĂNG TRƯỞNG NHANH NHẤT</div>
            <div class="hp-snap-hero-row">
              <span style="font-size:1.4rem">⚡</span>
              <div class="hp-snap-hero-name" style="font-size:0.85rem">Sơn Tùng M-TP Official</div>
            </div>
            <div class="hp-snap-ch-list">
              <div class="hp-snap-ch-row"><div class="hp-snap-av">ST</div><span class="hp-snap-ch-name">Sơn Tùng M-TP Official</span><span class="hp-snap-growth">+58.7%</span></div>
              <div class="hp-snap-ch-row"><div class="hp-snap-av">HH</div><span class="hp-snap-ch-name">HIEUTHUHAI Official</span><span class="hp-snap-growth">+34.2%</span></div>
              <div class="hp-snap-ch-row"><div class="hp-snap-av">IS</div><span class="hp-snap-ch-name">IShowSpeed</span><span class="hp-snap-growth">+28.1%</span></div>
              <div class="hp-snap-ch-row"><div class="hp-snap-av">BP</div><span class="hp-snap-ch-name">BLACKPINK</span><span class="hp-snap-growth">+26.3%</span></div>
              <div class="hp-snap-ch-row"><div class="hp-snap-av">MB</div><span class="hp-snap-ch-name">MrBeast</span><span class="hp-snap-growth">+24.7%</span></div>
            </div>
          </div>

          <div class="hp-snap-card">
            <div class="hp-snap-card-label">TỔNG LƯỢT XEM (24H QUA)</div>
            <div class="hp-snap-hero-row">
              <span style="font-size:1.4rem">📈</span>
              <div>
                <div class="hp-snap-views-big">182.4M</div>
                <div class="hp-snap-views-delta">+18.7% so với 24h trước</div>
              </div>
            </div>
            <div class="hp-snap-chart">
              <div class="hp-snap-chart-y">
                <span>200M</span><span>150M</span><span>100M</span><span>50M</span><span>0</span>
              </div>
              <div class="hp-snap-chart-svg">
                <svg viewBox="0 0 200 80" preserveAspectRatio="none" width="100%" height="72">
                  <defs>
                    <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#E8001D" stop-opacity="0.35"/>
                      <stop offset="100%" stop-color="#E8001D" stop-opacity="0"/>
                    </linearGradient>
                  </defs>
                  <path d="M0,72 C25,70 40,64 60,55 C80,46 95,42 115,33 C135,24 155,18 175,11 L200,4 L200,78 L0,78 Z" fill="url(#cg)"/>
                  <path d="M0,72 C25,70 40,64 60,55 C80,46 95,42 115,33 C135,24 155,18 175,11 L200,4" fill="none" stroke="#E8001D" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div class="hp-snap-chart-x">
                  <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
    """, height=420, scrolling=False)

    # ── 4. WHY VISION ────────────────────────────────────────────
    st.markdown("""
    <section class="hp-why">
      <div class="hp-why-inner">
        <h2 class="hp-why-title">Why Choose VISION?</h2>
        <div class="hp-why-grid">
          <div class="hp-why-card">
            <div class="hp-why-icon" style="background:rgba(232,0,29,0.1)">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="#E8001D"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <div class="hp-why-name">Instant Analysis</div>
            <div class="hp-why-desc">Just a few mouse clicks to analyze YouTube video trends in real-time with accurate data.</div>
            <a class="hp-why-link" href="?tab=predict" target="_self">Analyze Now →</a>
          </div>
          <div class="hp-why-card">
            <div class="hp-why-icon" style="background:rgba(232,0,29,0.1)">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><circle cx="12" cy="12" r="10"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div class="hp-why-name">XGBoost Model</div>
            <div class="hp-why-desc">The model is trained on real-world data from 150K+ YouTube videos and 7M+ comments with high accuracy.</div>
            <a class="hp-why-link" href="#" target="_self">Learn More →</a>
          </div>
          <div class="hp-why-card">
            <div class="hp-why-icon" style="background:rgba(232,0,29,0.1)">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            </div>
            <div class="hp-why-name">Comprehensive Data</div>
            <div class="hp-why-desc">8 key features.</div>
            <a class="hp-why-link" href="#" target="_self">View Details →</a>
          </div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # ── 5. FOOTER ────────────────────────────────────────────────
    st.markdown("""
    <div class="hp-footer">
      <div class="hp-footer-inner">
        <div class="hp-footer-brand">
          <div class="hp-footer-logo">
            <div class="hp-footer-logo-icon">▶</div>
            <span>VISION</span>
          </div>
          <p class="hp-footer-desc">VISION – An AI-Powered YouTube Trend Analysis & Prediction Platform Using XGBoost.</p>
          <div class="hp-footer-socials">
            <a class="hp-footer-social" href="#" title="GitHub">⊕</a>
            <a class="hp-footer-social" href="#" title="LinkedIn">in</a>
            <a class="hp-footer-social" href="mailto:vision.analytics.project@gmail.com" title="Email">✉</a>
          </div>
        </div>
        <div class="hp-footer-col">
          <div class="hp-footer-col-title">DATA</div>
          <div class="hp-footer-item">✓ YouTube Data API v3</div>
          <div class="hp-footer-item">✓ 150K+ videos around the World</div>
          <div class="hp-footer-item">✓ Regular Updates</div>
          <div class="hp-footer-item">✓ Data Warehouse</div>
        </div>
        <div class="hp-footer-col">
          <div class="hp-footer-col-title">CONTACT</div>
          <div class="hp-footer-item">Individual Contributors</div>
          <div class="hp-footer-item">✉ chgiabao36925@gmail.com</div>
        </div>
      </div>
      <div class="hp-footer-bottom">
        <span>© 2026 VISION Analytics. All rights reserved.</span>
        <span>Data Warehouse &amp; Machine Learning Project</span>
      </div>
    </div>
    """, unsafe_allow_html=True)