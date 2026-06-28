import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

from config.paths import RAW_COMMENT_PATH

# =============================
# LOAD ENV
# =============================

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8-sig", override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise Exception("DATABASE_URL not found in .env")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False
print("Connected to database")

# =============================
# CHECK FILE
# =============================

if not os.path.exists(RAW_COMMENT_PATH):
    raise FileNotFoundError(f"File not found: {RAW_COMMENT_PATH}")

# =============================
# TẠO BẢNG
# =============================

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS fact_comment (
    comment_id    TEXT PRIMARY KEY,
    video_id      TEXT NOT NULL,
    author_name   TEXT,
    comment_text  TEXT,
    like_count    INTEGER DEFAULT 0,
    published_at  TIMESTAMP,
    updated_at    TIMESTAMP,
    loaded_at     TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_comment_video_id
ON fact_comment(video_id);
"""

with conn.cursor() as cur:
    cur.execute(CREATE_TABLE_SQL)
conn.commit()
print("Table ready")

# =============================
# LOAD THEO CHUNK
# =============================

CHUNK_SIZE = 100_000
total_inserted = 0
chunk_num = 0

INSERT_SQL = """
    INSERT INTO fact_comment
        (comment_id, video_id, author_name, comment_text,
         like_count, published_at, updated_at)
    VALUES %s
    ON CONFLICT (comment_id) DO NOTHING
"""

for chunk in pd.read_csv(
    RAW_COMMENT_PATH,
    chunksize=CHUNK_SIZE,
    dtype={"comment_id": str, "video_id": str},
    parse_dates=["published_at", "updated_at"],
):
    chunk_num += 1

    chunk = chunk.drop_duplicates(subset="comment_id")

    chunk["like_count"] = (
        pd.to_numeric(chunk["like_count"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # Thay NaT/NaN bằng None để psycopg2 hiểu là NULL
    chunk = chunk.where(pd.notnull(chunk), None)

    rows = [
        (
            row["comment_id"],
            row["video_id"],
            row["author_name"],
            row["comment_text"],
            row["like_count"],
            row["published_at"],
            row["updated_at"],
        )
        for _, row in chunk.iterrows()
    ]

    try:
        with conn.cursor() as cur:
            execute_values(cur, INSERT_SQL, rows, page_size=1000)
        conn.commit()

        total_inserted += len(rows)
        print(f"Chunk {chunk_num}: +{len(rows)} | Total: {total_inserted}")

    except Exception as e:
        conn.rollback()
        print(f"Chunk {chunk_num} ERROR: {e}")
        continue

conn.close()
print(f"\nDONE — Inserted: {total_inserted} rows")