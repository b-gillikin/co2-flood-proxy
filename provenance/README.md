# Reviewed source compatibility

`source-snapshots/*.py.txt` holds exact historical source bytes referenced by
existing corrected EO run manifests. Filenames are their SHA-256 digests; these
are audit artifacts, not executable entry points or maintained code copies.

`config/limburg_eo_source_compatibility.json` records two explicitly reviewed
metadata-only transitions, binding each original digest and snapshot to the
exact replacement digest. It does not accept unknown revisions or changed
numerical encoder dependencies. The two-frame real-imagery comparison retained
bit-identical embeddings, validity masks and acquisition-day arrays.

Future extraction fingerprints `src/eo_population.py`, independently of
publication/validation code. Historical manifests and embeddings stay unchanged.
