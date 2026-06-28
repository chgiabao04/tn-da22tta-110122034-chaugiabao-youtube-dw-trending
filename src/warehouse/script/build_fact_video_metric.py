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

# Keep ALL snapshots in stats
stats_df = stats_df.drop_duplicates()

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
# SELECT VIDEO COLUMNS
# =============================

video_columns = [

    "video_id",

    "channel_id",

    "time_id",

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
# SELECT FACT COLUMNS
# =============================

fact_columns = [

    "video_id",

    "views",

    "likes",

    "comments",

    "snapshot_time",

    "is_trending"
]

fact_columns = [
    col for col in fact_columns
    if col in stats_df.columns
]

stats_df = stats_df[
    fact_columns
]

# =============================
# NUMERIC COLUMNS
# =============================

numeric_columns = [
    "views",
    "likes",
    "comments"
]

for col in numeric_columns:

    if col in stats_df.columns:

        stats_df[col] = pd.to_numeric(
            stats_df[col],
            errors="coerce"
        ).fillna(0).astype(int)

# =============================
# MERGE VIDEO + FACT
# =============================

fact_video_metrics = pd.merge(

    stats_df,

    video_df,

    on="video_id",

    how="left"
)

# =============================
# REMOVE DUPLICATES
# =============================

fact_video_metrics = (
    fact_video_metrics
    .drop_duplicates()
)

# =============================
# SORT
# =============================

if "snapshot_time" in fact_video_metrics.columns:

    fact_video_metrics = (
        fact_video_metrics
        .sort_values(
            by="snapshot_time"
        )
    )

# =============================
# SAVE CSV
# =============================

OUTPUT_PATH = (
    "warehouse/data/fact_video_metrics.csv"
)

os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

fact_video_metrics.to_csv(
    OUTPUT_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")

print(
    f"Total fact records: "
    f"{len(fact_video_metrics)}"
)
