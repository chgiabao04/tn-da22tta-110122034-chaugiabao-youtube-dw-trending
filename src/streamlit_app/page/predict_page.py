import html
import math

import streamlit as st

from predict_model import predict_trending
from utils import extract_features, extract_video_id, get_youtube_info


WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

# Static feature-importance ranking for the 8 features used by the
# production XGBoost model (subscriber_count, view_count, video_count,
# duration_seconds, like_rate, comment_rate, topic, country_region).
FEATURE_IMPORTANCE = [
    ("⏱️", "duration_seconds", 46),
    ("🏷️", "topic", 23),
    ("🌐", "country_region", 9),
    ("💬", "comment_rate", 7),
    ("❤️", "like_rate", 4),
    ("👁️", "view_count", 4),
    ("👤", "subscriber_count", 3),
    ("🎞️", "video_count", 2),
]


def _fmt_big(value: int | float) -> str:
    value = int(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _fmt_duration(seconds: int | float) -> str:
    seconds = int(seconds or 0)
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} giờ {minutes} phút"
    if minutes:
        return f"{minutes} phút {sec} giây"
    return f"{sec} giây"


def _repair_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    try:
        return text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return text


def _safe(text: object) -> str:
    return html.escape(str(text or ""))


def _feature_row(icon: str, label: str, value: str, width: float | None = None) -> str:
    """
    Dùng <table> thay <div> để tránh Streamlit sanitize nested divs.
    """
    bar_cell = ""
    if width is not None:
        width = max(3, min(100, width))
        bar_cell = (
            f'<td style="width:45%;padding:0 10px;">'
            f'<span style="display:block;height:6px;background:rgba(255,255,255,0.08);border-radius:999px;overflow:hidden;">'
            f'<span style="display:block;height:100%;width:{width:.0f}%;background:#E8001D;border-radius:999px;"></span>'
            f'</span></td>'
        )
    else:
        bar_cell = '<td style="width:45%;padding:0 10px;"></td>'

    return (
        f'<tr style="border-bottom:1px solid rgba(255,255,255,0.07);">'
        f'<td style="padding:9px 4px;white-space:nowrap;font-size:0.8rem;color:rgba(255,255,255,0.6);min-width:160px;">'
        f'<span style="margin-right:6px;">{icon}</span>{_safe(label)}'
        f'</td>'
        f'{bar_cell}'
        f'<td style="padding:9px 4px;text-align:right;font-weight:700;font-size:0.8rem;color:#fff;white-space:nowrap;">'
        f'{_safe(value)}'
        f'</td>'
        f'</tr>'
    )


def _gauge_html(pct: float, color: str, level: str) -> str:
    # NOTE: deliberately written as compact concatenation — NOT a multiline
    # triple-quoted string. The trailing \n + spaces that triple-quotes create
    # causes a "blank line → 4-space-indented content" sequence in the parent
    # f-string which the Markdown parser (even with unsafe_allow_html=True)
    # treats as a <pre><code> block, rendering raw HTML as visible text.
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
        f'<span>{icon}</span>'
        f'<strong>{_safe(value)}</strong>'
        f'<small>{_safe(label)}</small>'
        f'</div>'
    )


def _result_card(title_icon_label: str, body_html: str, badge: str | None = None, extra_class: str = "") -> str:
    """
    One cell of the results grid. All six cells are concatenated into a
    single HTML string and emitted via ONE st.markdown() call so they are
    real DOM siblings inside .results-grid — this is what makes the
    CSS Grid (equal heights, 2-col layout, consistent gap) actually work.
    """
    badge_html = f'<span class="pp-badge">{_safe(badge)}</span>' if badge else ""
    classes = f"result-card pp-card {extra_class}".strip()
    return (
        f'<div class="{classes}">'
        f'<div class="pp-card-title">{title_icon_label}</div>'
        f'{badge_html}'
        f'{body_html}'
        f'</div>'
    )


