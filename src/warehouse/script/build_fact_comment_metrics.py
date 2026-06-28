import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent.parent)
)

import pandas as pd

# =============================
# PATHS
# =============================

FACT_COMMENT_PATH = "warehouse/data/fact_comments.csv"

FACT_COMMENT_METRICS_PATH = "warehouse/data/fact_comment_metrics.csv"

# =============================
# LOAD FACT COMMENTS
# =============================

if not Path(FACT_COMMENT_PATH).exists():
    raise FileNotFoundError(
        f"File not found: {FACT_COMMENT_PATH}"
    )

fact_comments = pd.read_csv(
    FACT_COMMENT_PATH,
    dtype={"like_count": int}
)

print(f"fact_comments loaded: {len(fact_comments)} rows")

# =============================
# AGGREGATE BY VIDEO
# =============================

metrics = fact_comments.groupby("video_id").agg(

    total_comments=("comment_id", "count"),

    total_likes=("like_count", "sum"),

    avg_like_per_comment=("like_count", "mean"),

    max_like_comment=("like_count", "max"),

).reset_index()

# =============================
# SENTIMENT METRICS
# (chỉ tính nếu đã có sentiment từ Colab)
# =============================

if (
    "sentiment" in fact_comments.columns
    and fact_comments["sentiment"].notna().any()
):

    sentiment_counts = (
        fact_comments
        .groupby(["video_id", "sentiment"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # đảm bảo đủ 3 cột dù data thiếu
    for col in ["positive", "negative", "neutral"]:
        if col not in sentiment_counts.columns:
            sentiment_counts[col] = 0

    sentiment_counts = sentiment_counts.rename(columns={
        "positive": "positive_count",
        "negative": "negative_count",
        "neutral":  "neutral_count",
    })

    # tính sentiment_score: (positive - negative) / total
    sentiment_counts["sentiment_score"] = (
        (
            sentiment_counts["positive_count"]
            - sentiment_counts["negative_count"]
        )
        / (
            sentiment_counts["positive_count"]
            + sentiment_counts["negative_count"]
            + sentiment_counts["neutral_count"]
        )
    ).round(4)

    metrics = metrics.merge(
        sentiment_counts[[
            "video_id",
            "positive_count",
            "negative_count",
            "neutral_count",
            "sentiment_score",
        ]],
        on="video_id",
        how="left"
    )

else:

    # placeholder — sẽ fill sau khi Colab chạy xong
    metrics["positive_count"]  = None
    metrics["negative_count"]  = None
    metrics["neutral_count"]   = None
    metrics["sentiment_score"] = None

    print(
        "Sentiment chưa có → "
        "các cột sentiment để None, "
        "chạy lại sau khi Colab fill xong"
    )

# =============================
# ROUND FLOAT
# =============================

metrics["avg_like_per_comment"] = (
    metrics["avg_like_per_comment"].round(2)
)

# =============================
# SAVE CSV
# =============================

Path(FACT_COMMENT_METRICS_PATH).parent.mkdir(
    parents=True,
    exist_ok=True
)

metrics.to_csv(
    FACT_COMMENT_METRICS_PATH,
    index=False
)

# =============================
# DONE
# =============================

print("\nDONE")
print(f"fact_comment_metrics saved: {len(metrics)} rows")
print(f"Columns: {list(metrics.columns)}")