# add_bible_hard.py
# cards_data.json에 바이블 고난도 문제 12개 항목 추가

import json

CARDS_DATA_PATH = "cards_data.json"

# 고난도 문제 12개 데이터
HARD_PROBLEMS = [
    {
        "id": "바이블_1270",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형02. 이등변삼각형의 성질 ⑴ – 각의 크기"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p242_q1270.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1271",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형03. 이등변삼각형의 성질 ⑴ – 이웃한 이등변삼각형"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p242_q1271.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1272",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형07. 이등변삼각형이 되는 조건"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p242_q1272.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1273",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형04. 이등변삼각형의 성질 ⑴ – 각의 이등분선"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p242_q1273.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1274",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형05. 이등변삼각형의 성질 ⑴ – 여러 가지 도형"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p242_q1274.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1275",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형07. 이등변삼각형이 되는 조건"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p242_q1275.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1276",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["발전유형09. 이등변삼각형 모양의 종이접기"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p243_q1276.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1277",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["발전유형10. 합동인 삼각형을 찾아 각의 크기 구하기"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p243_q1277.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1278",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형12. 직각삼각형의 합동 조건의 응용 – RHA 합동"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p243_q1278.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1279",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형15. 각의 이등분선의 성질의 응용"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p243_q1279.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1280",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형13. 직각삼각형의 합동 조건의 응용 – RHS 합동"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p243_q1280.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
    {
        "id": "바이블_1281",
        "book": "바이블",
        "course": "중등수학 2-2",
        "chapter": "Ⅰ. 삼각형의 성질",
        "sub_chapter": "01. 삼각형의 성질(1)",
        "type_tags": ["유형15. 각의 이등분선의 성질의 응용"],
        "difficulty": "",
        "question_image": "바이블/output_crops/images/p243_q1281.png",
        "drive_file_id": "",
        "answer": "",
        "solution": "",
        "solution_image": "",
        "keywords": [],
        "similar": []
    },
]

def add_hard_problems():
    with open(CARDS_DATA_PATH, "r", encoding="utf-8-sig") as f:
        cards = json.load(f)

    print(f"📋 기존 문제 수: {len(cards)}개")

    # 중복 방지: 이미 있는 ID는 스킵
    existing_ids = {c["id"] for c in cards}
    to_add = [p for p in HARD_PROBLEMS if p["id"] not in existing_ids]

    if not to_add:
        print("⚠️ 이미 모든 고난도 문제가 추가되어 있습니다.")
        return

    cards.extend(to_add)

    with open(CARDS_DATA_PATH, "w", encoding="utf-8-sig") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"✅ 고난도 문제 {len(to_add)}개 추가 완료")
    print(f"📋 총 문제 수: {len(cards)}개")
    print(f"💾 저장 완료: {CARDS_DATA_PATH}")

if __name__ == "__main__":
    add_hard_problems()
