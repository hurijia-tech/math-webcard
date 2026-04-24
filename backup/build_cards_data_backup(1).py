"""
CSV → cards_data.json 자동 생성 스크립트
"""
import csv
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ── 교재 설정 ─────────────────────────────
BOOKS = [
    {
        "book":        "바이블",
        "course":      "중등수학 2-2",
        "chapter":     "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "difficulty":  "",
        "csv_path":    "바이블/output_crops/metadata.csv",
        "img_prefix":  "바이블/output_crops/images/",
        "id_prefix":   "바이블_",
        "id_col":      "question_id",
        "img_col":     "image_path",
    },
    {
        "book":        "자이스토리",
        "course":      "중등수학 2-2",
        "chapter":     "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "difficulty":  "",
        "csv_path":    "자이스토리/output_crops/metadata.csv",
        "img_prefix":  "자이스토리/output_crops/images/",
        "id_prefix":   "자이스토리_",
        "id_col":      "question_id",
        "img_col":     "image_path",
    },
    {
        "book":        "유형해결의법칙",
        "course":      "중등수학 2-2",
        "chapter":     "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "difficulty":  "",
        "csv_path":    "유형해결의법칙/output_crops/metadata.csv",
        "img_prefix":  "유형해결의법칙/output_crops/images/",
        "id_prefix":   "유형법칙_",
        "id_col":      "question_id",
        "img_col":     "image_path",
    },
]

# ── 생성 ─────────────────────────────────
all_cards = []

for b in BOOKS:
    csv_path = BASE_DIR / b["csv_path"]
    if not csv_path.exists():
        print(f"⚠️  CSV 없음: {csv_path}")
        continue

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid      = row[b["id_col"]].strip()
            img_file = Path(row[b["img_col"]].strip()).name
            img_path = b["img_prefix"] + img_file

            card = {
                "id":               b["id_prefix"] + qid,
                "book":             b["book"],
                "course":           b["course"],
                "chapter":          b["chapter"],
                "sub_chapter":      b["sub_chapter"],
                "type_tags":        [],        # 나중에 태깅
                "difficulty":       b["difficulty"],
                "question_image":   img_path,
                "answer":           "",
                "solution":         "",
                "solution_image":   "",
                "verification_status": "check",
                "verification_text":   "미검증",
                "similar":          [],        # 나중에 연결
            }
            all_cards.append(card)

    print(f"✅ {b['book']}: {sum(1 for c in all_cards if c['book']==b['book'])}개")

# ── 저장 ─────────────────────────────────
out_path = BASE_DIR / "cards_data.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_cards, f, ensure_ascii=False, indent=2)

print(f"\n💾 저장 완료: {out_path}")
print(f"   총 {len(all_cards)}개 문제")