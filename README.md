# Xây Dựng Data Warehouse và Mô Hình Machine Learning Phân Tích và Dự Đoán Video Trending Trên YouTube

## Giới thiệu

Đề tài tập trung xây dựng hệ thống Data Warehouse cho dữ liệu YouTube kết hợp mô hình Machine Learning nhằm phân tích và dự đoán khả năng trở thành video Trending.

Hệ thống thực hiện thu thập dữ liệu từ YouTube Data API v3, xây dựng quy trình ETL, lưu trữ dữ liệu theo mô hình Data Warehouse và áp dụng thuật toán XGBoost để dự đoán trạng thái Trending của video.

## Mục tiêu

* Thu thập dữ liệu video, kênh và bình luận từ YouTube.
* Xây dựng Data Warehouse phục vụ phân tích dữ liệu.
* Thực hiện ETL và tiền xử lý dữ liệu.
* Phân tích dữ liệu khám phá (EDA).
* Xây dựng mô hình Machine Learning dự đoán video Trending.
* Phân tích cảm xúc bình luận người dùng (Sentiment Analysis).
* Xây dựng Dashboard và ứng dụng trực quan hóa kết quả.

## Công nghệ sử dụng

### Data Collection

* YouTube Data API v3
* Python

### Data Warehouse

* PostgreSQL
* Star Schema

### Data Processing

* Pandas
* NumPy

### Machine Learning

* XGBoost
* Scikit-learn

### NLP

* XLM-RoBERTa

### Visualization

* Streamlit
* Power BI
* Matplotlib
* Seaborn

## Kiến trúc hệ thống

```text
YouTube Data API
        │
        ▼
 Data Crawling
        │
        ▼
     ETL
        │
        ▼
 Data Warehouse
        │
 ┌──────┴──────┐
 ▼             ▼
EDA      Machine Learning
 │             │
 ▼             ▼
Dashboard   Prediction
```

## Cấu trúc thư mục

```text
docs/
│
├── Thesis.docx
├── Thesis.pdf
├── Slide.pptx
├── Poster.pdf
└── User_Guide.pdf

src/
│
├── analysis/
├── config/
├── crawler/
├── data/
├── ETL/
├── keyword/
├── nlp/
├── streamlit_app/
└── warehouse/

README.md
```

## Dataset

Do dung lượng dữ liệu lớn nên bộ dữ liệu không được lưu trực tiếp trên GitHub.

Link tải Dataset:

**Google Drive:**
<https://drive.google.com/drive/folders/13p89Shl7HG2RsDRVVfhWN73h7DL1dDOf?usp=sharing>

Bao gồm:

* Raw Video Dataset
* Raw Channel Dataset
* Raw Comment Dataset
* Processed Dataset
* Machine Learning Dataset
* Data Warehouse Dataset

## Mô hình Machine Learning

Thuật toán sử dụng:

* XGBoost Classifier

Bài toán:

* Dự đoán video có trở thành Trending hay không.

Một số đặc trưng được sử dụng:

* View Count
* Like Count
* Comment Count
* Subscriber Count
* Duration
* Engagement Rate
* Like Rate
* Comment Rate
* Days Since Publish
* Views Per Subscriber
* Sentiment Features

## Hướng dẫn chạy dự án

### 1. Clone repository

```bash
git clone https://github.com/chgiabao04/tn-da22tta-110122034-chaugiabao-youtube-dw-trending.git
```

### 2. Cài đặt thư viện

```bash
- pandas
- numpy
- scikit-learn
- xgboost
- streamlit
- matplotlib
- seaborn
- transformers
- torch
```

### 3. Cấu hình API Key

Tạo file `.env`:

```env
YOUTUBE_API_KEY=YOUR_API_KEY
```

### 4. Chạy ứng dụng

```bash
streamlit run src/streamlit_app/app.py
```

## Kết quả

* Xây dựng thành công Data Warehouse cho dữ liệu YouTube.
* Thu thập hơn 150.000 video và hàng triệu bình luận.
* Thực hiện phân tích cảm xúc bình luận.
* Xây dựng mô hình XGBoost dự đoán Trending.
* Phát triển Dashboard trực quan hóa dữ liệu và hỗ trợ dự đoán.

## Tác giả

**Châu Gia Bảo**
MSSV: 110122034
Email: chgiabao36925@gmail.com

Đồ Án Tốt Nghiệp Ngành Công Nghệ Thông Tin
Trường Kỹ thuật và Công nghệ, Đại học Trà Vinh
