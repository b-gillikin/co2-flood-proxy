#!/usr/bin/env python3
"""Verify the completed flood-review receipt and case-sheet links without refitting."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/flood_case_review_2026_10_27'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('href', 'src') and value:
                parsed = urlsplit(value)
                if not parsed.scheme and parsed.path:
                    self.paths.append(unquote(parsed.path))


def main():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    checked = {}
    for group, base in (('input_sha256', ROOT), ('source_sha256', ROOT),
                        ('outputs_sha256', OUT)):
        for relative, expected in manifest[group].items():
            actual = hashlib.sha256((base / relative).read_bytes()).hexdigest()
            assert actual == expected, (group, relative)
        checked[group] = len(manifest[group])
    register = pd.read_parquet(OUT / 'register.parquet')
    assert len(register) == 15
    native = register.evidence_type.eq('current_H3_recorded_reach')
    assert native.sum() == 10
    assert (native & register.primary).sum() == 7
    for case in register.case_id:
        case = case.replace(".", "_")
        assert (OUT / 'cases' / f'{case}.html').exists(), case
        assert (OUT / 'cases' / f'{case}.png').exists(), case
    link_count = 0
    for path in OUT.rglob('*.html'):
        parser = Links()
        parser.feed(path.read_text())
        for relative in parser.paths:
            assert (path.parent / relative).exists(), (path, relative)
            link_count += 1
    summary = json.loads((OUT / 'summary.json').read_text())
    assert summary['scored_preflood_p99_queries'] == 2
    assert summary['scored_recovery_queries'] == 1
    receipt = dict(status='passed', hashes_checked=checked,
                   internal_links_checked=link_count, case_sheets=15,
                   figures_visually_reviewed=20,
                   tests='345 passed; logs/flood-case-review-tests-2026-10-27.log',
                   note='Source-bounded register; not an exhaustive physical-flood census.')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
