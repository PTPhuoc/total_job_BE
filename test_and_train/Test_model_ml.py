import csv
import re
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import joblib
import numpy as np
import torch
from linking_word import advanced_phrase_linking, load_linking_patterns, clean_text
from pathlib import Path

# Văn bản cần kiểm tra
scam1 = """shoppe tuyển dụng nhân viên
Làm online trên điện thoại. Không phải lên Shop.
- Thời gian:
+ Sáng: 8h00-11h
+ Chiều: 13h00-16h00
+ Tối: 19h30-22h30
Tùy ca bạn chọn, làm cả 3 thu nhập cao hơn.
Thu nhập trung bình: 4-8tr/tháng (không bán hàng online nha).
- Yêu cầu: từ 22-55 tuổi, có thẻ A.T.M để nhận lương
Ai giới thiệu hoặc có người quen cần việc làm thêm inbox để được tư vấn nhé
Vì số lượng bạn có nhu cầu làm việc lớn nên các bạn CHỦ ĐỘNG NHẮN TIN cho page để nhận mô tả công việc sớm nhất nhé"""

scam2 = """Xin chào, mình là giám đốc marketing của Shopee. 
hiện tại của hàng Shopee cần tuyển số lượng lớn nhân viên chuyên đặt hàng để nâng cao số lượng giao dịch và thứ hạng của cửa hàng. 
Chỉ cần có kinh nghiệm mua sắm trực tuyến. 
mỗi ngày bạn có thể dễ dàng kiếm 800.000 đồng bằng điện thoại di động và tiền lương sẽ được quyết toán ngay trong ngày. 
Nếu bạn muốn tham gia công việc này vui lòng add tài khoản Zalo của giám đốc marketing: 84567233168. 
Hiện tại chỉ còn 30 suất duy nhất, chỉ trong ngày hôm nay!
(Lưu ý: yêu cầu người tham gia từ 22 tuổi trở lên, học sinh sinh viên vui lòng không tham gia)"""

scam3 = """
1. Nhân viên bảo vệ
2. Nhân viên giám sát
3. Nhân viên kiểm soát vé
4. Nhân viên an ninh
- Phỏng vấn nhanh gọn lẹ, không thủ tục rườm rà! - Nhận kết quả ngay - Đi làm liền!
Nhận sinh viên làm thời vụ từ 1-3 tháng.
Ca làm việc linh hoạt Part-time & Full-time phù hợp với lịch học sinh viên/lịch cá nhân của từng người.
- Ca 4 tiếng: 8h-12h, 10h-14h, 14h-18h, 18h-22h, 19h-23h, 20h-24h.
- Ca 6 tiếng: 8h-14h, 9h-15h, 15h-21h, 10h-16h, 16h-22h - Ca 8 tiếng: 8h-16h, 16h -24h, 9h-17h, 14h-22h, 15h-23h - Ca 10 tiếng: 8h-18h,9h-19h, 10h-20h
- Ca 12 tiếng: 7h-19h, 19h-7h, 8h-20h, 20h-8h
Mức lương chính thức:
+ Ca Part-time 4h/6h/8h/10h: Lương 35 Ngàn /Giờ + Ca Full time 12 tiếng: (12 Triệu - 15 Triệu)/tháng. - Hỗ trợ nhà ở miễn phí đối với các bạn có nhu cầu - Phụ cấp chuyên cần, trách nhiệm, phụ cấp cơm, xắ từ 600.000₫ - 1.200.000đ/tháng
Yêu cầu: Nam/nữ tuổi 17-45, có sức khoẻ, có giấy tờ tuỳ thân đầy đủ, không yêu cầu kinh nghiệm bằng cấp.
Liên hệ trực tiếp cho Quản lý nhân sự để đăng ký ứng tuyển và nhận lịch phỏng vấn:
Hotline: 0931.923.127 - 0964.587.345 - Gặp Anh Trung (Vui lòng gọi, không nhắn tin)"""

scam4 = """công ty mình cần tuyển dụng nhân viên, nên hợp tác với nhiều trang tuyển dụng để tìm kiếm ứng viên phù hợp.
Bạn cũng có đăng tải tìm việc nên công ty có liên hệ của bạn nha.
Công ty mình đang chạy Dự án Seeding Makerting làm tương tác truyền thông cho các địa danh nổi tiếng về du lịch ,vận tải hàng không, khách sạn, nhà hàng...
Do vậy cần tuyển một số lượng lớn nhân viên CHUYÊN tương tác trên các nền tảng xã hội để tạo hiệu ứng tốt thúc đẩy sử dụng dịch vụ cho khách hàng đối tác với mức thu nhập từ 7tr – 12tr /tháng
Thời gian làm việc linh động chỉ cần rảnh từ (1-2 tiếng / ngày ) và có thể làm ở bất cứ đâu"""

scam5 = """Shopee thuê để xử lý hàng tồn kho cho người bán. Kiếm 300 - 1000k VND 1 ngày.
Yêu cầu công việc: Trên 23 tuổi, có kiến thức mạng đơn giản và kinh nghiệm mua sắm trực tuyến."""

