import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent)
)

import pandas as pd
import os

from config.paths import (
    RAW_CHANNEL_PATH
)

# =============================
# CHECK RAW CHANNEL FILE
# =============================

if not os.path.exists(RAW_CHANNEL_PATH):

    raise FileNotFoundError(
        f"File not found: {RAW_CHANNEL_PATH}"
    )

# =============================
# LOAD RAW CHANNEL
# =============================

channel_df = pd.read_csv(
    RAW_CHANNEL_PATH
)

if channel_df.empty:

    raise Exception(
        "raw_channel.csv is empty"
    )

# =============================
# REMOVE DUPLICATES
# =============================

channel_df = channel_df.drop_duplicates(
    subset="channel_id",
    keep="last"
)

# =============================
# NUMERIC COLUMNS
# =============================

numeric_columns = [
    "subscriber_count",
    "view_count",
    "video_count"
]

for col in numeric_columns:

    if col in channel_df.columns:

        channel_df[col] = pd.to_numeric(
            channel_df[col],
            errors="coerce"
        ).fillna(0).astype(int)

# =============================
# SELECT COLUMNS
# =============================

columns_to_select = [

    "channel_id",

    "channel_title",

    "custom_url",

    "channel_description",

    "published_at",

    "country",

    "subscriber_count",

    "view_count",

    "video_count"
]

dim_channel = channel_df[
    [
        col for col in columns_to_select
        if col in channel_df.columns
    ]
]

# =============================
# SAVE CSV
# =============================

OUTPUT_PATH = (
    "warehouse/data/dim_channel.csv"
)

# Create folder if not exists
os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

dim_channel.to_csv(
    OUTPUT_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")

print(
    f"Total channels: {len(dim_channel)}"
)
