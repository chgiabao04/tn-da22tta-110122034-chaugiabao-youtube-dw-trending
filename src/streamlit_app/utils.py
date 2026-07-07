import re
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import numpy as np

load_dotenv()

# ---------------------------------------------------------------------------
# API Key rotation
# ---------------------------------------------------------------------------

def _get_api_keys():
    """Đọc tất cả YOUTUBE_API_KEY_1 ... YOUTUBE_API_KEY_N từ .env"""
    keys = []
    i = 1
    while True:
        key = os.getenv(f"YOUTUBE_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1
    return keys

API_KEYS = _get_api_keys()
_key_index = 0

def _get_key():
    """Round-robin qua các API keys."""
    global _key_index
    if not API_KEYS:
        raise RuntimeError("Không tìm thấy API key nào trong .env (YOUTUBE_API_KEY_1, ...)")
    key = API_KEYS[_key_index % len(API_KEYS)]
    _key_index += 1
    return key

# ---------------------------------------------------------------------------
# Mapping tables
# ---------------------------------------------------------------------------

COUNTRY_TO_REGION = {
    # North America
    "US": "North America", "CA": "North America", "MX": "North America",
    # Southeast Asia
    "VN": "Southeast Asia", "TH": "Southeast Asia", "ID": "Southeast Asia",
    "MY": "Southeast Asia", "SG": "Southeast Asia", "PH": "Southeast Asia",
    "KH": "Southeast Asia", "LA": "Southeast Asia", "MM": "Southeast Asia",
    # Western Europe
    "GB": "Western Europe", "DE": "Western Europe", "FR": "Western Europe",
    "IT": "Western Europe", "ES": "Western Europe", "NL": "Western Europe",
    "BE": "Western Europe", "AT": "Western Europe", "CH": "Western Europe",
    "SE": "Western Europe", "NO": "Western Europe", "DK": "Western Europe",
    "FI": "Western Europe", "PT": "Western Europe", "GR": "Western Europe",
    # Eastern Europe
    "RU": "Eastern Europe", "UA": "Eastern Europe", "PL": "Eastern Europe",
    "CZ": "Eastern Europe", "SK": "Eastern Europe", "HU": "Eastern Europe",
    "RO": "Eastern Europe", "BG": "Eastern Europe", "HR": "Eastern Europe",
    "RS": "Eastern Europe", "BY": "Eastern Europe",
    # East Asia
    "CN": "East Asia", "JP": "East Asia", "KR": "East Asia", "TW": "East Asia",
    # South Asia
    "IN": "South Asia", "BD": "South Asia", "PK": "South Asia",
    "NP": "South Asia", "LK": "South Asia",
    # Central Asia
    "KZ": "Central Asia", "UZ": "Central Asia", "TM": "Central Asia",
    "KG": "Central Asia", "TJ": "Central Asia",
    # Middle East
    "SA": "Middle East", "AE": "Middle East", "IR": "Middle East",
    "IQ": "Middle East", "EG": "Middle East", "IL": "Middle East",
    # Africa
    "ZA": "Africa", "NG": "Africa", "KE": "Africa", "GH": "Africa",
    # South America
    "BR": "South America", "AR": "South America", "CL": "South America",
    "CO": "South America", "PE": "South America",
    # Oceania
    "AU": "Oceania", "NZ": "Oceania",
}

CATEGORY_ID_TO_TOPIC = {
    1: "film", 2: "autos", 10: "music", 15: "pets", 17: "sports",
    18: "short", 19: "travel", 20: "gaming", 21: "videoblogging",
    22: "people", 23: "comedy", 24: "entertainment", 25: "news",
    26: "howto", 27: "education", 28: "science", 29: "technology",
    30: "movies", 31: "animation", 32: "action", 33: "classics",
    34: "comedy", 35: "documentary", 36: "drama", 37: "familyfriendly",
    38: "foreign", 39: "horror", 40: "scifi", 41: "thriller",
    42: "shorts", 43: "shows", 44: "trailers", 45: "watches",
}

CATEGORY_TO_ML_TOPIC = {
    "film": "entertainment", "autos": "technology", "music": "music",
    "pets": "animals", "sports": "sports", "travel": "travel",
    "gaming": "gaming", "videoblogging": "vlog", "people": "vlog",
    "comedy": "entertainment", "entertainment": "entertainment",
    "news": "technology", "howto": "education", "education": "education",
    "science": "education", "technology": "technology", "movies": "entertainment",
    "animation": "entertainment", "action": "entertainment", "classics": "entertainment",
    "documentary": "entertainment", "drama": "entertainment", "familyfriendly": "kids",
    "foreign": "entertainment", "horror": "entertainment", "scifi": "entertainment",
    "thriller": "entertainment", "shorts": "entertainment", "shows": "entertainment",
    "trailers": "entertainment",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([A-Za-z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Invalid YouTube URL: {url}")


def _parse_duration(iso_str):
    """Convert ISO 8601 duration (PT1H2M3S) → seconds."""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_str or "PT0S")
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s

# ---------------------------------------------------------------------------
# Main fetch function — dùng YouTube Data API v3, không dùng yt-dlp
# ---------------------------------------------------------------------------

def get_youtube_info(video_id):
    """
    Lấy metadata video + channel qua YouTube Data API v3.
    Dùng key rotation từ .env (YOUTUBE_API_KEY_1 ... YOUTUBE_API_KEY_N).
    """
    key = _get_key()
    base = "https://www.googleapis.com/youtube/v3"

    # --- Video info ---
    video_resp = requests.get(
        f"{base}/videos",
        params={
            "part": "snippet,statistics,contentDetails",
            "id": video_id,
            "key": key,
        },
        timeout=10,
    ).json()

    if not video_resp.get("items"):
        raise ValueError(f"Không tìm thấy video: {video_id}")

    item     = video_resp["items"][0]
    snippet  = item["snippet"]
    stats    = item.get("statistics", {})
    details  = item.get("contentDetails", {})
    channel_id = snippet["channelId"]

    # --- Channel info ---
    channel_resp = requests.get(
        f"{base}/channels",
        params={
            "part": "snippet,statistics",
            "id": channel_id,
            "key": key,
        },
        timeout=10,
    ).json()

    ch         = channel_resp["items"][0] if channel_resp.get("items") else {}
    ch_stats   = ch.get("statistics", {})
    ch_snippet = ch.get("snippet", {})

    # published_at: giữ full ISO string "2023-04-01T15:30:00Z" để extract giờ chính xác
    published_raw = snippet.get("publishedAt", "")
    published_at  = published_raw  # full ISO, parse trong extract_features

    return {
        "video_id":           video_id,
        "title":              snippet.get("title", "Unknown"),
        "channel_name":       snippet.get("channelTitle", "Unknown"),
        "channel_id":         channel_id,
        "views":              int(stats.get("viewCount", 0) or 0),
        "likes":              int(stats.get("likeCount", 0) or 0),
        "comments":           int(stats.get("commentCount", 0) or 0),
        "duration":           _parse_duration(details.get("duration", "PT0S")),
        "published_at":       published_at,
        "category_id":        int(snippet.get("categoryId", 24)),
        "thumbnail":          snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "subscriber_count":   int(ch_stats.get("subscriberCount", 0) or 0),
        "channel_video_count":int(ch_stats.get("videoCount", 0) or 0),
        "channel_view_count":  int(ch_stats.get("viewCount", 0) or 0),
        "channel_country":    ch_snippet.get("country", "US"),
    }

# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def extract_features(video_info):
    """Extract và transform features cho model prediction."""

    views    = max(video_info["views"], 1)
    likes    = max(video_info["likes"], 1)
    comments = max(video_info["comments"], 1)

    like_rate    = likes / views
    comment_rate = comments / views

    pub_date = video_info.get("published_at", "")
    if pub_date:
        try:
            # publishedAt từ API là UTC ISO: "2023-04-01T15:30:00Z"
            dt = datetime.strptime(pub_date[:19], "%Y-%m-%dT%H:%M:%S")
            publish_hour        = dt.hour
            publish_weekday_num = dt.weekday()
        except ValueError:
            try:
                # fallback: format cũ "20230401"
                dt = datetime.strptime(pub_date[:8], "%Y%m%d")
                publish_hour        = 12
                publish_weekday_num = dt.weekday()
            except ValueError:
                publish_hour        = 12
                publish_weekday_num = 2
    else:
        publish_hour        = 12
        publish_weekday_num = 2

    category_id  = video_info.get("category_id", 24)
    category_name = CATEGORY_ID_TO_TOPIC.get(int(category_id), "entertainment")
    topic        = CATEGORY_TO_ML_TOPIC.get(category_name, "entertainment")

    country_code   = (video_info.get("channel_country") or "US").upper()
    country_region = COUNTRY_TO_REGION.get(country_code, "North America")

    subscriber_count_log = np.log1p(video_info["subscriber_count"])
    video_count_log      = np.log1p(video_info["channel_video_count"])
    duration_log         = np.log1p(video_info["duration"])
    view_count_log = np.log1p(video_info["views"])

    return {
        "subscriber_count":   subscriber_count_log,
        "view_count":         view_count_log,
        "video_count":        video_count_log,
        "duration_seconds":   duration_log,
        "like_rate":          like_rate,
        "comment_rate":       comment_rate,
        "publish_hour":       publish_hour,
        "publish_weekday_num":publish_weekday_num,
        "topic":              topic,
        "country_region":     country_region,
        # Raw values for display only
        "raw_views":   views,
        "raw_likes":   likes,
        "raw_comments":comments,
    }