text1 = """Mô tả công việc
Phát triển và duy trì mối quan hệ với đối tác ngân hàng Vietinbank;
Phối hợp với các cán bộ ngân hàng để đạt được chỉ tiêu kinh doanh chung của Chi nhánh/Phó giám đốc.
Tư vấn và chăm sóc khách hàng, đảm bảo khách hàng nắm rõ sản phẩm/dịch vụ của công ty FWD.
Làm việc tại các chi nhánh, phòng giao dịch của ngân hàng.
Thực hiện các báo cáo kinh doanh gửi cho cấp quản lý.

Yêu cầu ứng viên
Tuổi 22 - 35
Đã tốt nghiệp Cao đẳng trở lên.
Yêu thích công việc tư vấn, kinh doanh và có tối thiểu 1 năm kinh nghiệm làm sales. (Ưu tiên có kinh nghiệm trong lĩnh vực Bảo Hiểm, Tài Chính, Ngân hàng).
Có kỹ năng giao tiếp và đàm phán; Có kỹ năng tư vấn và chăm sóc khách hàng.
Có ước mơ, hoài bão, sự nhiệt huyết và niềm tin “khách hàng là trọng tâm” .
Chịu được áp lực công việc, tác phong chuyên nghiệp, tinh thần học hỏi và trách nhiệm trong công việc...
Thu nhập
Thu nhập: Thoả thuận
Lương cứng không phụ thuộc doanh số
Quyền lợi
Mức lương: 10 triệu - 12 triệu/1 tháng + Thưởng.
Thưởng hiệu suất kinh doanh và dịch vụ tốt hàng tháng, quý, năm.
Gói chăm sóc sức khoẻ hàng năm, hỗ trợ tiền điện thoại hàng tháng, hỗ trợ chi phí thai sản.
Được đào tạo bài bản, chuyên nghiệp, làm việc trong môi trường chuyên nghiệp năng động.
Chương trình phát triển nguồn nhân tài cùng cơ hội thăng tiến nội bộ.
Và những quyền lợi khác...
Cơ hội của bạn:

Được làm việc và phát triển trong kênh Bancassurance năng động và chuyên nghiệp nhất với đối tác Ngân hàng lớn, uy tín hàng đầu tại Việt Nam;
Phát triển kỹ năng nghể nghiệp trong ngành dịch vụ Tài chính;
Được làm việc, tương tác, cung cấp dịch vụ tư vấn sản phẩm Bảo hiểm tới Khách hàng, phối hợp với các cán bộ Ngân hàng để cùng chăm sóc khách hàng khi sử dụng dịch vụ.
Làm việc tại các chi nhánh, phòng giao dịch của ngân hàng.
Phát triển các kỹ năng cho bản thân và nghề nghiệp."""

# --- Tải mô hình và vectorizer ---
BASE_DIR = Path(__file__).resolve().parents[1]
ML_DIR = BASE_DIR / "mainproject" / "app" / "data_ml"

model = joblib.load(ML_DIR / "model_detect.pkl")
vectorizer = joblib.load(ML_DIR / "vectorizer_model_detect.pkl")
st_model = SentenceTransformer(str(ML_DIR / "sentence_finetuned"))
data_scam_template = joblib.load(ML_DIR / "scam_encode.pkl")
scam_sentences = data_scam_template["sentences"]
scam_embeddings = data_scam_template["embeddings"]
threshold = joblib.load(ML_DIR / "scam_threshold.pkl")
threshold_point = threshold["threshold"]

pattern_type0, pattern_type1, pattern_type2 = load_linking_patterns()

(sentences) = re.split(r'(?<=[.])\s+(?=[A-ZÀ-Ỹ\-\(])|\n+', scam1)

processed_sentences = []
for s in sentences:
    s_clean = clean_text(s.strip())
    s_linked = advanced_phrase_linking(s_clean, pattern_type0, pattern_type1, pattern_type2)
    if s_linked:
        processed_sentences.append(s_linked)

# for content in processed_sentences:
#     print(content)

# --- Biến đổi TF-IDF ---
X = vectorizer.transform(processed_sentences)
predictions = model.predict(X)
probabilities = model.predict_proba(X)[:, 1]

# --- In kết quả ---
score = 0
print("\nKết quả phân tích:\n")

for i, s in enumerate(processed_sentences):
    label = predictions[i]
    scam_prob = probabilities[i]
    max_sim = 0.0

    if label == 1:
        sent_emb = st_model.encode(s, convert_to_tensor=True)
        sims = util.cos_sim(sent_emb, scam_embeddings)[0]
        max_sim = float(torch.max(sims))
        if max_sim >= threshold_point:
            score += 1

    if label == 1:
        print(f"{s} → nghi ngờ ({scam_prob:.2f}) | tương đồng: {max_sim:.2f}")
    else:
        print(f"{s} → bình thường ({scam_prob:.2f})")

# --- Tính mức độ uy tín tổng thể ---
trust_score = ((len(processed_sentences) - score) / len(processed_sentences)) * 100 if processed_sentences else 100
print(f"\n----------\nMức độ uy tín tổng thể: {round(trust_score, 2)}%")