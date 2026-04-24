import re
import csv
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw

PDF_PATH = "유형해결의법칙_중2-2.pdf"
OUTPUT_DIR = "output_crops"
START_PAGE = 1
END_PAGE = None
ZOOM = 3.0
TOP_IGNORE = 10
BOTTOM_IGNORE = 45
X_MARGIN = 18
GUTTER = 8
QUESTION_TOP_PADDING = 8
QUESTION_BOTTOM_GAP = 6
FOOTER_MARGIN = 45
QUESTION_ID_REGEX = r"^\d{4}$"
SAVE_DEBUG_GUIDE = True

# 오른쪽 장식 탭 자동 제거
AUTO_TRIM_RIGHT_DECOR = True
BLANK_COLUMN_RATIO = 0.003
MIN_BLANK_GAP_PX = 28
MAX_DECOR_WIDTH_RATIO = 0.18
MIN_MAIN_CONTENT_WIDTH_RATIO = 0.18
RIGHT_CONTENT_PAD_PX = 8

# 하단의 추가 설명/대표문제/핵심포인트/유형박스 같은
# "문항 본문과 분리된 두 번째 블록"을 일반화해서 제거
AUTO_TRIM_BOTTOM_FOLLOWUP = True
BLANK_ROW_RATIO = 0.003
ROW_SMOOTH_KERNEL = 9
ROW_TINY_GAP_FILL_PX = 8
BLOCK_MERGE_GAP_PX = 26
MIN_SEPARATION_GAP_PX = 40
MIN_TOP_CLUSTER_PX = 120
MIN_BOTTOM_CLUSTER_PX = 90
MIN_BOTTOM_CLUSTER_INK_ROWS = 45
MIN_BOTTOM_START_RATIO = 0.38
BOTTOM_CONTENT_PAD_PX = 10
TOP_SEARCH_SKIP_PX = 18


def resolve_pdf_path(pdf_path_text: str) -> Path:
    p = Path(pdf_path_text)
    return p if p.is_absolute() else Path(__file__).resolve().parent / p


def is_question_id(text: str) -> bool:
    return re.fullmatch(QUESTION_ID_REGEX, text.strip()) is not None


def extract_question_anchors(page: fitz.Page):
    page_width = page.rect.width
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


def pil_to_binary_ink_mask(img: Image.Image) -> np.ndarray:
    arr = np.array(img.convert("RGB"))
    gray = arr.mean(axis=2)
    return gray < 245


def find_runs(bool_arr: np.ndarray):
    if len(bool_arr) == 0:
        return []
    runs, start, current = [], 0, bool(bool_arr[0])
    for i in range(1, len(bool_arr)):
        val = bool(bool_arr[i])
        if val != current:
            runs.append((current, start, i - 1))
            start, current = i, val
    runs.append((current, start, len(bool_arr) - 1))
    return runs


def close_small_gaps_1d(is_nonblank: np.ndarray, tiny_gap_fill_px: int = 8) -> np.ndarray:
    out = is_nonblank.copy()

    for i in range(1, len(out) - 1):
        if not out[i] and out[i - 1] and out[i + 1]:
            out[i] = True

    i = 0
    while i < len(out):
        if not out[i]:
            j = i
            while j + 1 < len(out) and not out[j + 1]:
                j += 1
            if i > 0 and j < len(out) - 1 and out[i - 1] and out[j + 1] and (j - i + 1) <= tiny_gap_fill_px:
                out[i:j + 1] = True
            i = j + 1
        else:
            i += 1
    return out


def detect_right_decor_cut_x(img: Image.Image):
    mask = pil_to_binary_ink_mask(img)
    h, w = mask.shape
    col_ink = mask.sum(axis=0)
    blank_threshold = max(1, int(h * BLANK_COLUMN_RATIO))
    is_nonblank = col_ink > blank_threshold
    is_nonblank = close_small_gaps_1d(is_nonblank, tiny_gap_fill_px=8)

    runs = find_runs(is_nonblank)
    if len(runs) < 3:
        return None

    edge_val, edge_start, edge_end = runs[-1]
    gap_val, gap_start, gap_end = runs[-2]
    main_val, main_start, main_end = runs[-3]
    edge_width = edge_end - edge_start + 1
    gap_width = gap_end - gap_start + 1
    main_width = main_end - main_start + 1

    if not edge_val or gap_val or not main_val:
        return None
    if edge_width > max(24, int(w * MAX_DECOR_WIDTH_RATIO)):
        return None
    if gap_width < MIN_BLANK_GAP_PX:
        return None
    if main_width < int(w * MIN_MAIN_CONTENT_WIDTH_RATIO):
        return None

    edge_band = mask[:, edge_start:edge_end + 1]
    if edge_band.any(axis=1).sum() < int(h * 0.10):
        return None

    cut_x = min(w, main_end + 1 + RIGHT_CONTENT_PAD_PX)
    return None if cut_x >= w - 2 else cut_x


