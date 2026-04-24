import re
import csv
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw

# ==========================================
# ⚙️ 자이스토리 전용 설정 (디버그 가이드 활성화)
# ==========================================
PDF_PATH = "자이스토리2-2 교사용.pdf"  # ⚠️ PDF 파일명이 정확한지 꼭 확인하세요!
OUTPUT_DIR = "zistory_crops"           # 저장될 최상위 폴더
START_PAGE = 12                      # 문제가 시작되는 페이지 번호
END_PAGE = 261                        # 테스트용 끝 페이지

QUESTION_ID_REGEX = r"^[a-zA-Z]\d{2,3}$"  # A16, I60 같은 번호 찾기
SAVE_DEBUG_GUIDE = True                  # ★ 가이드 선(디버그) 이미지 저장 켜기!

# 여백 설정 (필요시 조절 가능)
TOP_IGNORE = 10
BOTTOM_IGNORE = 45
X_MARGIN = 15
GUTTER = 5
QUESTION_TOP_PADDING = 10  # 문제 위 여백 (조금 넉넉하게 수정)
QUESTION_BOTTOM_GAP = 5    # 문제 아래 여백
FOOTER_MARGIN = 45


def resolve_pdf_path(pdf_path_text: str) -> Path:
    p = Path(pdf_path_text)
    return p if p.is_absolute() else Path(__file__).resolve().parent / p


def is_question_id(text: str) -> bool:
    return re.fullmatch(QUESTION_ID_REGEX, text.strip()) is not None


def extract_question_anchors(page: fitz.Page):
    page_height = page.rect.height
    anchors = []
    for w in page.get_text("words"):
        x0, y0, x1, y1, text = w[:5]
        text = str(text).strip()
        if not is_question_id(text):
            continue
        if y0 < TOP_IGNORE or y1 > (page_height - BOTTOM_IGNORE):
            continue
        anchors.append({
            "qid": text, "x0": float(x0), "y0": float(y0), "x1": float(x1), "y1": float(y1),
            "cx": float((x0 + x1) / 2.0),
        })
    deduped, seen = [], set()
    for a in sorted(anchors, key=lambda x: (x["y0"], x["x0"], x["qid"])):
        key = (a["qid"], round(a["x0"], 1), round(a["y0"], 1))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)
    return deduped


def split_by_columns(anchors, page_width):
    mid_x = page_width / 2.0
    left = sorted([a for a in anchors if a["cx"] < mid_x], key=lambda x: x["y0"])
    right = sorted([a for a in anchors if a["cx"] >= mid_x], key=lambda x: x["y0"])
    return left, right


