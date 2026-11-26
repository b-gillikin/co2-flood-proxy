# Limburg geospatial audit

Internal research notes, 24 November 2026. The review covers the active
discharge reconstruction, seasonal sensitivity, and Meuse and Rimburg
context. Earlier satellite flood-mapping experiments have their own
[data and reference audit](limburg-response-mapping-literature-and-data-2026-11-12.md).

**Readout.** Geometry, units and raster checks support the active comparisons.
The most consequential qualifications
are the Kaarst–Weckhoven correspondence, the coarse effective resolution of
ERA5-Land in the small catchments, and the difference between a gauge's
drainage catchment and a modeled outlet's contributing area.

## Coordinates, networks and independence

- Rechecked the 394 reference geometries, their gauge keys and their processing
  hashes in ETRS89 / LAEA Europe (EPSG:3035). All are valid and nonempty.
  Coordinates enter point geometry as longitude, latitude in EPSG:4326.
  Four local points fall within their reference polygons. The other three
  are 24–43 m outside. These distances are consistent with the scale of the
  delineation and warrant retaining the source coordinates. Polygon
  membership alone provides weak evidence for the identity of a river outlet.
- Rebuilt all GEOGLOWS full upstream polygons from incremental units using
  `LINKNO` and the directed downstream edges. The seven local proxies cover
  97.0–99.2% of each gauge polygon. The converse can differ materially. At
  Brommelen, 99.1% of the gauge basin is in the model support but only 79.6%
  of the model polygon is in the gauge basin. The regional stress cases have
  considerably weaker matches. Both modeled and measured flows use the gauge
  reference area when converted to mm/day (m³/s × 86.4 ÷ km²), so this is a
  common error scale. It does not turn a modeled reach into the same physical
  section or equalize what two equally deep errors mean in volume.
- The only material cross-role reference overlap is almost the entire
  Weckhoven (Gillbach, `DEA10430`) polygon shared with Kaarst (Nordkanal,
  `DEA10450`). Its area is 90.56 km². The Kaarst GEOGLOWS proxy and its own
  reference polygon have **zero** overlap. Five cross-role reference
  intersections exceed 1 m². Of the remaining four, the two local slivers
  cover at most 0.058% of a target and the other two are each about 7 m².
  Across roles, there is no shared GEOGLOWS reach ID and no routed-polygon
  intersection over 1 m². The Kaarst–Weckhoven issue is in the reference
  landscape linked to the labels, which a river-ID check would miss.
- Kaarst was marked as a spatial stress case and has usable labels in
  training and validation in all four external years. Rescoring the fixed
  predictions without Weckhoven leaves 48 external gauges and 1,037
  high-water gauge-days. AlphaEarth's MAE reduction versus C2 moves from
  +1.08% to +1.10%, and TESSERA's from +1.67% to +1.65%. Raw GEOGLOWS still
  has the lowest high-water RMSE. This bounds the influence of the affected
  target at scoring time. Kaarst's influence on the fit itself remains
  untested. Keep it flagged and omit it from a spatially clean donor
  sensitivity if these arms are refitted. Use **external target-label
  holdout with one materially overlapping reference catchment** for the
  completed external comparison.
