# Honsdorf replacement stage export: receipt and first audit

Status: internal source audit, 2026-10-01. This is not a new chapter result or
an addition to the six-gauge Waterschap cohort.

Jens Hammersen's 2026-10-01 message says the prior Honsdorf stage upload was
erroneous and supplies the missing 15-minute file. His 2026-10-13 follow-up
confirms that gaps in the delivered station series were not reconstructed from
neighbouring gauges: redundant water-level sensors at each station allowed
priority-1 sensor gaps to be closed. It also identifies post-July-2021
discharge as provisional, with the greatest uncertainty above warning levels
2 and 3 at Randerath and Herzogenrath. The message and CSV are preserved
unchanged under `data/raw/external_deliveries/lanuk_nrw/2026-10-01/honsdorf/`,
with SHA-256 checksums in `receipt.tsv`. The BSCW link in the email expires
2026-12-24; the preserved copy does not depend on that link.

| Check | Replacement stage export |
| --- | --- |
| Station, stream and parameter | Honsdorf, Beeckfließ, water level in cm |
| Header semantics | 15-minute means, timestamp at the right end of each interval |
| Span and rows | 2010-10-01 00:00 to 2025-12-31 00:00; 534,721 dated rows |
| Timestamp grid | Exactly 15 minutes between all consecutive rows; no duplicate timestamps |
| Numeric values | 534,709; range 8.056–132.8 cm; no zero or negative values |
| Missing cells | 12 blanks, all on 2019-03-25–26, in two runs of 4 and 8 rows |
| July 2021 | All 2,976 July timestamps have numeric values; maximum 132.8 cm at 2021-07-14 13:15 in source time |

The previously delivered file has only 36 isolated readings from 2012–2025;
it remains in the 2026-09-23 source folder as evidence of the original upload.
The replacement and already held Honsdorf 15-minute discharge export have
the same 12 blank timestamps in March 2019 and their July 2021 maxima share
the source timestamp 2021-07-14 13:15 (discharge 4.537 m³/s). This confirms a
usable continuous local stage trajectory and a direct time-index crosswalk;
it does not validate peak discharge or the stage–discharge relation.

The header gives a **current** gauge zero of 54.368 m NHN2016. It does not
establish historical datum or sensor stability. Jens's 2026-09-23 covering
email states that the timezone for all delivered data is UTC+1. The continuous
quarter-hour grid through clock-change dates is consistent with a fixed
offset; use UTC+1 for provisional cross-provider alignment while preserving
the source timestamps. Do not convert historical stage to absolute elevation
on the basis of the current gauge zero alone.

Honsdorf is on Beeckfließ. It remains conditional evidence for a separately
labelled German extension, not a seventh core tributary or a Wurm gauge. The
provider clarification and its implications are recorded in
`lanuk-provider-clarification-2026-10-13.md`. No main-analysis event, exposure
or model table changes from this file.
