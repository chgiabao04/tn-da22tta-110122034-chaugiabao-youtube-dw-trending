import base64
import html
import io
import os
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
import streamlit as st
import xgboost as xgb

from predict_model import predict_trending, KNOWN_TOPICS, KNOWN_REGIONS
from utils import extract_features, extract_video_id, get_youtube_info
from shap_utils import get_shap_explanation

# ── Load XGBoost model ───────────────────────────────────────────────────────
def load_xgb_model():
    model_path = os.path.join(
        os.path.dirname(__file__),
        "../models/xgb_trending_model.json"
    )
    if not os.path.exists(model_path):
        st.error(f"❌ File not found: {model_path}")
        raise FileNotFoundError(model_path)
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    return model

xgb_model = load_xgb_model()


WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

FEATURE_IMPORTANCE = [
    ("⏱️", "duration_seconds", 46),
    ("🏷️", "topic",            23),
    ("🌐", "country_region",   9),
    ("💬", "comment_rate",     7),
    ("❤️", "like_rate",        4),
    ("👁️", "view_count",       4),
    ("👤", "subscriber_count", 3),
    ("🎞️", "video_count",      2),
    ("🕐", "publish_hour",     1),
]

# ── Tiny helpers ─────────────────────────────────────────────────────────────
def _fmt_big(value) -> str:
    value = int(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _fmt_duration(seconds) -> str:
    seconds = int(seconds or 0)
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} hour {minutes} mins"
    if minutes:
        return f"{minutes} mins {sec} sec"
    return f"{sec} sec"


def _repair_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    try:
        return text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return text


def _safe(text) -> str:
    return html.escape(str(text or ""))


# ── HTML block builders ───────────────────────────────────────────────────────
def _gauge_html(pct: float, color: str, level: str) -> str:
    pct = max(0.0, min(100.0, pct))
    deg = pct * 3.6
    return (
        f'<div class="pp-gauge-wrap">'
        f'<div class="pp-gauge" style="background:conic-gradient({color} {deg:.1f}deg,rgba(255,255,255,0.08) {deg:.1f}deg);">'
        f'<div class="pp-gauge-inner">'
        f'<div class="pp-gauge-pct" style="color:{color};">{pct:.1f}<span>%</span></div>'
        f'<div class="pp-gauge-tag" style="color:{color};">{_safe(level)}</div>'
        f'</div></div></div>'
    )


def _stat_box(icon: str, value: str, label: str) -> str:
    return (
        f'<div class="pp-stat">'
        f'  <div class="pp-stat-icon-wrap">{icon}</div>'
        f'  <div class="pp-stat-info">'
        f'    <strong>{_safe(value)}</strong>'
        f'    <small>{_safe(label)}</small>'
        f'  </div>'
        f'</div>'
    )


def _shap_plot_to_b64(plot_fn, explanation) -> str:
    plt.figure(facecolor="white")
    plot_fn(explanation, show=False)
    fig = plt.gcf()
    fig.patch.set_facecolor("white")
    for ax in fig.axes:
        ax.set_facecolor("white")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")




def _generate_shap_insights(explanation):
    values = explanation.values
    feature_names = explanation.feature_names
    data = explanation.data

    feature_info = sorted(
        [{"feature": feature_names[i], "value": values[i], "data": data[i]}
         for i in range(len(values))],
        key=lambda x: abs(x["value"]),
        reverse=True,
    )

    items = []
    for item in feature_info[:5]:
        feature    = item["feature"]
        shap_value = item["value"]
        data_value = item["data"]
        positive   = shap_value > 0
        icon       = "✓" if positive else "⚠"
        color      = "#22C55E" if positive else "#FF9800"

        if feature == "topic":
            msg = f"The topic <b>{data_value}</b> {'is the most positive factor' if positive else 'is reducing the ability to Trending'} ({shap_value:+.2f})"
        elif feature == "view_count":
            msg = f"Current views {'support' if positive else 'reducing'} the probability of Trending ({shap_value:+.2f})"
        elif feature == "video_count":
            msg = f"Number of videos {'support' if positive else 'reducing'} the ability to Trending ({shap_value:+.2f})"
        elif feature == "publish_hour":
            msg = f"The upload time ({data_value}h) {'is supporting' if positive else 'is not optimal'} for Trending ({shap_value:+.2f})"
        elif feature == "duration_seconds":
            msg = f"The video duration {'is supporting' if positive else 'is reducing'} the ability to Trending ({shap_value:+.2f})"
        elif feature == "country_region":
            msg = f"The region <b>{data_value}</b> {'is supporting' if positive else 'is reducing'} the ability to Trending ({shap_value:+.2f})"
        else:
            msg = f"<b>{feature}</b> {'is supporting' if positive else 'is reducing'} the ability to Trending ({shap_value:+.2f})"

        items.append(
            f'<div style="margin-bottom:12px;padding:12px 14px;border-left:3px solid {color};'
            f'background:rgba(255,255,255,0.05);border-radius:8px;font-size:0.9rem;line-height:1.6;color:rgba(255,255,255,0.85);">'
            f'<span style="color:{color};font-weight:700;margin-right:4px;">{icon}</span> {msg}</div>'
        )
    return "".join(items)

