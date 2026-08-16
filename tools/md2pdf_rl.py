#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown -> PDF via markdown-it-py + reportlab (Cyrillic-safe, no external deps)."""

import re
import sys
import textwrap
from pathlib import Path

from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

FONTS_DIR = Path(r"C:\Windows\Fonts")


def register_fonts():
    pdfmetrics.registerFont(TTFont("Arial", str(FONTS_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONTS_DIR / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONTS_DIR / "ariali.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FONTS_DIR / "arialbi.ttf")))
    pdfmetrics.registerFont(TTFont("CourierNew", str(FONTS_DIR / "cour.ttf")))
    pdfmetrics.registerFont(TTFont("CourierNew-Bold", str(FONTS_DIR / "courbd.ttf")))
    pdfmetrics.registerFontFamily(
        "Arial",
        normal="Arial",
        bold="Arial-Bold",
        italic="Arial-Italic",
        boldItalic="Arial-BoldItalic",
    )


def make_styles():
    base = dict(fontName="Arial", fontSize=10.5, leading=15, textColor=colors.HexColor("#222222"))
    return {
        "body": ParagraphStyle("body", spaceAfter=6, **base),
        "h1": ParagraphStyle(
            "h1", fontName="Arial-Bold", fontSize=19, leading=24, alignment=TA_CENTER,
            spaceBefore=4, spaceAfter=14, textColor=colors.HexColor("#111111"),
        ),
        "h2": ParagraphStyle(
            "h2", fontName="Arial-Bold", fontSize=14.5, leading=19, spaceBefore=14,
            spaceAfter=6, textColor=colors.HexColor("#1a1a1a"),
        ),
        "h3": ParagraphStyle(
            "h3", fontName="Arial-Bold", fontSize=12, leading=16, spaceBefore=10,
            spaceAfter=4, textColor=colors.HexColor("#333333"),
        ),
        "h4": ParagraphStyle(
            "h4", fontName="Arial-Bold", fontSize=11, leading=15, spaceBefore=8,
            spaceAfter=4, textColor=colors.HexColor("#333333"),
        ),
        "code": ParagraphStyle(
            "code", fontName="CourierNew", fontSize=9, leading=12,
            backColor=colors.HexColor("#f5f5f5"), borderColor=colors.HexColor("#dddddd"),
            borderWidth=0.5, borderPadding=6, spaceBefore=4, spaceAfter=8,
            leftIndent=0,
        ),
        "quote": ParagraphStyle(
            "quote", fontName="Arial-Italic", fontSize=10.5, leading=15,
            leftIndent=14, borderColor=colors.HexColor("#cccccc"), borderWidth=0,
            textColor=colors.HexColor("#555555"), spaceAfter=6,
        ),
        "cell": ParagraphStyle("cell", fontSize=9.5, leading=13, **{k: v for k, v in base.items() if k != "fontSize" and k != "leading"}),
        "cell_head": ParagraphStyle(
            "cell_head", fontName="Arial-Bold", fontSize=9.5, leading=13,
            textColor=colors.HexColor("#111111"),
        ),
    }


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_inline(children):
    """Render markdown-it inline children to reportlab mini-HTML."""
    out = []
    for t in children or []:
        if t.type == "text":
            out.append(esc(t.content))
        elif t.type == "code_inline":
            out.append(
                '<font face="CourierNew" size="9" backColor="#f0f0f0">%s</font>' % esc(t.content)
            )
        elif t.type == "strong_open":
            out.append("<b>")
        elif t.type == "strong_close":
            out.append("</b>")
        elif t.type == "em_open":
            out.append("<i>")
        elif t.type == "em_close":
            out.append("</i>")
        elif t.type == "s_open":
            out.append("<strike>")
        elif t.type == "s_close":
            out.append("</strike>")
        elif t.type == "softbreak" or t.type == "hardbreak":
            out.append("<br/>")
        elif t.type == "link_open":
            out.append('<font color="#1a5fb4">')
        elif t.type == "link_close":
            out.append("</font>")
        elif t.type == "image":
            alt = t.content or ""
            out.append("[изображение: %s]" % esc(alt))
        elif t.type == "html_inline":
            pass  # drop raw html
        else:
            if t.content:
                out.append(esc(t.content))
    return "".join(out)


class MDRenderer:
    def __init__(self, styles):
        self.s = styles

    def render(self, tokens):
        flow = []
        i = 0
        list_stack = []  # ("bullet"|"ordered", counter)
        while i < len(tokens):
            t = tokens[i]
            if t.type == "heading_open":
                inline = tokens[i + 1]
                level = int(t.tag[1])
                style = self.s.get("h%d" % level, self.s["h4"])
                flow.append(Paragraph(render_inline(inline.children), style))
                if level == 2:
                    flow.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#dddddd"), spaceAfter=6))
                i += 3
            elif t.type == "paragraph_open":
                # skip paragraphs inside list items / blockquotes: handled by parents? No—flat stream.
                inline = tokens[i + 1]
                if inline.type == "inline":
                    indent = 18 * len(list_stack)
                    style = ParagraphStyle("tmp", parent=self.s["body"], leftIndent=indent)
                    prefix = ""
                    if list_stack and tokens[i - 1].type == "list_item_open":
                        kind, num = list_stack[-1]
                        prefix = ("• " if kind == "bullet" else "%d. " % num)
                        flow.append(Paragraph(prefix + render_inline(inline.children), style))
                    else:
                        flow.append(Paragraph(render_inline(inline.children), style))
                i += 3
            elif t.type == "bullet_list_open":
                list_stack.append(("bullet", 0))
                i += 1
            elif t.type == "ordered_list_open":
                start = int(t.attrs.get("start", 1)) if t.attrs else 1
                list_stack.append(("ordered", start - 1))
                i += 1
            elif t.type in ("bullet_list_close", "ordered_list_close"):
                list_stack.pop()
                flow.append(Spacer(1, 4))
                i += 1
            elif t.type == "list_item_open":
                if list_stack:
                    kind, num = list_stack[-1]
                    list_stack[-1] = (kind, num + 1)
                i += 1
            elif t.type == "list_item_close":
                i += 1
            elif t.type == "fence" or t.type == "code_block":
                code = t.content.rstrip("\n")
                wrapped_lines = []
                for line in code.split("\n"):
                    if len(line) > 96:
                        wrapped_lines.extend(textwrap.wrap(line, 96, replace_whitespace=False) or [""])
                    else:
                        wrapped_lines.append(line)
                flow.append(Preformatted("\n".join(wrapped_lines), self.s["code"]))
                i += 1
            elif t.type == "blockquote_open":
                # gather until close
                depth = 1
                j = i + 1
                inner = []
                while j < len(tokens) and depth:
                    if tokens[j].type == "blockquote_open":
                        depth += 1
                    elif tokens[j].type == "blockquote_close":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(tokens[j])
                    j += 1
                sub = MDRenderer(self.s)
                sub_flow = sub.render(inner)
                for f in sub_flow:
                    if isinstance(f, Paragraph):
                        f.style = ParagraphStyle("q", parent=self.s["quote"])
                flow.extend(sub_flow)
                i = j + 1
            elif t.type == "hr":
                flow.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cccccc"), spaceBefore=8, spaceAfter=8))
                i += 1
            elif t.type == "table_open":
                table_flow, i = self._render_table(tokens, i)
                flow.append(table_flow)
                flow.append(Spacer(1, 8))
            elif t.type == "html_block":
                i += 1
            else:
                i += 1
        return flow

    def _render_table(self, tokens, i):
        rows = []
        header_done = False
        j = i + 1
        current_row = None
        in_head = False
        while j < len(tokens) and tokens[j].type != "table_close":
            t = tokens[j]
            if t.type == "thead_open":
                in_head = True
            elif t.type == "thead_close":
                in_head = False
                header_done = True
            elif t.type == "tr_open":
                current_row = []
            elif t.type in ("th_open", "td_open"):
                inline = tokens[j + 1]
                style = self.s["cell_head"] if (in_head or t.type == "th_open") else self.s["cell"]
                current_row.append(Paragraph(render_inline(inline.children), style))
                j += 2  # skip inline + close
            elif t.type == "tr_close":
                if current_row is not None:
                    rows.append(current_row)
                current_row = None
            j += 1
        if not rows:
            return Spacer(1, 1), j + 1
        ncols = max(len(r) for r in rows)
        for r in rows:
            while len(r) < ncols:
                r.append(Paragraph("", self.s["cell"]))
        avail = A4[0] - 4 * cm
        col_w = [avail / ncols] * ncols
        tbl = Table(rows, colWidths=col_w, repeatRows=1)
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                ]
            )
        )
        return tbl, j + 1


