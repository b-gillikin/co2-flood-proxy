"""Local CEMS agreement conventions. Unknown and flood traces are not dry."""

import numpy as np


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
