import re
import csv
from pathlib import Path
import fitz  # PyMuPDF


# ============================================================
# [설정값] 바이블 고난도 전용
# ============================================================

PDF_PATH = "바이블_중2-2_Ⅰ-1.삼각형의성질_고난도.pdf"
OUTPUT_DIR = "output_crops"     

START_PAGE = 1
END_PAGE = None
PAGE_OFFSET = 241  # PDF 1페이지 = 실제 242쪽

ZOOM = 2.0

TOP_IGNORE = 10
BOTTOM_IGNORE = 45

X_MARGIN = 18
GUTTER = 8
QUESTION_TOP_PADDING = 8
QUESTION_BOTTOM_GAP = 6
FOOTER_MARGIN = 45

# 고난도 문제번호 패턴: 1270~1281 (4자리, 1로 시작)
QUESTION_ID_REGEX = r"^1[0-9]{3}$"


# ============================================================
# 내부 함수들
# ============================================================

def is_question_id(text: str) -> bool:
    return re.fullmatch(QUESTION_ID_REGEX, text.strip()) is not None


def extract_question_anchors(page: fitz.Page):
    page_width = page.rect.width
    page_height = page.rect.height
    words = page.get_text("words")

    anchors = []
    for w in words:
        x0, y0, x1, y1, text = w[:5]
        text = str(text).strip()

        if not is_question_id(text):
            continue
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
    mid_x = page_width / 2.0
    left = []
    right = []

    for a in anchors:
        if a["cx"] < mid_x:
            left.append(a)
        else:
            right.append(a)

    left.sort(key=lambda x: x["y0"])
    right.sort(key=lambda x: x["y0"])

    return left, right


def crop_questions_from_page(page: fitz.Page, page_number_1based: int, out_img_dir: Path):
    page_width = page.rect.width
    page_height = page.rect.height
    mid_x = page_width / 2.0

    anchors = extract_question_anchors(page)

    if not anchors:
        return []

    left_anchors, right_anchors = split_by_columns(anchors, page_width)

    column_x_ranges = {
        0: (X_MARGIN, mid_x - GUTTER),
        1: (mid_x + GUTTER, page_width - X_MARGIN)
    }

    all_rows = []

    for col_idx, col_anchors in [(0, left_anchors), (1, right_anchors)]:
        if not col_anchors:
            continue

        col_x0, col_x1 = column_x_ranges[col_idx]
        content_bottom = page_height - FOOTER_MARGIN

        for i, anchor in enumerate(col_anchors):
            qid = anchor["qid"]

            y0 = max(0, anchor["y0"] - QUESTION_TOP_PADDING)

            if i < len(col_anchors) - 1:
                next_anchor = col_anchors[i + 1]
                y1 = next_anchor["y0"] - QUESTION_BOTTOM_GAP
            else:
                y1 = content_bottom

            y1 = min(y1, content_bottom)

            if (y1 - y0) < 25:
                continue

            clip_rect = fitz.Rect(col_x0, y0, col_x1, y1)

            pix = page.get_pixmap(
                matrix=fitz.Matrix(ZOOM, ZOOM),
                clip=clip_rect,
                alpha=False
            )

            # 파일명: p001_q1270.png 형식
            filename = f"p{page_number_1based + PAGE_OFFSET:03d}_q{qid}.png"
            save_path = out_img_dir / filename
            pix.save(str(save_path))

            all_rows.append({
                "page": page_number_1based,
                "question_id": qid,
                "column": col_idx,
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
    print(f"[정보] 처리 범위: {start_idx} ~ {end_idx}")

    all_rows = []
    pages_with_questions = 0

    for pno in range(start_idx, end_idx + 1):
        page = doc[pno - 1]
        rows = crop_questions_from_page(page, pno, out_img_dir)

        if rows:
            pages_with_questions += 1
            all_rows.extend(rows)
            print(f"  - p{pno:03d}: {len(rows)}개 문항 저장")
        else:
            print(f"  - p{pno:03d}: 문항번호 미검출 (스킵)")

    metadata_csv = out_dir / "metadata_고난도.csv"
    save_metadata_csv(all_rows, metadata_csv)

    print("\n[완료]")
    print(f"문항 이미지 개수: {len(all_rows)}")
    print(f"문항이 검출된 페이지 수: {pages_with_questions}")
    print(f"이미지 폴더: {out_img_dir}")
    print(f"메타데이터: {metadata_csv}")

    # 검출된 문제번호 확인
    detected = sorted([r["question_id"] for r in all_rows])
    print(f"\n검출된 문제번호: {detected}")

    # 누락 확인 (1270~1281)
    expected = [str(i) for i in range(1270, 1282)]
    missing = [q for q in expected if q not in detected]
    if missing:
        print(f"⚠️  누락된 문제번호: {missing}")
    else:
        print("✅ 1270~1281 전체 검출 완료!")


if __name__ == "__main__":
    main()
