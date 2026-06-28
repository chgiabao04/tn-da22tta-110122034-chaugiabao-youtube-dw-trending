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

if "publish_time" not in video_df.columns:

    raise Exception(
        "Missing publish_time column"
    )

# =============================
# CONVERT DATETIME
# =============================

video_df["publish_time"] = pd.to_datetime(
    video_df["publish_time"],
    errors="coerce"
)

# Remove invalid datetime
video_df = video_df.dropna(
    subset=["publish_time"]
)

# =============================
# CREATE DIM TIME
# =============================

dim_time = pd.DataFrame()

dim_time = pd.DataFrame()

dim_time["time_id"] = (
    video_df["publish_time"]
    .dt.strftime("%Y%m%d%H")
    .astype(str)
)

dim_time["date"] = (
    video_df["publish_time"]
    .dt.date
    .astype(str)
)

dim_time["year"] = (
    video_df["publish_time"]
    .dt.year
)

dim_time["quarter"] = (
    video_df["publish_time"]
    .dt.quarter
)

dim_time["month"] = (
    video_df["publish_time"]
    .dt.month
)

dim_time["week_of_year"] = (
    video_df["publish_time"]
    .dt.isocalendar()
    .week
)

dim_time["day"] = (
    video_df["publish_time"]
    .dt.day
)

dim_time["weekday"] = (
    video_df["publish_time"]
    .dt.weekday
)

dim_time["hour"] = (
    video_df["publish_time"]
    .dt.hour
)


# =============================
# REMOVE DUPLICATES
# =============================

dim_time = dim_time.drop_duplicates(
    subset="time_id"
)

# =============================
# SORT
# =============================

dim_time = dim_time.sort_values(
    by="time_id"
)

# =============================
# SAVE CSV
# =============================

OUTPUT_PATH = (
    "warehouse/data/dim_time.csv"
)

os.makedirs( 
    os.path.dirname(OUTPUT_PATH), 
    exist_ok=True 
)

dim_time.to_csv(
    OUTPUT_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")

print(
    f"Total time records: {len(dim_time)}"
)
