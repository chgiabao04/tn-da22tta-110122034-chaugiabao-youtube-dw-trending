import shap
import xgboost as xgb
import pandas as pd

from predict_model import (
    topic_encoder,
    country_encoder,
    KNOWN_TOPICS,
    KNOWN_REGIONS,
    DEFAULT_TOPIC,
    DEFAULT_REGION,
)

model = xgb.XGBClassifier()
model.load_model("models/xgb_trending_model_v2.json")

explainer = shap.TreeExplainer(model)

FEATURES = [
    "subscriber_count",
    "view_count",
    "video_count",
    "duration_seconds",
    "like_rate",
    "comment_rate",
    "topic",
    "country_region",
    "publish_hour",
]


def _encode_features(feature_dict: dict) -> dict:
    """
    FIXED: 'topic' va 'country_region' phai duoc encode thanh so bang DUNG
    LabelEncoder da dung luc train (dung chung voi predict_model.py), vi model
    XGBoost chi nhan input so. Truoc day feature_dict['topic'] la string tho
    ('entertainment', 'North America'...) bi dua thang vao DataFrame roi feed
    vao explainer.shap_values(X) -> loi / ket qua sai.
    """
    encoded = dict(feature_dict)

    topic = encoded.get("topic", DEFAULT_TOPIC)
    if topic not in KNOWN_TOPICS:
        topic = DEFAULT_TOPIC

    region = encoded.get("country_region", DEFAULT_REGION)
    if region not in KNOWN_REGIONS:
        region = DEFAULT_REGION

    encoded["topic"] = topic_encoder.transform([topic])[0]
    encoded["country_region"] = country_encoder.transform([region])[0]
    encoded["publish_hour"] = feature_dict.get("publish_hour", 0)
    return encoded


def get_shap_values(feature_dict: dict):
    """
    Tra ve (shap_values, X) voi X da encode dung.
    """
    encoded = _encode_features(feature_dict)
    X = pd.DataFrame([encoded])[FEATURES]

    shap_values = explainer.shap_values(X)

    return shap_values[0], X


def get_shap_explanation(feature_dict: dict) -> shap.Explanation:
    """
    Tra ve shap.Explanation san sang de ve waterfall/bar plot
    (shap.plots.waterfall, shap.plots.bar).

    'data' hien thi dung gia tri GOC (de doc: 'entertainment' thay vi so 5)
    con 'values' van tinh tren input da encode.
    """
    values, X = get_shap_values(feature_dict)

    base_value = explainer.expected_value
    if hasattr(base_value, "__len__"):
        base_value = base_value[0] if len(base_value) else base_value

    # FIXED: X.iloc[0] la mot Series dtype float64 (vi toan bo input cho
    # model deu la so). Gan truc tiep string ('music', 'North America'...)
    # vao mot phan tu cua Series dtype float64 se raise
    # "Invalid value '...' for dtype 'float64'" o pandas ban moi. Thay vi
    # sua tren Series cu, dung mang moi voi dtype=object de tron loi nay.
    row = X.iloc[0]
    display_values = []
    for col in X.columns:
        if col == "topic":
            display_values.append(feature_dict.get("topic", DEFAULT_TOPIC))
        elif col == "country_region":
            display_values.append(feature_dict.get("country_region", DEFAULT_REGION))
        else:
            display_values.append(row[col])

    display_data = pd.Series(display_values, index=X.columns, dtype=object)

    return shap.Explanation(
        values=values,
        base_values=base_value,
        data=display_data.values,
        feature_names=list(X.columns),
    )