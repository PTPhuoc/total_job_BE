import joblib
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from linking_word import load_linking_patterns, advanced_phrase_linking, clean_text
from pathlib import Path

# --- Load mô hình đã fine-tune ---
BASE_DIR = Path(__file__).resolve().parents[1]
ML_DIR = BASE_DIR / "mainproject" / "app" / "data_ml"

model = SentenceTransformer(str(ML_DIR / "sentence_finetuned"))
data_scam_template = joblib.load(ML_DIR / "scam_encode.pkl")
scam_sentences = data_scam_template["sentences"]
scam_embeddings = data_scam_template["embeddings"]

pattern_type0, pattern_type1, pattern_type2 = load_linking_patterns()

# --- Load dữ liệu huấn luyện ---
df = pd.read_csv("data.csv", encoding="utf-8")
df = df[df["content"].str.strip().astype(bool)]  # Loại bỏ dòng rỗng
df = df.drop_duplicates(subset=["content"]).reset_index(drop=True)
df["content"] = df["content"].str.lower()  # Chuẩn hóa chữ thường

# --- Xử lý text ---
df["content_processed"] = df["content"].apply(
    lambda x: advanced_phrase_linking(clean_text(x), pattern_type0, pattern_type1, pattern_type2)
)

df_neg = df[df["type"] == 0].sample(99, random_state=24)
df_pos = df[df["type"] == 1].sample(99, random_state=24)

# Tính cosine cho các mẫu "0" (an toàn)
sim_neg = []
for _, row in df_neg.iterrows():
    emb = model.encode(row["content_processed"], convert_to_tensor=True)
    sims = util.cos_sim(emb, scam_embeddings)[0]
    max_sim = float(sims.max())
    sim_neg.append(max_sim)

# Tính cosine cho các mẫu "1" (Lừa đảo)
sim_pos = []
for _, row in df_pos.iterrows():
    emb = model.encode(row["content_processed"], convert_to_tensor=True)
    sims = util.cos_sim(emb, scam_embeddings)[0]
    max_sim = float(sims.max())
    sim_pos.append(max_sim)

threshold = (np.mean(sim_neg) + np.mean(sim_pos)) / 2

print(f"Ngưỡng loại 0: {np.mean(sim_neg):.3f}")
print(f"Ngưỡng loại 1: {np.mean(sim_pos):.3f}")
print(f"Ngưỡng trung bình: {threshold:.3f}")
joblib.dump({"threshold": threshold}, ML_DIR / "scam_threshold.pkl")
print("Đã xuất ngưỡng!")
