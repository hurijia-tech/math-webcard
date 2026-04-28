"""
update_drive_ids.py
구글 드라이브에서 이미지 파일ID를 수집하여
cards_data.json에 drive_file_id 필드를 추가합니다.

사용법:
    python update_drive_ids.py

결과:
    cards_data.json의 각 문제에 drive_file_id 필드 추가
"""

import json
from pathlib import Path
from googleapiclient.discovery import build

# ── 설정 ──────────────────────────────────────────
API_KEY = "AIzaSyAqlM2rYdvzJSamBzjtkvmppgknMpJQ1t4"  # Google Cloud Console에서 발급받은 API 키

FOLDER_IDS = {
    "바이블":        "1lhYvQz8ZaW_qY_SyZcDy3JmcID_ICViM",
    "자이스토리":    "1riTVv7-4pf5lM9OB2Oq4ybUTsrFq7MOp",
    "유형해결의법칙": "18EqwStBABMWl4b0LMvh0RYqzhEf0bDux",
}

BASE_DIR   = Path(__file__).resolve().parent
DATA_PATH  = BASE_DIR / "cards_data.json"

# ── 구글 드라이브에서 파일 목록 수집 ──────────────
def get_drive_files(folder_id: str) -> dict:
    """
    폴더 ID로 구글 드라이브 파일 목록을 가져옵니다.
    반환값: {파일명: 파일ID} 딕셔너리
    """
    service = build("drive", "v3", developerKey=API_KEY)
    files = {}
    page_token = None

    print(f"  📂 드라이브 파일 목록 수집 중...")

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name)",
            pageSize=1000,
            pageToken=page_token
        ).execute()

        for f in response.get("files", []):
            files[f["name"]] = f["id"]

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    print(f"  ✅ {len(files)}개 파일 수집 완료")
    return files


# ── 메인 ──────────────────────────────────────────
def main():
    # cards_data.json 읽기
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        cards = json.load(f)
    print(f"📚 총 {len(cards)}개 문제 로드")

    # 교재별 드라이브 파일 목록 수집
    drive_files = {}
    for book, folder_id in FOLDER_IDS.items():
        print(f"\n📖 {book} 파일 목록 수집...")
        drive_files[book] = get_drive_files(folder_id)

    # cards_data.json 업데이트
    matched   = 0
    unmatched = 0

    for card in cards:
        book  = card.get("book", "")
        q_img = card.get("question_image", "")

        if not q_img:
            card["drive_file_id"] = ""
            continue

        # 파일명만 추출 (경로에서 파일명만)
        filename = Path(q_img).name

        # 드라이브에서 파일ID 찾기
        file_id = drive_files.get(book, {}).get(filename, "")

        if file_id:
            matched += 1
        else:
            unmatched += 1
            if unmatched <= 5:  # 처음 5개만 출력
                print(f"  ⚠️  매칭 실패: {book} / {filename}")

        card["drive_file_id"] = file_id

    # 저장
    with open(DATA_PATH, "w", encoding="utf-8-sig") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 완료!")
    print(f"   매칭 성공: {matched}개")
    print(f"   매칭 실패: {unmatched}개")
    print(f"   저장: {DATA_PATH}")
    print(f"\n다음 단계: cards_ver7.html 수정")


if __name__ == "__main__":
    main()