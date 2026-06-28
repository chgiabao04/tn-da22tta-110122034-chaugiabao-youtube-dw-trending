from datetime import datetime
import pandas as pd
import os
import time
import isodate
from googleapiclient.errors import HttpError
from config.api_config import YouTubeClient

from config.paths import (
    RAW_VIDEO_PATH,
    RAW_VIDEO_STATS_PATH
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

video_df = pd.read_csv(RAW_VIDEO_PATH)

if video_df.empty:

    raise Exception(
        "raw_video.csv is empty"
    )

# =============================
# VALIDATE COLUMNS
# =============================

required_columns = [
    "video_id"
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
# GET UNIQUE VIDEO IDS
# =============================

video_ids = (
    video_df["video_id"]
    .astype(str)
    .unique()
    .tolist()
)

print(
    f"Loaded {len(video_ids)} videos"
)
trending_ids = set( 
    video_df[ 
        video_df["source"] == "trending" 
        ]["video_id"] 
        .astype(str) 
)

# =============================
# BATCH CONFIG
# =============================

BATCH_SIZE = 50

# =============================
# CRAWL
# =============================

stats = []

snapshot_time = pd.Timestamp.utcnow()

for i in range(0, len(video_ids), BATCH_SIZE):

    batch_ids = video_ids[
        i:i + BATCH_SIZE
    ]

    print(
        f"\nBatch {i//BATCH_SIZE + 1}"
    )

    while True:

        try:

            request = youtube.videos().list(
                part="statistics,contentDetails,snippet",
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

        statistics = item.get(
            "statistics",
            {}
        )

        snippet = item.get(
            "snippet",
            {}
        )

        content = item.get(
            "contentDetails",
            {}
        )

        # =============================
        # CONVERT DURATION
        # =============================

        try:

            duration_seconds = int(
                isodate.parse_duration(
                    content.get(
                        "duration",
                        "PT0S"
                    )
                ).total_seconds()
            )

        except Exception:

            duration_seconds = 0

        stats.append({

            "video_id": item.get("id"),

            "is_trending": int(
            item.get("id") in trending_ids
            ),
            
            "views": statistics.get(
                "viewCount",
                0
            ),

            "likes": statistics.get(
                "likeCount",
                0
            ),

            "comments": statistics.get(
                "commentCount",
                0
            ),

            "duration_seconds": duration_seconds,

            "definition": content.get(
                "definition"
            ),

            "caption": content.get(
                "caption"
            ),

            "dimension": content.get(
                "dimension"
            ),

            "licensed_content": content.get(
                "licensedContent"
            ),

            "category_id": snippet.get(
                "categoryId"
            ),

            "default_language": snippet.get(
                "defaultLanguage"
            ),

            "default_audio_language": snippet.get(
                "defaultAudioLanguage"
            ),

            "tags": ",".join(
                snippet.get("tags", [])
            ),

            "snapshot_time": snapshot_time
        })

# =============================
# CREATE DATAFRAME
# =============================

stats_df = pd.DataFrame(stats)

# =============================
# CHECK EMPTY DATAFRAME
# =============================

if stats_df.empty:

    raise Exception(
        "No stats collected"
    )

# =============================
# TYPE CASTING
# =============================

numeric_columns = [
    "views",
    "likes",
    "comments",
    "duration_seconds"
]

for col in numeric_columns:

    stats_df[col] = pd.to_numeric(
        stats_df[col],
        errors="coerce"
    ).fillna(0).astype(int)

# =============================
# REMOVE DUPLICATES
# =============================

stats_df = stats_df.drop_duplicates(
    subset=[
        "video_id",
        "snapshot_time"
    ]
)

# =============================
# LOAD OLD SNAPSHOTS
# =============================

if os.path.exists(RAW_VIDEO_STATS_PATH):

    old_df = pd.read_csv(
        RAW_VIDEO_STATS_PATH,
        dtype={
            "views": int,
            "likes": int,
            "comments": int,
            "duration_seconds": int
        }
    )

    # =============================
    # NORMALIZE DATETIME
    # =============================

    old_df["snapshot_time"] = pd.to_datetime(
        old_df["snapshot_time"]
    )

    stats_df = pd.concat(
        [old_df, stats_df],
        ignore_index=True
    )

    # =============================
    # NORMALIZE FINAL DATETIME
    # =============================

    stats_df["snapshot_time"] = pd.to_datetime(
        stats_df["snapshot_time"]
    )

    # =============================
    # RECAST AFTER CONCAT
    # =============================

    for col in numeric_columns:

        stats_df[col] = pd.to_numeric(
            stats_df[col],
            errors="coerce"
        ).fillna(0).astype(int)

# =============================
# FINAL DEDUPLICATION
# =============================

stats_df = stats_df.drop_duplicates(
    subset=[
        "video_id",
        "snapshot_time"
    ]
)

# =============================
# SAVE CSV
# =============================

stats_df.to_csv(
    RAW_VIDEO_STATS_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")

print(
    "Stats collected:",
    len(stats)
)

print(
    "Total snapshots:",
    len(stats_df)
)
