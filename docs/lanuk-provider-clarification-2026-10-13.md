# LANUK clarification on sensor continuity and provisional high flows

Status: internal source audit, 2026-10-13. This records provider evidence and
does not convert provisional German discharge into validated peak flow.

Jens Hammersen re-examined the four delivered LANUK time series and clarified
that their gaps were **not** reconstructed from neighbouring stations. Each
station has at least one redundant water-level sensor, allowing gaps in its
priority-1 sensor to be closed from another sensor at the same station. The
delivered continuity therefore should not be described as neighbour-gauge
reconstruction. The available correspondence does not provide row-level
sensor-selection flags, so individual substitutions cannot be identified.

LANUK also states that the period following the July 2021 flood remains
provisional. Mean and low water levels are supported by discharge
measurements, while the greatest uncertainty is expected above warning levels
2 and 3 at Randerath and Herzogenrath. At Randerath, inundation of the
foreland above reporting level 3 adds uncertainty to high-flow estimation.
The supplied `Kurvengültigkeiten` documents list the validity periods of the
discharge curves, including provisional curves.

## Consequences for the active experiment

- German stage trajectories can be used as continuous local observations,
  subject to the held timestamp, datum and sensor-history limitations.
- Do not label the delivered series as filled from upstream or downstream
  gauges.
- Preserve post-July-2021 discharge as provisional and distinguish ordinary
  or low-flow support from high-flow uncertainty.
- Do not treat the July 2021 Randerath or Herzogenrath discharge peaks as exact
  validation targets. Stage, curve era and the stated uncertainty must travel
  together in event objects and evidence packets.
- An answer that reports an exact high-flow discharge without the provisional
  qualifier is a provenance error. Appropriate abstention remains correct
  where the requested conclusion depends on an exact peak.

The reply closes the outstanding reconstruction question and substantially
clarifies the provisional period. It does not explicitly map every discharge
row to a sensor or independently confirm the calculation applied to each row.
The curve-validity documents remain the authoritative era record.

Conditions for academic citation, derived publication and third-party
disclosure were promised after departmental review in the 2026-09-23 message
and were not supplied in this reply. Analysis can continue, but those terms
remain outstanding before publishing or redistributing LANUK data or derived
material where permission is required.

The preserved email and checksum are under
`data/raw/external_deliveries/lanuk_nrw/2026-10-13/`.
