# Limburg: flood-focused case review

Completed 2026-10-27. Internal evidence and interpretation aid for Brian, not dissertation prose. This extends the completed analogue analysis through case review; it does not fit another model, select new hyperparameters or establish operational warning skill.

## What was done

1. Assembled every supplied-series H3 episode and bounded official documentary additions, retaining uncertain dates and unconfirmed impacts.
2. Traced cases through native measurements, source problems, p99 episodes, H1 assessments, exposure support and exact future-response eligibility. Reviewed whole episodes alongside the original 72-hour evaluation window.
3. Reconstructed saved donor pools and selections for the recorded conventional, raw-Q, TTM, AlphaEarth and EO settings. Recomputed continuous mean-trajectory errors from the saved donor IDs.
4. Distinguished missing precedent, retrieval misses and translation/averaging problems, without using withheld responses to improve retrieval.
5. Produced 15 linked case sheets and native timelines, five model-response atlases, saved-analogue browsers, machine-readable tables and a hash manifest.

Open the [case index](../results/flood_case_review_2026_10_27/index.html). Reproduce using `.venv-foundation/bin/python scripts/143_review_flood_cases.py`; verify the completed bundle using `.venv-foundation/bin/python scripts/144_audit_flood_case_review.py`. The runner uses the existing local archives; source paths are in `config/limburg_flood_review_evidence.json`.

## Population and evidence boundaries

There are **15 register rows, not 15 independent floods**. Ten rows are recorded reaches of current Dutch H3 values in supplied series; seven belong to the core gauges and cover four regional episodes. Three are ancillary/composite-series cases. Five documentary rows add context and German coverage, including overlapping July 2021 cases. Applying current thresholds retrospectively does not reconstruct the warning issued at the time or independently establish inundation.

| Register cases | Evidence and treatment |
| --- | --- |
| Worm/Hambos, July 2014 | Core H3 reach; pre-flood p99 query has usable continuous-response scores. |
| Worm/Hambos, April 2018 | Core H3 reach; assessable in the existing H1 study, but not a scoreable exact-Q p99 query under its history requirements. |
| Eyserbeek, Geleenbeek, Voer and Worm/Hambos, July 2021 | Four core H3 cases within one regional disaster; retain measurement/history exclusions and shared-storm dependence. |
| Voer, May 2024 | Core H3 reach; one pre-flood query and one later recovery query, not two independent floods. |
| Hommerich and Selzerbeek/Partij, July 2021 | Two ancillary H3 reaches, kept distinct from the core cohort. |
| Oud Roosteren composite series, October 2023 | Ancillary H3 reach with the source-series warning retained; not promoted into a core validated flood. |
| Cottessen, July 2021 | Provider documents flume/range and inundation context; disturbed discharge makes absence of recorded H3 inconclusive. Not independent mapped inundation evidence. |
| Herzogenrath and Randerath, July 2021 | Official local impact documentation and German stage context. Provisional discharge is not used as an exact-Q benchmark. No Dutch H3 label is assigned to German gauges. |
| Herzogenrath, 2018 | Official impact account identifies the year only. Nine p99 candidates remain candidates, not nine confirmed floods or an assumed match to April 30. |
| Herzogenrath, early May 2024 | Official high-water statement, without independently established inundation or exact event date. Five May candidates remain unresolved. |

No qualifying Gulp case in this source-bounded register means insufficient qualifying evidence here, not proof that flooding never occurred. German cases remain valuable documentary/stage context even when they cannot enter an exact-Q score.

Only **three date-resolved linked p99 queries** have saved continuous-response scores: Worm 2014, Voer May 17 2024, and Voer May 20 2024. The last is recovery after the first H3 reach. Thus only **two are pre-flood queries**. These few positive cases support detailed diagnosis, not a new population-level superiority claim.

## Findings: where the chain breaks

### 1. Archive support is part of the result

In the existing main/pooled all-river H1-to-H3 Q-history analysis, a prior observed H3-positive case was eligible for six of seven positive cases. With five donors, TTM selected a positive precedent for only one case: five had positive precedents available but none selected, and one had no observed positive precedent available. With ten donors it selected positives for three cases. Raw matching selected positives for two of seven at five donors and three at ten.

Positive-class mean squared loss remained poor: raw/TTM were 0.897/0.949 at five donors and 0.894/0.919 at ten. Donor reach shares are not calibrated flood probabilities. These counts concern the existing H1 task and modern local H3 labels; they are not an inventory of all historical physical floods.

