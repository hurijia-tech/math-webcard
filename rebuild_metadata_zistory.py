"""
자이스토리 metadata.csv 재생성 스크립트
실제 크롭된 PNG 파일명 기준으로 page, question_id, image_path 추출
파일명 형식: p012_A14.png → page=12, question_id=A14
"""
import csv
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "자이스토리" / "output_crops" / "images"
OUT_CSV    = BASE_DIR / "자이스토리" / "output_crops" / "metadata.csv"

# ── 파일 스캔 ─────────────────────────────
if not IMAGES_DIR.exists():
    print(f"❌ 이미지 폴더 없음: {IMAGES_DIR}")
    exit()

pattern = re.compile(r"^p(\d+)_(.+)\.png$", re.IGNORECASE)

rows = []
skipped = []

for f in sorted(IMAGES_DIR.glob("*.png")):
    m = pattern.match(f.name)
    if not m:
        skipped.append(f.name)
        continue

    page       = int(m.group(1))          # 012 → 12
    question_id = m.group(2)              # A14
    image_path  = f"output_crops/images/{f.name}"

    rows.append({
        "page":        page,
        "question_id": question_id,
        "image_path":  image_path,
    })

# ── 정렬: 페이지 → question_id ────────────
rows.sort(key=lambda r: (r["page"], r["question_id"]))

# ── CSV 저장 ──────────────────────────────
with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["page", "question_id", "image_path"])
    writer.writeheader()
    writer.writerows(rows)

# ── 결과 출력 ─────────────────────────────
print(f"✅ metadata.csv 생성 완료: {OUT_CSV}")
print(f"   총 {len(rows)}개 문제")

pages = sorted(set(r["page"] for r in rows))
print(f"   페이지 목록: {pages}")

if skipped:
    print(f"\n⚠️  패턴 불일치로 건너뛴 파일 {len(skipped)}개:")
    for s in skipped:
        print(f"   {s}")

print("\n📋 샘플 (첫 5개):")
for r in rows[:5]:
    print(f"   page={r['page']:3d}  question_id={r['question_id']:6s}  {r['image_path']}")