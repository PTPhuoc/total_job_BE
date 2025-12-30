import joblib
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import pandas as pd
import re
import csv
import numpy as np
from linking_word import load_linking_patterns, advanced_phrase_linking, clean_text
from pathlib import Path

# --- Đọc CSV và phân loại ---
pattern_type0, pattern_type1, pattern_type2 = load_linking_patterns()


def get_scam_template():
    df_scam = pd.read_csv('data_embedding.csv', encoding='utf-8', on_bad_lines='skip')
    df_scam = df_scam[df_scam["type"] == 1]  # chỉ lấy nhãn scam
    df_scam = df_scam.dropna(subset=["sentence1", "sentence2"])
    sentences = pd.concat([df_scam["sentence1"], df_scam["sentence2"]], ignore_index=True)
    sentences = sentences.drop_duplicates().str.strip().str.lower()
    sentences = sentences[sentences.astype(bool)]  # bỏ rỗng

    # Làm sạch và xử lý nối cụm
    sentences_processed = sentences.apply(
        lambda x: advanced_phrase_linking(clean_text(x), pattern_type0, pattern_type1, pattern_type2)
    ).tolist()

    return sentences_processed


# --- Load dữ liệu ---
df = pd.read_csv("data_embedding.csv")
df["sentence1_processed"] = df["sentence1"].apply(lambda x: advanced_phrase_linking(clean_text(x), pattern_type0, pattern_type1, pattern_type2))
df["sentence2_processed"] = df["sentence2"].apply(lambda x: advanced_phrase_linking(clean_text(x), pattern_type0, pattern_type1, pattern_type2))

# --- Tạo InputExample ---
train_examples = [
    InputExample(texts=[row.sentence1_processed, row.sentence2_processed], label=float(row.type))
    for _, row in df.iterrows()
]

# Model gốc (hiểu tiếng Việt khá tốt)
model = SentenceTransformer("keepitreal/vietnamese-sbert")

# Dataset và DataLoader
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

# Loss function
train_loss = losses.MultipleNegativesRankingLoss(model)

# Fine-tune
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=10,
    warmup_steps=100,
    show_progress_bar=True
)

# --- Lưu mô hình ---
BASE_DIR = Path(__file__).resolve().parents[1]
ML_DIR = BASE_DIR / "mainproject" / "app" / "data_ml"

model.save(str(ML_DIR / "sentence_finetuned"))
print("Lưu mô hình thành công!")

list_scam = get_scam_template()
embeddings = model.encode(list_scam, batch_size=16, convert_to_tensor=True, show_progress_bar=True)
joblib.dump({"sentences": list_scam, "embeddings": embeddings}, ML_DIR / "scam_encode.pkl")
print("Đã lưu scam encode chứa embedding và câu gốc.")