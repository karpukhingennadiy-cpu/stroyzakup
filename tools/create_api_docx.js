import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType,
  Document,
  Footer,
  Header,
  HeadingLevel,
  Packer,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) {
  throw new Error("Usage: node create_api_docx.js /absolute/path/output.docx");
}

// Read API.md
const root = path.resolve(path.dirname(import.meta.url.replace("file:///", "")));
const mdPath = path.join(root, "..", "docs", "API.md");
const mdText = fs.readFileSync(mdPath, "utf-8");

const palette = {
  dark: "263238",
  primary: "37474F",
  light: "78909C",
  border: "D8E0E3",
  fill: "EEF3F6",
};

const font = {
  ascii: "Arial",
  hAnsi: "Arial",
  cs: "Arial",
};

const run = (text, options = {}) =>
  new TextRun({ text, font, size: 22, ...options });

const para = (children, options = {}) =>
  new Paragraph({
    spacing: { after: 120, line: 280 },
    ...options,
    children: Array.isArray(children) ? children : [children],
  });

const heading = (text, level = 1) =>
  para(run(text, { bold: true, size: level === 1 ? 28 : level === 2 ? 24 : 22, color: palette.dark }), {
    heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 120 },
  });

const cell = (text, options = {}) =>
  new TableCell({
    children: [para(run(text), { spacing: { after: 60, line: 240 } })],
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    ...options,
  });

// Simple markdown parser for API.md structure
const lines = mdText.split("\n");
const children = [];
let i = 0;

while (i < lines.length) {
  const line = lines[i];

  // Title (H1)
  if (line.startsWith("# ")) {
    children.push(
      para(run(line.slice(2), { bold: true, size: 32, color: palette.dark }), {
        heading: HeadingLevel.TITLE,
        alignment: AlignmentType.CENTER,
        spacing: { after: 360 },
      })
    );
    i++;
    continue;
  }

  // H2
  if (line.startsWith("## ")) {
    children.push(heading(line.slice(3), 1));
    i++;
    continue;
  }

  // H3
  if (line.startsWith("### ")) {
    children.push(heading(line.slice(4), 2));
    i++;
    continue;
  }

  // Table
  if (line.startsWith("|")) {
    const tableLines = [];
    while (i < lines.length && lines[i].startsWith("|")) {
      tableLines.push(lines[i]);
      i++;
    }
    // Skip separator line
    const dataLines = tableLines.filter((l) => !l.match(/^\|[\s\-:|]+\|$/));
    if (dataLines.length > 0) {
      const rows = dataLines.map((rowLine) => {
        const cells = rowLine
          .split("|")
          .slice(1, -1)
          .map((c) => c.trim());
        return new TableRow({
          children: cells.map((c, idx) =>
            cell(c, {
              shading:
                idx === 0
                  ? { type: ShadingType.CLEAR, fill: palette.fill }
                  : undefined,
            })
          ),
        });
      });
      const ncols = Math.max(...dataLines.map((l) => l.split("|").length - 2));
      const colW = 9000 / Math.max(ncols, 1);
      children.push(
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          columnWidths: Array(ncols).fill(colW),
          rows,
        })
      );
      children.push(new Paragraph({ spacing: { after: 120 } }));
    }
    continue;
  }

  // Code block
  if (line.startsWith("```")) {
    const lang = line.slice(3).trim();
    i++;
    const codeLines = [];
    while (i < lines.length && !lines[i].startsWith("```")) {
      codeLines.push(lines[i]);
      i++;
    }
    i++; // skip ```
    children.push(
      para(run(codeLines.join("\n"), { font: { ascii: "Courier New", hAnsi: "Courier New", cs: "Courier New" }, size: 18 }), {
        spacing: { after: 120 },
        shading: { type: ShadingType.CLEAR, fill: "F5F5F5" },
      })
    );
    continue;
  }

  // Inline code
  if (line.includes("`")) {
    const parts = [];
    let text = line;
    let match;
    while ((match = text.match(/`([^`]+)`/)) !== null) {
      const idx = text.indexOf(match[0]);
      if (idx > 0) {
        parts.push(run(text.slice(0, idx)));
      }
      parts.push(
        run(match[1], {
          font: { ascii: "Courier New", hAnsi: "Courier New", cs: "Courier New" },
          size: 20,
        })
      );
      text = text.slice(idx + match[0].length);
    }
    if (text) parts.push(run(text));
    children.push(para(parts));
    i++;
    continue;
  }

  // Regular paragraph (skip empty)
  if (line.trim()) {
    children.push(para(run(line.trim())));
  }
  i++;
}

const doc = new Document({
  features: { updateFields: false },
  sections: [
    {
      properties: {
        page: {
          margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [
            para(run("API Reference — Минитендер.рф", { bold: true, color: palette.primary }), {
              alignment: AlignmentType.CENTER,
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            para(new TextRun({ children: [PageNumber.CURRENT] }), {
              alignment: AlignmentType.CENTER,
            }),
          ],
        }),
      },
      children,
    },
  ],
});

const buffer = await Packer.toBuffer(doc);
fs.writeFileSync(outputPath, buffer);
console.log("DOCX created:", outputPath);
