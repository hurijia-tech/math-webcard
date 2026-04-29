# apply_keywords.py
# keyword_mappings/ 의 JSON을 읽어 cards_data.json에 keywords 필드 적용

import json
import os

CARDS_DATA_PATH = "cards_data.json"
KEYWORD_MAPPINGS_DIR = "keyword_mappings"

KEYWORD_LABEL_MAP = {
    "대표문제": "대표문제",
    "서술형": "서술형",
    "잘틀리는문제": "잘틀리는문제",
    "고난도": "고난도",
    "창의사고력": "창의/사고력"
}

def load_keyword_mappings():
    """keyword_mappings/ 폴더에서 교재별 키워드 매핑 로드"""
    # 문제ID → 키워드 리스트 딕셔너리로 변환
    id_to_keywords = {}

    for filename in os.listdir(KEYWORD_MAPPINGS_DIR):
        if not filename.endswith("_keywords.json"):
            continue

        filepath = os.path.join(KEYWORD_MAPPINGS_DIR, filename)
        with open(filepath, "r", encoding="utf-8-sig") as f:
            mapping = json.load(f)

        book_name = filename.replace("_keywords.json", "")
        print(f"📂 로드: {book_name}")

        for kw_key, id_list in mapping.items():
            label = KEYWORD_LABEL_MAP.get(kw_key, kw_key)
            for problem_id in id_list:
                if problem_id not in id_to_keywords:
                    id_to_keywords[problem_id] = []
                if label not in id_to_keywords[problem_id]:
                    id_to_keywords[problem_id].append(label)

    return id_to_keywords


def apply_keywords():
    # cards_data.json 로드
    with open(CARDS_DATA_PATH, "r", encoding="utf-8-sig") as f:
        cards = json.load(f)

    print(f"\n📋 총 문제 수: {len(cards)}개")

    # 키워드 매핑 로드
    id_to_keywords = load_keyword_mappings()
    print(f"🔑 키워드 매핑된 문제 수: {len(id_to_keywords)}개\n")

    # keywords 필드 적용
    updated_count = 0
    for card in cards:
        card_id = card.get("id", "")

        # ID에서 숫자/문자 부분만 추출
        # 예: "바이블_0014" → "0014"
        # 예: "자이스토리_A14" → "A14"
        # 예: "유형해결의법칙_0011" → "0011"
        parts = card_id.split("_")
        problem_num = parts[-1] if len(parts) > 1 else card_id

        if problem_num in id_to_keywords:
            card["keywords"] = id_to_keywords[problem_num]
            updated_count += 1
        else:
            # 키워드 없는 문제는 빈 리스트 유지
            if "keywords" not in card:
                card["keywords"] = []

    # 저장
    with open(CARDS_DATA_PATH, "w", encoding="utf-8-sig") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"✅ keywords 적용 완료: {updated_count}개 문제 업데이트")
    print(f"💾 저장 완료: {CARDS_DATA_PATH}")

    # 키워드별 통계
    print("\n=== 키워드별 적용 현황 ===")
    kw_counts = {}
    for card in cards:
        for kw in card.get("keywords", []):
            kw_counts[kw] = kw_counts.get(kw, 0) + 1
    for kw, cnt in sorted(kw_counts.items()):
        print(f"  [{kw}]: {cnt}개")


if __name__ == "__main__":
    apply_keywords()