def pixmap_to_pil(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    return Image.frombytes(mode, [pix.width, pix.height], pix.samples)

# ==========================================
# 🪄 빨간색 해설 투명화 (그대로 유지)
# ==========================================
def remove_red_ink(pil_img: Image.Image) -> Image.Image:
    arr = np.array(pil_img.convert("RGB"))
    R = arr[:, :, 0].astype(int)
    G = arr[:, :, 1].astype(int)
    B = arr[:, :, 2].astype(int)

    is_red = (R > 120) & (R > G + 30) & (R > B + 30)
    arr[is_red] = [255, 255, 255] 
    return Image.fromarray(arr.astype('uint8'))

# ==========================================
# 🔍 가이드 선(디버그) 이미지 생성 함수
# ==========================================
def build_debug_guide(page: fitz.Page, page_number_1based: int, rect_records, debug_dir: Path):
    if not SAVE_DEBUG_GUIDE:
        return
    
    # 디버그 이미지는 너무 클 필요 없으므로 해상도(Matrix)를 살짝 낮춤
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    img = pixmap_to_pil(pix).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # PDF 좌표를 픽셀 좌표로 변환하는 비율
    sx, sy = img.width / page.rect.width, img.height / page.rect.height
    
    # 단을 나누는 중앙선 그리기 (파란색)
    mid_x = (page.rect.width / 2.0) * sx
    draw.line((mid_x, 0, mid_x, img.height), fill=(0, 120, 255), width=2)
    
    # 잘라낸 영역에 사각형 그리기
    for r in rect_records:
        # 1단(왼쪽)은 빨간색, 2단(오른쪽)은 초록색 테두리
        color = (255, 0, 0) if r["column"] == 0 else (0, 170, 0)
        draw.rectangle(
            (r["x0"] * sx, r["y0"] * sy, r["x1"] * sx, r["y1"] * sy), 
            outline=color, 
            width=3
        )
        # 번호 글씨 써주기 (보기 편하게)
        draw.text((r["x0"] * sx, r["y0"] * sy - 15), r["question_id"], fill=color)

    # 디버그 폴더에 p008_guide.png 형태로 저장
    img.save(debug_dir / f"p{page_number_1based:03d}_guide.png")


def crop_questions_from_page(page: fitz.Page, page_number_1based: int, out_img_dir: Path, debug_dir: Path):
    page_width, page_height = page.rect.width, page.rect.height
    mid_x = page_width / 2.0
    
    anchors = extract_question_anchors(page)
    if not anchors:
        return []
        
    left_anchors, right_anchors = split_by_columns(anchors, page_width)
    column_x_ranges = {0: (X_MARGIN, mid_x - GUTTER), 1: (mid_x + GUTTER, page_width - X_MARGIN)}
    all_rows, rect_records = [], []

    for col_idx, col_anchors in [(0, left_anchors), (1, right_anchors)]:
        if not col_anchors:
            continue
        base_x0, base_x1 = column_x_ranges[col_idx]
        content_bottom = page_height - FOOTER_MARGIN
        
        for i, anchor in enumerate(col_anchors):
            y0 = max(0, anchor["y0"] - QUESTION_TOP_PADDING)
            y1 = (col_anchors[i + 1]["y0"] - QUESTION_BOTTOM_GAP) if i < len(col_anchors) - 1 else content_bottom
            y1 = min(y1, content_bottom)
            
            if (y1 - y0) < 25:
                continue

            # 1. 실제 문제 이미지 고화질로 자르기
            clip_rect = fitz.Rect(base_x0, y0, base_x1, y1)
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0), clip=clip_rect, alpha=False)
            pil_img = pixmap_to_pil(pix).convert("RGB")
            
            # 빨간색 지우기
            pil_img = remove_red_ink(pil_img)

            save_path = out_img_dir / f"p{page_number_1based:03d}_{anchor['qid']}.png"
            pil_img.save(save_path)

            row = {
                "page": page_number_1based,
                "question_id": anchor["qid"],
                "column": col_idx,
                "x0": round(clip_rect.x0, 2),
                "y0": round(clip_rect.y0, 2),
                "x1": round(clip_rect.x1, 2),
                "y1": round(clip_rect.y1, 2),
                "image_path": str(save_path),
            }
            all_rows.append(row)
            # 디버그 박스를 그리기 위해 좌표 정보 저장
            rect_records.append(row)

    # ★ 한 페이지의 크롭이 끝나면 디버그 이미지 생성 함수 호출 ★
    build_debug_guide(page, page_number_1based, rect_records, debug_dir)
    
    return all_rows


def save_metadata_csv(rows, csv_path: Path):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "page", "question_id", "column", "x0", "y0", "x1", "y1",
                "image_path"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    pdf_file = resolve_pdf_path(PDF_PATH)
    if not pdf_file.exists():
        print(f"❌ [오류] PDF 파일을 찾을 수 없습니다: {pdf_file}")
        return
        
    out_dir = Path(OUTPUT_DIR)
    out_img_dir = out_dir / "images"
    debug_dir = out_dir / "debug_guides"  # ★ 디버그 폴더
    
    out_img_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(str(pdf_file))
    total_pages = len(doc)
    start_idx = max(1, START_PAGE)
    end_idx = total_pages if END_PAGE is None else min(END_PAGE, total_pages)
    
    print(f"🚀 [시작] 작업 범위: {start_idx}페이지 ~ {end_idx}페이지")
    
    all_rows = []
    for pno in range(start_idx, end_idx + 1):
        rows = crop_questions_from_page(doc[pno - 1], pno, out_img_dir, debug_dir)
        all_rows.extend(rows)
        print(f"  -> {pno:03d}페이지: {len(rows)}문제 자르기 완료 (가이드 생성됨)")
        
    metadata_csv = out_dir / "metadata.csv"
    save_metadata_csv(all_rows, metadata_csv)
    
    print("\n🎉 [작업 완료]")
    print(f"📁 잘라낸 문제: zistory_crops/images 폴더 확인")
    print(f"🔍 가이드 선(디버그): zistory_crops/debug_guides 폴더 확인")


if __name__ == "__main__":
    main()