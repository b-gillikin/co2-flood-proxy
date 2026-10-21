# OlmoEarth and Galileo: token-mask recovery

Status: diagnosis reproduced; isolated full-census recovery running. This is an
input-correctness repair, not a new scientific comparison or empirical finding.

## Diagnosis

All 1,074 saved OlmoEarth errors reported an empty-token assertion; all 2,696
saved Galileo errors reported indexing an empty token sequence. Representative
real inputs reproduce both exceptions. Both published implementations explicitly
assume spatial masks constant within token blocks, then read masks at the
block's upper-left pixel. The original adapter supplied pixel-level masks.
Thin observed slivers can therefore have valid pixels but zero visible tokens.
Mixed blocks also affect successful embeddings and their reported support.

Representative saved error tiles:

- OlmoEarth: `monthly_6354a09d56be695723a3`, bounds
  `(278400, 5625600, 288000, 5635200)`. Of 225 patch origins, 139 had some
  observations in every frame; 55 of those had mixed token blocks and three
  had no visible tokens. The original tile stopped after 22 receipts, leaving
  203 origins without receipts.
- Galileo: `recent_91231ee5605d94f4c07c`, bounds
  `(288000, 5635200, 297600, 5644800)`. Of 900 origins, 314 had some
  observations in every frame; 313 had mixed token blocks and three had no
  visible tokens. There were 803 origins without receipts.

These are diagnostic examples, not estimates of archive-wide prevalence.
Saved local tracebacks and counts: `logs/eo-mask-review/`.

## Repair

`src/eo_token_masks.py` constructs block-consistent masks: a token is observed
only when all pixels it consumes are observed (4×4 for this OlmoEarth adapter,
8×8 for Galileo). This conservative support convention avoids representing
zero-filled missing pixels as observations. It can reduce usable area; it is
not a minimum catchment-coverage cutoff. The existing complete-frame sequence
rule is retained. No new data, model, event sample or research question is added.

Script 110 revisits every available context/tile/patch and records unsupported
sequences explicitly. It catches unexpected failures per patch, so they cannot
skip later patch origins in the same tile. Saved masks reflect actual model
support, and the existing aggregation retains the full catchment denominator.
Coverage still needs reviewing after completion; these models' token scales
and input modalities differ, so their supported populations cannot be assumed
identical.

The existing runner/adapters and active Presto source fingerprints are unchanged.
Old outputs remain intact. Recovery has its own code fingerprint and directory:
`data/processed/limburg_eo_token_consistent_sequences/`.

Verified OlmoEarth MPS outputs may be hard-linked into the new run only when
weights, checkpoint, packages, seed and source hashes match, frame identities
match, the saved pixel masks exactly equal the corrected masks, and file hashes
and finite embeddings verify. Changed masks require recalculation. Galileo's
old CPU embeddings are not reused in the new MPS run. New receipts identify
reused sources; bytes and their checksums are preserved.

## Execution and verification

Script 111 serializes recovery on MPS: OlmoEarth, then Galileo, then each model's
exact-area aggregation. Separate aggregation destinations end in
`per_model/<model>/token_consistent`; these do not silently replace the previous
comparison inputs. Integrate only after examining census completion, failures,
coverage and provenance. This is verification of the repaired inputs, not a
scientific pass/fail gate for the chapter.

Both final adapters passed real 12-frame monthly smoke tests on MPS: finite
embeddings and exact repeatability. Thirteen focused tests passed, including
thin slivers, temporal missingness, no invented observations and preservation
of fully observed blocks. Lint passes. Full-census completion is still pending.

Live recovery: `logs/eo-token-recovery/progress.json` and model logs alongside it.
The old suspended Galileo process was terminated after verifying its command;
its files were retained. Presto continues unchanged under the original queue.
The original queue does not track this recovery: consult both progress files.