# 8 feature cards shown on the landing (pre-prediction) state.
# (icon, accent_color, title, description)
FEATURE_CARDS = [
    ("⏱️", "#A855F7", "Thời lượng video",
     "Độ dài video (giây). Video quá ngắn hoặc quá dài có thể ảnh hưởng đến hiệu suất."),
    ("🏷️", "#E8001D", "Chủ đề (Topic)",
     "Chủ đề nội dung của video. Một số chủ đề có xu hướng lên trending cao hơn."),
    ("🌐", "#22C55E", "Quốc gia / Khu vực",
     "Quốc gia hoặc khu vực của video. Xu hướng trending khác nhau theo vùng."),
    ("❤️", "#FF4D6D", "Tỷ lệ like",
     "Tỷ lệ like trên lượt xem. Thể hiện mức độ yêu thích của khán giả."),
    ("💬", "#FF9800", "Tỷ lệ comment",
     "Tỷ lệ bình luận trên lượt xem. Đo lường mức độ tương tác của video."),
    ("👁️", "#3B82F6", "Lượt xem",
     "Tổng số lượt xem của video. Yếu tố quan trọng phản ánh độ phổ biến."),
    ("👥", "#8B5CF6", "Số lượng subscriber",
     "Số lượng người đăng ký của kênh. Kênh có nhiều subscriber thường có lợi thế."),
    ("🎥", "#06B6D4", "Số lượng video",
     "Tổng số video đã đăng trên kênh. Kênh hoạt động lâu dài thường ổn định hơn."),
]

LANDING_STRIP_ITEMS = [
    ("🧠", "Mô hình", "XGBoost Classifier"),
    ("🗃️", "Dữ liệu huấn luyện", "126K+ videos"),
    ("🎯", "Độ chính xác", "ROC-AUC 98.72%"),
    ("🛡️", "Bảo mật", "Không lưu trữ dữ liệu"),
    ("⚡", "Cập nhật", "Thời gian thực"),
]


def _model_strip_html(items: list[tuple[str, str, str]]) -> str:
    cells = "".join(
        f'<div><span>{icon}</span><div><strong>{_safe(title)}</strong><small>{_safe(sub)}</small></div></div>'
        for icon, title, sub in items
    )
    return f'<div class="pp-model-strip">{cells}</div>'


def _promo_card_html() -> str:
    return """
    <div class="pp-card pp-promo-card">
        <div class="pp-promo-illustration">
            <div class="pp-promo-play">▶</div>
            <div class="pp-promo-target">🎯</div>
            <div class="pp-promo-chart">📊</div>
        </div>
        <div class="pp-promo-title">AI phân tích 8 đặc trưng chính của video</div>
        <div class="pp-promo-sub">Sử dụng mô hình XGBoost được huấn luyện trên 126K+ video để dự đoán chính xác khả năng lên trending.</div>
    </div>
    """


def _features_grid_html() -> str:
    cards = "".join(
        f'<div class="pp-feature-card">'
        f'<div class="pp-fc-icon" style="background:{color}26;color:{color};">{icon}</div>'
        f'<div class="pp-fc-title">{_safe(title)}</div>'
        f'<div class="pp-fc-desc">{_safe(desc)}</div>'
        f'</div>'
        for icon, color, title, desc in FEATURE_CARDS
    )
    return f"""
    <div class="pp-features-section">
        <div class="pp-features-head">
            <div class="pp-features-title">8 ĐẶC TRƯNG ĐƯỢC PHÂN TÍCH BỞI AI</div>
            <div class="pp-features-underline"></div>
        </div>
        <div class="pp-features-grid">{cards}</div>
    </div>
    """


def render_predict() -> None:
    with st.container(key="predict_content"):
        _render_predict_body()


