---
name: paper-sharing
description: "Generate formatted Word reading notes from academic PDF papers. Use when the user wants to create a structured Word document (with title, abstract, background, results, conclusion, references, source) from a PDF paper, including captured figure screenshots with captions preserved. The workflow includes: (1) capture figures from the PDF via PyMuPDF, (2) generate a Word document with Chinese-formatted content via python-docx. Ideal for paper sharing, journal clubs, or study notes."
---

# Paper Sharing

Generate a formatted Word document from an academic PDF paper, with captured figures (including captions) and structured Chinese-language reading notes.

## Workflow Overview

The skill follows an end-to-end pipeline:

```
PDF paper -> Analyze & extract content -> Capture figures with captions -> Generate Word -> .docx output (only on Desktop)
```

## Output File Naming

The output Word document is named using the format: **"生成日期 英文文章标题.docx"**
Example: "2026.6.29 Assessing the interaction of invasive species invasion risks and ecosystem services.docx"

**Windows compatibility**: Replace colons (:) in the title with spaces or hyphens since Windows filenames cannot contain colons.

Only one file is produced: the .docx on the user's Desktop. No intermediate files are saved.

## Prerequisites

Python packages: `PyMuPDF` (fitz), `python-docx`

Install if needed:
```
pip install PyMuPDF python-docx
```

## Scripts

Two scripts are located in the skill's scripts/ directory:

- **capture_figures.py** - Extract figure screenshots from a PDF (captions preserved)
- **generate_word.py** - Generate a formatted Word document

## Capture Figures from PDF

Use `capture_figures.py` to extract figure screenshots from the PDF.

The script accepts a JSON config file that defines which regions to capture.

### Cover page capture

Config format:
```json
{
  "cover_page": {
    "page": 0,
    "end_marker": "ABSTRACT",
    "top_offset": 5,
    "filename": "cover_page.png"
  }
}
```

The cover is captured from the top of page 0 up to the `end_marker` text (e.g., "ABSTRACT" or "A R T I C L E   I N F O" for Elsevier papers). This ensures only the title, authors, and affiliations are captured -- not the ARTICLE INFO or ABSTRACT body.

### Regular figure capture

Config format:
```json
{
  "figures": [
    {
      "id": 1,
      "page": 4,
      "filename": "figure1.png",
      "auto_detect": true,
      "image_index": 0,
      "top_margin": 10,
      "bottom_margin": 60
    }
  ]
}
```

**Important figure capture guidelines:**

1. **Single figure per screenshot**: Each screenshot must contain exactly one figure/chart. Never merge multiple figures into one screenshot.
2. **Captions must be preserved**: When `auto_detect: true`, the script automatically searches for caption-like text (e.g., "Fig. 1. ...", "Figure 1.", "Table 1.") immediately above or below the detected image and includes it in the screenshot. Set `caption_search_distance` (default 120 pts) and `caption_margin` (default 6 pts) to fine-tune.
3. **No text residue**: Use `bottom_margin` (40-80 points) to avoid capturing page numbers, footers, or running headers.
4. **Legacy fallback**: If `caption_height` is set explicitly and no auto-detected caption is found, the image is extended downward by that amount (for backward compatibility).

Usage:
```bash
python scripts/capture_figures.py --pdf paper.pdf --output ./figures --config figures.json [--zoom 3.0]
```

## Generate Word Document

Use `generate_word.py` to create the formatted Word document from captured figures and structured content.

Usage:
```bash
# With a content JSON file:
python scripts/generate_word.py --content content.json --figures ./figures --output note.docx

# Pipe content via stdin (no intermediate JSON file):
python scripts/generate_word.py --figures ./figures --output Desktop/note.docx --cleanup
```

The `--cleanup` flag automatically deletes the figures directory after generating the document.

### Content section types

#### 使用规范（重要）
- **标题无编号**：章节标题（研究背景、研究目的、研究结果、结论等）不要加数字编号
- **必含研究目的**：在“研究背景”之后、“研究结果”之前，必须单独设置“研究目的”章节，使用 （1）…（2）…（3）… 全角编号逐条列出（每条一个 paragraph），内容须提炼自本文实际研究目标（引言结尾/关键问题+方法+贡献），通常 4-6 条；**每条精简为一行单句**，不展开方法细节
- **没有研究方法**：文献分享文档不包含研究方法部分
- **最小空行**：标题与正文之间不要有空行，唯一空行在参考文献之前
- **结果子标题**：研究结果内使用 subheading 类型呈现编号子标题（1. xxx / 2. xxx）
- **结论一段**：结论部分合并为一段即可
- **正文段落格式**：所有正文段落（摘要、研究背景、研究结果、结论）默认**两端对齐**，**首行缩进 2 字符**（10.5 号字约 21 pt），除非显式将 `first_line_indent` 设为 false

#### Section types available in content JSON
- **title** (`text`, `size`): Centered, bold title
- **heading** (`text`, `size`): Section heading, bold, left-aligned
- **subheading** (`text`, `size`): Numbered subheading, bold, left-aligned
- **paragraph** (`text`, `size`, `bold`, `first_line_indent`): Body text. Default: justified alignment + first-line indent 2 characters. Set `first_line_indent: false` to disable indentation (e.g., for URLs).
- **image** (`file`, `width`): Centered figure screenshot
- **reference** (`text`, `size`): Single paper citation entry (left-aligned, no indent)
- **source** (`text`, `size`): Generates heading "文献来源" followed by the DOI/URL paragraph (left-aligned, no indent)
- **blank**: Empty paragraph for spacing

Font: Chinese text uses Song Ti (宋体), English uses Times New Roman.

## Optimized Workflow (Minimal Output)

To reduce intermediate files and token usage, the recommended workflow:

### Step 1: Analyze the PDF
Use Python to extract text and understand the paper structure (title, abstract, introduction, results, conclusion sections).

### Step 2: Build content and capture figures
In a single step, build both the figure config and content JSON, then:
1. Run capture_figures.py to extract screenshots (with captions)
2. Pipe the content JSON to generate_word.py with --cleanup

### Step 3: Verify output
Review the generated Word document and adjust if needed.

This produces **only one output file** (the .docx on Desktop). No intermediate JSON or figures directories persist.

## Document Structure Requirements (Important)

When building the content JSON for generate_word.py, follow this exact structure:

### Cover page
1. Title in Chinese (type: title, size: 16)
2. Cover screenshot (showing authors + affiliations only, no ABSTRACT/ARTICLE INFO)

### Abstract
3. Heading: "摘要"
4. Paragraph: Chinese translation of the abstract, one paragraph only (justified, first-line indent 2)

### Background (研究背景)
5. Heading: "研究背景"
6. Paragraphs: 3-4 paragraphs summarizing the introduction (justified, first-line indent 2). Keep this section focused on background/context and the research gap — do NOT put the numbered research objectives here.

### Objectives (研究目的)  ← REQUIRED, placed AFTER 研究背景 and BEFORE 研究结果
7. Heading: "研究目的"
8. Objective paragraphs: A numbered list using the full-width format （1）…（2）…（3）… , with each objective as its own body paragraph (type: paragraph, justified, first-line indent 2). Typically 4-6 objectives.
   - **内容精简（重要）**：每条目标压缩为**单行、1 个完整句子**，突出“要做什么 + 达到什么目的/揭示什么”，不要展开方法细节或写成多行长段。例如“（1）运用 MaxEnt 模型模拟四科水鸟在周边耕地中的栖息地适宜性并识别主导驱动因子；”。
   - Content MUST be derived from THIS paper's actual aims — read the end of the Introduction ("this study aims to…" / the key questions), plus the methods and stated contributions. Never copy objectives from another paper.
   - Recommended coverage when applicable: (a) data & core method (e.g., which datasets + model such as MaxEnt), (b) analytical technique & what it quantifies (e.g., OHSA hotspot dynamics), (c) spatio-temporal patterns to reveal, (d) overlap/interaction analysis (e.g., GIS overlay with policy zones), (e) mechanism/interpretation, (f) practical & scientific contribution.

### Results (研究结果)
9. Heading: "研究结果"
10. For each result subsection:
   - Subheading (type: subheading): "1. xxx", "2. xxx" etc.
   - Paragraph starting with "图X展示了……结果表明……" (justified, first-line indent 2)
   - The paragraph should first translate the original English result to Chinese, then condense appropriately
   - Include the figure screenshot (type: image) right after the paragraph that first mentions it
   - **Important**: Keep more of the result text - don't over-condense. Start with the full Chinese translation, then only lightly trim.

### Conclusion (结论)
11. Heading: "结论"
12. Paragraph: Chinese translation of the conclusion, merged into one paragraph (justified, first-line indent 2)

### References (参考文献)
13. Blank line (type: blank)
14. Heading: "参考文献"
15. Single reference entry (type: reference) using the **paper's own citation format**, not the paper's reference list. Example:
    > Li, F., Jiang, Y., Wu, L., Zhang, Z. (2025). Spatial and temporal dynamics of fragmentation and an ecosystem health assessment of plateau blue landscapes: A case study of the Caohai wetland. CATENA, Volume 250, 108730.

### Source (文献来源)
16. Heading: "文献来源"
17. Paragraph (type: source): The paper's DOI URL, e.g., `https://doi.org/10.1016/j.ecolind.2025.113443`

## Typical Usage (End-to-End)

When working with a new paper:

1. Open the PDF with PyMuPDF to extract text and understand structure
2. Identify figure locations by examining pages
3. Build a figures config JSON for capture_figures.py (let it auto-detect captions)
4. Run capture_figures.py to extract screenshots
5. Build content JSON following the Document Structure Requirements above
6. Run generate_word.py with --cleanup to produce the final .docx

All figures should be captioned as "图X" (Figure X) or "表X" (Table X) in the results section.
