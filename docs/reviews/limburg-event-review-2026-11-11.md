# Limburg event review — 11 November 2026

Internal research aid. Brian writes dissertation/article prose. This explanatory
review follows the completed, fixed-model evaluation; it is not a new
confirmatory mechanism experiment, target fitting or changed reference policy.

## Finding after review

The calendar-based reference update reduced average **flood-class agreement**.
The review identifies a major route: areas previously classified as flood become
classified as permanent water when the newer reference is supplied. Water versus
land agreement can remain stable or improve. Calling this a general deterioration
in water detection would therefore overstate the result.

This does not prove that P1 pixels contain permanent water. A two-date model can
interpret water-like conditions at both dates as permanent even when the water
is transient or part of an earlier/ongoing flood. The fixed label and the new
reference may describe different temporal baselines. That is an applied
information-quality limitation of the tested policy, not a reason to discard the
completed comparison or begin another model search.

## Evidence reviewed

- All **913** harmonized triplets on the original deduplicated common support;
  all three training seeds for each learned method and the fixed physical rule.
- Per-class P0-to-P1 transitions and VH/VV radar contrasts over the entire paired
  census. Their event totals reconstruct the original true-positive counts
  exactly. Dark-return diagnostics reuse the source-calibrated **VH < -21 dB**
  criterion; this threshold is not selected on the reviewed events.
- The nine original tile-IoU-extreme atlas cases and nine whole-event driver
  cases, with one case shared: **17 distinct external tiles visually inspected**.
  Driver selection asks how changing only a tile changes whole-activation IoU,
  averaged across seeds. It avoids letting a tiny high-contrast tile stand in
  for the whole event. These are diagnostic selections after results, not a
  representative validation sample.
- All 14 local acquisition-case score summaries; direct transitions for the
  **35** local inputs whose references actually changed. The other 132 inputs
  retain P1=P0. Local cases are one July 2021 flood episode.
- Pinned official CEMS activation metadata for all nine activations, with AOI
  names, descriptions and current sensor/product times. Two Ecuador government
  reports were downloaded, extracted and the relevant report page rendered and
  visually checked. Current CEMS product versions are context, not replacements
  for the released labels used in scoring.

## Detection and attribution are empirically different

Episode-balanced IoU, averaging source seeds within activation and using the
existing eight conservative episode blocks:

| Method | Flood P0 | Flood P1 | Water/land P0 | Water/land P1 |
| --- | ---: | ---: | ---: | ---: |
| Copernicus-FM | 0.396 | 0.274 | 0.519 | 0.541 |
| U-Net | 0.380 | 0.269 | 0.512 | 0.508 |
| Physical rule | 0.295 | 0.227 | 0.486 | 0.488 |

Water/land collapses permanent water and flood into one class using the existing
confusion matrices. It is an explanatory diagnostic, not a replacement endpoint.
The primary flood result remains reported. With only eight blocks and a
post-result diagnostic, small binary-water changes should not become a new
claim of general superiority.

Across all paired mapped pixels and seed runs, **74.3%** of Copernicus's gross
lost correct flood detections switch to permanent water; **89.0%** for U-Net and
**96.2%** for the physical rule. These are pooled transition shares, not
event-balanced estimates or independent pixel samples. The physical rule's
permanent-water switch is partly built into its explicit before/after logic.
All nine event-level transition tables remain available.

For the Copernicus pixels switching from correct flood to permanent water,
**23.6%** have a low VH return in P0 versus **78.5%** in P1. This directly
documents changed radar evidence at the affected pixels. Smooth soil, shadow,
vegetation and geometry can also affect return; this is not independent water
verification. Aggregate flood-area means can hide the localized changes.

## Event-by-event account

Numbers below are Copernicus three-seed means on the same paired support.
Water IoU includes permanent and flood. A class switch is a model behavior;
interpretations of the underlying landscape retain the qualifications shown.

