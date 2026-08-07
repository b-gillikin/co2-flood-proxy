"""How much should the barometric gain change for the observed water rise?

This is a physical bound, not a statistical test, and it is what turns the
chapter's negative result from "we saw nothing" into a statement about what could
have been seen.

The mechanism is compression of a connected air-filled void. If the void has
vertical extent H and the water table rises by dh, the air-filled volume falls
by roughly dh/H, and the barometric gain falls by about the same fraction:

    d(gain) / gain  ~=  dh / H

That is a deliberately crude one-parameter model. It needs only the void's
vertical extent, which is unmeasured, so the result is reported as a sensitivity
across plausible H rather than a single number.

**The noise floor is not a constant, and treating it as one overstates the
case.** An earlier version of this script fixed the comparison against the
scatter of two-week windows and concluded the effect was about two orders of
magnitude below detection. That was wrong. Window-to-window scatter falls faster
than 1/sqrt(n) as windows lengthen -- 21.7 ppm/hPa at two weeks against 3.8 at
eight -- which is the signature of estimation noise rather than real variability
in the underlying gain. Estimation noise shrinks with data.

So the script now sweeps window length and reports the comparison at each. The
conclusion survives, for three better reasons that the output makes explicit:

1. The effect scales with dh. More years of 20 cm water swings give more data but
   never a larger signal, so only the noise side improves.
2. Longer windows buy precision and cost windows. At eight weeks there are four,
   spanning 20 cm of water level, which is too little variation to correlate
   against.
3. Even at the most favourable window length and the thinnest plausible void, the
   predicted effect is at or below the noise, not comfortably above it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.signal_frame import CO2_COL, contiguous_blocks, load_signal_frame

OUTPUT_PATH = Path("results/barometric_response/forward_gain_bound.txt")

# Observed corrected water-level range inside the clean IoT overlap block
# (2025-06-26 to 2025-08-26); see results/groundwater/barometric_efficiency.txt.
OBSERVED_RISE_M = 0.20

# Plausible vertical extents for a connected air-filled void above the water
# table, from a thin perched space to a deep unsaturated column. The water table
# sits roughly 21 m below ground at the primary well, bounding the upper end.
# The instantaneous barometric response argues for the thin end of this range.
VOID_EXTENTS_M = (1.0, 2.0, 5.0, 10.0, 21.0)

WINDOW_LENGTHS_H = (336, 672, 1008, 1344)
PRESSURE_COL = "knmi_pressure_hpa"


def gain_scatter(frame, window_hours):
    """Standard deviation of the windowed static gain at one window length."""
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("brf", ROOT / "scripts" / "19_barometric_response.py")
    brf = module_from_spec(spec)
    spec.loader.exec_module(brf)

    observed = frame.index[frame[CO2_COL].notna()]
    gains = []
    for _, index in contiguous_blocks(observed, min_hours=window_hours):
        block = frame.loc[index]
        step = max(window_hours // 4, 24)
        for start in range(0, len(block) - window_hours + 1, step):
            window = block.iloc[start : start + window_hours]
            impulse, _ = brf.deconvolve(window[CO2_COL], window[PRESSURE_COL])
            if impulse is None:
                continue
            gains.append(float(np.cumsum(impulse)[-1]))
    if len(gains) < 4:
        return np.nan, np.nan, len(gains)
    return float(np.std(gains, ddof=1)), float(np.median(gains)), len(gains)


def main():
    frame = load_signal_frame()

    lines = ["Forward Bound on Water-Driven Gain Change", ""]
    lines.append(f"Observed water rise over the clean block: {OBSERVED_RISE_M:.2f} m")
    lines.append("")
    lines.append("Noise floor depends on window length:")
    lines.append(f"  {'window (h)':>11} {'windows':>8} {'median gain':>12} {'SD':>8}")

    floors = {}
    for window_hours in WINDOW_LENGTHS_H:
        scatter, median, count = gain_scatter(frame, window_hours)
        if np.isnan(scatter):
            lines.append(f"  {window_hours:>11} {count:>8}   too few windows")
            continue
        floors[window_hours] = (scatter, median, count)
        lines.append(f"  {window_hours:>11} {count:>8} {median:>+12.2f} {scatter:>8.2f}")

    lines.append("")
    lines.append("Scatter falling faster than 1/sqrt(n) means it is estimation noise, which")
    lines.append("more data reduces. It is not a fixed property of the site.")

    if floors:
        best_window = min(floors, key=lambda w: floors[w][0])
        best_sd, best_median, best_count = floors[best_window]
        reference_gain = abs(best_median)
        lines.append("")
        lines.append(
            f"Best case, {best_window} h windows: noise {best_sd:.2f} ppm/hPa "
            f"on a gain of {reference_gain:.2f}, from {best_count} windows."
        )
        lines.append("")
        lines.append("Predicted effect against that floor:")
        lines.append(f"  {'H (m)':>7} {'change':>9} {'effect (ppm/hPa)':>18} {'vs noise':>10}")
        rows = []
        for extent in VOID_EXTENTS_M:
            fraction = OBSERVED_RISE_M / extent
            effect = fraction * reference_gain
            ratio = effect / best_sd
            rows.append(
                {
                    "void_extent_m": extent,
                    "predicted_fractional_change": fraction,
                    "predicted_effect_ppm_per_hpa": effect,
                    "noise_sd_ppm_per_hpa": best_sd,
                    "effect_over_noise": ratio,
                    "window_hours": best_window,
                }
            )
            lines.append(f"  {extent:7.1f} {fraction * 100:8.1f}% {effect:18.2f} {ratio:9.2f}x")
        pd.DataFrame(rows).to_csv(OUTPUT_PATH.with_name("forward_gain_bound.csv"), index=False)

        lines.append("")
        lines.append(
            f"  Even the thinnest void reaches only {rows[0]['effect_over_noise']:.2f}x the noise,"
        )
        lines.append(f"  and it is estimated from {best_count} windows spanning")
        lines.append(f"  {OBSERVED_RISE_M:.2f} m of water level, which is too little variation")
        lines.append("  to correlate against.")

    lines.append("")
    lines.append("Reading this:")
    lines.append(
        "  - The model is one parameter and deliberately crude. It bounds the\n"
        "    effect size; it does not simulate transport."
    )
    lines.append(
        "  - More data of the same kind shrinks the noise but never grows the\n"
        "    signal, because the effect scales with how far the water moves."
    )
    lines.append(
        "  - What would work: metres of water movement, as in decadal mine-water\n"
        "    recovery or documented pumping; or measuring occupancy directly, to\n"
        "    remove the largest non-barometric source of variance by design."
    )
    lines.append(
        "  - A negative result here means the effect was at or below the\n"
        "    resolution of this record, not that the mechanism is absent."
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
