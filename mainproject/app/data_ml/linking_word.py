import csv
import re
import os
from django.conf import settings


def clean_text(text):
    text = re.sub(r'^[\-\–\+]\s*', '', text.strip())
    text = re.sub(r'[.]+$', "", text)
    text = re.sub(r'[\:\,\!\•\;]', "", text)
    return text.lower()


def load_linking_patterns():
    csv_path = os.path.join(settings.BASE_DIR, "app", "data_ml", "linking_word.csv")
    phrases_type0 = set()  # nối cụm
    phrases_type1 = set()  # nối phải
    phrases_type2 = set()  # nối trái

    # --- Đọc CSV ---
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row["text"].strip().lower()
            type_ = row.get("type", "0").strip()
            if not text:
                continue
            if type_ == "1":
                phrases_type1.add(text)
            elif type_ == "2":
                phrases_type2.add(text)
            else:
                phrases_type0.add(text)

    # --- Tạo pattern ---
    pattern_type0 = (
        re.compile(
            r'(?<![\wÀ-ỹ])(?:' + '|'.join(map(re.escape, sorted(phrases_type0, key=len, reverse=True))) + r')(?![\wÀ-ỹ])',
            flags=re.IGNORECASE
        )
        if phrases_type0 else None
    )

    pattern_type1 = (
        re.compile(
            r'(?<![\wÀ-ỹ])(?:' + '|'.join(map(re.escape, sorted(phrases_type1, key=len, reverse=True))) + r')\s+(\w+)',
            flags=re.IGNORECASE
        )
        if phrases_type1 else None
    )

    pattern_type2 = (
        re.compile(
            r'(\w+)\s+(?:' + '|'.join(map(re.escape, sorted(phrases_type2, key=len, reverse=True))) + r')(?![\wÀ-ỹ])',
            flags=re.IGNORECASE
        )
        if phrases_type2 else None
    )

    # --- Trả về 3 biến ---
    return pattern_type0, pattern_type1, pattern_type2


def advanced_phrase_linking(sentence, pattern_type0, pattern_type1, pattern_type2):
    # Nối cụm đầy đủ
    if pattern_type0:
        sentence = pattern_type0.sub(lambda m: m.group(0).replace(" ", "_"), sentence)
    # Nối phải
    if pattern_type1:
        sentence = pattern_type1.sub(lambda m: m.group(0).replace(" ", "_"), sentence)
    # Nối trái
    if pattern_type2:
        sentence = pattern_type2.sub(lambda m: m.group(0).replace(" ", "_"), sentence)
    return sentence