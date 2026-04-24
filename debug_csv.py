import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

csv_files = [
    ("바이블",        BASE_DIR / "바이블" / "output_crops" / "metadata.csv"),
    ("자이스토리",    BASE_DIR / "자이스토리" / "output_crops" / "metadata.csv"),
    ("유형해결의법칙", BASE_DIR / "유형해결의법칙" / "output_crops" / "metadata.csv"),
]

for name, csv_path in csv_files:
    print(f"\n{'='*50}")
    print(f"[{name}] {csv_path}")
    if not csv_path.exists():
        print("❌ 파일 없음!")
        continue
    print("✅ 파일 존재")
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        print("❌ 데이터 행 없음")
        continue
    print(f"   컬럼명: {list(rows[0].keys())}")
    print(f"   총 행 수: {len(rows)}")
    print(f"   첫 번째 행: {dict(rows[0])}")
    print(f"   두 번째 행: {dict(rows[1]) if len(rows) > 1 else '없음'}")