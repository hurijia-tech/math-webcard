"""
CSV → cards_data.json 자동 생성 스크립트
1단원 삼각형의 성질 해당 페이지만 추출
"""
import csv
import json
from pathlib import Path, PureWindowsPath

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
        "pages":       list(range(7, 27)),     # 7~26페이지 (p007~p026, p008 없음)
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
        "pages":       list(range(12, 26)),    # 12~25페이지
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
        "pages":       list(range(1, 15)),    # 1~14페이지
    },
]

# ── 생성 ─────────────────────────────────
all_cards = []

for b in BOOKS:
    csv_path = BASE_DIR / b["csv_path"]
    if not csv_path.exists():
        print(f"⚠️  CSV 없음: {csv_path}")
        continue

    count = 0
    with open(csv_path, encoding="utf-8-sig") as f:  # ← BOM 처리
        reader = csv.DictReader(f)
        for row in reader:
            # 페이지 필터링
            try:
                page = int(str(row.get("page", "")).strip())
            except ValueError:
                continue
            if page not in b["pages"]:
                continue

            qid = row[b["id_col"]].strip()

            # 백슬래시(\) 경로도 안전하게 파일명만 추출
            raw_img = row[b["img_col"]].strip().replace("\\", "/")
            img_file = raw_img.split("/")[-1]
            img_path = b["img_prefix"] + img_file

            card = {
                "id":               b["id_prefix"] + qid,
                "book":             b["book"],
                "course":           b["course"],
                "chapter":          b["chapter"],
                "sub_chapter":      b["sub_chapter"],
                "type_tags":        [],
                "difficulty":       b["difficulty"],
                "question_image":   img_path,
                "answer":           "",
                "solution":         "",
                "solution_image":   "",
                "verification_status": "check",
                "verification_text":   "미검증",
                "similar":          [],
            }
            all_cards.append(card)
            count += 1

    print(f"✅ {b['book']}: {count}개")

# ── 저장 ─────────────────────────────────
out_path = BASE_DIR / "cards_data.json"
with open(out_path, "w", encoding="utf-8-sig") as f:
    json.dump(all_cards, f, ensure_ascii=False, indent=2)

print(f"\n💾 저장 완료: {out_path}")
print(f"   총 {len(all_cards)}개 문제")