import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8-sig", override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise Exception("DATABASE_URL not found")

engine = create_engine(DATABASE_URL)
print("Connected PostgreSQL")

os.makedirs("analysis/data", exist_ok=True)

# =========================
# OUTPUT 1: final_dataset
# (giữ nguyên logic load_dw.py cũ)
# =========================

df_video   = pd.read_sql("SELECT * FROM public.dim_video",          engine)
df_channel = pd.read_sql("SELECT * FROM public.dim_channel",        engine)
df_topic   = pd.read_sql("SELECT * FROM public.dim_topic",          engine)
df_time    = pd.read_sql("SELECT * FROM public.dim_time",           engine)
df_metrics = pd.read_sql("SELECT * FROM public.fact_video_metrics", engine)

print("dim_video:    ", df_video.shape)
print("dim_channel:  ", df_channel.shape)
print("dim_topic:    ", df_topic.shape)
print("dim_time:     ", df_time.shape)
print("fact_metrics: ", df_metrics.shape)

df_video = df_video.drop(
    columns=["channel_id", "time_id", "source", "channel_title"],
    errors="ignore"
)

df_final = (
    df_metrics
    .merge(df_video,   on="video_id",   how="left")
    .merge(df_channel, on="channel_id", how="left")
    .merge(df_time,    on="time_id",    how="left")
)

CATEGORY_TOPIC_MAP = {
    1: "film", 2: "cars", 10: "music", 15: "pets", 17: "sports",
    19: "travel", 20: "gaming", 22: "people", 23: "comedy", 24: "entertainment",
    25: "news", 26: "howto", 27: "education", 28: "science", 29: "nonprofit", 30: "movies",
    31: "anime", 32: "action", 33: "classics", 34: "comedy_movies", 35: "documentary",
    36: "drama", 37: "family", 38: "foreign", 39: "horror", 40: "sci_fi",
    41: "thriller", 42: "shorts", 43: "shows", 44: "trailers"
}

mask = df_final["topic"] == "trending"
df_final.loc[mask, "topic"] = (
    df_final.loc[mask, "category_id"]
    .map(CATEGORY_TOPIC_MAP)
    .fillna("trending")
)

print("Topic distribution after fix:")
print(df_final["topic"].value_counts())

df_final.to_csv("analysis/data/final_dataset.csv", index=False)
print(f"\nSaved final_dataset.csv — {df_final.shape}")

# =========================
# OUTPUT 2: comment_dataset
# (thêm mới)
# =========================

print("\n--- Building comment_dataset ---")

chunks = []
for chunk in pd.read_sql(
    """
    SELECT comment_id, video_id, comment_text, like_count, published_at
    FROM public.fact_comment
    """,
    engine,
    chunksize=100_000
):
    chunks.append(chunk)

df_comment_dataset = pd.concat(chunks, ignore_index=True)
print(f"fact_comment: {df_comment_dataset.shape}")

df_comment_dataset.to_csv("analysis/data/comment_dataset.csv", index=False, encoding="utf-8")


print(f"Saved comment_dataset.parquet — {df_comment_dataset.shape}")
print(f"Columns: {df_comment_dataset.columns.tolist()}")

# =========================
# DONE
# =========================

print("\nDONE — 2 files exported:")
print("  analysis/data/final_dataset.csv")
print("  analysis/data/comment_dataset.csv")