def smooth_1d(values: np.ndarray, kernel_size: int) -> np.ndarray:
    kernel_size = max(1, int(kernel_size))
    if kernel_size == 1:
        return values.astype(float)
    kernel = np.ones(kernel_size, dtype=float) / kernel_size
    return np.convolve(values.astype(float), kernel, mode="same")


def build_content_clusters(mask: np.ndarray):
    h, w = mask.shape
    row_ink = mask.sum(axis=1)
    smooth_row_ink = smooth_1d(row_ink, ROW_SMOOTH_KERNEL)
    blank_threshold = max(1, int(w * BLANK_ROW_RATIO))
    is_nonblank = smooth_row_ink > blank_threshold
    is_nonblank = close_small_gaps_1d(is_nonblank, tiny_gap_fill_px=ROW_TINY_GAP_FILL_PX)

    search_start = min(h - 1, TOP_SEARCH_SKIP_PX)
    runs = find_runs(is_nonblank[search_start:])
    abs_runs = [(val, s + search_start, e + search_start) for val, s, e in runs]

    raw_clusters = []
    for val, start, end in abs_runs:
        if not val:
            continue
        raw_clusters.append({
            "start": int(start),
            "end": int(end),
            "height": int(end - start + 1),
            "ink_rows": int(mask[start:end + 1].any(axis=1).sum()),
            "ink_sum": float(mask[start:end + 1].sum()),
        })

    if not raw_clusters:
        return []

    clusters = [raw_clusters[0].copy()]
    for c in raw_clusters[1:]:
        prev = clusters[-1]
        gap_h = c["start"] - prev["end"] - 1
        if gap_h <= BLOCK_MERGE_GAP_PX:
            prev["end"] = c["end"]
            prev["height"] = prev["end"] - prev["start"] + 1
            prev["ink_rows"] += c["ink_rows"]
            prev["ink_sum"] += c["ink_sum"]
        else:
            prev["gap_after"] = gap_h
            clusters.append(c.copy())
    clusters[-1]["gap_after"] = None

    for c in clusters:
        c["mean_ink_per_row"] = c["ink_sum"] / max(1, c["height"])
        c["start_ratio"] = c["start"] / max(1, h)
        c["end_ratio"] = c["end"] / max(1, h)
    return clusters


def detect_bottom_followup_cut_y(img: Image.Image):
    mask = pil_to_binary_ink_mask(img)
    h, w = mask.shape
    clusters = build_content_clusters(mask)
    if len(clusters) < 2:
        return None

    # "첫 번째 큰 콘텐츠 덩어리" 이후에 큰 공백이 있고,
    # 그 아래에 또 충분히 큰 두 번째 덩어리가 나오면 하단 부가 블록으로 판단한다.
    for i in range(len(clusters) - 1):
        top = clusters[i]
        bottom = clusters[i + 1]
        gap_h = bottom["start"] - top["end"] - 1

        if top["height"] < MIN_TOP_CLUSTER_PX:
            continue
        if gap_h < MIN_SEPARATION_GAP_PX:
            continue
        if bottom["height"] < MIN_BOTTOM_CLUSTER_PX:
            continue
        if bottom["ink_rows"] < MIN_BOTTOM_CLUSTER_INK_ROWS:
            continue
        if bottom["start_ratio"] < MIN_BOTTOM_START_RATIO:
            continue

        # 아주 작은 하단 잔여(풀이표시, 페이지 하단 아이콘 등)는 제외
        if bottom["mean_ink_per_row"] < max(8, w * 0.012):
            continue

        cut_y = min(h, top["end"] + 1 + BOTTOM_CONTENT_PAD_PX)
        if cut_y >= h - 2:
            return None
        return cut_y

    return None


