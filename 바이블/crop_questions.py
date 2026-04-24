import re
import csv
from pathlib import Path
import fitz  # PyMuPDF


# ============================================================
# [초보자용 설정값] 여기만 먼저 바꿔서 써도 됨
# ============================================================

PDF_PATH = "book.pdf"             # 입력 PDF 경로
OUTPUT_DIR = "output_crops"       # 결과 저장 폴더

START_PAGE = 7                   # PDF 기준 시작 페이지(1부터)
END_PAGE = None                   # PDF 기준 끝 페이지 (None이면 끝까지)

ZOOM = 2.0                        # 이미지 해상도 배율 (2.0~3.0 추천)
                                  # 높일수록 선명하지만 용량 커짐

# 문항번호 탐지 시 무시할 영역 (페이지 위/아래 머리말/꼬리말 제거용)
TOP_IGNORE = 10                   # 페이지 상단 70pt 영역 무시
BOTTOM_IGNORE = 45                # 페이지 하단 45pt 영역 무시

# 크롭 영역 미세 조정
X_MARGIN = 18                     # 좌우 여백
GUTTER = 8                        # 가운데 컬럼 경계 여백
QUESTION_TOP_PADDING = 8          # 문항번호 위로 조금 포함
QUESTION_BOTTOM_GAP = 6           # 다음 문항 시작 전 간격
FOOTER_MARGIN = 45                # 마지막 문항 하단 제한 (꼬리말 제거)

# 문항번호 패턴 (예: 0001, 0123)
QUESTION_ID_REGEX = r"^\d{4}$"


# ============================================================
# 내부 함수들
# ============================================================

def is_question_id(text: str) -> bool:
    """문항번호(0001 형태)인지 검사"""
    return re.fullmatch(QUESTION_ID_REGEX, text.strip()) is not None


def extract_question_anchors(page: fitz.Page):
    """
    페이지에서 문항번호 위치(앵커) 추출
    반환 형식:
    [
      {"qid":"0007","x0":...,"y0":...,"x1":...,"y1":...,"cx":...},
      ...
    ]
    """
    page_width = page.rect.width
    page_height = page.rect.height

    # words 형식:
    # (x0, y0, x1, y1, "text", block_no, line_no, word_no)
    words = page.get_text("words")

    anchors = []
    for w in words:
        x0, y0, x1, y1, text = w[:5]
        text = str(text).strip()

        # 1) 문항번호 패턴 확인
        if not is_question_id(text):
            continue

        # 2) 머리말/꼬리말 근처는 제외
        if y0 < TOP_IGNORE:
            continue
        if y1 > (page_height - BOTTOM_IGNORE):
            continue

        anchors.append({
            "qid": text,
            "x0": float(x0),
            "y0": float(y0),
            "x1": float(x1),
            "y1": float(y1),
            "cx": float((x0 + x1) / 2.0),
            "page_width": float(page_width),
            "page_height": float(page_height),
        })

    # 중복 제거 (같은 번호가 같은 위치에 중복 추출되는 경우 대비)
    deduped = []
    seen = set()
    for a in sorted(anchors, key=lambda x: (x["y0"], x["x0"], x["qid"])):
        key = (a["qid"], round(a["x0"], 1), round(a["y0"], 1))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)

    return deduped


def split_by_columns(anchors, page_width):
    """
    2단 컬럼 기준으로 좌/우 나누기
    """
    mid_x = page_width / 2.0
    left = []
    right = []

    for a in anchors:
        if a["cx"] < mid_x:
            left.append(a)
        else:
            right.append(a)

    # 위에서 아래 순서 정렬
    left.sort(key=lambda x: x["y0"])
    right.sort(key=lambda x: x["y0"])

    return left, right


