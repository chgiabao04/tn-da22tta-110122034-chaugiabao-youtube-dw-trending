import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = r"D:\tn-da22tta-110122034-chaugiabao-youtube-dw-trending\src\analysis\data\cleaned_video.csv"

RED = "#E8001D"
GRAY = "#3A3A3A"
PLOT_FONT = dict(family="DM Sans, sans-serif", color="#E8E8E8", size=12)

WEEKDAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_MAP = {
    "monday": "Mon", "mon": "Mon",
    "tuesday": "Tue", "tue": "Tue",
    "wednesday": "Wed", "wed": "Wed",
    "thursday": "Thu", "thu": "Thu",
    "friday": "Fri", "fri": "Fri",
    "saturday": "Sat", "sat": "Sat",
    "sunday": "Sun", "sun": "Sun",
}


USECOLS = [
    "video_id", "channel_id", "is_trending", "snapshot_time",
    "topic", "country_region", "publish_weekday", "publish_hour",
    "views", "likes", "comments", "subscriber_count", "duration_seconds",
    "date",
]


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, usecols=USECOLS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data
def video_level(df: pd.DataFrame) -> pd.DataFrame:
    """One row per video (first snapshot) so multi-snapshot rows don't
    inflate counts/distributions."""
    sort_col = "snapshot_time" if "snapshot_time" in df.columns else "date"
    return df.sort_values(sort_col).drop_duplicates("video_id", keep="first").copy()


def _base_layout(height: int = 280, margin: dict | None = None) -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=PLOT_FONT,
        margin=margin or dict(l=10, r=10, t=10, b=10),
        height=height,
    )


def render_dashboard() -> None:
    st.markdown('<div class="ov-page"></div>', unsafe_allow_html=True)

    df = load_data()
    dfv = video_level(df)

    with st.container(key="overview_content"):
        _render_header(df)
        with st.container(key="ov_kpi_row"):
            _render_kpis(dfv)

        col1, col2 = st.columns(2)
        with col1:
            with st.container(key="ov_card_trend"):
                _render_trend_donut(dfv)
        with col2:
            with st.container(key="ov_card_topic"):
                _render_top_topics(dfv)

        col3, col4 = st.columns(2)
        with col3:
            with st.container(key="ov_card_weekday"):
                _render_weekday(dfv)
        with col4:
            with st.container(key="ov_card_hour"):
                _render_hour(dfv)

        col5, col6 = st.columns(2)
        with col5:
            with st.container(key="ov_card_region"):
                _render_region(dfv)
        with col6:
            with st.container(key="ov_card_corr"):
                _render_correlation(dfv)


