"""
extract_types.py
교재 PDF에서 유형명과 문제번호를 자동 추출하여
type_mappings/ 폴더에 JSON으로 저장

사용법:
    python extract_types.py

출력:
    type_mappings/바이블_types.json
    type_mappings/자이스토리_types.json
    type_mappings/유형해결의법칙_types.json
"""

import re
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


# ── 제어문자 제거 ─────────────────────────────────
def clean(s: str) -> str:
    return re.sub(r'[\u200c\u200b\x07\x08\ue34c\ufeff\x0c]', '', s).strip()


# ── PDF → 줄 리스트 ───────────────────────────────
def pdf_to_lines(pdf_path: Path) -> list[str]:
    result = subprocess.run(
        ['pdftotext', str(pdf_path), '-'],
        capture_output=True, text=True, errors='ignore'
    )
    return [clean(l) for l in result.stdout.split('\n')]


# ── PDF 파일 자동 탐색 ────────────────────────────
def find_pdf(book_name: str) -> Path | None:
    folder = BASE_DIR / book_name
    if not folder.exists():
        print(f"  ⚠️  폴더 없음: {folder}")
        return None
    pdfs = list(folder.glob("*.pdf"))
    if not pdfs:
        print(f"  ⚠️  PDF 없음: {folder}")
        return None
    for pdf in pdfs:
        if book_name in pdf.name:
            return pdf
    return pdfs[0]


# ════════════════════════════════════════════════
# 바이블 (유형명 하드코딩 + 정확한 문제번호 매핑)
# ════════════════════════════════════════════════

BIBLE_NAMES = {
    1:  "이등변삼각형의 성질",
    2:  "이등변삼각형의 성질 ⑴ – 각의 크기",
    3:  "이등변삼각형의 성질 ⑴ – 이웃한 이등변삼각형",
    4:  "이등변삼각형의 성질 ⑴ – 각의 이등분선",
    5:  "이등변삼각형의 성질 ⑴ – 여러 가지 도형",
    6:  "이등변삼각형의 성질 ⑵",
    7:  "이등변삼각형이 되는 조건",
    8:  "이등변삼각형이 되는 조건 – 종이접기",
    9:  "이등변삼각형 모양의 종이접기",
    10: "합동인 삼각형을 찾아 각의 크기 구하기",
    11: "직각삼각형의 합동 조건",
    12: "직각삼각형의 합동 조건의 응용 – RHA 합동",
    13: "직각삼각형의 합동 조건의 응용 – RHS 합동",
    14: "각의 이등분선의 성질",
    15: "각의 이등분선의 성질의 응용",
}

# 유형별 정확한 문제번호 매핑
# 구성: B파트(유형별 문제) + 개념확인(0001~0013) + 중단원마무리(0093~0117)
BIBLE_QMAP = {
    1:  [                                                           # B파트
         "0014", "0015", "0016",
        ],
    2:  ["0001", "0002",                                           # 개념확인
         "0017", "0018", "0019", "0020", "0021", "0022", "0023", "0024",  # B파트
         "0093",                                                   # 마무리
        ],
    3:  ["0025", "0026", "0027", "0028", "0029", "0030", "0031",  # B파트
         "0094", "0095", "0096",                                   # 마무리
        ],
    4:  ["0032", "0033", "0034", "0035", "0036", "0037",          # B파트
         "0097", "0098",                                           # 마무리
        ],
    5:  ["0038", "0039", "0040", "0041", "0042", "0043",          # B파트
         "0099",                                                   # 마무리
        ],
    6:  ["0003",                                                   # 개념확인
         "0044", "0045", "0046", "0047", "0048",                  # B파트
         "0100", "0107",                                           # 마무리
        ],
    7:  ["0004", "0005", "0006",                                   # 개념확인
         "0049", "0050", "0051", "0052", "0053",                  # B파트
         "0054", "0055", "0056", "0057",                          # B파트
         "0101", "0102", "0103",                                   # 마무리
        ],
    8:  ["0058", "0059", "0060", "0061",                          # B파트
         "0104",                                                   # 마무리
        ],
    9:  ["0062", "0063", "0064",                                   # B파트
         "0105",                                                   # 마무리
        ],
    10: ["0065", "0066", "0067",                                   # B파트
         "0106", "0108",                                           # 마무리
        ],
    11: ["0007", "0008", "0009",                                   # 개념확인
         "0068", "0069", "0070", "0071", "0072", "0073",          # B파트
         "0109",                                                   # 마무리
        ],
    12: ["0074", "0075", "0076", "0077", "0078", "0079",          # B파트
         "0110", "0111",                                           # 마무리
        ],
    13: ["0080", "0081", "0082", "0083", "0084",                  # B파트
         "0112", "0113", "0116",                                   # 마무리
        ],
    14: ["0010", "0011", "0012", "0013",                          # 개념확인
         "0085", "0086", "0087",                                   # B파트
         "0114",                                                   # 마무리
        ],
    15: ["0088", "0089", "0090", "0091", "0092",                  # B파트
         "0115", "0117",                                           # 마무리
        ],
}


