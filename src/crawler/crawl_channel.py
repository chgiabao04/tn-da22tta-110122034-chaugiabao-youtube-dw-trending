import pandas as pd
import os
import time

from googleapiclient.errors import HttpError

from config.api_config import YouTubeClient

from config.paths import (
    RAW_VIDEO_PATH,
    RAW_CHANNEL_PATH
)

# =============================
# INIT
# =============================

yt = YouTubeClient()

youtube = yt.get_client()

# =============================
# CHECK RAW VIDEO FILE
# =============================

if not os.path.exists(RAW_VIDEO_PATH):

    raise FileNotFoundError(
        f"File not found: {RAW_VIDEO_PATH}"
    )

# =============================
# LOAD VIDEOS
# =============================

video_df = pd.read_csv(
    RAW_VIDEO_PATH
)

if video_df.empty:

    raise Exception(
        "raw_video.csv is empty"
    )

# =============================
# VALIDATE COLUMNS
# =============================

required_columns = [
    "channel_id"
]

missing_columns = [
    col for col in required_columns
    if col not in video_df.columns
]

if missing_columns:

    raise Exception(
        f"Missing columns: {missing_columns}"
    )

# =============================
# GET UNIQUE CHANNEL IDS
# =============================

channel_ids = (
    video_df["channel_id"]
    .astype(str)
    .unique()
    .tolist()
)

print(
    f"Loaded {len(channel_ids)} channels"
)

# =============================
# BATCH CONFIG
# =============================

BATCH_SIZE = 50

# =============================
# CRAWL
# =============================

channels = []

for i in range(0, len(channel_ids), BATCH_SIZE):

    batch_ids = channel_ids[
        i:i + BATCH_SIZE
    ]

    print(
        f"\nBatch {i//BATCH_SIZE + 1}"
    )

    while True:

        try:

            request = youtube.channels().list(
                part="snippet,statistics",
                id=",".join(batch_ids)
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

    # =============================
    # SKIP FAILED BATCH
    # =============================

    if response is None:
        continue

    items = response.get("items", [])

    # =============================
    # SKIP EMPTY ITEMS
    # =============================

    if not items:
        continue

    for item in items:

        snippet = item.get(
            "snippet",
            {}
        )

        statistics = item.get(
            "statistics",
            {}
        )

        channels.append({

            "channel_id": item.get("id"),

            "channel_title": snippet.get(
                "title"
            ),

            "custom_url": snippet.get(
                "customUrl"
            ),

            "channel_description": snippet.get(
                "description"
            ),

            "published_at": snippet.get(
                "publishedAt"
            ),

            "country": snippet.get(
                "country"
            ),

            "subscriber_count": statistics.get(
                "subscriberCount",
                0
            ),

            "view_count": statistics.get(
                "viewCount",
                0
            ),

            "video_count": statistics.get(
                "videoCount",
                0
            ),

            "hidden_subscriber_count": statistics.get(
                "hiddenSubscriberCount",
                False
            )
        })

# =============================
# CREATE DATAFRAME
# =============================

channel_df = pd.DataFrame(
    channels
)

# =============================
# CHECK EMPTY DATAFRAME
# =============================

if channel_df.empty:

    raise Exception(
        "No channels collected"
    )

# =============================
# TYPE CASTING
# =============================

numeric_columns = [
    "subscriber_count",
    "view_count",
    "video_count"
]

for col in numeric_columns:

    channel_df[col] = pd.to_numeric(
        channel_df[col],
        errors="coerce"
    ).fillna(0).astype(int)

# =============================
# REMOVE DUPLICATES
# =============================

channel_df = channel_df.drop_duplicates(
    subset="channel_id",
    keep="last"
)

# =============================
# LOAD OLD CHANNELS
# =============================

if os.path.exists(RAW_CHANNEL_PATH):

    old_df = pd.read_csv(
        RAW_CHANNEL_PATH,
        dtype={
            "subscriber_count": int,
            "view_count": int,
            "video_count": int
        }
    )

    channel_df = pd.concat(
        [old_df, channel_df],
        ignore_index=True
    )

    # Recast after concat
    for col in numeric_columns:
        channel_df[col] = pd.to_numeric(
            channel_df[col],
            errors="coerce"
        ).fillna(0).astype(int)

# =============================
# FINAL DEDUPLICATION
# =============================

channel_df = channel_df.drop_duplicates(
    subset="channel_id",
    keep="last"
)

# =============================
# SAVE CSV
# =============================

channel_df.to_csv(
    RAW_CHANNEL_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")

print(
    "Channels collected:",
    len(channel_df)
)
