# Limburg — high-water assessment with alternative discharge information

**Current direction — approved 14 November 2026:** paired observed versus
GEOGLOWS discharge inputs on the same NL/DE rivers, with conventional assessment,
simple calibration and task-specific AI corrections. The six audit corrections
are implemented. The seven-target Stages 1–2 are prepared and verified; full
comparisons are not launched. No new EO extraction is required.

- [Current one-pager](docs/chapter-one-pager.md)
- [Research design and execution guide](docs/limburg-geoglows-stages12-protocol-v2-2026-11-14.md)
- [Active configuration](config/limburg_geoglows_stages12_v2.json)
- [Reviewed reach mappings](config/limburg_geoglows_reaches_v1.json)
- [Handoff](docs/HANDOFF.md)

**Below: preserved earlier mapping-study documentation.** It describes completed
or superseded work; the active continuation is the design linked above.

---

# Limburg: pre-flood information and satellite-AI flood mapping

**Active scope — accepted by Brian, 10 November 2026.**

> How do satellite AI and conventional methods compare in mapping new flood
> events, and how does the choice of pre-flood reference affect their performance?

One empirical study compares Copernicus-FM's frozen paired-SAR encoder with a
trained spatial head, a same-input standard U-Net, and a competent physical SAR
change/water method. Each uses the delivered reference (P0) and an updated,
compatible pre-flood reference chosen without test labels (P1). The event image
and trained weights stay fixed. There is no target fine-tuning experiment.

- [Living one-pager](docs/chapter-one-pager.md)
- [Agreed scope and dissertation-sizing rationale](docs/limburg-chapter-sized-study-2026-11-10.md)
- [Current handoff and next work](docs/HANDOFF.md)
- [Data held and still needed](docs/data-needs.md)
- [Canonical active-study pointer](config/limburg_current_study.json)
- [Latest scientific/data/compute audit](docs/reviews/limburg-chapter-scope-audit-2026-11-10.md)
- [Scoped compute policy](config/limburg_chapter_sized_compute_v1.json)
- [Future ideas and superseded planning archive](archive/future-ideas/2026-11-10-broad-spatial-programme/README.md)

The candidate external cohort is the full eligible census of nine GEOID heldout
activations (1,301 released tiles before overlap/compatibility checks), with the
existing Dutch/German radar cases as a contextual receiving case. Gauge records
support timing and measurement interpretation; they are not flood-pixel labels.

**Status:** preparation, not a new running queue. The external SAR/reference-mask
package is pinned at 9.068 GiB but not downloaded by this scope decision; updated
P1 imagery remains to inventory. Existing compatible source fits should be reused.
No new accuracy result has been produced for this comparison.

Completed discharge/analogue and spatial studies, raw data, source code, literature,
weights and recovery records remain preserved. Their results are not erased or
relabelled as prospective findings. Start with the [completed spatial findings](docs/limburg-consolidated-findings-2026-11-10.md)
and [completion/recovery audit](docs/reviews/limburg-completion-recovery-audit-2026-11-10.md).
Older dated plans and scripts reproduce those studies; they do not define current
completion requirements. Brian writes dissertation prose and sends emails.
