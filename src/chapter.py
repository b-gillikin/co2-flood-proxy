"""Structural checks for the evidence-bounded chapter draft."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_HEADINGS = (
    "# Introduction",
    "# Study Context and Predecessor Evidence",
    "# Data and Provenance",
    "# Analytical Design",
    "# Results",
    "# Discussion",
    "# Limitations",
    "# Conclusion",
)
CLAIM_BRANCHES = (
    "supported_site_level",
    "site_specific",
    "coverage_inconclusive",
    "null_boundary",
)
FORBIDDEN_CLAIMS = (
    "groundwater causes the co2 signal",
    "the model predicts floods",
    "transfer is successful",
    "positive 10-day signal",
)

PLACEHOLDER_RE = re.compile(r"\{\{FROZEN:([a-z0-9_.-]+)\}\}")
CITATION_RE = re.compile(r"(?<![\w])@([A-Za-z][A-Za-z0-9:_-]*)")
BIB_KEY_RE = re.compile(r"^@\w+\{([^,]+),", flags=re.MULTILINE)
CLAIM_BRANCH_RE = re.compile(r"<!--\s*CLAIM_BRANCH:([a-z_]+)\s*-->")


@dataclass(frozen=True)
class ChapterCheck:
    """Machine-readable structural status for a chapter draft."""

    status: str
    require_final: bool
    headings: list[str]
    missing_headings: list[str]
    placeholders: list[str]
    citations: list[str]
    missing_citations: list[str]
    claim_branches: list[str]
    forbidden_claims: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def bibliography_keys(text: str) -> set[str]:
    """Return citation keys declared by a BibTeX bibliography."""
    return {key.strip() for key in BIB_KEY_RE.findall(text)}


def check_chapter_text(
    text: str,
    bibliography_text: str,
    *,
    require_final: bool = False,
) -> ChapterCheck:
    """Check chapter structure, citations, placeholders, and claim branches."""
    headings = [line.strip() for line in text.splitlines() if line.startswith("#")]
    missing_headings = [heading for heading in REQUIRED_HEADINGS if heading not in headings]
    placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
    citations = sorted(set(CITATION_RE.findall(text)))
    missing_citations = sorted(set(citations) - bibliography_keys(bibliography_text))
    claim_branches = CLAIM_BRANCH_RE.findall(text)
    forbidden_claims = [claim for claim in FORBIDDEN_CLAIMS if claim in text.lower()]

    errors: list[str] = []
    if missing_headings:
        errors.append("missing required chapter headings")
    if missing_citations:
        errors.append("citation keys are absent from the bibliography")
    if not require_final and sorted(claim_branches) != sorted(CLAIM_BRANCHES):
        errors.append("working draft must contain each prespecified claim branch exactly once")
    if forbidden_claims:
        errors.append("draft contains forbidden overclaim or stale-result language")
    if not placeholders and not require_final:
        errors.append("working draft must expose frozen-result placeholders")
    if require_final:
        if placeholders:
            errors.append("final draft contains unresolved frozen-result placeholders")
        if len(claim_branches) != 1 or claim_branches[0] not in CLAIM_BRANCHES:
            errors.append("final draft must retain exactly one claim branch")

    return ChapterCheck(
        status="ok" if not errors else "failed",
        require_final=require_final,
        headings=headings,
        missing_headings=missing_headings,
        placeholders=placeholders,
        citations=citations,
        missing_citations=missing_citations,
        claim_branches=claim_branches,
        forbidden_claims=forbidden_claims,
        errors=errors,
    )


def check_chapter_files(
    chapter_path: Path,
    bibliography_path: Path,
    *,
    require_final: bool = False,
) -> ChapterCheck:
    """Load and check a chapter and its bibliography."""
    return check_chapter_text(
        chapter_path.read_text(encoding="utf-8"),
        bibliography_path.read_text(encoding="utf-8"),
        require_final=require_final,
    )
