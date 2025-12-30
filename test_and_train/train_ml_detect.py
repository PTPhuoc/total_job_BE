import pandas as pd
import csv
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sentence_transformers import SentenceTransformer, util
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
import joblib
from linking_word import load_linking_patterns, advanced_phrase_linking, clean_text
from pathlib import Path

# Đọc CSV và phân loại ---
pattern_type0, pattern_type1, pattern_type2 = load_linking_patterns()


# with open("data.csv", "r", encoding="utf-8") as f:
#     reader = csv.reader(f)
#     for i, row in enumerate(reader, start=1):
#         if len(row) != 3:
#             print(f"Lỗi ở dòng {i}: {row}")

# Đọc dữ liệu
df = pd.read_csv('data.csv', encoding='utf-8', on_bad_lines='skip')
df = df[df["content"].str.strip().astype(bool)]  # Loại bỏ dòng rỗng
df = df.drop_duplicates(subset=['content']).reset_index(drop=True)
df["content"] = df["content"].str.lower()  # Chuẩn hóa chữ thường

# Tiền xử lý tiếng Việt
df["content_processed"] = df["content"].apply(lambda x: advanced_phrase_linking(clean_text(x), pattern_type0, pattern_type1, pattern_type2))
print(f"Số dòng rỗng: {df['content'].apply(lambda x: len(x.strip()) == 0).sum()}")
# Loại bỏ các câu trùng nhau (dựa trên cột content)
df = df.drop_duplicates(subset=['content']).reset_index(drop=True)

# In và kiểm tra dữ liệu
for index, row in df.iterrows():
    print(row["content_processed"])

# 3. Vẽ biểu đồ phân phối nhãn
# plt.figure(figsize=(6, 4))
# sns.countplot(x='type', data=df)
# plt.title('Phân phối nhãn trong dữ liệu')
# plt.xlabel('Nhãn (0=An toàn, 1=Lừa đảo)')
# plt.ylabel('Số lượng mẫu')
# plt.show()

# 4. Thống kê độ dài câu theo nhãn
# df['length'] = df['content'].apply(lambda x: len(x.split()))
# plt.figure(figsize=(8, 5))
# sns.boxplot(x='type', y='length', data=df)
# plt.title('Độ dài câu theo từng nhãn')
# plt.xlabel('Nhãn (0=An toàn, 1=Lừa đảo)')
# plt.ylabel('Số từ trong câu')
# plt.show()

# --- 3. Chuẩn bị dữ liệu ---
X = df["content_processed"]
y = df["type"]

# TF-IDF ---
vectorizer = TfidfVectorizer(
    max_features=5000,
    sublinear_tf=True
)

X_tfidf = vectorizer.fit_transform(X)

# Chia train/test
X_train, X_test, y_train, y_test = train_test_split(
    X_tfidf, y, test_size=0.2, random_state=42
)

# Khởi tạo 3 mô hình
models = {
    'SVM': SVC(kernel='linear', probability=True, random_state=42),
    'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
    'NaiveBayes': MultinomialNB()
}

# 7. Train và đánh giá
for name, model in models.items():
    print(f"\n--- Đánh giá mô hình {name} ---")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, digits=4))

# 8. Lưu mô hình tốt nhất
BASE_DIR = Path(__file__).resolve().parents[1]
ML_DIR = BASE_DIR / "mainproject" / "app" / "data_ml"

best_model = models['SVM']
joblib.dump(best_model, ML_DIR / 'model_detect.pkl')
joblib.dump(vectorizer, ML_DIR / 'vectorizer_model_detect.pkl')
print("\nĐã lưu mô hình thành công.")

