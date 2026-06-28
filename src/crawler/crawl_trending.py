from datetime import datetime
import pandas as pd
import os

from googleapiclient.errors import HttpError

from config.api_config import YouTubeClient
from config.paths import RAW_VIDEO_PATH

# =============================
# INIT
# =============================

yt = YouTubeClient()

youtube = yt.get_client()

# =============================
# REGIONS
# =============================

REGIONS = [

    # North America
    "US", "CA", "MX", "GT", "CU", "DO", "PR", "HN", "SV", "NI", "CR", "PA",

    # South America
    "BR", "AR", "CL", "CO", "PE", "VE", "EC", "BO", "PY", "UY",

    # Europe
    "GB", "FR", "DE", "IT", "ES", "NL", "PL", "SE", "NO",
    "DK", "FI", "RU", "UA", "PT", "GR", "CZ", "RO", "HU",
    "CH", "IE", "AT", "BE", "BG", "HR", "SK", "RS", "LT",
    "LV", "EE", "SI", "BA", "MK", "AL", "ME", "MD", "BY",
    "LU", "MT", "IS", "CY",

    # Asia
    "VN", "JP", "KR", "CN", "HK", "TW", "IN", "PK",
    "BD", "ID", "TH", "MY", "PH", "SG", "LK", "NP",
    "MM", "KH", "LA", "MN", "KZ", "UZ", "AZ", "GE",
    "AF", "IR", "IQ",

    # Oceania
    "AU", "NZ", "PG", "FJ",

    # Middle East
    "AE", "SA", "IL", "TR", "EG", "JO", "LB", "KW", "QA", "BH", "OM", "YE",

    # Africa
    "ZA", "NG", "KE", "MA", "GH", "CM", "TZ", "ET", "SN",
    "CI", "TN", "DZ", "LY", "UG", "ZW", "MZ", "AO",
]

# =============================
# LOAD EXISTING IDS
# =============================

existing_ids = set()

if os.path.exists(RAW_VIDEO_PATH):

    old_df = pd.read_csv(RAW_VIDEO_PATH)

    existing_ids = set(
        old_df["video_id"]
        .astype(str)
    )

# =============================
# CRAWL
# =============================

videos = []

crawl_time = datetime.utcnow()

for region in REGIONS:

    print(f"\nTrending videos: {region}")

    next_page_token = None

    while True:

        try:

            request = youtube.videos().list(
                part="snippet",
                chart="mostPopular",
                regionCode=region,
                maxResults=50,
                pageToken=next_page_token
            )

            response = request.execute()

        except HttpError as e:

            if "quotaExceeded" in str(e):

                yt.switch_key()

                youtube = yt.get_client()

                continue

            print(e)

            break

        items = response.get("items", [])

        if not items:
            break

        for item in items:

            snippet = item["snippet"]

            video_id = item["id"]

            # =============================
            # UNIQUE VIDEO ONLY
            # =============================

            if video_id in existing_ids:
                continue

            videos.append({

                "video_id": video_id,

                "title": snippet.get("title"),

                "description": snippet.get("description"),

                "channel_id": snippet.get("channelId"),

                "channel_title": snippet.get("channelTitle"),

                "publish_time": snippet.get("publishedAt"),

                "thumbnail": snippet.get("thumbnails", {})
                .get("default", {})
                .get("url"),

                "keyword": "trending",

                "topic": "trending",

                "source": "trending",

                "discover_time": crawl_time
            })

            existing_ids.add(video_id)

        # =============================
        # PAGINATION
        # =============================

        next_page_token = response.get(
            "nextPageToken"
        )

        if not next_page_token:
            break

# =============================
# SAVE CSV
# =============================

new_df = pd.DataFrame(videos)

if os.path.exists(RAW_VIDEO_PATH):

    old_df = pd.read_csv(RAW_VIDEO_PATH)

    new_df = pd.concat(
        [old_df, new_df],
        ignore_index=True
    )

new_df = new_df.drop_duplicates(
    subset="video_id"
)

new_df.to_csv(
    RAW_VIDEO_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")
print("New videos:", len(videos))
print("Total videos:", len(new_df))
