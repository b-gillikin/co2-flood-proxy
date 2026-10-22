"""Stable extraction population identity, independent of result publication code."""

import json
from pathlib import Path

from src.eo_inputs import sha256

ROOT = Path(__file__).resolve().parents[1]


def input_population(archive, preparation, context=None, *, root=ROOT):
    """Bind data and logical locations; host absolute paths are not identities.

    External archives use explicit role resolvers at validation, outside this
    fingerprint. Project-contained ledgers remain portable on ordinary restore.
    """
    root = Path(root).resolve()
    archive, preparation = Path(archive).resolve(), Path(preparation).resolve()
    contexts = json.loads((preparation / "contexts.json").read_text())
    ids = [c["context_id"] for c in contexts]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate context IDs")
    if context is not None and context not in ids:
        raise ValueError("Unknown context")

    def location(path, role):
        try:
            return {"base": "project", "path": str(path.relative_to(root))}
        except ValueError:
            return {"base": role, "path": path.name}

    return {
        "schema_version": 2,
        "jobs_location": location(archive / "jobs.json", "archive"),
        "contexts_location": location(preparation / "contexts.json", "preparation"),
        "jobs_sha256": sha256(archive / "jobs.json"),
        "contexts_sha256": sha256(preparation / "contexts.json"),
        "selection": "single_context" if context else "full_census",
        "expected_context_ids": [context] if context else ids,
    }