def convert(md_path: Path, pdf_path: Path, title: str):
    md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    text = md_path.read_text(encoding="utf-8")
    tokens = md.parse(text)
    styles = make_styles()
    renderer = MDRenderer(styles)
    story = renderer.render(tokens)

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Arial", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(2 * cm, A4[1] - 1.2 * cm, title)
        canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm, "стр. %d" % doc.page)
        canvas.restoreState()

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=title,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=on_page)])
    doc.build(story)


def main():
    register_fonts()
    if len(sys.argv) >= 3:
        pairs = [(Path(sys.argv[1]), Path(sys.argv[2]))]
    else:
        # default batch: README + docs/*.md -> docs/pdf/
        root = Path(r"D:\Work\SaleManager\stroyzakup")
        out = root / "docs" / "pdf"
        pairs = [(root / "README.md", out / "README.pdf")]
        for md_file in sorted((root / "docs").glob("*.md")):
            pairs.append((md_file, out / (md_file.stem + ".pdf")))
    ok, fail = 0, 0
    for md_path, pdf_path in pairs:
        try:
            convert(md_path, pdf_path, md_path.stem)
            print("OK  %s -> %s" % (md_path, pdf_path))
            ok += 1
        except Exception as e:
            print("FAIL %s: %s" % (md_path, e))
            fail += 1
    print("done: %d ok, %d failed" % (ok, fail))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