def _generate_recommendations(explanation):
    values = explanation.values
    feature_names = explanation.feature_names

    recommendations = []

    feature_info = sorted(
        zip(feature_names, values),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    for feature, shap_value in feature_info:
        if shap_value >= 0:
            continue

        if feature == "like_rate":
            recommendations.append(
                "Increase audience engagement through stronger thumbnails, titles, and calls-to-action."
            )

        elif feature == "comment_rate":
            recommendations.append(
                "Encourage viewers to leave comments by asking questions or creating discussion-driven content."
            )

        elif feature == "publish_hour":
            recommendations.append(
                "Test different publishing times to reach more viewers"
            )

        elif feature == "duration_seconds":
            recommendations.append(
                "Adjust video length to better match successful trending content."
            )

        elif feature == "video_count":
            recommendations.append(
                "Upload content consistently to strengthen channel performance."
            )

        elif feature == "subscriber_count":
            recommendations.append(
                "Increase subscriber growth through consistent content and audience retention."
            )

        elif feature == "view_count":
            recommendations.append(
                "Increase video exposure through SEO optimization and cross-platform promotion."
            )

        elif feature == "country_region":
            recommendations.append(
                "Consider tailoring content for regions with stronger trending potential."
            )

        elif feature == "topic":
            recommendations.append(
                "Explore content topics that historically perform better with your audience."
            )

    if not recommendations:
        recommendations.append(
            "All major features are contributing positively. Continue maintaining the current content strategy."
        )

    return recommendations[:4]
# ── Render results shared by both modes ──────────────────────────────────────
def _render_results(prob, reasoning, features, video_info):
    prob_pct = prob * 100
    level = "HIGH" if prob_pct >= 60 else ("MEDIUM" if prob_pct >= 35 else "LOW")
    verdict_color = "#22C55E" if prob_pct >= 60 else ("#FF9800" if prob_pct >= 35 else "#E8001D")

    views            = int(video_info.get("views", 0) or 0)
    likes            = int(video_info.get("likes", 0) or 0)
    comments         = int(video_info.get("comments", 0) or 0)
    subscribers      = int(video_info.get("subscriber_count", 0) or 0)
    video_count      = int(video_info.get("channel_video_count", 0) or 0)
    duration_seconds = int(video_info.get("duration", 0) or 0)

    topic        = str(features.get("topic", "Unknown")).capitalize()
    region       = str(features.get("country_region", "Unknown"))
    publish_hour = int(features.get("publish_hour", 12))
    reasoning_text = _repair_text(reasoning)

    like_rate_pct    = features["like_rate"] * 100
    comment_rate_pct = features["comment_rate"] * 100

    thumbnail = _safe(video_info.get("thumbnail", ""))
    title     = _safe(video_info.get("title", "—"))
    channel   = _safe(video_info.get("channel_name", "—"))
    publish_date = video_info.get("published_at", "")
    try:
        publish_date = datetime.strptime(
            publish_date[:19],
            "%Y-%m-%dT%H:%M:%S"
        ).strftime("%d/%m/%Y")
    except:
        publish_date = "N/A"

    # ── SHAP ─────────────────────────────────────────────────────────────────
    try:
        shap_explanation = get_shap_explanation(features)
        shap_available   = True
    except Exception:
        shap_available   = False

    # ── ROW 1: VIDEO INFO + SCORE ─────────────────────────────────────────────
    # Thumbnail / title block
    if thumbnail:
        thumb_html = (
            f'<div class="pp-vi-thumb-wrap">'
            f'<img src="{thumbnail}" class="pp-vi-thumb" />'
            f'</div>'
        )
    else:
        thumb_html = '<div class="pp-vi-thumb-wrap pp-vi-thumb-placeholder">▶</div>'

    video_info_html = (
        f'<div class="pp-vi-layout">'
        + thumb_html
        + f'<div class="pp-vi-meta">'
        f'<div class="pp-vi-title">{title}</div>'
        f'<div class="pp-vi-channel">'
        f'<span class="pp-avatar">{channel[:1].upper()}</span>'
        f'<span class="pp-vi-chname">{channel}</span>'
        f'<span class="pp-vi-subs">{_fmt_big(subscribers)} subscribers</span>'
        f'</div>'
        f'<div class="pp-vi-stats">'
        f'<span>👁️ {_fmt_big(views)} views</span>'
        f'<span>👍 {_fmt_big(likes)} like</span>'
        f'<span>💬 {comments} comments</span>'
        f'<span>⏱️ {_fmt_duration(duration_seconds)}</span>'
        f'<span>📅 {publish_date}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

    # Score / gauge block
    gauge_html = _gauge_html(prob_pct, verdict_color, level)
    score_html = (
        f'<p class="pp-score-label">Video probability to become trending:'
        f'<strong style="color:{verdict_color};">{_safe(level)}</strong></p>'
        + gauge_html
        + f'<p class="pp-score-sub">Based on the analysis of 9 key video features.</p>'
        + f'<div class="pp-score-badge">'
        + f'<span>🤖 XGBoost Classifier</span>'
        + f'<span class="pp-score-auc">Accuracy 93.68% | Precision 80.06% | Recall 97.13% | F1 87.78% | AUC 98.97%</span>'
        + f'</div>'
    )

    # ── ROW 2: FEATURE IMPORTANCE + DATA ─────────────────────────────────────
    importance_rows = "".join(
        f'<tr class="pp-fi-row">'
        f'<td class="pp-fi-name"><span>{icon}</span>{_safe(name)}</td>'
        f'<td class="pp-fi-bar"><div class="pp-fi-track"><div class="pp-fi-fill" style="width:{pct}%;"></div></div></td>'
        f'<td class="pp-fi-pct">{pct}%</td>'
        f'</tr>'
        for icon, name, pct in FEATURE_IMPORTANCE
    )
    importance_html = f'<table class="pp-fi-table">{importance_rows}</table>'
    data_html = (

        f'<div class="pp-stat-grid">'
        + _stat_box("⏱️", _fmt_duration(duration_seconds), "DURATION")
        + _stat_box("🏷️", topic, "TOPIC")
        + _stat_box("🌐", region, "REGION")
        + _stat_box("❤️", f"{like_rate_pct:.2f}%", "LIKE RATE")
        + _stat_box("💬", f"{comment_rate_pct:.3f}%", "COMMENT RATE")
        + _stat_box("👁️", _fmt_big(views), "VIEW COUNT")
        + _stat_box("👤", _fmt_big(subscribers), "SUBSCRIBER COUNT")
        + _stat_box("🎞️", _fmt_big(video_count), "VIDEO COUNT")
        + _stat_box("🕐", str(publish_hour), "PUBLISH HOUR")
        + f'</div>'
    )

    # ── SHAP ─────────────────────────────────────────────────────────────────
    if shap_available:
        waterfall_b64   = _shap_plot_to_b64(shap.plots.waterfall, shap_explanation)
        shap_insights   = _generate_shap_insights(shap_explanation)
        recommendations = _generate_recommendations(shap_explanation)

        # Conclusion from insights
        conclusion = (
            "This video is highly likely to become TRENDING." if prob_pct >= 60
            else (
                "This video has a moderate chance of becoming TRENDING." if prob_pct >= 35
                else "This video has a low chance of becoming TRENDING."
            )
        )
        recommendations_html = "".join(
            [
                f'<div class="pp-rec-item">💡 {rec}</div>'
                for rec in recommendations
            ]
        )
        shap_html = (
    f'<p class="pp-shap-sub">The impact of each feature on the predicted probability (SHAP values).</p>'

    f'<div class="pp-shap-layout">'

    f'<div class="pp-shap-plot-col">'
    f'<div class="pp-shap-plot-label">WATERFALL PLOT</div>'
    f'<img src="data:image/png;base64,{waterfall_b64}" class="pp-shap-img" />'
    f'</div>'

    f'<div class="pp-shap-insight-col">'

    f'<div class="pp-shap-plot-label">EXPLAIN</div>'
    + shap_insights

    + f'<div class="pp-shap-plot-label" style="margin-top:18px;">RECOMMENDATIONS</div>'

    + recommendations_html

    + f'<div class="pp-conclusion">✦ Conclusion: {_safe(conclusion)}</div>'

    f'</div>'
    f'</div>'
)
        shap_section = (
            f'<div class="pp-card pp-shap-card">'
            f'<div class="pp-card-header">'
            f'<span class="pp-card-title-text">SHAP EXPLANATION</span>'
            f'<span class="pp-card-badge">INSIGHT</span>'
            f'</div>'
            + shap_html
            + f'</div>'
        )
    else:
        shap_section = ""

    # ── Assemble & render ─────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="pp-results-wrap">
          <!-- Row 1 -->
          <div class="pp-row pp-row-2">
            <div class="pp-card">
              <div class="pp-card-header">
                <span class="pp-card-title-text">VIDEO INFORMATION</span>
                <span class="pp-card-badge">VIDEO INFO</span>
              </div>
              {video_info_html}
            </div>
            <div class="pp-card pp-score-card">
              <div class="pp-card-header">
                <span class="pp-card-title-text">ABILITY TO BECOME TRENDING</span>
                <span class="pp-card-badge">SCORE</span>
              </div>
              {score_html}
            </div>
          </div>
          <!-- Row 2 -->
          <div class="pp-row pp-row-2">
            <div class="pp-card">
              <div class="pp-card-header">
                <span class="pp-card-title-text">FEATURE IMPORTANCE</span>
                <span class="pp-card-badge">IMPORTANCE</span>
              </div>
              {importance_html}
            </div>
            <div class="pp-card">
              <div class="pp-card-header">
                <span class="pp-card-title-text">INPUT FEATURES (9 FEATURES)</span>
                <span class="pp-card-badge">DATA</span>
              </div>
              {data_html}
            </div>
          </div>
          <!-- Row 3: SHAP -->
          {shap_section}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Main render entry point ───────────────────────────────────────────────────
def render_predict() -> None:
    # ── Page heading ─────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="pp-page-heading">
          <div class="pp-page-title">
            ABILITY TO BECOME TRENDING
          </div>
          <div class="pp-page-underline"></div>
          <div class="pp-page-sub">Enter video information to predict the probability of appearing in the YouTube trending list.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Mode tabs ─────────────────────────────────────────────────────────────
    tab_url, tab_manual = st.tabs(["🔗  Predict by URL", "✏️  Custom Prediction"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 – Predict by URL
    # ════════════════════════════════════════════════════════════════════════
    with tab_url:
        st.markdown('<div class="pp-url-tab-wrap">', unsafe_allow_html=True)
        col_input, col_info = st.columns([1, 1.8], gap="large")

        with col_input:
            # ── URL form ─────────────────────────────────────────────────────
            with st.form("url_form"):
                video_url = st.text_input(
                    "URL video YouTube",
                    value=st.session_state.get("predict_url", ""),
                    placeholder="https://www.youtube.com/watch?v=...",
                    label_visibility="collapsed",
                )
                submitted_url = st.form_submit_button(
                    "🎯  Predict", use_container_width=True, type="primary"
                )

            # ── Examples + security — ONE html block so Streamlit margin
            #    resets don't squish them ──────────────────────────────────────
            st.markdown(
                """
                <div class="pp-below-form">
                  <div class="pp-examples-label">Or try with examples</div>
                  <div class="pp-example-list">
                    <div class="pp-example-item">
                      <span class="pp-ex-label">▶ Tây Thi – MCK</span>
                      <span class="pp-ex-url">https://www.youtube.com/watch?v=s0JICY2omJY&list=RDs0JICY2omJY&start_radio=1</span>
                    </div>
                    <div class="pp-example-item">
                      <span class="pp-ex-label">▶ Dừng Làm Trái Tim Anh Đau – Sơn Tùng M-TP</span>
                      <span class="pp-ex-url">https://www.youtube.com/watch?v=abPmZCZZrFA&list=RDabPmZCZZrFA&start_radio=1</span>
                    </div>
                    <div class="pp-example-item">
                      <span class="pp-ex-label">▶ See Tình – Hoàng Thùy Linh</span>
                      <span class="pp-ex-url">https://www.youtube.com/watch?v=gJHSDZfJrRY&list=RDgJHSDZfJrRY&start_radio=1</span>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_info:
            if not submitted_url:
                st.markdown(
                    """
                    <div class="pp-placeholder-card">
                      <div class="pp-placeholder-icon">🎬</div>
                      <div class="pp-placeholder-title">Enter a URL to start analyzing</div>
                      <div class="pp-placeholder-sub">
                        Paste the YouTube video link into the box on the left and click <strong>Predict</strong>.
                        The system will automatically extract metadata and analyze 9 important features.
                      </div>
                      <div class="pp-placeholder-features">
                        <span>⏱️ Duration</span>
                        <span>🏷️ Topic</span>
                        <span>🌐 Region</span>
                        <span>❤️ Like Rate</span>
                        <span>💬 Comment Rate</span>
                        <span>👁️ Views</span>
                        <span>👤 Subscribers</span>
                        <span>🎞️ Video Count</span>
                        <span>🕐 Publish Hour</span>
                      </div>
                      <div class="pp-placeholder-model">
                        <span class="pp-pm-item"> XGBoost Classifier</span>
                        <span class="pp-pm-item"> Accuracy 93.68%</span>
                        <span class="pp-pm-item"> Trained on 1.17M+ records</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted_url:
            if not video_url.strip():
                st.warning("Please enter YouTube URL before analyzing.")
            else:
                try:
                    with st.spinner("Analyzing video..."):
                        video_id   = extract_video_id(video_url)
                        video_info = get_youtube_info(video_id)
                        features   = extract_features(video_info)
                        prob, reasoning = predict_trending(features)
                except ValueError as exc:
                    st.error(f"URL không hợp lệ: {exc}")
                except RuntimeError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Lỗi: {exc}")
                else:
                    st.session_state["predict_url"] = video_url
                    _render_results(prob, reasoning, features, video_info)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 – Custom Prediction
    # ════════════════════════════════════════════════════════════════════════
    with tab_manual:
        st.markdown(
            """
            <div class="pp-manual-desc">
              Enter video parameters directly to predict without a URL.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("manual_form"):
            c1, c2, c3 = st.columns(3, gap="medium")

            with c1:
                st.markdown("**Video Info**")
                m_duration = st.number_input(
                    "Duration (seconds)",
                    min_value=1, max_value=86400, value=300,
                    help="Video duration in seconds"
                )
                m_topic = st.selectbox(
                    "Topic",
                    options=KNOWN_TOPICS,
                    index=KNOWN_TOPICS.index("entertainment"),
                )
                m_publish_hour = st.slider(
                    "Publish hour (UTC)", min_value=0, max_value=23, value=14,
                    help="Video publish hour in UTC"
                )

            with c2:
                st.markdown("**Interaction Metrics**")
                m_views = st.number_input(
                    "Views", min_value=1, value=1_000_000, step=1000
                )
                m_likes = st.number_input(
                    "Likes", min_value=0, value=50_000, step=100
                )
                m_comments = st.number_input(
                    "Comments", min_value=0, value=2_000, step=10
                )

            with c3:
                st.markdown("**Channel Info**")
                m_subscribers = st.number_input(
                    "Subscribers", min_value=0, value=500_000, step=1000
                )
                m_video_count = st.number_input(
                    "Video count", min_value=1, value=100, step=1
                )
                m_region = st.selectbox(
                    "Region",
                    options=KNOWN_REGIONS,
                    index=KNOWN_REGIONS.index("Southeast Asia"),
                )

            submitted_manual = st.form_submit_button(
                "🎯  Predict", use_container_width=True, type="primary"
            )

        if submitted_manual:
            views    = max(int(m_views), 1)
            likes    = max(int(m_likes), 0)
            comments = max(int(m_comments), 0)

            like_rate    = likes / views
            comment_rate = comments / views

            features = {
                "subscriber_count": np.log1p(m_subscribers),
                "view_count":       np.log1p(views),
                "video_count":      np.log1p(m_video_count),
                "duration_seconds": np.log1p(m_duration),
                "like_rate":        like_rate,
                "comment_rate":     comment_rate,
                "publish_hour":     m_publish_hour,
                "publish_weekday_num": 2,
                "topic":            m_topic,
                "country_region":   m_region,
                "raw_views":        views,
                "raw_likes":        likes,
                "raw_comments":     comments,
            }

            # Build a fake video_info dict for display
            video_info = {
                "title":              "Custom Prediction",
                "channel_name":       "—",
                "thumbnail":          "",
                "views":              views,
                "likes":              likes,
                "comments":           comments,
                "subscriber_count":   m_subscribers,
                "channel_video_count": m_video_count,
                "duration":           m_duration,
            }

            try:
                with st.spinner("Đang tính toán..."):
                    prob, reasoning = predict_trending(features)
            except Exception as exc:
                st.error(f"Lỗi dự đoán: {exc}")
            else:
                _render_results(prob, reasoning, features, video_info)