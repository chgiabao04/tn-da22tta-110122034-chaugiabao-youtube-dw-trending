# test_yt.py — để trong D:\KLTN\streamlit_app\
from yt_dlp import YoutubeDL

video_id = "SlQR9iu09bQ"

ydl_opts = {
    'quiet': False,   # bật verbose để thấy nó đang làm gì
    'no_warnings': False,
    'skip_download': True,
    'noplaylist': True,
    'socket_timeout': 15,
}

print("Bắt đầu fetch...")
with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

print("Xong!")
print("title:", info.get('title'))
print("views:", info.get('view_count'))
print("channel_follower_count:", info.get('channel_follower_count'))
print("uploader_country:", info.get('uploader_country'))