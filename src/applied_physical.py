"""Transparent source-scale physical controls on the SAME task tensors.

No labels or test-dependent constants enter prediction. Thresholds and index
choice are selected only against the held validation event. These are simple
physical controls, not claims to reproduce a production flood mapping service.
"""

import numpy as np


def candidates(task):
    if task in {"terramind", "prithvi"}:
        return [
            dict(method=m, threshold=float(t))
            for m in ["ndwi", "mndwi"]
            for t in np.linspace(-0.8, 0.8, 33)
        ]
    if task == "galileo":
        return [
            dict(method="radar_dark", polarization=p, threshold_db=t)
            for p in [0, 1]
            for t in range(-30, -4)
        ]
    if task == "copernicus":
        return [
            dict(method="radar_change", polarization=p, threshold_db=t, drop_db=d)
            for p in [0, 1]
            for t in [-24, -21, -18, -15, -12]
            for d in [0, 3, 6]
        ]
    raise ValueError("Unknown task")


def source_features(x, task):
    """Invert declared task normalization; preserve prior resampling/clipping.

    Prithvi uses its actual B8A NIR and224px view; no invented10m B8.
    Copernicus features retain author input clipping at0.15 linear intensity.
    Input is C,H,W after that task's preprocessing, BEFORE tensor imputation
    matters on evaluated pixels. Native label/source masks are applied later.
    """
    x = np.asarray(x, dtype=np.float32)
    if task == "terramind":
        indices = [2, 7, 11]  # B3, B8, B11 in original13-band order
        raw = x[indices] * np.array([1833.702, 1727.26, 1331.411])[:, None, None]
        raw += np.array([2082.986, 3040.560, 2472.825])[:, None, None]
    elif task == "prithvi":
        raw = x[[1, 3, 4]] * np.array([2179, 1850, 1242])[:, None, None]
        raw += np.array([1342, 2734, 1958])[:, None, None]
    elif task == "galileo":
        means = np.array([-11.728724389184965, -18.85558188024017])[:, None, None]
        stds = np.array([4.887145774840316, 5.730270320384293])[:, None, None]
        return {"db": x * 4 * stds + means - 2 * stds}
    elif task == "copernicus":
        raw = x * np.array([0.0430, 0.0174, 0.0981, 0.0253])[:, None, None]
        raw += np.array([0.0981, 0.0253, 0.0981, 0.0253])[:, None, None]
        return {"db": 10 * np.log10(np.maximum(raw, 1e-10))}
    else:
        raise ValueError("Unknown task")

    def index(a, b):
        den = a + b
        return np.divide(a - b, den, out=np.zeros_like(a), where=np.abs(den) > 1e-6)

    return {"ndwi": index(raw[0], raw[1]), "mndwi": index(raw[0], raw[2])}


def predict(features, candidate):
    m = candidate["method"]
    if m in {"ndwi", "mndwi"}:
        return (features[m] > candidate["threshold"]).astype(np.uint8)
    p = candidate["polarization"]
    db = features["db"]
    if m == "radar_dark":
        return (db[p] < candidate["threshold_db"]).astype(np.uint8)
    if m != "radar_change":
        raise ValueError("Unknown physical control")
    pre, post = db[p], db[p + 2]
    pre_wet, post_wet = pre < candidate["threshold_db"], post < candidate["threshold_db"]
    y = np.zeros(pre.shape, dtype=np.uint8)
    y[pre_wet & post_wet] = 1
    y[~pre_wet & post_wet & ((pre - post) >= candidate["drop_db"])] = 2
    return y
