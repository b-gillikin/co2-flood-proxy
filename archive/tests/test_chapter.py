import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.chapter import CLAIM_BRANCHES, check_chapter_files, check_chapter_text


class ChapterCheckTests(unittest.TestCase):
    def test_working_chapter_is_structurally_valid(self) -> None:
        result = check_chapter_files(
            ROOT / "chapter" / "chapter-draft.md",
            ROOT / "chapter-prework" / "chapter-references.bib",
        )

        self.assertEqual(result.status, "ok")
        self.assertTrue(result.placeholders)
        self.assertEqual(sorted(result.claim_branches), sorted(CLAIM_BRANCHES))
        self.assertFalse(result.missing_citations)

    def test_unknown_citation_fails(self) -> None:
        text = _minimal_chapter("A statement [@Missing2026]. {{FROZEN:test.value}}")
        result = check_chapter_text(text, "@article{Known2026, title={Known}}")

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.missing_citations, ["Missing2026"])

    def test_working_chapter_cannot_pass_final_gate(self) -> None:
        result = check_chapter_files(
            ROOT / "chapter" / "chapter-draft.md",
            ROOT / "chapter-prework" / "chapter-references.bib",
            require_final=True,
        )

        self.assertEqual(result.status, "failed")
        self.assertIn(
            "final draft contains unresolved frozen-result placeholders",
            result.errors,
        )
        self.assertIn("final draft must retain exactly one claim branch", result.errors)

    def test_final_gate_accepts_resolved_single_branch(self) -> None:
        text = _minimal_chapter(
            "Resolved result. <!-- CLAIM_BRANCH:null_boundary -->",
            all_branches=False,
        )
        result = check_chapter_text(text, "", require_final=True)

        self.assertEqual(result.status, "ok")


def _minimal_chapter(body: str, *, all_branches: bool = True) -> str:
    headings = "\n\n".join(
        (
            "# Introduction",
            "# Study Context and Predecessor Evidence",
            "# Data and Provenance",
            "# Analytical Design",
            "# Results",
            "# Discussion",
            "# Limitations",
            "# Conclusion",
        )
    )
    branches = (
        "\n".join(f"<!-- CLAIM_BRANCH:{branch} -->" for branch in CLAIM_BRANCHES)
        if all_branches
        else ""
    )
    return f"{headings}\n\n{body}\n{branches}\n"
