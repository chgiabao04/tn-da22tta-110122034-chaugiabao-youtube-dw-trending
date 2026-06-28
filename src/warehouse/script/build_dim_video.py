import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent)
)

import pandas as pd
import os

from config.paths import (
    RAW_VIDEO_PATH,
    RAW_VIDEO_STATS_PATH
)

# =============================
# CHECK FILES
# =============================

if not os.path.exists(RAW_VIDEO_PATH):

    raise FileNotFoundError(
        f"File not found: {RAW_VIDEO_PATH}"
    )

if not os.path.exists(RAW_VIDEO_STATS_PATH):

    raise FileNotFoundError(
        f"File not found: {RAW_VIDEO_STATS_PATH}"
    )

# =============================
# LOAD DATA
# =============================

video_df = pd.read_csv(
    RAW_VIDEO_PATH
)

stats_df = pd.read_csv(
    RAW_VIDEO_STATS_PATH
)

if video_df.empty:

    raise Exception(
        "raw_video.csv is empty"
    )

if stats_df.empty:

    raise Exception(
        "raw_video_stats.csv is empty"
    )

# =============================
# REMOVE DUPLICATES
# =============================

video_df = video_df.drop_duplicates(
    subset="video_id",
    keep="last"
)

stats_df = stats_df.drop_duplicates(
    subset="video_id",
    keep="last"
)

# =============================
# SELECT VIDEO COLUMNS
# =============================

video_columns = [

    "video_id",

    "title",

    "description",

    "channel_id",

    "channel_title",

    "publish_time",

    "thumbnail",

    "country",

    "keyword",

    "topic",

    "source"
]

video_columns = [
    col for col in video_columns
    if col in video_df.columns
]

video_df = video_df[
    video_columns
]

# =============================
# SELECT STATS COLUMNS
# =============================

stats_columns = [

    "video_id",
    "duration_seconds",
    "definition",
    "caption",
    "licensed_content",
    "category_id",
    "default_language",
    "default_audio_language",
    "tags"
]

stats_columns = [
    col for col in stats_columns
    if col in stats_df.columns
]

stats_df = stats_df[
    stats_columns
]

# =============================
# CREATE TIME ID
# =============================

video_df["publish_time"] = pd.to_datetime(
    video_df["publish_time"],
    errors="coerce"
)

video_df["time_id"] = (
    video_df["publish_time"]
    .dt.strftime("%Y%m%d%H")
    .astype(str)
)

# =============================
# MERGE VIDEO + STATS
# =============================

dim_video = pd.merge(

    video_df,

    stats_df,

    on="video_id",

    how="left"
)

# =============================
# REMOVE DUPLICATES
# =============================

dim_video = dim_video.drop_duplicates(
    subset="video_id",
    keep="last"
)

# =============================
# SAVE CSV
# =============================

OUTPUT_PATH = (
    "warehouse/data/dim_video.csv"
)

os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

dim_video.to_csv(
    OUTPUT_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")

print(
    f"Total videos: {len(dim_video)}"
)
