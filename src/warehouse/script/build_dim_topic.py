import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import os

from config.paths import (
    RAW_VIDEO_PATH
)
# =============================
# CHECK RAW VIDEO FILE
# =============================

if not os.path.exists(RAW_VIDEO_PATH):

    raise FileNotFoundError(
        f"File not found: {RAW_VIDEO_PATH}"
    )

# =============================
# LOAD RAW VIDEO
# =============================

video_df = pd.read_csv(
    RAW_VIDEO_PATH
)

if video_df.empty:

    raise Exception(
        "raw_video.csv is empty"
    )

# =============================
# CHECK COLUMN
# =============================

if "topic" not in video_df.columns:

    raise Exception(
        "Missing topic column"
    )

# =============================
# CLEAN TOPIC
# =============================

video_df["topic"] = (
    video_df["topic"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Remove null / empty topic
video_df = video_df[
    video_df["topic"].notna()
]

video_df = video_df[
    video_df["topic"] != ""
]

# =============================
# CREATE DIM TOPIC
# =============================

unique_topics = sorted(
    video_df["topic"]
    .unique()
)

dim_topic = pd.DataFrame({

    "topic_id": range(
        1,
        len(unique_topics) + 1
    ),

    "topic_name": unique_topics
})

# =============================
# SAVE CSV
# =============================

OUTPUT_PATH = (
    "warehouse/data/dim_topic.csv"
)

# Create folder if not exists
os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

dim_topic.to_csv(
    OUTPUT_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")

print(
    f"Total topics: {len(dim_topic)}"
)
