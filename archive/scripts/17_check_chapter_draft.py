#!/usr/bin/env python3
"""Validate the chapter draft's structure and evidence boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.chapter import check_chapter_files


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chapter",
        type=Path,
        default=ROOT / "chapter" / "chapter-draft.md",
    )
    parser.add_argument(
        "--bibliography",
        type=Path,
        default=ROOT / "chapter-prework" / "chapter-references.bib",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "chapter" / "chapter_draft_status.json",
    )
    parser.add_argument(
        "--require-final",
        action="store_true",
        help="Reject frozen placeholders and require exactly one claim branch.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the chapter check and persist its result."""
    args = parse_args()
    result = check_chapter_files(
        args.chapter,
        args.bibliography,
        require_final=args.require_final,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    print(
        f"Chapter check: {result.status}; "
        f"{len(result.placeholders)} frozen fields; "
        f"{len(result.citations)} citation keys; "
        f"{len(result.claim_branches)} claim branches"
    )
    for error in result.errors:
        print(f"ERROR: {error}")
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
