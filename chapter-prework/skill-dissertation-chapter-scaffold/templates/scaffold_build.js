// Scaffold .docx generator template
// =====================================
// Copy this to your project's build/ directory and customize the `children` array.
// Helper functions (H1, H2, BulCite, Note, Body, Code) stay as-is across chapters.
//
// Usage:
//   1. npm install docx (in the build/ directory)
//   2. Edit the children array — assemble sections from reference/section_canonical.md
//   3. node scaffold_build.js
//   4. python validate.py output.docx  (optional)

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle
} = require('docx');

// ---------- helpers (reuse across all chapters) ----------
const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text })],
  spacing: { before: 360, after: 180 },
});

const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text })],
  spacing: { before: 240, after: 120 },
});

const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text })],
  spacing: { before: 180, after: 100 },
});

// BulCite — bold citation + annotation + optional DOI in muted color
const BulCite = (cite, note, doi) => {
  const runs = [
    new TextRun({ text: cite, bold: true }),
    new TextRun({ text: " — " + note }),
  ];
  if (doi) {
    runs.push(new TextRun({ text: "  https://doi.org/" + doi, color: "808080" }));
  }
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: runs,
    spacing: { after: 100 },
  });
};

const Note = (label, text) => new Paragraph({
  children: [
    new TextRun({ text: label + " ", bold: true, italics: true }),
    new TextRun({ text, italics: true }),
  ],
  spacing: { before: 80, after: 160 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: "999999", space: 8 } },
  indent: { left: 240 },
});

const Body = (text) => new Paragraph({
  children: [new TextRun({ text })],
  spacing: { after: 160 },
});

const Code = (text) => new Paragraph({
  children: [new TextRun({ text, font: "Consolas", size: 20 })],
  spacing: { after: 80, before: 40 },
  indent: { left: 360 },
  border: { left: { style: BorderStyle.SINGLE, size: 8, color: "BFBFBF", space: 8 } },
});

// ---------- content — CUSTOMIZE THIS ARRAY PER CHAPTER ----------
const children = [];

// Title
children.push(new Paragraph({
  children: [new TextRun({ text: "Chapter Scaffold — [CHAPTER TITLE]", bold: true, size: 36 })],
  spacing: { after: 80 },
}));
children.push(new Paragraph({
  children: [new TextRun({
    text: "[CHAPTER SUBTITLE — one line stating the claim or scope]",
    size: 26, italics: true,
  })],
  spacing: { after: 240 },
}));
children.push(new Paragraph({
  children: [new TextRun({
    text: "Working scaffold, [DATE]. Sized for a [MSc/PhD] chapter. Each section gives a brief framing paragraph, a short list of load-bearing references with DOIs, and inline notes where the literature is thin or a methodological position needs to be taken.",
    italics: true
  })],
  spacing: { after: 240 },
}));

// Section 0 — Framing
children.push(H1("0. Framing and positioning"));
children.push(Body("[STATE THE CLAIM PLAINLY. Name predecessor work if any. State the methodological frame. Two paragraphs total.]"));
children.push(Body("[POSITIONING — name 2-3 active research conversations the chapter speaks to. State the contribution at the intersection.]"));

// Section 1 — Context
children.push(H1("1. Context / setting"));
// ... use H2 for sub-sections, BulCite for references
// Example:
// children.push(H2("1.1 [Sub-context]"));
// children.push(Body("[brief framing]"));
// children.push(BulCite("Author Year, Venue", "annotation.", "10.xxxx/yyyyy"));

// Section 9 — Predecessor work (if applicable)
// children.push(H1("9. Predecessor work — the empirical foundation"));
// ...

// Section 12 — Gaps and contribution (always)
children.push(H1("[N]. Gaps and contribution"));
children.push(Body("[Three to five gaps in the published literature define the contribution space.]"));
children.push(BulCite("Gap A — [name]", "[one-sentence framing]."));
children.push(BulCite("Gap B — [name]", "[one-sentence framing]."));
children.push(BulCite("Gap C — [name]", "[one-sentence framing]."));
children.push(Body("[Single-sentence contribution statement, or three claims structured as methodological / empirical / applied.]"));

// ---------- assemble ----------
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Calibri", color: "1F3864" },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Calibri", color: "2E75B6" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, italics: true, font: "Calibri" },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children,
  }],
});

// Save to your workspace folder (adjust path as needed)
const outPath = "[/path/to/workspace]/Chapter scaffold.docx";
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log("wrote scaffold");
});
