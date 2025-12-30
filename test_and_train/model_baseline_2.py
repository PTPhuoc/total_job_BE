from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from linking_word import load_linking_patterns, advanced_phrase_linking, clean_text
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

pattern_type0, pattern_type1, pattern_type2 = load_linking_patterns()


def preprocess_sentence(s):
    return advanced_phrase_linking(clean_text(s), pattern_type0, pattern_type1, pattern_type2)


def get_scam_template():
    df = pd.read_csv('data_embedding.csv', encoding='utf-8', on_bad_lines='skip')
    df = df[df["type"] == 1]  # chỉ lấy nhãn scam
    df = df.dropna(subset=["sentence1", "sentence2"])

    sentences = pd.concat([df["sentence1"], df["sentence2"]], ignore_index=True)
    sentences = sentences.drop_duplicates().str.strip().str.lower()
    sentences = sentences[sentences.astype(bool)]

    return sentences.apply(preprocess_sentence).tolist()


# === Load template scam ===
scam_templates = get_scam_template()

# === Build TF-IDF model ===
vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
tfidf_matrix = vectorizer.fit_transform(scam_templates)

def baseline2_check_scam(text):
    text_processed = preprocess_sentence(text)
    vec = vectorizer.transform([text_processed])
    sims = cosine_similarity(vec, tfidf_matrix)[0]
    return max(sims)


df = pd.read_csv("data.csv")
scores_1 = [baseline2_check_scam(s) for s in df[df["type"] == 1]["content"]]
scores_0 = [baseline2_check_scam(s) for s in df[df["type"] == 0]["content"]]
thr_1 = sum(scores_1) / len(scores_1)
thr_0 = sum(scores_0) / len(scores_0)
SCAM_THR = (thr_1 + thr_0) / 2


def baseline2_check_scam(text):
    text_processed = preprocess_sentence(text)
    vec = vectorizer.transform([text_processed])
    sims = cosine_similarity(vec, tfidf_matrix)[0]
    return max(sims) if len(sims) > 0 else 0


def baseline2_predict(text):
    sim = baseline2_check_scam(text)
    label = 1 if sim >= SCAM_THR else 0
    return label, sim


df = pd.read_csv('data.csv')

# Chia tập train/test (80-20)
df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df['type'])


test_texts = df_test["content"].tolist()
true_labels = df_test["type"].tolist()

predicted_labels = []
similarity_scores = []

for text in test_texts:
    label, sim = baseline2_predict(text)
    predicted_labels.append(label)
    similarity_scores.append(sim)

accuracy = accuracy_score(true_labels, predicted_labels)
precision = precision_score(true_labels, predicted_labels, pos_label=1, zero_division=0)
recall = recall_score(true_labels, predicted_labels, pos_label=1, zero_division=0)
f1 = f1_score(true_labels, predicted_labels, pos_label=1, zero_division=0)

print(f"\n--- KẾT QUẢ CHÍNH ---")
print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-Score:  {f1:.4f}")

print(f"\n--- BÁO CÁO PHÂN LOẠI CHI TIẾT CHO PHƯƠNG PHÁP TƯƠNG ĐỒNG TF-IDF ---")
report = classification_report(true_labels, predicted_labels,
                               target_names=['An toàn', 'Lừa đảo'],
                               digits=4)
print(report)
