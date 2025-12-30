import pandas as pd
import joblib
from pathlib import Path
import re
import torch
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, \
    confusion_matrix
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer, util

from linking_word import load_linking_patterns, advanced_phrase_linking, clean_text

# Đọc dữ liệu gốc
df = pd.read_csv('data.csv')
df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df['type'])
BASE_DIR = Path(__file__).resolve().parents[1]
ML_DIR = BASE_DIR / "mainproject" / "app" / "data_ml"

try:
    model = joblib.load(ML_DIR / "model_detect.pkl")
    vectorizer = joblib.load(ML_DIR / "vectorizer_model_detect.pkl")
    st_model = SentenceTransformer(str(ML_DIR / "sentence_finetuned"))
    data_scam_template = joblib.load(ML_DIR / "scam_encode.pkl")
    scam_sentences = data_scam_template["sentences"]
    scam_embeddings = data_scam_template["embeddings"]
    threshold = joblib.load(ML_DIR / "scam_threshold.pkl")
    threshold_point = threshold["threshold"]

except Exception as e:
    print(f"✗ Lỗi khi tải mô hình: {e}")
    print("Đang sử dụng mô hình mặc định từ code gốc...")
    # Fallback nếu không tải được
    model = None
    vectorizer = None
    st_model = None
    scam_embeddings = None
    threshold_point = 0.628

pattern_type0, pattern_type1, pattern_type2 = load_linking_patterns()


def predict_simple(text):
    s_clean = clean_text(text.strip())
    s_linked = advanced_phrase_linking(s_clean, pattern_type0, pattern_type1, pattern_type2)

    if not s_linked:
        return 0, 0.0, 0.0

    X = vectorizer.transform([s_linked])
    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0, 1]

    similarity = 0.0
    if prediction == 1 and st_model and scam_embeddings is not None:
        sent_emb = st_model.encode(s_linked, convert_to_tensor=True)
        sims = util.cos_sim(sent_emb, scam_embeddings)[0]
        similarity = float(torch.max(sims))

        if similarity >= threshold_point:
            final_label = 1
        else:
            final_label = 0
    else:
        final_label = prediction

    return final_label, probability, similarity


true_labels = df_test['type'].tolist()
test_texts = df_test['content'].tolist()

predicted_labels = []
probabilities = []
similarities = []

for i, text in enumerate(test_texts):
    label, prob, sim = predict_simple(text)
    predicted_labels.append(label)
    probabilities.append(prob)
    similarities.append(sim)

accuracy = accuracy_score(true_labels, predicted_labels)
precision = precision_score(true_labels, predicted_labels, pos_label=1, zero_division=0)
recall = recall_score(true_labels, predicted_labels, pos_label=1, zero_division=0)
f1 = f1_score(true_labels, predicted_labels, pos_label=1, zero_division=0)

print(f"\n--- KẾT QUẢ CHÍNH ---")
print(f"Accuracy:  {accuracy:.4f} ({accuracy * 100:.2f}%)")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-Score:  {f1:.4f}")

print(f"\n--- BÁO CÁO PHÂN LOẠI CHI TIẾT CHO PHƯƠNG PHÁP GỐC ---")
report = classification_report(true_labels, predicted_labels,
                               target_names=['An toàn', 'Lừa đảo'],
                               digits=4)
print(report)
