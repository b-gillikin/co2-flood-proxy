# Hostache et al. (2012): full-text research notes

Read 11 November 2026 from the publisher PDF supplied by Brian. This supplements the abstract-only review dated 10 November; historical access statements remain historical.

Citation: Hostache, R., Matgen, P., and Wagner, W. (2012). Change detection approaches for flood extent mapping: How to select the most adequate reference image from online archives? International Journal of Applied Earth Observation and Geoinformation, 19, 205–213. DOI: 10.1016/j.jag.2012.05.003.

Local PDF: `data/raw/literature/reference-selection/Hostache2012ReferenceImage.pdf`

SHA-256: `4afc763265cc6e276adfbdf1d776e892a5f4b3da5d4bccebb3a198ceb8adbcef`

## Author method and evidence

- Select candidates matching the crisis image's imaging mode, polarization and track. Season can also matter. Equal raster resolution alone does not establish comparable acquisition geometry (§2.1).
- Mask permanent water before calculating the percentile-spread index; the authors require residual permanent water to occupy less than 5% of pixels. Index 1 is p95 minus p5, rescaled to 0–1 (§2.2).
- Index 2 measures distributional distance from a reference constructed by taking the temporal median at each pixel and sorting those medians. It is also rescaled to 0–1. The displayed norm does not, by itself, specify a unique computational implementation; do not invent a norm or normalization recipe when claiming exact replication.
- Index 3 is sqrt(index1² + index2²); its minimum selects an actual acquisition balancing comparatively dry and representative conditions. A representative median alone can still describe flooded conditions, particularly in monsoon settings.
- Three contrasting settings are examined: Severn, Red River and Meghna. Quantitative downstream mapping sensitivity is demonstrated for Severn only (§4.2, Fig. 6). Several unflooded references perform comparably; large-scale flooding in reference images causes markedly worse mapping.
- Severn's benchmark is a 3 m TerraSAR-X-derived map acquired 39 hours before the 150 m ENVISAT flood scene. The endpoint is percentage correctly classified, not flood-class IoU. The authors discuss temporal stability, but this is not simultaneous field truth.
- Historical archive examples include acquisitions after the flood. A prospective application must restrict candidate images AND all selection statistics to information available before the assessment. A later retrospective study must identify its different information boundary explicitly.
- Distribution anomalies can also reflect snow, freezing, irrigation, wind or measurement problems. Small flooded areas need not materially change an entire region's histogram. Selection cannot solve every mapping limitation.

## Implications for our next comparison

The paper directly precedes the reference-contamination mechanism seen in our event review. Do not claim that mechanism as new. Our modern AI-versus-conventional comparison, independent event coverage and any demonstrated corrective benefit are separate propositions requiring evidence.

A literature-grounded actual-acquisition selector is a candidate corrective comparator, not an approved new experiment or an established improvement. Before implementing, specify candidate history, permanent-water mask, spatial support, distance/normalization and past-only availability. Check reference geometry against the post/crisis image, rather than merely matching two references to each other. Keep current results and their geometry limitations visible.

No model, data pull, scoring result or scientific design was changed by this reading. Brian retains all dissertation prose writing.
