import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent.parent)
)

import os
import pandas as pd

from sqlalchemy import (
    create_engine
)

from dotenv import load_dotenv

# =============================
# LOAD ENV
# =============================

env_path = (
    Path(__file__)
    .parent
    .parent
    / ".env"
)

print(
    f"Looking for .env at: "
    f"{env_path.resolve()}"
)

print(
    f"File exists: "
    f"{env_path.exists()}"
)

load_dotenv(
    dotenv_path=env_path,
    encoding="utf-8-sig",
    override=True
)

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

print(
    f"\nDATABASE_URL: "
    f"{DATABASE_URL}"
)

if DATABASE_URL is None:

    raise Exception(
        "DATABASE_URL not found in .env"
    )

# =============================
# CONNECT DATABASE
# =============================

engine = create_engine(
    DATABASE_URL
)

print(
    "\nConnected to database successfully!"
)

# =============================
# TABLES TO LOAD
# =============================

tables = [

    (
        "dim_topic",
        "warehouse/data/dim_topic.csv"
    ),

    (
        "dim_channel",
        "warehouse/data/dim_channel.csv"
    ),

    (
        "dim_time",
        "warehouse/data/dim_time.csv"
    ),

    (
        "dim_video",
        "warehouse/data/dim_video.csv"
    ),

    (
        "fact_video_metrics",
        "warehouse/data/fact_video_metrics.csv"
    )
]

# =============================
# LOAD CSV TO POSTGRES
# =============================

for table_name, path in tables:

    # Skip missing file
    if not os.path.exists(path):

        print(
            f"\nSkip missing file: {path}"
        )

        continue

    # Load CSV
    df = pd.read_csv(path)

    # Skip empty dataframe
    if df.empty:

        print(
            f"\nSkip empty file: {path}"
        )

        continue

    # Load to PostgreSQL
    df.to_sql(

        table_name,

        engine,

        if_exists="replace",

        index=False,

        method="multi",

        chunksize=10000
    )

    print(
        f"\nLoaded {table_name}: "
        f"{len(df)} rows"
    )

# =============================
# DONE
# =============================

print("\nDONE")