def extract_bible(lines: list[str], id_prefix: str, q_min: int, q_max: int) -> list[dict]:
    type_names = dict(BIBLE_NAMES)
    print(f"  📋 유형 {len(type_names)}개 (하드코딩)")
    for k in sorted(type_names):
        print(f"     유형{k:02d}. {type_names[k]}")

    mappings = []
    total = 0
    for num in sorted(type_names):
        questions = [id_prefix + q for q in BIBLE_QMAP.get(num, [])]
        total += len(questions)
        mappings.append({
            "type_num":  num,
            "type_name": f"유형{num:02d}. {type_names[num]}",
            "questions": questions,
        })

    print(f"  📝 총 {total}개 문제 배분 완료 (BIBLE_QMAP 정확한 매핑)")
    return mappings


# ════════════════════════════════════════════════
# 유형해결의법칙 (유형명 하드코딩 + 정확한 문제번호 매핑)
# ════════════════════════════════════════════════

YUHYUNG_NAMES = {
    1:  "이등변삼각형의 성질에 대한 설명",
    2:  "이등변삼각형의 성질 ⑴",
    3:  "이등변삼각형의 성질 ⑵",
    4:  "이등변삼각형의 성질을 이용하여 각의 크기 구하기 ⑴ - 이웃한 이등변삼각형",
    5:  "이등변삼각형의 성질을 이용하여 각의 크기 구하기 ⑵ - 각의 이등분선",
    6:  "이등변삼각형의 성질을 이용하여 각의 크기 구하기 ⑶ - 여러 가지 도형",
    7:  "이등변삼각형이 되는 조건에 대한 설명",
    8:  "이등변삼각형이 되는 조건",
    9:  "직사각형 모양의 종이접기",
    10: "이등변삼각형 모양의 종이접기",
    11: "합동인 삼각형을 찾아 각의 크기 구하기",
    12: "직각삼각형의 합동 조건",
    13: "직각삼각형의 합동 조건의 활용 ⑴ - RHA 합동",
    14: "직각삼각형의 합동 조건의 활용 ⑵ - RHS 합동",
    15: "각의 이등분선의 성질 ⑴",
    16: "각의 이등분선의 성질 ⑵",
}

# 유형별 정확한 문제번호 매핑
# 구성: STEP2(유형마스터) + STEP3(내신마스터) 분산 배치
YUHYUNG_QMAP = {
    1:  ["0011", "0012",                                    # STEP2
         "0078",                                            # STEP3
        ],
    2:  ["0013", "0014", "0015", "0016", "0017", "0018",   # STEP2
         "0079",                                            # STEP3
        ],
    3:  ["0019", "0020", "0021",                           # STEP2
         "0080", "0081",                                    # STEP3
        ],
    4:  ["0022", "0023", "0024", "0025", "0026",           # STEP2
         "0082",                                            # STEP3
        ],
    5:  ["0027", "0028",                                    # STEP2
         "0083",                                            # STEP3
        ],
    6:  ["0029", "0030", "0031", "0032", "0033",           # STEP2
        ],
    7:  ["0034", "0035",                                    # STEP2
        ],
    8:  ["0036", "0037", "0038", "0039", "0040", "0041",   # STEP2
         "0084",                                            # STEP3
        ],
    9:  ["0042", "0043", "0044", "0045",                   # STEP2
         "0085",                                            # STEP3
        ],
    10: ["0046", "0047",                                    # STEP2
         "0086",                                            # STEP3
        ],
    11: ["0048", "0049", "0050",                           # STEP2
         "0087", "0088", "0089",                           # STEP3
        ],
    12: ["0057", "0058", "0059", "0060",                   # STEP2
         "0090",                                            # STEP3
        ],
    13: ["0061", "0062", "0063", "0064", "0065", "0066",   # STEP2
         "0091",                                            # STEP3
        ],
    14: ["0067", "0068", "0069", "0070",                   # STEP2
         "0092", "0093",                                    # STEP3
        ],
    15: ["0071", "0072",                                    # STEP2
        ],
    16: ["0073", "0074", "0075", "0076", "0077",           # STEP2
         "0094", "0095",                                    # STEP3
        ],
}


