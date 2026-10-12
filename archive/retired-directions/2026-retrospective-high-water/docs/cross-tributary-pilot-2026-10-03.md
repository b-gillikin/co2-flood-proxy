# Cross-tributary event-footprint pilot

Status: internal exploratory audit, 2026-10-03. This is a response to the
first-fit result and Brian's renewed interest in relationships among high-water
events across tributaries. It is not a replacement protocol or dissertation
prose. The existing case-crossover analysis and its limitations remain recorded.

## Scientific direction to test

Ask how the observed high-water footprint and onset timing vary across the
regional tributary network during shared weather episodes. Start with the six
Waterschap watercourses already in the reviewed cohort. Examine which streams
cross their own valid, era-specific high-water thresholds, the order and spread
of those crossings, and whether the spatial rainfall pattern and antecedent
flow state help describe variation among episodes. Do not infer forecast skill,
physical flood-wave propagation between separate basins, or a regional
distance-decay curve from these observations.

Define candidate weather episodes from rainfall independently of discharge
before estimating a probability that a stream responds; grouping on high-water
onsets alone would select on the outcome. Compare at least one shorter and one
longer event-separation rule and preserve the original 72-hour onset groups as
descriptive historical output. This is a bounded redesign, not a new data
request or a commitment to another model family.

## Existing Dutch event-table diagnostic

Read `results/event_study/real_data_v1/events.csv`, retain rows with
`onset_pair_admissible=True`, group by its existing `storm_id`, and count
distinct `watercourse` values per group. The 240 groups contain:

| Distinct watercourses with an onset | Groups |
|---:|---:|
| 1 | 83 |
| 2 | 35 |
| 3 | 30 |
| 4 | 31 |
| 5 | 21 |
| 6 | 40 |

Thus 157 groups have at least two watercourses. These are **onset-linked
groups**, not independently defined rainfall storms or response probabilities.
Single linkage permits a group to span longer than its 72-hour link rule; the
multi-watercourse onset spread has a median of about 5 hours but a long tail.
The counts show variation worth examining, not a chapter finding.

## German station decision

The four LANUK 15-minute discharge exports delivered 2026-09-23 are much more
usable for this purpose than the older irregular public archive. Each has
560,929 ordered quarter-hour timestamps from 2010-01-01 00:00 to 2025-12-31
00:00 in source time, no duplicated or off-grid timestamp, and complete July
2021 rows. Herzogenrath 1 and Randerath have numeric values throughout;
Herzogenrath 2 and Honsdorf each have 12 blanks. Header semantics identify
trailing 15-minute means, and Jens's covering email states UTC+1 for all
delivered data. This matches the Waterschap sampling interval and fixed UTC+1
offset sufficiently for a provisional time crosswalk.

The four gauges are **not four independent tributaries**. Herzogenrath 1 and
Randerath both measure the Wurm at different contributing areas (93.37 and
305.16 km²); Herzogenrath 2 is on Broicher Bach (41.39 km²), and Honsdorf is
on Beeckfließ (56.55 km²). Confirm network topology and management status
before interpreting them as distinct regional responses. A German extension
could use a single Wurm representative plus the other branches, or explicitly
model nested stations as separate reaches.

Jens's outstanding answers concern reconstructed/filled periods and the
provisional discharge/rating history, particularly Herzogenrath 1 and
Randerath. These affect high-water onset validity, not basic calendar overlap.
The Honsdorf replacement stage file provides an independent trajectory but
does not itself certify discharge, historical datum stability or threshold
equivalence. Keep German data as a **parallel candidate extension** while the
Dutch analysis proceeds. Do not silently merge provisional German event labels
into the Dutch main cohort. Reassess whether an accepted subset adds a useful
cross-border comparison after provider answers and station-level event QA.

## Immediate next pass

1. Audit rainfall-defined episode candidates and their separation sensitivity
   using the held RADOLAN series; preserve their explicit time windows.
2. Cross-tabulate valid Dutch p99 onsets and near-threshold states by episode,
   season, site and rainfall footprint. Inspect multi-site and single-site
   examples, including provider-flagged high water.
3. Check how much of the apparent onset order comes from threshold placement,
   nested catchments, sampling conventions or uncertain ratings. State a
   narrow contribution only after this diagnostic.
4. Separately audit LANUK rating validity, reconstructed periods and topology
   when Jens replies. Include German sites only where the same event definition
   and defensible within-site high-water label can be applied; otherwise
   report them as a separate descriptive comparison.

No gate or minimum number of German sites is imposed. Missing source answers
limit the affected German claims; they do not stop the Dutch network study.
