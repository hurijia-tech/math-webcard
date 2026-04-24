"""
apply_types.py
type_mappings/ 폴더의 JSON을 읽어 cards_data.json의 type_tags를 업데이트

사용법:
    python apply_types.py

주의:
    - 이미 type_tags가 채워진 문제는 덮어쓰지 않음 (보존)
    - --force 옵션으로 강제 덮어쓰기 가능
      python apply_types.py --force
"""

import json
import sys
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent
DATA_FILE   = BASE_DIR / "cards_data.json"
MAPPING_DIR = BASE_DIR / "type_mappings"

FORCE = "--force" in sys.argv

# ── cards_data.json 로드 ──────────────────────────
def load_cards() -> list[dict]:
    if not DATA_FILE.exists():
        print(f"❌ cards_data.json 없음: {DATA_FILE}")
        exit()
    with open(DATA_FILE, encoding="utf-8-sig") as f:
        return json.load(f)

# ── type_mappings/ JSON 로드 ──────────────────────
def load_mappings() -> dict[str, str]:
    """card_id → type_name 딕셔너리 반환"""
    id_to_type = {}

    if not MAPPING_DIR.exists():
        print(f"❌ type_mappings/ 폴더 없음. 먼저 extract_types.py를 실행하세요.")
        exit()

    for json_file in sorted(MAPPING_DIR.glob("*_types.json")):
        with open(json_file, encoding="utf-8-sig") as f:
            mappings = json.load(f)

        book_name = json_file.stem.replace("_types", "")
        count = 0
        for m in mappings:
            for card_id in m.get("questions", []):
                id_to_type[card_id] = m["type_name"]
                count += 1
        print(f"  📂 {book_name}: {len(mappings)}개 유형, {count}개 문제 매핑 로드")

    return id_to_type

# ── 적용 ─────────────────────────────────────────
def apply(cards: list[dict], id_to_type: dict[str, str]) -> tuple[int, int, int]:
    applied = 0    # 새로 적용
    skipped = 0    # 이미 있어서 스킵
    notfound = 0   # 매핑에 없음

    for card in cards:
        cid = card["id"]
        if cid in id_to_type:
            new_type = id_to_type[cid]
            existing = card.get("type_tags", [])

            # 이미 채워진 경우 --force 없으면 스킵
            if existing and not FORCE:
                skipped += 1
                continue

            card["type_tags"] = [new_type]
            applied += 1
        else:
            notfound += 1

    return applied, skipped, notfound

# ── 메인 실행 ─────────────────────────────────────
def main():
    print("=" * 50)
    print("📌 apply_types.py 실행")
    if FORCE:
        print("  ⚠️  --force 모드: 기존 type_tags 덮어쓰기")
    print("=" * 50)

    print("\n1️⃣  type_mappings/ 로드 중...")
    id_to_type = load_mappings()
    print(f"\n  총 {len(id_to_type)}개 문제 매핑 로드 완료")

    print("\n2️⃣  cards_data.json 로드 중...")
    cards = load_cards()
    print(f"  총 {len(cards)}개 카드 로드")

    print("\n3️⃣  유형 적용 중...")
    applied, skipped, notfound = apply(cards, id_to_type)

    print(f"\n  ✅ 적용됨:     {applied}개")
    print(f"  ⏭️  스킵(이미 있음): {skipped}개  (--force로 강제 적용 가능)")
    print(f"  ❓ 매핑 없음:  {notfound}개")

    # ── 저장 ──
    with open(DATA_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장 완료: {DATA_FILE}")

    # ── 결과 샘플 출력 ──
    print("\n📋 적용 결과 샘플 (type_tags 있는 첫 5개):")
    shown = 0
    for card in cards:
        if card.get("type_tags"):
            print(f"  {card['id']:25s} → {card['type_tags']}")
            shown += 1
            if shown >= 5:
                break

    if applied == 0 and skipped == 0:
        print("\n⚠️  적용된 문제가 없습니다.")
        print("   extract_types.py를 먼저 실행했는지 확인하세요.")

if __name__ == "__main__":
    main()