def extract_yuhyung(lines: list[str], id_prefix: str, q_min: int, q_max: int) -> list[dict]:
    type_names = dict(YUHYUNG_NAMES)
    print(f"  📋 유형 {len(type_names)}개 (하드코딩)")
    for k in sorted(type_names):
        print(f"     유형{k:02d}. {type_names[k]}")

    mappings = []
    total = 0
    for num in sorted(type_names):
        questions = [id_prefix + q for q in YUHYUNG_QMAP.get(num, [])]
        total += len(questions)
        mappings.append({
            "type_num":  num,
            "type_name": f"유형{num:02d}. {type_names[num]}",
            "questions": questions,
        })

    print(f"  📝 총 {total}개 문제 배분 완료 (YUHYUNG_QMAP 정확한 매핑)")
    return mappings


# ════════════════════════════════════════════════
# 자이스토리 (유형명 하드코딩 + 문제번호는 metadata.csv에서 읽기)
# PDF 의존 없음 → Windows 한글 깨짐 문제 완전 해결
# ════════════════════════════════════════════════

ZISTORY_NAMES = {
    1:  "이등변삼각형의 성질 ⑴ - 밑각의 크기",
    2:  "이등변삼각형의 성질 ⑵ - 꼭지각의 이등분선",
    3:  "이등변삼각형의 성질을 이용하여 각의 크기 구하기",
    4:  "이등변삼각형의 밑각의 이등분선 (고난도)",
    5:  "여러 가지 도형에의 활용",
    6:  "이등변삼각형이 되는 조건",
    7:  "폭이 일정한 종이 접기 (고난도)",
    8:  "직각삼각형의 합동 조건",
    9:  "직각삼각형의 합동 조건의 응용 - RHA 합동",
    10: "직각삼각형의 합동 조건의 응용 - RHS 합동",
    11: "각의 이등분선의 성질 - 변의 길이 구하기",
    12: "각의 이등분선의 성질 - 각의 크기 구하기",
}

# 유형별 문제 수 (교재에서 직접 확인한 값)
ZISTORY_COUNTS = {
    1: 6, 2: 0, 3: 11, 4: 5, 5: 2, 6: 8,
    7: 21, 8: 18, 9: 1, 10: 4, 11: 6, 12: 1
}

# 유형별 정확한 문제번호 매핑 (확정)
ZISTORY_QMAP = {
    1:  ["A14", "A16", "A17", "A15", "A18", "A62"],
    2:  [],
    3:  ["A19", "A22", "A20", "A23", "A21", "A24", "A25", "A61",
         "A75", "A76", "A77", "A79", "A81", "A82", "A83", "A84"],
    4:  ["A28", "A26", "A29", "A27", "A30"],
    5:  ["A31", "A32", "A33", "A69"],
    6:  ["A34", "A35", "A36", "A37", "A38", "A39", "A85", "A86"],
    7:  ["A40", "A41", "A42", "A45", "A67", "A87", "A88"],
    8:  ["A43", "A44", "A46", "A47"],
    9:  ["A48", "A49", "A50", "A64", "A65", "A71", "A89", "A90", "A91", "A92"],
    10: ["A51", "A52", "A53", "A63", "A66", "A68"],
    11: ["A54", "A56", "A57", "A58", "A70", "A72", "A73", "A74",
         "A78", "A93", "A94", "A95", "A96"],
    12: ["A55", "A59", "A60", "A80"],
}

