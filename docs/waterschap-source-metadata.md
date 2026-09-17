# Waterschap Limburg Discharge Source Metadata

Status: provider follow-up received 2026-09-07 and reviewed 2026-09-14. This
note interprets source semantics and station QA without calculating thresholds,
episodes, peaks or signal contrasts.

## Source contract

Waterschap Limburg states that each value is the mean of the preceding 15
minutes. A blank means that no data are available because the measurement is
unreliable or the station is not operational; the delivery does not distinguish
those causes. No validation flags are available. The supplied series are
semi-finished, not fully validated and may differ from reality. The provider
strongly advises against forwarding them to third parties.

Units are documented as m3/s and no station relocation occurred during the
requested period. Two source semantics remain unresolved:

- whether the header `GMT+1` means a fixed UTC+1 offset or Dutch civil time
  with daylight-saving transitions; and
- whether zero is always a physical or controlled zero rather than a sentinel.

Consequently `sampling_semantics_verified` and `units_verified` can be true,
but `timezone_verified`, `zero_sentinel_verified` and
`rating_curve_verified` remain false. A rating-curve sheet being present does
not establish that every reported value is within its applicable domain.

## July 2021 source assessment

| series | instrument evidence | discharge implication |
| --- | --- | --- |
| 11.Q.32 Eyserbeek Eys | operational | candidate only after checking the event against the rating domain |
| 6.Q.18 Brommelen | no operational problem reported | candidate only after range and curve checks |
| 6.Q.24 Millen | no operational problem reported | split-branch representativeness remains unresolved |
| 6.Q.22 Munstergeleen | no operational problem reported | mill control and summer vegetation make the rating relation uncertain |
| 10.Q.29 Cottessen | water-level sensor continued | discharge exceeded the 27.5 m3/s range and was disturbed by inundation and deposits; exclude affected event discharge |
| 10.Q.30 Hommerich | stage and discharge failed on 14 July | exclude the failed/disturbed event interval; do not infer its exact onset from this series |
| 13.Q.34 Azijnfabriek | Gulp locations reported operational | curve documentation reports poor accuracy and calibration only to about 3 m3/s |
| 12.Q.31 Selzerbeek Partij | 14 July wave out of range; station failed on 15 July | exclude the out-of-range and failed event interval |
| 6.Q.25 Nieuwstadt | no operational problem reported | candidate only after range and split-system checks |
| 15.Q.41 Mesch | Voer locations reported operational | candidate only after range and curve checks |
| 18.Q.45 Rimburg | sensor reportedly operational | observed stage of 86.427 m NAP exceeded the documented 86.027 m rating-domain limit; censor the peak discharge |
| 6.Q.27 Oud-Roosteren | stage and electrical systems operational | summer discharge is a composite estimate that omits flood-wave travel time; exclude it as direct high-flow evidence |
| 12.Q.46 Selzerbeek Molentak | operational | automatic weir closed the branch; exclude from the natural-tributary cohort and do not interpret zeros as natural no-flow without clarification |
| 10.Q.36 Meerssen | stage worked initially; discharge measurement failed on 14 July | gravel deposits produced implausibly low discharge; no measurements are documented until 15 July 2022 |

## Methodological consequences

Raw availability and analytical usability are separate. The availability audit
continues to count populated cells exactly as delivered. Its source-QA output
now records why those cells may remain unusable.

The future hourly ingest must:

1. retain the complete source grid and leave blanks missing;
2. interpret values as trailing 15-minute means, with an explicitly verified
   timezone conversion before aggregation;
3. aggregate an hour only from four complete, admissible quarter-hours;
4. apply rating-curve validity periods and domains before event detection;
5. set documented failures, range exceedances and structurally unsuitable
   series to missing rather than interpolate or reconstruct them;
6. keep censored July 2021 events descriptive and exclude them from exact-onset
   contrasts; and
7. exclude controlled branches and composite estimates from the primary
   natural-tributary cohort.

The metadata follow-up narrows the unresolved work but does not open the
regional gate. Fixed timezone/DST semantics, zero semantics, numerical
coordinates, natural/managed classification, a defensible cohort of sufficient
watercourses and supervisor approval of the numerical floors are still needed.

## Preserved evidence

The native email, station-status DOCX, 14 rating-curve PDFs and a checksum
receipt are preserved under
`data/raw/external_deliveries/waterschap_limburg/2026-09-07/`. The original
quarter-hour CSV/XLSX delivery remains unchanged under the 2026-08-19 folder.
