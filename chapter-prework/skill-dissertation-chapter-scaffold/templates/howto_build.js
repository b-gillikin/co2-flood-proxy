// Monthly How-To .docx generator template
// =========================================
// Copy this to your project's build/ directory and customize per chapter.
// Each month gets its own How-To doc; concatenate or split as needed.

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle
} = require('docx');

// ---------- helpers ----------
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
const Body = (text) => new Paragraph({
  children: [new TextRun({ text })],
  spacing: { after: 160 },
});
const Bul = (text) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: [new TextRun({ text })],
  spacing: { after: 80 },
});
const BulLabel = (label, text) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: [
    new TextRun({ text: label, bold: true }),
    new TextRun({ text: " — " + text }),
  ],
  spacing: { after: 80 },
});
const Code = (text) => new Paragraph({
  children: [new TextRun({ text, font: "Consolas", size: 20 })],
  spacing: { after: 80, before: 40 },
  indent: { left: 360 },
  border: { left: { style: BorderStyle.SINGLE, size: 8, color: "BFBFBF", space: 8 } },
});
const Note = (label, text) => new Paragraph({
  children: [
    new TextRun({ text: label + " ", bold: true, italics: true }),
    new TextRun({ text, italics: true }),
  ],
  spacing: { before: 80, after: 160 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: "999999", space: 8 } },
  indent: { left: 240 },
});

function titleBlock(title, subtitle, preamble) {
  return [
    new Paragraph({ children: [new TextRun({ text: title, bold: true, size: 36 })], spacing: { after: 80 } }),
    new Paragraph({ children: [new TextRun({ text: subtitle, size: 26, italics: true })], spacing: { after: 240 } }),
    new Paragraph({ children: [new TextRun({ text: preamble, italics: true })], spacing: { after: 240 } }),
  ];
}

// ---------- task structure ----------
// Each task in the plan has: Why, How, Output, Time.
// Use BulLabel for each. Add Code blocks for commands/code.
//
// Each WEEK has 3-6 tasks.
// Each MONTH has 3-5 weeks.
// Month 1 should include a Pre-work section before Week 1.

function taskBlock(taskName, why, how, output, time, watch) {
  const block = [
    new Paragraph({
      heading: HeadingLevel.HEADING_2,
      children: [new TextRun({ text: taskName })],
      spacing: { before: 240, after: 120 },
    }),
    BulLabel("Why", why),
    BulLabel("How", how),
    BulLabel("Output", output),
    BulLabel("Time", time),
  ];
  if (watch) block.splice(4, 0, BulLabel("Watch for", watch));
  return block;
}

function killCheck(name, criterion, rule, compareTo, output) {
  return [
    new Paragraph({
      heading: HeadingLevel.HEADING_2,
      children: [new TextRun({ text: `KILL CHECK — ${name}` })],
      spacing: { before: 240, after: 120 },
    }),
    BulLabel("Criterion", criterion),
    BulLabel("Rule", rule),
    compareTo ? BulLabel("Compare to", compareTo) : null,
    BulLabel("Output", output),
  ].filter(Boolean);
}

// ---------- example: customize per chapter ----------
const monthChildren = [
  ...titleBlock(
    "[MONTH] 2026 — How-To",
    "Month [N]: [PHASE NAME]",
    "Goal for the month: [one-paragraph goal statement]."
  ),

  // Month 1 only: pre-work section
  H1("Pre-work (do these before the sprint starts)"),
  Body("[Foundational tasks done before the regular schedule starts.]"),
  ...taskBlock(
    "PW-1. [Pre-work task name]",
    "[reason]",
    "[step-by-step]",
    "[output file/result]",
    "[time estimate]"
  ),

  H1("Week 1 ([dates]): [phase name]"),
  ...taskBlock(
    "Task 1.1 — [name]",
    "[why]",
    "[how]",
    "[output]",
    "[time]",
    "[watch for]"
  ),

  // Insert kill checks where appropriate
  ...killCheck(
    "[check name]",
    "[specific measurable criterion]",
    "[outcome A → proceed; outcome B → pause; outcome C → redirect]",
    "[external benchmark for sanity check]",
    "decision recorded in docs/decisions.md"
  ),

  H1("End-of-month review"),
  Bul("[ ] [check item 1]"),
  Bul("[ ] [check item 2]"),
  Note("If a check fails", "Don't paper over it. Document and consult supervisor."),
];

// ---------- assemble and write ----------
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
    children: monthChildren,
  }],
});

const outPath = "[/path/to/workspace]/[Month] - How-To.docx";
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log("wrote how-to");
});
