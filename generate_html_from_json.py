"""
통합 문제 카드 HTML 생성기
cards_data.json → cards.html

사용법:
  python generate_html_from_json.py
"""

import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH   = PROJECT_DIR / "cards_data.json"
TEMPLATE_PATH = PROJECT_DIR / "cards.html"
OUTPUT_PATH = PROJECT_DIR / "cards_output.html"

# ── 실행 ─────────────────────────────────
with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

with open(TEMPLATE_PATH, encoding="utf-8") as f:
    html = f.read()

# 인라인 데이터 삽입 (fetch 실패 대비)
data_json = json.dumps(data, ensure_ascii=False)
html = html.replace("/*INLINE_DATA*/[]", f"/*INLINE_DATA*/{data_json}")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 생성 완료: {OUTPUT_PATH}")
print(f"   총 {len(data)}개 문제")
