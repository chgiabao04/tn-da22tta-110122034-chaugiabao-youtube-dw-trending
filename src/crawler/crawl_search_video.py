from datetime import datetime
import pandas as pd
import random
import os
import time

from googleapiclient.errors import HttpError

from config.api_config import YouTubeClient
from config.paths import (
    RAW_VIDEO_PATH,
    KEYWORD_PATH
)

# =============================
# INIT
# =============================

yt = YouTubeClient()

youtube = yt.get_client()

# =============================
# CHECK KEYWORD FILE
# =============================

if not os.path.exists(KEYWORD_PATH):

    raise FileNotFoundError(
        f"Keyword file not found: {KEYWORD_PATH}"
    )

# =============================
# LOAD KEYWORDS
# =============================

keyword_df = pd.read_csv(KEYWORD_PATH)

# =============================
# VALIDATE COLUMNS
# =============================

required_columns = [
    "keyword",
    "topic",
    "active"
]

missing_columns = [
    col for col in required_columns
    if col not in keyword_df.columns
]

if missing_columns:

    raise Exception(
        f"Missing columns: {missing_columns}"
    )

# =============================
# FILTER ACTIVE KEYWORDS
# =============================

keyword_df = keyword_df[
    keyword_df["active"] == 1
]

# =============================
# CHECK EMPTY KEYWORDS
# =============================

if keyword_df.empty:

    raise Exception(
        "No active keywords found"
    )

print(
    f"Loaded {len(keyword_df)} keywords"
)

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
# SEARCH CONFIG
# =============================

MAX_PAGES = 3

ORDERS = [
    "date",
    "relevance",
    "viewCount"
]

# =============================
# CRAWL
# =============================

videos = []

crawl_time = datetime.utcnow()

for _, row in keyword_df.iterrows():

    keyword = row["keyword"]

    topic = row["topic"]

    order = random.choice(ORDERS)

    print(f"\nKeyword: {keyword}")

    next_page_token = None

    for page in range(MAX_PAGES):

        while True:

            try:

                request = youtube.search().list(
                    q=keyword,
                    part="snippet",
                    type="video",
                    maxResults=50,
                    order=order,
                    pageToken=next_page_token
                )

                response = request.execute()

                break

            except HttpError as e:

                error_text = str(e)

                # =============================
                # SWITCH API KEY
                # =============================

                if "quotaExceeded" in error_text:

                    print(
                        "\nQuota exceeded..."
                    )

                    try:

                        yt.switch_key()

                        youtube = yt.get_client()

                        time.sleep(1)

                        continue

                    except Exception as switch_error:

                        print(switch_error)

                        raise Exception(
                            "All API keys exhausted"
                        )

                print(e)

                response = None

                break

        if response is None:
            break

        items = response.get("items", [])

        if not items:
            break

        for item in items:

            snippet = item["snippet"]

            video_id = item["id"]["videoId"]

            # =============================
            # SKIP DUPLICATE
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

                "keyword": keyword,

                "topic": topic,

                "source": "search",

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
print("New search videos:", len(videos))
print("Total videos:", len(new_df))