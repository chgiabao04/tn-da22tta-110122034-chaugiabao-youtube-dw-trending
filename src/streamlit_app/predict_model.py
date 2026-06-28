import os
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder

# Load model safely
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "xgb_trending_model.json")

try:
    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)
except Exception as e:
    raise RuntimeError(
        f"Không thể load model từ '{MODEL_PATH}'. "
        f"Kiểm tra file có tồn tại không.\nLỗi gốc: {e}"
    )

# 8 features đúng với model đã train
FEATURES = [
    "subscriber_count",
    "view_count",
    "video_count",
    "duration_seconds",
    "like_rate",
    "comment_rate",
    "topic",
    "country_region",
]

# LabelEncoders cho categorical features
topic_encoder = LabelEncoder()
country_encoder = LabelEncoder()

# FIXED: Đúng 25 topics khớp với training data (03_model_xgboost_1.ipynb)
# Thứ tự alphabet quan trọng — LabelEncoder encode theo thứ tự này
KNOWN_TOPICS = [
    'animals', 'beauty', 'business', 'cars', 'comedy', 'education',
    'entertainment', 'film', 'finance', 'fitness', 'food', 'gaming',
    'howto', 'kids', 'motivation', 'music', 'news', 'nonprofit',
    'people', 'pets', 'science', 'sports', 'technology', 'travel', 'vlog'
]

# FIXED: Đúng thứ tự alphabet cho regions
KNOWN_REGIONS = [
    'Africa', 'Central Asia', 'East Asia', 'Eastern Europe',
    'Middle East', 'North America', 'Oceania', 'South America',
    'South Asia', 'Southeast Asia', 'Western Europe'
]

topic_encoder.fit(KNOWN_TOPICS)
country_encoder.fit(KNOWN_REGIONS)

DEFAULT_TOPIC  = 'entertainment'
DEFAULT_REGION = 'North America'


def predict_trending(features_dict):
    """
    Predict trending probability.
    Input : dict với 8 keys khớp FEATURES (topic & country_region là string).
    Output: (probability float, reasoning_text str)
    """

    # Encode categorical — fallback nếu gặp nhãn lạ
    topic = features_dict.get('topic', DEFAULT_TOPIC)
    if topic not in KNOWN_TOPICS:
        topic = DEFAULT_TOPIC

    region = features_dict.get('country_region', DEFAULT_REGION)
    if region not in KNOWN_REGIONS:
        region = DEFAULT_REGION

    topic_encoded   = topic_encoder.transform([topic])[0]
    country_encoded = country_encoder.transform([region])[0]

    # Đúng 8 features, đúng thứ tự model đã train
    X_input = np.array([[
        features_dict['subscriber_count'],
        features_dict['view_count'],
        features_dict['video_count'],
        features_dict['duration_seconds'],
        features_dict['like_rate'],
        features_dict['comment_rate'],
        topic_encoded,
        country_encoded,
    ]])

    proba = model.predict_proba(X_input)[0, 1]

    # Reasoning
    like_rate    = features_dict['like_rate']
    comment_rate = features_dict['comment_rate']
    raw_views    = features_dict.get('raw_views', 0)

    # Like rate
    if raw_views < 1000:
        reason1 = "Video còn ít lượt xem"
    elif like_rate < 0.01:
        reason1 = "Tỉ lệ like thấp"
    elif like_rate > 0.05:
        reason1 = "Tỉ lệ like rất tốt"
    else:
        reason1 = "Tỉ lệ like ổn định"

    # Comment rate
    if raw_views < 1000:
        reason2 = "chưa đủ dữ liệu tương tác"
    elif comment_rate < 0.0005:
        reason2 = "bình luận thấp"
    elif comment_rate > 0.002:
        reason2 = "tương tác bình luận tốt"
    else:
        reason2 = "bình luận ở mức trung bình"

    # Subscriber context
    sub_log = features_dict.get('subscriber_count', 0)
    sub_count = int(np.expm1(sub_log))
    if sub_count < 1000:
        reason3 = "Kênh nhỏ (dưới 1K subscribers)"
    elif sub_count < 100_000:
        reason3 = f"Kênh vừa (~{sub_count//1000}K subscribers)"
    else:
        reason3 = f"Kênh lớn (~{sub_count//1000}K subscribers)"

    reasoning = f"{reason1}, {reason2} | {reason3} | Topic: {topic} | Vùng: {region}"
    return proba, reasoning