def _render_predict_body() -> None:
    st.markdown(
        """
        <div class="pp-page">
            <div class="pp-heading">
                <div class="pp-title" style="color:var(--red);">
                    <span class="pp-title-icon">🎯</span>
                    DỰ ĐOÁN KHẢ NĂNG LÊN TRENDING
                </div>
                <div class="pp-heading-underline"></div>
                <div class="pp-subtitle">Nhập URL video YouTube để dự đoán khả năng video xuất hiện trong danh sách thịnh hành.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    hero_left, hero_right = st.columns([1.3, 1], gap="medium")

    with hero_left:
        st.markdown(
            """
            <div class="pp-input-card">
                <div class="pp-input-label">URL video YouTube</div>
            """,
            unsafe_allow_html=True,
        )

        default_url = st.session_state.get("predict_url", "https://www.youtube.com/watch?v=WwiaxC49hNg")
        with st.form("prediction_form"):
            input_col, button_col = st.columns([5, 1], gap="small")
            with input_col:
                video_url = st.text_input(
                    "URL video YouTube",
                    value=default_url,
                    placeholder="Dán URL video YouTube vào đây...",
                    label_visibility="collapsed",
                )
            with button_col:
                submitted = st.form_submit_button("🎯 Dự đoán", use_container_width=True)

            st.markdown(
                """
                <div class="pp-examples">
                    <span class="pp-ex-label">Ví dụ:</span>
                    <span>youtu.be/dQw4w9WgXcQ</span>
                    <span>youtu.be/3JZ_D3ELwOQ</span>
                    <span>youtu.be/tgbNymZ7vqY</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)  # close pp-input-card

        st.markdown(
            """
            <div class="pp-sec-bar">
                <span>🛡️</span>
                <span class="pp-sec-text">Chúng tôi không lưu trữ dữ liệu của bạn. URL chỉ được sử dụng để trích xuất thông tin công khai.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_right:
        st.markdown(_promo_card_html(), unsafe_allow_html=True)

    if not submitted:
        st.markdown(_features_grid_html(), unsafe_allow_html=True)
        st.markdown(_model_strip_html(LANDING_STRIP_ITEMS), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)  # close pp-page
        return

    if not video_url:
        st.warning("Vui lòng nhập URL YouTube trước khi phân tích.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    try:
        with st.spinner("Đang phân tích video..."):
            video_id = extract_video_id(video_url)
            video_info = get_youtube_info(video_id)
            features = extract_features(video_info)
            prob, reasoning = predict_trending(features)
    except ValueError as exc:
        st.error(f"URL không hợp lệ: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    except RuntimeError as exc:
        st.error(str(exc))
        st.markdown("</div>", unsafe_allow_html=True)
        return
    except Exception as exc:
        st.error(f"Lỗi: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    prob_pct = prob * 100
    level = "CAO" if prob_pct >= 60 else ("TRUNG BÌNH" if prob_pct >= 35 else "THẤP")

    views            = int(video_info.get("views", 0) or 0)
    likes            = int(video_info.get("likes", 0) or 0)
    comments         = int(video_info.get("comments", 0) or 0)
    subscribers      = int(video_info.get("subscriber_count", 0) or 0)
    video_count      = int(video_info.get("channel_video_count", 0) or 0)
    channel_views    = int(video_info.get("channel_view_count", 0) or 0)
    duration_seconds = int(video_info.get("duration", 0) or 0)

    topic        = str(features.get("topic", "Unknown")).capitalize()
    region       = str(features.get("country_region", "Unknown"))
    weekday      = WEEKDAYS[int(features.get("publish_weekday_num", 0)) % 7]
    publish_hour = int(features.get("publish_hour", 12))
    reasoning_text = _repair_text(reasoning)

    like_rate_pct    = features["like_rate"] * 100
    comment_rate_pct = features["comment_rate"] * 100

    # Insight items: (text, is_warning)
    insight_items = [
        (
            f"Tỉ lệ like ({like_rate_pct:.2f}%) {'cao hơn mức trung bình của các video trong cùng chủ đề.' if like_rate_pct >= 2 else 'thấp hơn mức trung bình.'}",
            like_rate_pct < 2,
        ),
        (
            f"Tỉ lệ comment ({comment_rate_pct:.3f}%) {'cho thấy mức độ tương tác cộng đồng tốt.' if comment_rate_pct >= 0.05 else 'cho thấy mức độ tương tác cộng đồng còn thấp.'}",
            comment_rate_pct < 0.05,
        ),
        (
            f"Kênh có lượng subscriber {'ổn định' if subscribers >= 10_000 else 'còn ít, độ tin cậy còn thấp'} (~{_fmt_big(subscribers)} subscribers).",
            subscribers < 10_000,
        ),
        (
            f"Chủ đề {topic} {'có tỉ lệ xuất hiện trending cao.' if prob_pct >= 50 else 'có tỉ lệ xuất hiện trending chưa cao.'}",
            prob_pct < 50,
        ),
    ]
    conclusion = (
        "Tổng thể video có khả năng lên trending CAO!"
        if prob_pct >= 60
        else ("Tổng thể video có khả năng lên trending TRUNG BÌNH." if prob_pct >= 35
              else "Tổng thể video có khả năng lên trending THẤP.")
    )

    verdict_color = "#22C55E" if prob_pct >= 60 else ("#FF9800" if prob_pct >= 35 else "#E8001D")

    thumbnail = _safe(video_info.get("thumbnail", ""))
    title     = _safe(video_info.get("title", "Unknown"))
    channel   = _safe(video_info.get("channel_name", "Unknown"))

    # ── ROW 1, LEFT: VIDEO INFO ─────────────────────────────────────────────
    # NOTE: thumbnail intentionally capped at 160px here (not the global 260px).
    # In the 2-col results grid each card is ~half the viewport, and at 260px
    # the remaining content area is only ~324px — too narrow for the tags and
    # the 4-cell stat row. 160px gives ~424px content width which comfortably
    # fits all tags on one line and the 4 stat cells without overflow.
    video_body = (
        f'<div class="pp-video-layout" style="align-items:flex-start;gap:1rem;">'
        f'<img src="{thumbnail}" alt="thumb" class="pp-thumb" style="width:160px;height:90px;border-radius:10px;object-fit:cover;flex-shrink:0;"/>'
        f'<div class="pp-video-body" style="flex:1;min-width:0;">'
        f'<div class="pp-video-title" style="font-size:1.1rem;margin-bottom:0.45rem;">{title}</div>'
        f'<div class="pp-channel" style="flex-wrap:nowrap;gap:0.4rem;margin-bottom:0.5rem;font-size:0.8rem;">'
        f'<span class="pp-avatar">{channel[:1].upper()}</span>'
        f'<strong style="color:var(--black);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px;">{channel}</strong>'
        f'<span style="flex-shrink:0;">•</span>'
        f'<span style="white-space:nowrap;">{_fmt_big(subscribers)} subscribers</span>'
        f'</div>'
        f'<div class="pp-tags" style="margin-bottom:0.85rem;gap:0.35rem;">'
        f'<span>Topic: {_safe(topic)}</span>'
        f'<span>Region: {_safe(region)}</span>'
        f'<span>Duration: {_safe(_fmt_duration(duration_seconds))}</span>'
        f'</div>'
        f'<div class="pp-stat-grid" style="grid-template-columns:repeat(4,1fr);gap:0.45rem;">'
        + _stat_box("👁️", _fmt_big(views), "Views")
        + _stat_box("👍", _fmt_big(likes), "Likes")
        + _stat_box("💬", _fmt_big(comments), "Comments")
        + _stat_box("👥", _fmt_big(subscribers), "Subscribers")
        + f'</div></div></div>'
    )

    # ── ROW 1, RIGHT: TRENDING PROBABILITY ──────────────────────────────────
    # score_body is built with string concatenation (NOT a multiline f-string)
    # to avoid the code-block trap: a blank-line-then-4-space-indented-line
    # inside a triple-quoted string triggers CommonMark's code-block rule even
    # with unsafe_allow_html=True. Also uses <table> for the bottom stat boxes
    # (consistent with _feature_row) because Streamlit strips bare <div> children
    # in certain HTML contexts.
    gauge_html = _gauge_html(prob_pct, verdict_color, level)
    _stat_td = (
        '<td style="text-align:center;background:rgba(255,255,255,0.05);'
        'border:1px solid rgba(255,255,255,0.08);border-radius:10px;'
        'padding:0.65rem 0.5rem;vertical-align:middle;">'
    )
    score_body = (
        f'<p style="text-align:center;font-size:0.85rem;color:var(--gray-700);margin:0 0 0.4rem;">'
        f'Video có khả năng lên trending <strong style="color:{verdict_color};">{_safe(level)}</strong></p>'
        + gauge_html
        + '<p style="text-align:center;font-size:0.75rem;color:var(--gray-500);margin:0.35rem 0 0.75rem;">'
        + 'Dựa trên phân tích 8 đặc trưng của video.<br/>Kết quả dự đoán bởi mô hình XGBoost.</p>'
        + '<table width="100%" cellspacing="0" cellpadding="0" style="border-collapse:separate;border-spacing:8px 0;"><tr>'
        + _stat_td
        + '<span style="font-size:1.05rem;display:block;margin-bottom:0.15rem;">📈</span>'
        + '<strong style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.35rem;font-weight:800;color:#fff;display:block;line-height:1;">98.72%</strong>'
        + '<small style="font-size:0.62rem;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:0.5px;">ROC-AUC (Model)</small>'
        + '</td>'
        + _stat_td
        + '<span style="font-size:1.05rem;display:block;margin-bottom:0.15rem;">🗃️</span>'
        + '<strong style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.35rem;font-weight:800;color:#fff;display:block;line-height:1;">126K+</strong>'
        + '<small style="font-size:0.62rem;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:0.5px;">Dữ liệu huấn luyện</small>'
        + '</td></tr></table>'
    )

    # ── ROW 2, LEFT: FEATURE IMPORTANCE ─────────────────────────────────────
    importance_rows = "".join(
        _feature_row(icon, name, f"{pct}%", pct)
        for icon, name, pct in FEATURE_IMPORTANCE
    )
    importance_body = f'<table style="width:100%;border-collapse:collapse;">{importance_rows}</table>'

    # ── ROW 2, RIGHT: ANALYZED FEATURES (8 DATA POINTS) ─────────────────────
    data_body = f"""
        <div class="pp-stat-grid">
            {_stat_box("⏱️", _fmt_duration(duration_seconds), "Duration")}
            {_stat_box("🏷️", topic, "Topic")}
            {_stat_box("🌐", region, "Region")}
            {_stat_box("❤️", f"{like_rate_pct:.2f}%", "Like Rate")}
            {_stat_box("💬", f"{comment_rate_pct:.3f}%", "Comment Rate")}
            {_stat_box("👁️", _fmt_big(views), "View Count")}
            {_stat_box("👤", _fmt_big(subscribers), "Subscriber Count")}
            {_stat_box("🎞️", _fmt_big(video_count), "Video Count")}
        </div>
    """

    # ── ROW 3, LEFT: AI INSIGHT ──────────────────────────────────────────────
    insight_rows = "".join(
        (
            f'<tr><td style="padding:8px 0;border-bottom:1px solid var(--border);font-size:0.84rem;color:var(--gray-700);">'
            f'<span style="color:{"#FF9800" if is_warn else "#22C55E"};font-weight:700;margin-right:8px;">{"⚠" if is_warn else "✓"}</span>'
            f'{_safe(text)}</td></tr>'
        )
        for text, is_warn in insight_items
    )
    insight_body = f"""
        <table style="width:100%;border-collapse:collapse;">{insight_rows}</table>
        <p style="margin:12px 0 10px;font-size:0.78rem;color:var(--gray-500);background:rgba(255,255,255,0.04);border-left:3px solid var(--red);border-radius:0 8px 8px 0;padding:8px 12px;">{_safe(reasoning_text)}</p>
        <p class="pp-conclusion" style="margin:0;border-radius:12px;padding:12px 14px;font-size:0.85rem;font-weight:700;">✦ Kết luận: {_safe(conclusion)}</p>
    """

    # ── ROW 3, RIGHT: MODEL INFORMATION ─────────────────────────────────────
    modelinfo_body = """
        <div class="pp-modelinfo-grid">
            <div>
                <div class="pp-modelinfo-label">Model</div>
                <div class="pp-modelinfo-value">XGBoost Classifier</div>
            </div>
            <div>
                <div class="pp-modelinfo-label">Test Size</div>
                <div class="pp-modelinfo-value">31,615</div>
            </div>
            <div>
                <div class="pp-modelinfo-label">Features</div>
                <div class="pp-modelinfo-value">8</div>
            </div>
            <div>
                <div class="pp-modelinfo-label">ROC-AUC</div>
                <div class="pp-modelinfo-value">0.9872</div>
            </div>
            <div>
                <div class="pp-modelinfo-label">Train Size</div>
                <div class="pp-modelinfo-value">126,458</div>
            </div>
            <div>
                <div class="pp-modelinfo-label">Avg Precision</div>
                <div class="pp-modelinfo-value">0.9634</div>
            </div>
        </div>
    """

    # ── ASSEMBLE: success banner + the ENTIRE results grid in ONE markdown
    #    call, so it is one real DOM tree and CSS Grid can actually own the
    #    layout, gaps, and equal-height behaviour across all six cards. ──────
    st.markdown(
        f"""
        <div class="pp-success-banner">
            <div class="pp-success-icon">✅</div>
            <div>
                <div class="pp-success-title">Phân tích hoàn tất</div>
                <div class="pp-success-sub">Dự đoán dựa trên phân tích 8 đặc trưng của video</div>
            </div>
        </div>
        <section class="results-section">
            <div class="results-grid">
                {_result_card("🎬 THÔNG TIN VIDEO", video_body, badge="AI ANALYSIS", extra_class="pp-video-card")}
                {_result_card("🎯 KHẢ NĂNG LÊN TRENDING", score_body, extra_class="pp-score")}
                {_result_card("📊 FEATURE IMPORTANCE", importance_body)}
                {_result_card("📋 DỮ LIỆU PHÂN TÍCH (8 ĐẶC TRƯNG)", data_body)}
                {_result_card("🤖 AI INSIGHT", insight_body, extra_class="pp-insight")}
                {_result_card("🧠 THÔNG TIN MÔ HÌNH", modelinfo_body)}
            </div>
        </section>
        <div class="pp-model-strip">
            <div><span>🧠</span><div><strong>Model</strong><small>XGBoost Classifier</small></div></div>
            <div><span>🗃️</span><div><strong>Train data</strong><small>126K+ videos</small></div></div>
            <div><span>🎯</span><div><strong>ROC-AUC</strong><small>98.72%</small></div></div>
            <div><span>🔄</span><div><strong>Cập nhật</strong><small>Thời gian thực</small></div></div>
            <div><span>🌐</span><div><strong>Coverage</strong><small>200+ quốc gia</small></div></div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )