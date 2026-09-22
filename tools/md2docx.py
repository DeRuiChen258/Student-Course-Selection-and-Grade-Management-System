"""Markdown → docx（A4、页边距 2.5cm、正文小四、1.5 倍行距、页脚页码、三线表、图注）。

用法：
    python3 tools/md2docx.py --input docs/设计说明书.md --output docs/out/设计说明书.docx
    python3 tools/md2docx.py ... --toc-json docs/out/toc.json    # 第二遍：填入真实页码
"""

import argparse
import json
import os
import re
import subprocess

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SONG = "宋体"
HEI = "黑体"
MONO = "Consolas"
BODY_SIZE = Pt(12)
CODE_SIZE = Pt(10.5)
BODY_LINE = Pt(20)          # 小四字号下等效 1.5 倍行距
CODE_LINE = Pt(13.5)


def set_cjk(run, name):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:eastAsia"), name)
    fonts.set(qn("w:ascii"), name)
    fonts.set(qn("w:hAnsi"), name)


def configure(document):
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    for attr in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(section, attr, Cm(2.5))

    normal = document.styles["Normal"]
    normal.font.size = BODY_SIZE
    normal.font.name = SONG
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    normal.paragraph_format.line_spacing = BODY_LINE
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    normal.paragraph_format.space_after = Pt(0)

    for level, size in ((1, Pt(16)), (2, Pt(14)), (3, Pt(12))):
        try:
            style = document.styles[f"Heading {level}"]
        except KeyError:
            continue
        style.font.size = size
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.name = HEI
        style.element.rPr.rFonts.set(qn("w:eastAsia"), HEI)
        style.paragraph_format.space_before = Pt(12 if level == 1 else 8)
        style.paragraph_format.space_after = Pt(8 if level == 1 else 6)
        style.paragraph_format.line_spacing = Pt(26 if level == 1 else 22)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        if level == 1:
            style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(document.sections[0])
    relax_header_footer(document)
    return document


def relax_header_footer(document):
    """页眉页脚里的图片同样不能被精确行距裁剪（模板封面校徽踩过这个坑）。"""
    for section in document.sections:
        for name in ("header", "footer", "first_page_header", "first_page_footer",
                     "even_page_header", "even_page_footer"):
            try:
                holder = getattr(section, name)
                linked = holder.is_linked_to_previous
            except Exception:
                continue
            if linked:
                continue
            for paragraph in holder.paragraphs:
                paragraph.paragraph_format.line_spacing = None
                paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE


def setup_document():
    return configure(Document())


def add_page_number(section):
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    set_cjk(run, SONG)
    run.font.size = Pt(10.5)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._element.append(begin)
    run._element.append(instr)
    run._element.append(end)


def add_runs(paragraph, text, size=BODY_SIZE, mono=False):
    for piece in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**"):
            run = paragraph.add_run(piece[2:-2])
            run.bold = True
        elif piece.startswith("`") and piece.endswith("`"):
            run = paragraph.add_run(piece[1:-1])
            set_cjk(run, MONO)
            run.font.size = Pt(size.pt - 0.5)
            continue
        else:
            run = paragraph.add_run(piece)
        set_cjk(run, MONO if mono else SONG)
        run.font.size = size
    return paragraph


def add_body(document, text):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Pt(24)
    add_runs(paragraph, text)
    return paragraph


def add_code(document, lines):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = CODE_LINE
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    paragraph.paragraph_format.left_indent = Pt(12)
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(6)
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), "F5F5F5")
    paragraph._element.get_or_add_pPr().append(shading)
    for index, line in enumerate(lines):
        run = paragraph.add_run(line)
        set_cjk(run, MONO)
        run.font.size = CODE_SIZE
        if index != len(lines) - 1:
            run.add_break()
    return paragraph


def set_cell(cell, text, bold=False, size=Pt(10.5)):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.line_spacing = Pt(12.5)
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = size
    set_cjk(run, HEI if bold else SONG)


def display_width(text):
    return sum(2 if ord(ch) > 0x2000 else 1 for ch in text)


def three_line_table(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge, size in (("top", 12), ("bottom", 12)):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:color"), "000000")
        borders.append(element)
    for edge in ("left", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "none")
        element.set(qn("w:sz"), "0")
        borders.append(element)
    tbl_pr.append(borders)
    for cell in table.rows[0].cells:
        tc_pr = cell._tc.get_or_add_tcPr()
        cell_borders = OxmlElement("w:tcBorders")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "8")
        bottom.set(qn("w:color"), "000000")
        cell_borders.append(bottom)
        tc_pr.append(cell_borders)


def add_table(document, header, rows, caption=None):
    caption_paragraph = None
    if caption:
        caption_paragraph = document.add_paragraph()
        caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_paragraph.paragraph_format.space_before = Pt(6)
        run = caption_paragraph.add_run(caption)
        run.bold = True
        run.font.size = Pt(10.5)
        set_cjk(run, HEI)
    table = document.add_table(rows=1, cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    size = Pt(9.5) if len(header) >= 5 else Pt(10)
    weights = []
    for index, title in enumerate(header):
        longest = max([display_width(title)] + [display_width(row[index]) if index < len(row) else 0
                                                for row in rows])
        weights.append(min(max(longest, 6), 24))
    total = sum(weights)
    widths = [Cm(16.0 * weight / total) for weight in weights]
    for index, width in enumerate(widths):
        table.columns[index].width = width
    for index, text in enumerate(header):
        set_cell(table.rows[0].cells[index], text, bold=True, size=size)
    for row in rows:
        cells = table.add_row().cells
        for index in range(len(header)):
            set_cell(cells[index], row[index] if index < len(row) else "", size=size)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            cell.width = widths[index]
    three_line_table(table)
    document.add_paragraph()
    anchor = caption_paragraph if caption_paragraph is not None else table.rows[0].cells[0].paragraphs[0]
    return anchor, table


def add_image(document, path, caption, width_cm=15):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    # 图片所在段落必须使用单倍行距，否则精确行距会把图片裁剪成一条
    paragraph.paragraph_format.line_spacing = None
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    run = paragraph.add_run()
    run.add_picture(path, width=Cm(width_cm))
    caption_paragraph = document.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_after = Pt(10)
    run = caption_paragraph.add_run(caption)
    run.font.size = Pt(10.5)
    run.bold = True
    set_cjk(run, HEI)
    return paragraph


def add_toc(document, entries, placeholder):
    heading = document.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.paragraph_format.page_break_before = True   # 目录单独成页
    run = heading.add_run("目　录")
    run.bold = True
    run.font.size = Pt(16)
    set_cjk(run, HEI)
    document.add_paragraph()
    for entry in entries:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.line_spacing = Pt(18)
        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        paragraph.paragraph_format.left_indent = Pt(0 if entry["level"] == 1 else 20)
        tab_stops = paragraph.paragraph_format.tab_stops
        tab_stops.add_tab_stop(Cm(16), WD_TAB_ALIGNMENT.RIGHT, 1)   # 1 = 点线前导符
        run = paragraph.add_run(entry["title"])
        set_cjk(run, HEI if entry["level"] == 1 else SONG)
        run.font.size = BODY_SIZE if entry["level"] == 1 else Pt(11)
        run = paragraph.add_run("\t" + ("?" if placeholder else str(entry.get("page", ""))))
        run.font.size = BODY_SIZE if entry["level"] == 1 else Pt(11)
        set_cjk(run, SONG)
    document.add_page_break()
    return None


def parse_markdown(document, lines, toc_entries, toc_placeholder):
    index = 0
    pending_caption = None
    pending_break = False

    def mark_break(paragraph):
        nonlocal pending_break
        if pending_break and paragraph is not None:
            paragraph.paragraph_format.page_break_before = True
            pending_break = False
        return paragraph

    while index < len(lines):
        line = lines[index].rstrip("\n")
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped == "@toc":
            add_toc(document, toc_entries, toc_placeholder)
            pending_break = False
            index += 1
            continue
        if stripped == "@pagebreak":
            pending_break = True
            index += 1
            continue
        if stripped.startswith("```"):
            block = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index].rstrip("\n"))
                index += 1
            index += 1
            mark_break(add_code(document, block))
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and set(lines[index + 1].strip()) <= set("|-: "):
            header = [cell.strip() for cell in stripped.strip("|").split("|")]
            rows = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            caption = pending_caption
            pending_caption = None
            anchor, _ = add_table(document, header, rows, caption)
            mark_break(anchor)
            continue
        if stripped.startswith("@table"):
            pending_caption = stripped[len("@table"):].strip()
            index += 1
            continue
        if stripped.startswith("!["):
            match = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
            if match:
                mark_break(add_image(document, match.group(2), match.group(1)))
            index += 1
            continue
        if stripped.startswith("@center"):
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            mark_break(paragraph)
            add_runs(paragraph, stripped[len("@center"):].strip(), size=Pt(14))
            index += 1
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            mark_break(document.add_heading(text, level=min(level, 4)))
            index += 1
            continue
        if stripped.startswith("> "):
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Pt(24)
            mark_break(paragraph)
            add_runs(paragraph, stripped[2:], size=Pt(11))
            index += 1
            continue
        if stripped.startswith("- "):
            paragraph = document.add_paragraph(style="List Bullet")
            mark_break(paragraph)
            add_runs(paragraph, stripped[2:])
            index += 1
            continue
        match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if match:
            paragraph = document.add_paragraph(style="List Number")
            mark_break(paragraph)
            add_runs(paragraph, match.group(2))
            index += 1
            continue
        mark_break(add_body(document, stripped))
        index += 1


def collect_toc(lines):
    entries = []
    in_code = False
    seen_toc_marker = False
    for line in lines:
        stripped = line.strip()
        if stripped == "@toc":
            seen_toc_marker = True
            continue
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        if level <= 2:
            if not seen_toc_marker:
                continue     # 封面标题不进目录
            entries.append({"level": level, "title": stripped[level:].strip()})
    return entries


def scan_pages(pdf_path, entries):
    probe = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True, check=True)
    total = 0
    for line in probe.stdout.splitlines():
        if line.startswith("Pages:"):
            total = int(line.split(":")[1].strip())
    page_texts = []
    for page in range(1, total + 1):
        result = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), pdf_path, "-"],
                                capture_output=True, text=True, check=True)
        page_texts.append(re.sub(r"\s+", "", result.stdout))
    # 目录页本身也包含全部标题，必须从目录之后开始定位页码
    toc_pages = [index for index, text in enumerate(page_texts[:8])
                 if text.count("....") >= 5 or text.count("----") >= 5]
    first_body = max(toc_pages) + 1 if toc_pages else 0
    print(f"检测到目录页 {[p + 1 for p in toc_pages]}，正文从第 {first_body + 1} 页开始定位")
    for entry in entries:
        key = re.sub(r"\s+", "", entry["title"])
        entry["page"] = next((index + 1 for index, text in enumerate(page_texts[first_body:], start=first_body)
                              if key in text), "")
    print("扫描到页码：", ", ".join(f"{e['title']}={e['page']}" for e in entries[:6]), "...")
    return entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="设计说明书")
    parser.add_argument("--toc-json", default=None)
    parser.add_argument("--scan-pdf", default=None, help="扫描 PDF 生成目录页码（配合 --toc-json 使用）")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as handle:
        lines = handle.readlines()

    toc_entries = collect_toc(lines)
    if args.scan_pdf:
        toc_entries = scan_pages(args.scan_pdf, toc_entries)
        target = args.toc_json or os.path.join(os.path.dirname(os.path.abspath(args.output)), "toc.json")
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump({"entries": toc_entries}, handle, ensure_ascii=False, indent=2)
        print(f"目录页码已写入 {target}")
        return
    if args.toc_json and os.path.exists(args.toc_json):
        with open(args.toc_json, encoding="utf-8") as handle:
            pages = {item["title"]: item.get("page") for item in json.load(handle)["entries"]}
        for entry in toc_entries:
            entry["page"] = pages.get(entry["title"], "")

    document = setup_document()
    parse_markdown(document, lines, toc_entries, args.toc_json is None)
    core = document.core_properties
    core.title = args.title
    core.author = "数据库原理与应用 课程作业"

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    document.save(args.output)
    print(f"已生成 {args.output}（目录条目 {len(toc_entries)} 条"
          + ("，占位页码" if args.toc_json is None else "，真实页码") + "）")


if __name__ == "__main__":
    main()
