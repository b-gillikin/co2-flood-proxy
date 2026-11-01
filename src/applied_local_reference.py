"""Local CEMS agreement conventions. Unknown and flood traces are not dry."""

import numpy as np

from applied_evaluation import count_metrics


def reference_labels(assessed, flooded, trace, permanent, stream):
    """Binary mapped-flood proxy on assessed, non-hydrographic support only.

    Trace-only polygons show prior inundation, not water at image time. Mapped
    hydrography is incomplete and not a certified permanent-water inventory.
    """
    assessed, flooded, trace, permanent, stream = np.broadcast_arrays(
        assessed, flooded, trace, permanent, stream
    )
    support = assessed.astype(bool) & ~permanent.astype(bool) & ~stream.astype(bool)
    support &= ~(trace.astype(bool) & ~flooded.astype(bool))
    labels = np.full(assessed.shape, 255, dtype=np.uint8)
    labels[support] = 0
    labels[support & flooded.astype(bool)] = 1
    return labels


def reference_agreement(reference, prediction, valid, kind):
    """Counts/metrics on exact common pixels; never interpret them as field truth."""
    reference, prediction, valid = np.broadcast_arrays(reference, prediction, valid)
    if kind not in {"surface_water", "three_class_flood"}:
        raise ValueError("Declare the task's prediction semantics")
    allowed = {0, 1} if kind == "surface_water" else {0, 1, 2}
    support = (reference != 255) & valid.astype(bool) & np.isin(prediction, list(allowed))
    wet = prediction == (1 if kind == "surface_water" else 2)
    truth = reference == 1
    tp = int((support & truth & wet).sum())
    fn = int((support & truth & ~wet).sum())
    fp = int((support & ~truth & wet).sum())
    tn = int((support & ~truth & ~wet).sum())

    def ratio(a, b):
        return a / b if b else None

    return dict(
        tp=tp,
        fn=fn,
        fp=fp,
        tn=tn,
        support_pixels=int(support.sum()),
        reference_flood_pixels=tp + fn,
        predicted_positive_pixels=tp + fp,
        iou=ratio(tp, tp + fn + fp),
        precision=ratio(tp, tp + fp),
        recall=ratio(tp, tp + fn),
        f1=ratio(2 * tp, 2 * tp + fn + fp),
    )


def summarize_cases(results):
    """Pool disjoint grid counts per AOI/acquisition, not tile IoUs.

    Individual and common support are both retained. No interval is fabricated
    from dependent July2021 AOIs or repeated acquisitions of the same flood.
    """
    groups = {}
    for row in results:
        groups.setdefault((row["case"], row["model"]), []).append(row)
    summaries = []
    for (case, model), rows in sorted(groups.items()):
        metadata = {(r["reference_offset_hours"], r["reference_dependence"]) for r in rows}
        if len(metadata) != 1:
            raise ValueError("A case must represent one acquisition/reference comparison")
        eligible = sum(r["eligible_reference_pixels"] for r in rows)
        metrics = {}
        for scope, field in [("common", "metrics"), ("individual", "individual_metrics")]:
            counts = {k: sum(r[field][k] for r in rows) for k in ["tp", "fn", "fp", "tn"]}
            metrics[scope] = count_metrics(counts)
            metrics[scope]["eligible_reference_pixels"] = eligible
            metrics[scope]["coverage_fraction"] = (
                metrics[scope]["support_pixels"] / eligible if eligible else None
            )
            metrics[scope]["unknown_or_unobserved_reference_pixels"] = (
                eligible - metrics[scope]["support_pixels"]
            )
            if all(r.get("pixel_area_m2") is not None for r in rows):
                metrics[scope]["area_m2"] = {
                    k: sum(r[field][k] * r["pixel_area_m2"] for r in rows)
                    for k in ["tp", "fn", "fp", "tn"]
                }
                metrics[scope]["eligible_reference_area_m2"] = sum(
                    r["eligible_reference_pixels"] * r["pixel_area_m2"] for r in rows
                )
        offset, dependence = next(iter(metadata))
        summaries.append(
            dict(
                case=case,
                model=model,
                grids=len(rows),
                support=metrics,
                reference_offset_hours=offset,
                reference_dependence=dependence,
            )
        )
    return summaries
