from dotenv import load_dotenv
from googleapiclient.discovery import build
import os

# =============================
# LOAD ENV
# =============================

load_dotenv()

# =============================
# LOAD API KEYS
# =============================

API_KEYS = []

for i in range(1, 31):

    key = os.getenv(
        f"YOUTUBE_API_KEY_{i}"
    )

    if key:

        API_KEYS.append(key)

# =============================
# CHECK API KEYS
# =============================

if not API_KEYS:

    raise Exception(
        "No YouTube API keys found"
    )

print(f"Loaded {len(API_KEYS)} API keys")

# =============================
# YOUTUBE CLIENT
# =============================

class YouTubeClient:

    def __init__(self):

        self.key_index = 0

        self.youtube = self.build_client()

    # =============================
    # BUILD CLIENT
    # =============================

    def build_client(self):

        return build(
            "youtube",
            "v3",
            developerKey=API_KEYS[self.key_index]
        )

    # =============================
    # SWITCH API KEY
    # =============================

    def switch_key(self):

        self.key_index += 1

        if self.key_index >= len(API_KEYS):

            raise Exception(
                "All API keys exhausted"
            )

        print(
            f"\nSwitching to API key "
            f"{self.key_index + 1}"
        )

        self.youtube = self.build_client()

    # =============================
    # GET CLIENT
    # =============================

    def get_client(self):

        return self.youtube