def extract_zistory(lines: list[str], id_prefix: str) -> list[dict]:
    import csv as csv_mod

    type_names = dict(ZISTORY_NAMES)
    print(f"  📋 유형 {len(type_names)}개 (하드코딩)")

    # metadata.csv에서 문제번호 순서대로 읽기
    csv_path = BASE_DIR / "자이스토리" / "output_crops" / "metadata.csv"
    all_q = []

    if csv_path.exists():
        with open(csv_path, encoding='utf-8-sig') as f:
            reader = csv_mod.DictReader(f)
            seen = set()
            for row in reader:
                # question_id 컬럼에서 A번호 추출
                qid_key = next((k for k in row if 'question_id' in k.lower()), None)
                if not qid_key:
                    continue
                qid = row[qid_key].strip()
                if qid and qid not in seen:
                    all_q.append(qid)
                    seen.add(qid)
        print(f"  📝 metadata.csv에서 문제번호 {len(all_q)}개 수집")
    else:
        # CSV 없으면 cards_data.json에서 순서대로 읽기
        data_path = BASE_DIR / "cards_data.json"
        import json as json_mod
        if data_path.exists():
            with open(data_path, encoding='utf-8-sig') as f:
                cards = json_mod.load(f)
            for card in cards:
                if card.get('book') == '자이스토리':
                    qid = card['id'].replace(id_prefix, '')
                    all_q.append(qid)
            print(f"  📝 cards_data.json에서 문제번호 {len(all_q)}개 수집")
        else:
            print("  ❌ metadata.csv와 cards_data.json 모두 없음")
            return []

    # ZISTORY_QMAP 기준으로 유형별 문제 배분
    mappings = []
    for num in sorted(type_names):
        questions = [id_prefix + q for q in ZISTORY_QMAP.get(num, [])]
        mappings.append({
            "type_num":  num,
            "type_name": f"유형{num:02d}. {type_names[num]}",
            "questions": questions,
        })

    total = sum(len(m['questions']) for m in mappings)
    print(f"  ✅ 총 {total}개 문제 배분 완료 (ZISTORY_QMAP 정확한 매핑)")
    return mappings

# ════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════
BOOKS = [
    {"name": "바이블",        "func": "bible",   "id_prefix": "바이블_",   "q_min": 1,  "q_max": 117},
    {"name": "유형해결의법칙", "func": "yuhyung", "id_prefix": "유형법칙_", "q_min": 11, "q_max": 95},
    {"name": "자이스토리",     "func": "zistory", "id_prefix": "자이스토리_"},
]


def main():
    out_dir = BASE_DIR / "type_mappings"
    out_dir.mkdir(exist_ok=True)

    for cfg in BOOKS:
        book_name = cfg["name"]
        print(f"\n{'='*55}")
        print(f"📚 {book_name}")

        pdf_path = find_pdf(book_name)
        if not pdf_path:
            continue
        print(f"  📄 {pdf_path.name}")

        lines = pdf_to_lines(pdf_path)
        print(f"  📝 총 {len(lines)}줄 추출")

        func = cfg["func"]
        if func == "bible":
            mappings = extract_bible(lines, cfg["id_prefix"], cfg["q_min"], cfg["q_max"])
        elif func == "yuhyung":
            mappings = extract_yuhyung(lines, cfg["id_prefix"], cfg["q_min"], cfg["q_max"])
        else:
            mappings = extract_zistory(lines, cfg["id_prefix"])

        if not mappings:
            print(f"  ❌ 추출 실패")
            continue

        total = sum(len(m['questions']) for m in mappings)
        print(f"\n  ✅ 유형 {len(mappings)}개, 문제 {total}개:")
        for m in mappings:
            print(f"     {m['type_name'][:50]} → {len(m['questions'])}개")

        out_path = out_dir / f"{book_name}_types.json"
        with open(out_path, "w", encoding="utf-8-sig") as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        print(f"  💾 저장: {out_path}")

    print(f"\n\n✅ 완료!")
    print("다음 단계: python apply_types.py")


if __name__ == "__main__":
    main()