def build_debug_guide(page: fitz.Page, page_number_1based: int, anchors_by_col, rect_records, debug_dir: Path):
    if not SAVE_DEBUG_GUIDE:
        return
    page_width = page.rect.width
    mid_x = page_width / 2.0
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    img = pixmap_to_pil(pix).convert("RGB")
    draw = ImageDraw.Draw(img)
    sx, sy = img.width / page.rect.width, img.height / page.rect.height
    draw.line((mid_x * sx, 0, mid_x * sx, img.height), fill=(0, 120, 255), width=2)
    for col_idx, anchors in anchors_by_col.items():
        color = (255, 70, 70) if col_idx == 0 else (60, 180, 75)
        for a in anchors:
            draw.rectangle((a["x0"] * sx, a["y0"] * sy, a["x1"] * sx, a["y1"] * sy), outline=color, width=2)
    for r in rect_records:
        color = (255, 0, 0) if r["column"] == 0 else (0, 170, 0)
        draw.rectangle((r["x0"] * sx, r["y0"] * sy, r["x1"] * sx, r["y1"] * sy), outline=color, width=3)
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

            clip_rect = fitz.Rect(base_x0, y0, base_x1, y1)
            pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip_rect, alpha=False)
            pil_img = pixmap_to_pil(pix).convert("RGB")
            trim_right_px = 0
            trim_bottom_px = 0

            if col_idx == 1 and AUTO_TRIM_RIGHT_DECOR:
                cut_x = detect_right_decor_cut_x(pil_img)
                if cut_x is not None:
                    trim_right_px = pil_img.width - cut_x
                    pil_img = pil_img.crop((0, 0, cut_x, pil_img.height))

            if AUTO_TRIM_BOTTOM_FOLLOWUP:
                cut_y = detect_bottom_followup_cut_y(pil_img)
                if cut_y is not None:
                    trim_bottom_px = pil_img.height - cut_y
                    pil_img = pil_img.crop((0, 0, pil_img.width, cut_y))

            save_path = out_img_dir / f"p{page_number_1based:03d}_q{anchor['qid']}.png"
            pil_img.save(save_path)

            pdf_per_px_x = clip_rect.width / pix.width
            pdf_per_px_y = clip_rect.height / pix.height
            final_x1 = clip_rect.x1 - (trim_right_px * pdf_per_px_x)
            final_y1 = clip_rect.y1 - (trim_bottom_px * pdf_per_px_y)

            row = {
                "page": page_number_1based,
                "question_id": anchor["qid"],
                "column": col_idx,
                "x0": round(clip_rect.x0, 2),
                "y0": round(clip_rect.y0, 2),
                "x1": round(final_x1, 2),
                "y1": round(final_y1, 2),
                "auto_trim_right_px": int(trim_right_px),
                "auto_trim_bottom_px": int(trim_bottom_px),
                "image_path": str(save_path),
            }
            all_rows.append(row)
            rect_records.append(row)

    build_debug_guide(page, page_number_1based, {0: left_anchors, 1: right_anchors}, rect_records, debug_dir)
    return all_rows


def save_metadata_csv(rows, csv_path: Path):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "page", "question_id", "column", "x0", "y0", "x1", "y1",
                "auto_trim_right_px", "auto_trim_bottom_px", "image_path"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    pdf_file = resolve_pdf_path(PDF_PATH)
    if not pdf_file.exists():
        print(f"[오류] PDF 파일을 찾을 수 없습니다: {pdf_file}")
        return
    out_dir = Path(OUTPUT_DIR)
    out_img_dir = out_dir / "images"
    debug_dir = out_dir / "debug_guides"
    out_img_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_file))
    total_pages = len(doc)
    start_idx = max(1, START_PAGE)
    end_idx = total_pages if END_PAGE is None else min(END_PAGE, total_pages)
    print(f"[시작] PDF 열기: {pdf_file}")
    print(f"[정보] 전체 페이지 수: {total_pages}")
    print(f"[정보] 처리 범위: {start_idx} ~ {end_idx} (PDF 페이지 기준)")
    all_rows = []
    for pno in range(start_idx, end_idx + 1):
        rows = crop_questions_from_page(doc[pno - 1], pno, out_img_dir, debug_dir)
        all_rows.extend(rows)
        trimmed_right = sum(1 for r in rows if r["auto_trim_right_px"] > 0)
        trimmed_bottom = sum(1 for r in rows if r["auto_trim_bottom_px"] > 0)
        print(f"  - p{pno:03d}: {len(rows)}개 문항 저장 (오른쪽 자동 트림 {trimmed_right}개, 하단 분리블록 제거 {trimmed_bottom}개)")
    metadata_csv = out_dir / "metadata.csv"
    save_metadata_csv(all_rows, metadata_csv)
    print("\n[완료]")
    print(f"문항 이미지 개수: {len(all_rows)}")
    print(f"이미지 폴더: {out_img_dir}")
    print(f"디버그 가이드: {debug_dir}")
    print(f"메타데이터: {metadata_csv}")


if __name__ == "__main__":
    main()
