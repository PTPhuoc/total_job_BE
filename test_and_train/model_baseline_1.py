import pandas as pd
import re
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split


KEYWORDS_FEE = [
    "đặt cọc", "đóng phí", "lệ phí", "phí hồ sơ", "phí đào tạo", "chuyển khoản", "nộp phí",
    "tiền đặt cọc", "phí nhận việc", "phí ủy quyền", "phí đồng phục", "tiền đồng phục",
]

KEYWORDS_URGENCY = [
    "tuyển gấp", "nhanh tay", "còn vài suất", "duy nhất hôm nay", "số lượng có hạn",
    "ưu tiên nộp sớm", "chỉ còn ít ngày", "số lượng không nhiều", "cần gấp ứng viên"
]

KEYWORDS_EASY_JOB = [
    "việc nhẹ lương cao", "không cần kinh nghiệm", "làm online", "làm tại nhà",
    "nhận việc ngay", "thu nhập cao", "không cần bằng cấp", "không cần đến văn phòng"
]

ALL_KEYWORDS = KEYWORDS_FEE + KEYWORDS_URGENCY + KEYWORDS_EASY_JOB


def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def count_keywords(text, keywords):
    count = 0
    found = []
    for kw in keywords:
        if kw in text:
            count += 1
            found.append(kw)
    return count, found


def predict_scam_label(text, threshold=0.03):
    text = normalize(text)
    total_keywords = len(ALL_KEYWORDS)
    matched_count, _ = count_keywords(text, ALL_KEYWORDS)
    score = matched_count / total_keywords if total_keywords > 0 else 0
    return 1 if score >= threshold else 0


df = pd.read_csv('data.csv')
df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df['type'])


def evaluate_threshold(threshold, X, y_true):
    y_pred = X.apply(lambda x: predict_scam_label(x, threshold=threshold))
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    rec = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)

    return acc, prec, rec, f1


# Thử các ngưỡng khác nhau
thresholds = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07]
results = []

for thresh in thresholds:
    acc, prec, rec, f1 = evaluate_threshold(thresh, df_train['content'], df_train['type'])
    results.append({
        'Threshold': thresh,
        'Accuracy': acc,
        'Precision': prec,
        'Recall': rec,
        'F1-Score': f1
    })

df_threshold_results = pd.DataFrame(results)
print("\nKết quả thử nghiệm các ngưỡng:")
print(df_threshold_results.round(4))

# Chọn ngưỡng tốt nhất (thường chọn F1 cao nhất)
best_threshold = df_threshold_results.loc[df_threshold_results['F1-Score'].idxmax(), 'Threshold']
print(f"\nNgưỡng tốt nhất: {best_threshold} (F1-Score: {df_threshold_results['F1-Score'].max():.4f})")

# Dự đoán trên tập test
y_true = df_test['type'].values
y_pred = df_test['content'].apply(lambda x: predict_scam_label(x, threshold=best_threshold)).values

# Tính các metrics
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
recall = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)

print(f"\n--- KẾT QUẢ CHÍNH ---")
print(f"Accuracy:  {accuracy:.4f} ({accuracy * 100:.2f}%)")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-Score:  {f1:.4f}")

print(f"\n--- BÁO CÁO PHÂN LOẠI CHI TIẾT CHO PHƯƠNG PHÁP TỪ KHÓA ---")
print(classification_report(y_true, y_pred, target_names=['An toàn', 'Lừa đảo']))


