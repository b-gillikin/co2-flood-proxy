#!/usr/bin/env python3
"""BibTeX export template for chapter references.

Each entry's `keywords` field becomes a Mendeley/Zotero tag, which lets you
organize the imported references into folders matching the scaffold sections
in one click.

Usage:
    1. Populate the `entries` list with (citekey, type, fields, section_tag) tuples
    2. python bibtex_export.py
    3. Drop the .bib into your reference manager
"""

# Each entry: (citekey, type, fields_dict, section_tag)
# Supported types: article, book, incollection, inproceedings, mastersthesis,
#                  phdthesis, techreport, misc
# section_tag is used as the keyword field; pick names that map to your
# scaffold sections (e.g. "2 Post-mining hydrogeology").

entries = [
    # Example article
    # ("Author2024",  "article", {
    #     "author": "Author, A. B. and Other, C. D.",
    #     "title": "Title of the paper",
    #     "journal": "Journal of Examples",
    #     "year": "2024", "volume": "10", "number": "2", "pages": "100--110",
    #     "doi": "10.xxxx/yyyyy"
    # }, "1.1 Section name"),

    # Example book
    # ("Author2020Book",  "book", {
    #     "author": "Author, A.",
    #     "title": "Title of the Book",
    #     "publisher": "Publisher",
    #     "year": "2020",
    #     "isbn": "978-0-123-45678-9"
    # }, "Section name"),

    # Example thesis
    # ("Predecessor2022",  "mastersthesis", {
    #     "author": "Last, First",
    #     "title": "Thesis title",
    #     "school": "University Name, Department",
    #     "year": "2022",
    #     "note": "Supervisor: Name. N pp."
    # }, "9 Predecessor work"),
]


def fmt_entry(citekey, etype, fields, section):
    """Format one entry in BibTeX syntax. Field ordering follows convention."""
    lines = [f"@{etype}{{{citekey},"]
    fields = dict(fields)
    fields["keywords"] = section
    keys_order = ["author", "title", "journal", "booktitle", "editor", "publisher",
                  "school", "institution", "address", "series", "edition",
                  "volume", "number", "pages", "year", "month",
                  "doi", "url", "isbn", "note", "howpublished", "keywords"]
    for k in keys_order:
        if k in fields:
            v = fields[k]
            lines.append(f"  {k} = {{{v}}},")
    if lines[-1].endswith(","):
        lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def main():
    header = (
        "% Chapter references\n"
        "% Encoding: UTF-8 (LaTeX-escaped where convenient)\n"
        "% Keywords on each entry correspond to chapter scaffold section.\n"
        "% Import: drop into Mendeley/Zotero/EndNote; the keywords become tags.\n\n"
    )
    out_path = "[/path/to/workspace]/chapter-references.bib"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        for citekey, etype, fields, section in entries:
            f.write(fmt_entry(citekey, etype, fields, section))
            f.write("\n\n")
    print(f"Wrote {len(entries)} entries to {out_path}")


if __name__ == "__main__":
    main()
