import csv
import os

# Tên file CSV
filename = "data.csv"
fieldnames = ["content", "type"]

# Kiểm tra và tạo file nếu chưa tồn tại
if not os.path.exists(filename):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
    print(f"Đã tạo file mới: {filename}")

# Đọc dữ liệu hiện có (nếu có)
rows = []
with open(filename, mode="r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    # Kiểm tra đúng cột
    if reader.fieldnames != fieldnames:
        print("File CSV không đúng định dạng cột!")
        exit()
    for row in reader:
        rows.append(row)

# Nhập liệu mới từ console
while True:
    print("\nNhập nội dung mới (gõ 'exit' để thoát):")
    content = input("Nội dung câu (content): ").strip()
    if content.lower() == "exit":
        break

    type_input_str = input("Loại (type - ví dụ: 'lừa đảo' = 1 hoặc 'tin cậy' = 0): ").strip()
    if not type_input_str:
        type_input_str = input().strip()
    if type_input_str not in ['0', '1']:
        print("⚠ Loại không hợp lệ! Chỉ nhận 'lừa đảo' = 1 hoặc 'tin cậy' = 0.")
        continue

    type_input = int(type_input_str)

    rows.append({"content": content, "type": type_input})
    print("✓ Đã thêm vào bộ dữ liệu.")

# Ghi đè lại file CSV
with open(filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n✅ Đã ghi {len(rows)} dòng vào file '{filename}'.")
