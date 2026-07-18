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
            <svg width="24" height="17" viewBox="0 0 24 17" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M23.495 2.656a3.016 3.016 0 0 0-2.122-2.136C19.505 0 12 0 12 0S4.495 0 2.627.52A3.016 3.016 0 0 0 .505 2.656 31.64 31.64 0 0 0 0 8.5a31.64 31.64 0 0 0 .505 5.844 3.016 3.016 0 0 0 2.122 2.136C4.495 17 12 17 12 17s7.505 0 9.373-.52a3.016 3.016 0 0 0 2.122-2.136A31.64 31.64 0 0 0 24 8.5a31.64 31.64 0 0 0-.505-5.844z" fill="#E8001D"/><path d="M9.6 12.143l6.285-3.643L9.6 4.857v7.286z" fill="#fff"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">158K+</div>
            <div class="hp-kpi-label">Videos Analyzed</div>
            <div class="hp-kpi-sub">Historical Dataset</div>
          </div>
        </div>
        <div class="hp-kpi-card">
          <div class="hp-kpi-icon" style="background:rgba(232,0,29,0.15)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">93%</div>
            <div class="hp-kpi-label">Model Accuracy</div>
            <div class="hp-kpi-sub">XGBoost Model</div>
          </div>
        </div>
        <div class="hp-kpi-card">
          <div class="hp-kpi-icon" style="background:rgba(232,0,29,0.15)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="#E8001D"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">8M+</div>
            <div class="hp-kpi-label">Comments Processed</div>
            <div class="hp-kpi-sub">Real-time</div>
          </div>
        </div>
        <div class="hp-kpi-card">
          <div class="hp-kpi-icon" style="background:rgba(232,0,29,0.15)">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          </div>
          <div>
            <div class="hp-kpi-num">8</div>
            <div class="hp-kpi-label">Geographic Regions</div>
            <div class="hp-kpi-sub">Worldwide Coverage</div>
          </div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)



    # ── 4. WHY VISION ────────────────────────────────────────────
    st.markdown("""
    <section class="hp-why">
      <div class="hp-why-inner">
        <h2 class="hp-why-title">WHY CHOOSE <span class="hp-red">VISION?</span></h2>
        <div class="hp-why-grid">
          <div class="hp-why-card">
            <div class="hp-why-card-header">
              <div class="hp-why-icon" style="background:rgba(232,0,29,0.1)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="#E8001D"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              </div>
              <div class="hp-why-name">Instant Analysis</div>
            </div>
            <div class="hp-why-divider"></div>
            <div class="hp-why-desc">Just a few clicks to analyze YouTube video trends in real-time with accurate data.</div>
          </div>
          <div class="hp-why-card">
            <div class="hp-why-card-header">
              <div class="hp-why-icon" style="background:rgba(232,0,29,0.1)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </div>
              <div class="hp-why-name">Advanced AI Models</div>
            </div>
            <div class="hp-why-divider"></div>
            <div class="hp-why-desc">Trained on real-world data from 150K+ YouTube videos and 7M+ comments with high accuracy.</div>
          </div>
          <div class="hp-why-card">
            <div class="hp-why-card-header">
              <div class="hp-why-icon" style="background:rgba(232,0,29,0.1)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              </div>
              <div class="hp-why-name">Comprehensive Analysis</div>
            </div>
            <div class="hp-why-divider"></div>
            <div class="hp-why-desc">Multi-dimensional analysis across content, engagement, audience, and geographic insights.</div>
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
          <div class="hp-footer-item">Trà Vinh University - DA22TTA - 110122034 - Graduation Project </div>
          <div class="hp-footer-item">Vĩnh Long, Trà Vinh Ward, Vietnam</div>
        </div>
      </div>
      <div class="hp-footer-bottom">
        <span>© 2026 VISION Analytics. All rights reserved.</span>
        <span>Data Warehouse & Youtube Trending Prediction</span>
      </div>
    </div>
    """, unsafe_allow_html=True)