| Activation / region | Flood IoU P0→P1 | Water IoU P0→P1 | Review interpretation |
| --- | --- | --- | --- |
| EMSR857, Mozambique | .681→.671 | .725→.734 | Strong local flood-to-permanent switches occur in already darkening lowlands, while other gains largely offset them at activation scale. The Bela Vista tile extreme overstates the activation-wide loss. Official CEMS context describes rains/flooding beginning in December, before the catalogue's January date. This does not date inundation at every pixel. |
| EMSR858, January Italy | .021→.006 | .680→.657 | Flood detection is poor with both references; only 10,041 reference flood pixels occur on the paired support. Narrow flood features, a 2–5-day listed radar/label discrepancy and differing CEMS source products make this an unresolved reference/timing case. No supported simple P1-already-wet explanation. |
| EMSR861, Spain/Portugal | .424→.360 | .519→.591 | The Benalup driver shows existing dark areas in P1 becoming permanent-water predictions. 86% of gross lost Copernicus flood detections switch to permanent water. CEMS describes storm effects from January 26 but lists an event time on January 28; this is a regional chronology warning, not proof of the exact local onset in Benalup. |
| EMSR864, Portugal | .591→.438 | .592→.614 | The Salvaterra de Magos driver shows part of the eventual mapped inundation already dark in the January 26 reference. About 77% of gross lost correct detections become permanent. Broader water recognition is preserved. Earlier water-like conditions are supported by imagery; local water history is not independently established. |
| EMSR865, Colombia | .403→.383 | .481→.490 | Existing dark pools explain selected dramatic tile examples, but **background rejection accounts for most Copernicus gross losses** across the activation; only 26% go to permanent. The whole-event driver still detects much of the new inundation. Do not force this event into a single already-wet mechanism. |
| EMSR866, France | .314→.194 | .362→.369 | The Cognac driver shows dark river-connected parcels in P1 and loss of the flood designation while retaining water. 63% of gross losses become permanent; other losses are background. Some CEMS labels use the same nominal Sentinel-1 observation as the tested event image, so this remains reference-map agreement. |
| EMSR868, Greece | .387→.062 | .533→.635 | A clear attribution failure: reference flood pixels called permanent rise from **15.1% to 78.7%**. The February 18 reference already resembles the February 19 inundation pattern. The official February 18 Evros Red Code gives regional high-water context, not pixel truth. The CEMS Feres source has the same nominal post-SAR observation time. |
| EMSR870, Ecuador | .499→.056 | .453→.473 | A strong existing-water candidate: February 19 P1 and March event imagery show similar dark spatial patterns; 86.8% of gross lost flood detections become permanent. Government reports document Babahoyo flooding on February 4, 11, 13 and 18, before the P1 image, whereas the catalogue event date is March 2. The regional chronology failure is independently corroborated; exact water coverage of every evaluated pixel is not. A >4-day label/SAR gap remains in the Babahoyo examples. |
| EMSR871, March Italy | .353→.424 | .365→.369 | The useful counterexample. P1 improves flood IoU primarily through reduced false flood classifications: precision rises .512→.667 while recall is .556→.540. The newer reference is brighter over much of the labeled flood footprint, and flood remains visibly distinct in the post image. No evidence here that recency itself guarantees the improvement. |

## What the official chronology adds

“Before the catalogue event date” is not verified “before local inundation.”
The clearest independently documented example is Babahoyo:

- Dataset event time: March 2; P1 acquisition: February 19.
- Ecuador SNGR SitRep 01, February 5, p3 documents river-overflow flooding in
  Babahoyo on February 4.
- SitRep 05, February 19, pp3–4 reports further local flooding on February 11,
  13 and 18. Its canton-level account cannot validate every raster pixel.

The source documents are retained at
`data/raw/limburg_chapter_event_context_v1/`; URLs and SHA256 records are in
`source-records.json` and `government-reports.json` there. Sources:
[SNGR report index](https://www.gestionderiesgos.gob.ec/sitrep-afectaciones-por-lluvias-2025-2026/),
[SNGR February 19 report](https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/02/SITREP-Nro.-05-Lluvias_Los-Rios-desde-el-01_02_2026-al-19_02_2026-1.pdf),
[CEMS January Iberian chronology](https://mapping.emergency.copernicus.eu/news/storm-kristin-and-flooding-in-central-portugal-and-andalusia-spain-emsr861/),
[Greek Civil Protection February 18 notice](https://civilprotection.gov.gr/deltia-tupou/anakoinosi-ypoyrgeioy-klimatikis-krisis-kai-politikis-prostasias-48),
[CEMS Evros report](https://mapping.emergency.copernicus.eu/news/flood-in-evros-river-basin-greece-emsr868/).

## Local receiving cases

Only the July 16 orbit-139 cases obtain a newer compatible same-platform scene:
June 28 P0 becomes July 10 P1. The original acquisition census and offsets are
retained. Venlo's proxy is nominally simultaneous with its July 16 event radar;
the German proxies are from July 18, about 53 hours later than those radar cases.

All three changed local cases have lower Copernicus flood IoU with P1. The loss
routes vary: Venlo includes both permanent-water and background switches;
Wassenberg's Copernicus losses are mostly background. They support reference
sensitivity, not a universal existing-water explanation. The 132 unchanged-input
records remain zero-change outcomes. Source-aware hydrography/trace exclusions
prevent calling mapped non-flood independently confirmed dry land.

## Interpretation for this chapter

Supported: the tested reference policy changes flood attribution substantially,
often without a comparable deterioration in broader water recognition. Localized
water-like conditions in P1 explain many of the affected predictions. Independent
records show that a pre-catalogue-date image can already fall inside a regional
flooding period. Model differences remain secondary and context dependent.

Unresolved: the exact water state/cause at every P1 pixel, how much of each
change is transient water versus seasonal/managed water, and simultaneous ground
truth at mismatched label times. No new data request or another full model run
is required to report those limitations honestly.

Practical implication: document the reference's observed hydrological condition
and its temporal relationship to the mapping target. Calendar recency alone is
an insufficient quality rule. This study has not yet validated an automatic
replacement-selection rule or operational warning benefit.

## Reproduction and audit

`250_review_chapter_events.py` computes the full paired radar/transition census;
`251_review_event_driver_maps.py` creates the additional driver atlas;
`252_summarize_event_review.py` checks transition conservation and separates
water/flood agreement, including local changed cases; `253_plot_event_review.py`
generates the diagnostic plots. Outputs and completion hashes are in
`results/limburg_chapter_sized_v1/event_review/`.

No source weights, images, target labels, acquisition policy, fitted threshold
or primary score was changed. The original maximum-tile-change atlas remains
preserved. Explanatory diagnostics are labeled as post-result work. Tests protect
the distinction between water detection and flood attribution, empty targets,
and the gain/loss accounting. These diagnostics do not enlarge independent n.