def _render_header(df: pd.DataFrame) -> None:
    date_min, date_max = df["date"].min(), df["date"].max()
    date_range = (
        f"{date_min:%d/%m/%Y} - {date_max:%d/%m/%Y}"
        if pd.notna(date_min) and pd.notna(date_max)
        else "—"
    )
    st.markdown(
        f"""
        <div class="ov-header">
            <div>
                <div class="ov-eyebrow">— DASHBOARD</div>
                <div class="ov-title">YOUTUBE DATASET <span class="accent">OVERVIEW</span></div>
                <div class="ov-subtitle">Overview of YouTube data collected from YouTube Data API v3 and stored in the Data Warehouse.</div>
            </div>
            <div class="ov-daterange">📅 {date_range}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _render_kpis(dfv: pd.DataFrame) -> None:
    total_videos = dfv["video_id"].nunique()
    total_channels = dfv["channel_id"].nunique()
    # Tổng số comment thực tế đã crawl
    total_comments = 6652295
    trending_rate = dfv["is_trending"].mean() * 100

    sparklines = [
        "M0,32 C25,28 45,18 70,22 C95,26 115,12 140,10 C160,8 180,16 200,12",
        "M0,28 C20,24 40,30 65,22 C90,14 110,20 135,16 C158,12 180,22 200,16",
        "M0,30 C30,26 50,18 75,20 C100,22 118,8 142,6 C162,4 182,16 200,14",
        "M0,24 C22,20 44,28 68,22 C92,16 112,10 136,14 C158,18 180,8 200,6",
    ]
    VIDEO_ICON = """
<svg viewBox="0 0 24 24" width="22" height="22" fill="none"
stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<rect x="2" y="4" width="20" height="16" rx="3"/>
<polygon points="10,8 16,12 10,16"/>
</svg>
"""
    
    CHANNEL_ICON = """
<svg viewBox="0 0 24 24" width="22" height="22" fill="none"
stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="8" cy="8" r="3"/>
<path d="M2 20c0-4 3-6 6-6s6 2 6 6"/>
<circle cx="17" cy="8" r="2.5"/>
<path d="M14.5 19.5c.7-3 2.9-5 5.3-5 1.6 0 2.7.6 3.7 1.6"/>
</svg>
"""
    COMMENT_ICON = """
<svg viewBox="0 0 24 24" width="22" height="22" fill="none"
stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z"/>
<path d="M8 10h8"/>
<path d="M8 13h5"/>
</svg>
"""
    TREND_ICON = """
<svg viewBox="0 0 24 24" width="22" height="22" fill="none"
stroke="#E8001D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 2s4 4 4 8a4 4 0 0 1-8 0c0-2 1-4 4-8z"/>
<path d="M12 14c1 1 2 2 2 4a2 2 0 1 1-4 0c0-1.2.5-2.2 2-4z"/>
</svg>
"""
    cards = [
        (VIDEO_ICON, "TOTAL VIDEO", f"{total_videos:,}", "Videos collected", sparklines[0]),
        (CHANNEL_ICON, "TOTAL CHANNELS", f"{total_channels:,}", "Channels collected", sparklines[1]),
        (COMMENT_ICON, "TOTAL COMMENTS", f"{total_comments / 1_000_000:.1f}M+", "Comments collected", sparklines[2]),
        (TREND_ICON, "TRENDING RATE", f"{trending_rate:.1f}%", "Trending videos", sparklines[3]),
    ]
    cells = "".join(
        f'<td style="padding: 0 0.6rem; vertical-align: top;">' +
        f'<div class="ov-kpi-card" style="position:relative; padding-bottom:0.5rem; overflow:hidden;">' +
        f'<span class="ov-kpi-label" style="display:block; margin-bottom:0.75rem;">{label}</span>' +
        f'<span class="ov-kpi-value" style="display:block;">{value}</span>' +
        f'<span class="ov-kpi-sub" style="display:block; margin-bottom:0.9rem;">{sub}</span>' +
        f'<div style="position:absolute; bottom:0; left:0; right:0; line-height:0;">' +
        f'<svg viewBox="0 0 200 40" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:44px; display:block;">' +
        f'<defs><linearGradient id="sg{i}" x1="0" y1="0" x2="0" y2="1">' +
        f'<stop offset="0%" stop-color="#E8001D" stop-opacity="0.2"/>' +
        f'<stop offset="100%" stop-color="#E8001D" stop-opacity="0"/>' +
        f'</linearGradient></defs>' +
        f'<path d="{spark} L200,40 L0,40 Z" fill="url(#sg{i})"/>' +
        f'<path d="{spark}" stroke="#E8001D" stroke-width="1.8" fill="none"/>' +
        f'</svg></div></div></td>'
        for i, (icon, label, value, sub, spark) in enumerate(cards)
    )
    st.markdown(
        '<style>.ov-kpi-card::after { display: none !important; }</style>' +
        f'<table style="width:100%; table-layout:fixed;"><tr>{cells}</tr></table>',
        unsafe_allow_html=True,
    )


def _render_trend_donut(dfv: pd.DataFrame) -> None:
    st.markdown(
        '<div class="ov-card-title"><span>DISTRIBUTION TRENDING VS NON-TRENDING</span></div>',
        unsafe_allow_html=True,
    )
    total = len(dfv)
    trending = int(dfv["is_trending"].sum())
    non_trending = total - trending

    fig = go.Figure(
        go.Pie(
            labels=["Trending", "Non-Trending"],
            values=[trending, non_trending],
            hole=0.68,
            sort=False,
            textinfo="none",
            marker=dict(colors=[RED, GRAY], line=dict(color="#131313", width=2)),
        )
    )
    fig.update_layout(
        **_base_layout(320),
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{total:,}</b><br><span style='font-size:11px;color:rgba(255,255,255,0.45)'>TOTAL</span>",
                x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="#fff"),
            )
        ],
    )

    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with c2:
        trend_pct = trending / total * 100 if total else 0
        st.markdown(
            f"""
            <div class="ov-legend">
                <div class="ov-legend-row">
                    <span class="ov-legend-dot" style="background:{RED}"></span>
                    Trending<span class="ov-legend-val">{trending:,} ({trend_pct:.1f}%)</span>
                </div>
                <div class="ov-legend-row">
                    <span class="ov-legend-dot" style="background:{GRAY}"></span>
                    Non-Trending<span class="ov-legend-val">{non_trending:,} ({100 - trend_pct:.1f}%)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_top_topics(dfv: pd.DataFrame) -> None:
    st.markdown(
        '<div class="ov-card-title"><span>TOP 10 TOPICS VIDEO</span></div>',
        unsafe_allow_html=True,
    )
    counts = dfv["topic"].value_counts().head(10).sort_values()
    fig = go.Figure(
        go.Bar(
            x=counts.values,
            y=counts.index,
            orientation="h",
            marker=dict(color=RED),
            text=[f"{v:,}" for v in counts.values],
            textposition="outside",
            textfont=dict(color="#E8E8E8", size=11),
        )
    )
    fig.update_layout(
        **_base_layout(320, margin=dict(l=10, r=40, t=10, b=10)),
        xaxis=dict(visible=False),
        yaxis=dict(showgrid=False, color="#E8E8E8"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_weekday(dfv: pd.DataFrame) -> None:
    st.markdown(
        '<div class="ov-card-title"><span>DISTRIBUTION VIDEO BY DAY OF WEEK</span></div>',
        unsafe_allow_html=True,
    )
    raw = dfv["publish_weekday"].astype(str).str.strip()
    wd = raw.str.lower().map(WEEKDAY_MAP).fillna(raw.str[:3].str.title())
    counts = wd.value_counts().reindex(WEEKDAY_ORDER).fillna(0)

    fig = go.Figure(go.Bar(x=WEEKDAY_ORDER, y=counts.values, marker=dict(color=RED)))
    fig.update_layout(
        **_base_layout(260),
        xaxis=dict(showgrid=False, color="#E8E8E8"),
        yaxis=dict(
            title="Number of Videos",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            color="rgba(255,255,255,0.45)",
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_hour(dfv: pd.DataFrame) -> None:
    st.markdown(
        '<div class="ov-card-title"><span>Publish Hour Distribution (UTC)</span></div>',
        unsafe_allow_html=True,
    )
    counts = dfv["publish_hour"].value_counts().reindex(range(24)).fillna(0)
    fig = go.Figure(
        go.Scatter(
            x=list(range(24)),
            y=counts.values,
            mode="lines+markers",
            line=dict(color=RED, width=2),
            marker=dict(color=RED, size=5),
            fill="tozeroy",
            fillcolor="rgba(232,0,29,0.12)",
        )
    )
    fig.update_layout(
        **_base_layout(260),
        xaxis=dict(title="Publish Hour", showgrid=False, color="rgba(255,255,255,0.45)", dtick=3),
        yaxis=dict(
            title="Number of Videos",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            color="rgba(255,255,255,0.45)",
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_region(dfv: pd.DataFrame) -> None:
    st.markdown(
        '<div class="ov-card-title"><span>DISTRIBUTION VIDEO BY REGION</span></div>',
        unsafe_allow_html=True,
    )
    counts = dfv["country_region"].value_counts().sort_values()
    fig = go.Figure(
        go.Bar(
            x=counts.values,
            y=counts.index,
            orientation="h",
            marker=dict(color=RED),
            text=[f"{v:,}" for v in counts.values],
            textposition="outside",
            textfont=dict(color="#E8E8E8", size=11),
        )
    )
    fig.update_layout(
        **_base_layout(320, margin=dict(l=10, r=50, t=10, b=10)),
        xaxis=dict(visible=False),
        yaxis=dict(showgrid=False, color="#E8E8E8"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_correlation(dfv: pd.DataFrame) -> None:
    st.markdown(
        '<div class="ov-card-title"><span>CORRELATION MATRIX OF FEATURES</span></div>',
        unsafe_allow_html=True,
    )
    cols = ["views", "likes", "comments", "subscriber_count", "duration_seconds"]
    labels = ["view_count", "like_count", "comment_count", "subscriber_count", "duration_seconds"]
    corr = dfv[cols].corr().values

    fig = go.Figure(
        go.Heatmap(
            z=corr,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale=[[0, "#3A3A3A"], [0.5, "#7A1018"], [1, RED]],
            text=[[f"{v:.2f}" for v in row] for row in corr],
            texttemplate="%{text}",
            textfont=dict(size=11, color="#fff"),
            colorbar=dict(thickness=12, outlinewidth=0, tickfont=dict(color="rgba(255,255,255,0.5)", size=10)),
        )
    )
    fig.update_layout(
        **_base_layout(320, margin=dict(l=10, r=10, t=10, b=70)),
        xaxis=dict(showgrid=False, color="#E8E8E8", side="bottom"),
        yaxis=dict(showgrid=False, color="#E8E8E8", autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})