Voer May 17 illustrates the loss of precedent through data requirements. The H1 archive has six earlier labelled H3-positive cases. The different exact-Q p99 archive retains one (Worm 2014), and the all-ten EO intersection retains none. These are different task/pool definitions, not a controlled causal ablation. Prithvi's own model-available snapshot pool retains the one positive; its five-donor TTM combination still does not select it. The other nine model-available snapshot pools have no confirmed positive precedent. Unknown German outcomes remain unknown rather than negatives.

### 2. Retrieval can miss useful response information

For Voer May 17, the broad exact-Q raw and TTM selections both miss the one labelled H3-positive precedent at five donors. Looking at withheld outcomes, the closest single eligible trajectory is Geleenbeek on January 12 2011: normalized RMSE 1.030, versus 1.680 for the selected raw mean and 1.655 for the selected TTM mean.

This **post-outcome single-trajectory oracle is diagnostic only**. It is not an equal-five-donor comparator, an achievable forecast or a tuning target. Its value is to show that archive absence alone does not explain the error. A labelled H3 event need not be the closest trajectory, and a closer trajectory need not carry an H3 label. The all-ten EO archive cannot use that 2011 example because required imagery support is absent.

### 3. Severe responses are poorly represented, and averaging can further weaken them

Voer May 17's subsequent peak is 6.906 times its p99 normalization. Across the ten own-model-available snapshot EO+TTM selections, the largest selected donor peak is only about 1.39–3.21 times p99, and the mean-trajectory peak about 1.07–1.36. Thus this miss is not merely averaging: every selected member understates the observed extreme.

Worm 2014 shows a different failure. Its observed peak is 3.682 times p99 and selected raw/TTM donors include a member peaking at 4.592. Yet their mean trajectories peak at only 1.496 and 1.941. Mean individual donor peaks are 2.063 and 2.494; averaging across different peak times loses a further 0.567 and 0.553. Member dilution and timing differences matter even when a severe member exists. Displaying members and severity support is therefore worth preserving; this review does not establish that using an envelope would yield calibrated predictions or acceptable false alarms.

### 4. The assessment anchor can miss the relevant transition

Eyserbeek July 2021 first reaches H3 about **90 hours after its linked p99 onset**, outside the original 72-hour response target. Its native H1-to-H3 interval is about 18.75 hours. The original p99 assessment is not a test of that later transition. Whole-episode timelines reveal this mismatch without changing the completed analysis's target after seeing outcomes.

The Voer May 20 query describes recovery, and cannot serve as an earlier precedent for May 17; both are also in the same storm group. Neither is evidence of two successful flood predictions.

## Sources and measurement correction

Primary documentary additions were saved with URL/checksum receipts: [Herzogenrath Wurmpromenade history](https://www.herzogenrath.de/freizeit-tourismus/im-gruenen/wurmpromenade/), [Herzogenrath May 2024 statement](https://www.herzogenrath.de/aktuelles/2024/mai/erster-spatenstich-wurmpromenade-soll-herzogenraths-neue-flaniermeile-werden/), [Heinsberg climate concept, p. 68](https://www.heinsberg.de/stadt-heinsberg/rathaus/klimaschutz/integriertes-klimaschutzkonzept/klimaschutzkonzept-endbericht-stadt-heinsberg-ratsbeschluss-15-12-21.pdf?cid=hxv), and [LANUK July 15 2021 situation report, p. 2](https://www.lanuk.nrw.de/fileadmin/lanuv/wasser/lageberichte/20210715_Hydrol_Lagebericht_4.pdf). German reporting levels are not interchangeable with Dutch H1–H3. The configuration also references the held Waterschap measurement report and LANUK provider email.

An earlier narrative statement that hourly averaging hid Voer's 2024 H3 crossing was incorrect and has been corrected. Native peak 5.432 and hourly peak 5.24525 m³/s both exceed H3=4.8 m³/s. Saved numerical outcomes were already correct; no result was refitted.

## Validation and interpretation

The full suite passes **345 tests**. The read-only audit verifies 64 input hashes, 32 source hashes and 50 output hashes, all 15 case sheets/timelines and 52 internal links. Twenty figures were visually reviewed. Continuous selected-curve RMSE reconstruction agrees with saved scores; donor chronology/storm/quality checks report no violations. Bootstrap estimates and earlier population comparisons are unchanged.

The case review provides concrete explanations beyond average ranking: restricted archives, missed precedents, insufficient extreme members, trajectory averaging and assessment timing all contribute. It supplies no new evidence that EO or TTM can reliably forecast flood escalation. A potentially useful operational product would expose those support limits and individual precedents; operator benefit would still require separate testing. The completed evidence is ready for Brian's interpretation and writing, without another encoder extraction or automatic extension of scope.
