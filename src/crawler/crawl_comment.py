import pandas as pd
import os
import time
from googleapiclient.errors import HttpError
from config.api_config import YouTubeClient
from config.paths import RAW_VIDEO_PATH, RAW_COMMENT_PATH

# =============================
# INIT
# =============================

yt = YouTubeClient()
youtube = yt.get_client()

MAX_COMMENTS = 100
SAVE_EVERY = 5

# =============================
# LOAD VIDEOS
# =============================

if not os.path.exists(RAW_VIDEO_PATH):
    raise FileNotFoundError(f"File not found: {RAW_VIDEO_PATH}")

video_df = pd.read_csv(RAW_VIDEO_PATH)

if video_df.empty:
    raise Exception("raw_video.csv is empty")

video_ids = video_df["video_id"].astype(str).unique().tolist()
print(f"Loaded {len(video_ids)} videos")

# =============================
# LOAD EXISTING IDS ONLY
# =============================

existing_comment_ids = set()
existing_video_ids = set()

if os.path.exists(RAW_COMMENT_PATH):
    tmp = pd.read_csv(RAW_COMMENT_PATH, usecols=["comment_id", "video_id"])
    tmp = tmp.drop_duplicates(subset="comment_id")
    existing_comment_ids = set(tmp["comment_id"].astype(str))
    existing_video_ids = set(tmp["video_id"].astype(str))
    del tmp
    print(f"Resuming: {len(existing_video_ids)} videos done, {len(existing_comment_ids)} comments collected")

# =============================
# HELPER: SAVE PROGRESS
# =============================

def save_progress(new_comments):
    if not new_comments:
        return

    new_df = pd.DataFrame(new_comments)
    new_df["like_count"] = pd.to_numeric(new_df["like_count"], errors="coerce").fillna(0).astype(int)

    new_df.to_csv(
        RAW_COMMENT_PATH,
        mode="a",
        header=not os.path.exists(RAW_COMMENT_PATH),
        index=False
    )

    print(f"  [Saved] +{len(new_df)} comments")

# =============================
# CRAWL
# =============================

comments = []

for idx, video_id in enumerate(video_ids):

    if video_id in existing_video_ids:
        print(f"Skip crawled video: {video_id}")
        continue

    print(f"\nVideo {idx + 1}/{len(video_ids)}: {video_id}")

    collected = 0
    next_page_token = None

    while collected < MAX_COMMENTS:
        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                order="relevance",
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()

        except HttpError as e:
            error_text = str(e)

            if "commentsDisabled" in error_text or "videoNotFound" in error_text:
                print(f"  Skip: comments disabled or video not found")
                break

            if "quotaExceeded" in error_text:
                print("\nQuota exceeded, switching API key...")
                try:
                    yt.switch_key()
                    youtube = yt.get_client()
                    time.sleep(1)
                    continue
                except Exception as switch_error:
                    print(switch_error)
                    raise Exception("All API keys exhausted")

            print(f"  Error: {e}")
            break

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            top_comment = item.get("snippet", {}).get("topLevelComment", {})
            comment_snippet = top_comment.get("snippet", {})
            comment_id = top_comment.get("id")

            if comment_id in existing_comment_ids:
                continue

            comments.append({
                "comment_id":   comment_id,
                "video_id":     video_id,
                "author_name":  comment_snippet.get("authorDisplayName"),
                "comment_text": comment_snippet.get("textDisplay"),
                "like_count":   comment_snippet.get("likeCount", 0),
                "published_at": comment_snippet.get("publishedAt"),
                "updated_at":   comment_snippet.get("updatedAt"),
            })

            existing_comment_ids.add(comment_id)
            collected += 1

            if collected >= MAX_COMMENTS:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    existing_video_ids.add(video_id)

    if (idx + 1) % SAVE_EVERY == 0 and comments:
        save_progress(comments)
        comments = []

# =============================
# FINAL SAVE
# =============================

save_progress(comments)

# =============================
# DONE
# =============================

print("\nDONE")
print(f"Total videos processed: {len(existing_video_ids)}")