- At local scale, cross-river intersections are under 0.01 m² in both
  polygon families. Herzogenrath 1, Rimburg and Randerath are nested in
  that upstream-to-downstream order and held out together as Wurm. At
  regional scale, 12 donor reaches and two reserved reaches serve multiple
  gauges. Each repeated reach, and every group of byte-identical reference
  polygons, stays within one analysis river group. Gauge-days from nested
  outlets or shared storm fields should not be presented as independent
  events. Temporal block ranges are conditional on these rivers and do
  not quantify uncertainty for new basins. [Neri et al.](https://doi.org/10.5194/hess-24-5149-2020)

## Raster support, scale and meaning

| Input | Verified handling | Interpretation |
| --- | --- | --- |
| ERA5-Land weather, soil water and snow | Native 0.1° grid, polygon fractions, pixel-area weighting and common valid support. Local soil/snow and weather area ratios agree for each gauge. Plane-area ratios for the weather/state tables span about 0.92–1.09. | These ratios are diagnostics of the raster reduction against vector area, not literal valid-area percentages. The local polygons intersect 3–11 cells; area concentration gives the equivalent of about 1.9–6.1 equally weighted cells. One cell accounts for 63% of Brommelen. Retain these as broad weather and antecedent-state predictors. They do not resolve rainfall placement over individual hillslopes or flash responses. |
| C2 WorldCover and relief | Eleven land-cover class indicators are summarized separately on the source grid and their fractions sum to one for each catchment. Terrain uses native-grid p90 minus p10. Area checks for both agree with polygon area within 0.02%. | This is catchment composition and relief. Do not interpolate category codes or infer an inundation depth or an absolute water level from the relief metric. |
| C2 SoilGrids clay | Converted g/kg to mass percent. Finite means are based on valid cells. Coverage is 36.3–99.9% overall and 50.3–99.0% locally. | Missing cells are not zero clay. The valid-area mean may be unrepresentative if omissions follow land cover or location. C2 adds inputs as a bundle, so it cannot identify a clay effect. |
| AlphaEarth | Fractionally weighted 10 m EPSG:3035 means of 64 bands. The 2020 geometry hashes agree with the processing polygons. The five shared local rows independently extracted for 2020 agree with the matched table to within 1.5×10⁻¹⁴ per component. | Pixel count times nominal pixel area runs 100.12–100.88% of polygon area. Edge counting makes it a support check rather than literal coverage. A smaller vector norm after averaging unit vectors is expected. Catchment vectors describe a fixed imagery year; they do not observe each high-water event. |
| TESSERA | Decoded 128 bands with the source scales, excluded invalid cells, split the polygons by UTM zone, and used fractional overlap weights. Same reference geometry source as matched 2020 AlphaEarth. Valid-area coverage is 99.67–100%. | A whole-catchment mean discards position within the catchment. It cannot locate a source area or flood patch. The observation years and the imagery vintage are separate. |

The effective-cell count is the reciprocal of the sum of squared fractions
of local catchment area in each ERA5-Land grid cell. It is a measure of
concentration and does not count independent weather observations.
Reference boundaries and resolution can affect aggregate features. The
matched experiment keeps the receiving polygons and data rows fixed for
each comparison, so changes in skill cannot be used to identify which
within-catchment feature produced them.
[Earth Engine region weights](https://developers.google.com/earth-engine/guides/reducers_reduce_region) ·
[ERA5-Land data catalog](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR) ·
[SoilGrids units](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html) ·
[AlphaEarth data catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL)

## Rimburg, the Meuse and flood interpretation

The Google Rimburg HydroBASINS polygon has equal incremental and upstream
reported area and no other level-12 upstream units. Its polygon is the
full support at that delineation, making the published 93.2% and 95.2%
overlaps comparable. HydroRIVERS confirms the Wurm route to the physical
gauge downstream and the modeled tributary joining at the Google outlet.
Neither the match nor the paired error comparison removes the outlet
difference, model forcing, routing or possible training overlap. Larger
mainstem outlets can have many upstream units. Use their reported
upstream area or upstream union for any future full-basin comparison.
[HydroBASINS documentation](https://www.hydrosheds.org/products/hydrobasins)

Borgharen and Venlo are connected along the Meuse, with modeled comparison
outlets offset from the gauges. Keep the measured peak-time differences
as differences between maxima in the same event windows. They are not
parcel travel times, a closed water balance or isolated tributary
contributions. Daily Google values provide contextual comparison at
different river sections. The gauge-defined seasonal or all-season p99
locates unusually high discharge at a section. It carries no information
by itself about inundated land, exposed people, flood damage or the timing
of an official warning.

## Reproduce

Run `.venv-dise/bin/python scripts/301_audit_dise_geospatial.py` with the
existing DISE geospatial environment. The audit writes catchment support,
cross-role and local-pair intersections, and paired error sensitivities to
`results/limburg_representation_extension_v1/c2_multiyear_v1/geospatial_audit/`
with input and output hashes. The paired scores use equal river weights and
equal gauge weights within river. The 1 m² floor separates sub-metre
boundary slivers from the review table. The 1% and 10% output exclusions
are descriptive comparisons and select the same target here.
