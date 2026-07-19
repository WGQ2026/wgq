#!/usr/bin/env python3
"""Capture figures/screenshots from a PDF with configurable regions.

Supports cover page capture (up to a text marker) and individual figure regions
via auto-detection of embedded images or manual y-coordinates. When auto-detecting
a figure, the script attempts to include its caption (text blocks that look like
"Fig. X ..." or "Table X ..." located immediately above or below the image).

Usage:
    python capture_figures.py --pdf input.pdf --output ./figures --config figures.json
"""

import argparse
import json
import os
import re
import fitz  # PyMuPDF


CAPTION_RE = re.compile(r"^(Fig\.?|Figure|Table|Tbl\.?)\s*\d+", re.IGNORECASE)


def capture_region(page, output_path, top_y, bottom_y, left_margin=30, right_margin=30, zoom=3.0):
    """Capture a rectangular region from a PDF page."""
    clip_rect = fitz.Rect(left_margin, top_y, page.rect.width - right_margin, bottom_y)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip_rect)
    pix.save(output_path)
    return clip_rect


def find_caption_bbox(page, image_bbox, max_distance=120, prefer="below"):
    """Find the nearest caption-like text block immediately above or below the image.

    Returns the bbox (x0, y0, x1, y1) of the caption block, or None if no caption is found.
    The `prefer` argument can be 'below' or 'above'. If no caption is found in the
    preferred direction, the other direction is tried.
    """
    text_dict = page.get_text("dict")
    candidates_below = []
    candidates_above = []

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:  # skip non-text blocks
            continue
        x0, y0, x1, y1 = block["bbox"]
        text_parts = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text_parts.append(span.get("text", ""))
        text = "".join(text_parts).strip()
        if not text:
            continue
        if not CAPTION_RE.match(text):
            continue

        # Caption below the image
        if y0 >= image_bbox[3] and (y0 - image_bbox[3]) <= max_distance:
            candidates_below.append((y0 - image_bbox[3], y0, y1, (x0, y0, x1, y1)))
        # Caption above the image
        if y1 <= image_bbox[1] and (image_bbox[1] - y1) <= max_distance:
            candidates_above.append((image_bbox[1] - y1, y0, y1, (x0, y0, x1, y1)))

    chosen = None
    if prefer == "below" and candidates_below:
        candidates_below.sort(key=lambda item: item[0])
        chosen = candidates_below[0][3]
    elif prefer == "above" and candidates_above:
        candidates_above.sort(key=lambda item: item[0])
        chosen = candidates_above[0][3]

    # Fallback: try the opposite direction if preferred direction yielded nothing
    if chosen is None:
        if candidates_below:
            candidates_below.sort(key=lambda item: item[0])
            chosen = candidates_below[0][3]
        elif candidates_above:
            candidates_above.sort(key=lambda item: item[0])
            chosen = candidates_above[0][3]

    return chosen


def main():
    parser = argparse.ArgumentParser(description="Capture figures from a PDF")
    parser.add_argument("--pdf", required=True, help="Path to input PDF")
    parser.add_argument("--output", required=True, help="Output directory for screenshots")
    parser.add_argument("--config", required=True, help="JSON config file with figure definitions")
    parser.add_argument("--zoom", type=float, default=3.0, help="Zoom factor (default: 3.0)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    doc = fitz.open(args.pdf)
    print(f"PDF pages: {len(doc)}, width: {doc[0].rect.width:.1f} pts")

    # Process cover page (capture from page top up to a text marker)
    cover = config.get("cover_page")
    if cover:
        page = doc[cover["page"]]
        markers = page.search_for(cover["end_marker"])
        if markers:
            bottom_y = markers[0].y0 - cover.get("top_offset", 5)
            path = os.path.join(args.output, cover.get("filename", "cover_page.png"))
            capture_region(page, path, 0, bottom_y, zoom=args.zoom)
            print(f"  Cover captured: {path}")

    # Process individual figures
    for fig in config.get("figures", []):
        page = doc[fig["page"]]
        page_height = page.rect.height

        if fig.get("auto_detect"):
            imgs = page.get_image_info()
            idx = fig.get("image_index", 0)
            if idx < len(imgs):
                bbox = list(imgs[idx]["bbox"])
                top_y = bbox[1] - fig.get("top_margin", 10)
                bottom_y = bbox[3]

                # Try to auto-detect and include caption
                caption_bbox = find_caption_bbox(
                    page,
                    bbox,
                    max_distance=fig.get("caption_search_distance", 120),
                    prefer=fig.get("caption_prefer", "below"),
                )
                if caption_bbox:
                    bottom_y = caption_bbox[3] + fig.get("caption_margin", 6)
                    # If caption is above, adjust top_y
                    if caption_bbox[3] < bbox[1]:
                        top_y = caption_bbox[0] - fig.get("caption_margin", 6)
                else:
                    # Fallback to legacy caption_height if no caption detected
                    bottom_y = bbox[3] + fig.get("caption_height", 0)
            else:
                print(f"  Warning: image index {idx} not found on page {fig['page']}")
                continue
        else:
            top_y = fig.get("top_y", 0)
            bottom_y = fig.get("bottom_y", page_height)

        # Clamp bottom to avoid page numbers / footers
        clamp = page_height - fig.get("bottom_margin", 40)
        if bottom_y > clamp:
            bottom_y = clamp
        if top_y < 0:
            top_y = 0

        path = os.path.join(args.output, fig["filename"])
        capture_region(page, path, top_y, bottom_y, zoom=args.zoom)
        print(f"  Figure captured: {path} (y: {top_y:.0f}-{bottom_y:.0f})")

    doc.close()
    print("Capture complete!")


if __name__ == "__main__":
    main()