def crop_questions_from_page(page: fitz.Page, page_number_1based: int, out_img_dir: Path):
    """
    한 페이지에서 문항별 크롭 이미지를 저장하고 metadata 행 목록 반환
    """
    page_width = page.rect.width
    page_height = page.rect.height
    mid_x = page_width / 2.0

    anchors = extract_question_anchors(page)

    if not anchors:
        return []

    left_anchors, right_anchors = split_by_columns(anchors, page_width)

    # 컬럼별 x 범위
    column_x_ranges = {
        0: (X_MARGIN, mid_x - GUTTER),             # 왼쪽 컬럼
        1: (mid_x + GUTTER, page_width - X_MARGIN) # 오른쪽 컬럼
    }

    all_rows = []

    for col_idx, col_anchors in [(0, left_anchors), (1, right_anchors)]:
        if not col_anchors:
            continue

        col_x0, col_x1 = column_x_ranges[col_idx]
        content_bottom = page_height - FOOTER_MARGIN

        for i, anchor in enumerate(col_anchors):
            qid = anchor["qid"]

            # 현재 문항 시작 y
            y0 = max(0, anchor["y0"] - QUESTION_TOP_PADDING)

            # 다음 문항 시작 전까지
            if i < len(col_anchors) - 1:
                next_anchor = col_anchors[i + 1]
                y1 = next_anchor["y0"] - QUESTION_BOTTOM_GAP
            else:
                # 컬럼 마지막 문항은 페이지 하단(꼬리말 제외)까지
                y1 = content_bottom

            y1 = min(y1, content_bottom)

            # 너무 작은 영역은 스킵 (오탐 방지)
            if (y1 - y0) < 25:
                continue

            clip_rect = fitz.Rect(col_x0, y0, col_x1, y1)

            # 렌더링 (이미지 저장)
            pix = page.get_pixmap(
                matrix=fitz.Matrix(ZOOM, ZOOM),
                clip=clip_rect,
                alpha=False
            )

            filename = f"p{page_number_1based:03d}_q{qid}.png"
            save_path = out_img_dir / filename
            pix.save(str(save_path))

            all_rows.append({
                "page": page_number_1based,
                "question_id": qid,
                "column": col_idx,   # 0=left, 1=right
                "x0": round(col_x0, 2),
                "y0": round(y0, 2),
                "x1": round(col_x1, 2),
                "y1": round(y1, 2),
                "image_path": str(save_path)
            })

    return all_rows


def save_metadata_csv(rows, csv_path: Path):
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["page", "question_id", "column", "x0", "y0", "x1", "y1", "image_path"]
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    pdf_file = Path(PDF_PATH)
    if not pdf_file.exists():
        print(f"[오류] PDF 파일을 찾을 수 없습니다: {pdf_file}")
        return

    out_dir = Path(OUTPUT_DIR)
    out_img_dir = out_dir / "images"
    out_img_dir.mkdir(parents=True, exist_ok=True)

    print(f"[시작] PDF 열기: {pdf_file}")
    doc = fitz.open(str(pdf_file))

    total_pages = len(doc)
    start_idx = max(1, START_PAGE)
    end_idx = total_pages if END_PAGE is None else min(END_PAGE, total_pages)

    print(f"[정보] 전체 페이지 수: {total_pages}")
    print(f"[정보] 처리 범위: {start_idx} ~ {end_idx} (PDF 페이지 기준)")

    all_rows = []
    pages_with_questions = 0

    for pno in range(start_idx, end_idx + 1):
        page = doc[pno - 1]  # PyMuPDF는 0부터 시작
        rows = crop_questions_from_page(page, pno, out_img_dir)

        if rows:
            pages_with_questions += 1
            all_rows.extend(rows)
            print(f"  - p{pno:03d}: {len(rows)}개 문항 저장")
        else:
            print(f"  - p{pno:03d}: 문항번호 미검출 (스킵)")

    # metadata 저장
    metadata_csv = out_dir / "metadata.csv"
    save_metadata_csv(all_rows, metadata_csv)

    print("\n[완료]")
    print(f"문항 이미지 개수: {len(all_rows)}")
    print(f"문항이 검출된 페이지 수: {pages_with_questions}")
    print(f"이미지 폴더: {out_img_dir}")
    print(f"메타데이터: {metadata_csv}")


if __name__ == "__main__":
    main()