"""Auditable long-episode and high-water measurement review for Limburg."""

from __future__ import annotations

import json
import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location(
    "cross_tributary", ROOT / "scripts/53_cross_tributary_rain_episodes.py"
)
core = module_from_spec(spec)
spec.loader.exec_module(core)
OUT = core.OUT


def rain_pulse_stats(rain, start, end):
    """Count pulses separated by at least six entirely dry regional hours."""
    regional = rain.loc[start:end].max(axis=1)
    wet = np.flatnonzero(regional.ge(core.WET_MM_H).to_numpy())
    if not len(wet):
        return 0, 0
    dry = np.diff(wet) - 1
    return int(1 + (dry >= 6).sum()), int(dry.max()) if len(dry) else 0


def build_audit(episodes, sites, rain):
    rows = []
    for event in episodes.itertuples(index=False):
        subset = sites.loc[sites.episode_id.eq(event.episode_id)]
        pulses, max_dry = rain_pulse_stats(rain, event.rain_start_utc, event.rain_end_utc)
        rows.append(
            {
                "episode_id": event.episode_id,
                "rain_start_utc": event.rain_start_utc,
                "duration_hours": event.duration_hours,
                "rain_pulses_6h": pulses,
                "max_internal_dry_hours": max_dry,
                "n_sites_high": int(subset.any_high_water.sum()),
                "n_sites_sustained_3h": int(subset.longest_high_run_hours.ge(3).sum()),
                "n_high_without_reviewed_onset": int(
                    (subset.any_high_water & subset.first_onset_utc.isna()).sum()
                ),
                "n_sites_low_coverage": int(subset.valid_hour_fraction.lt(0.9).sum()),
                "n_sites_high_outside_rating_domain": int(
                    subset.any_high_outside_rating_domain.sum()
                ),
                "n_sites_high_above_gulp_calibration": int(
                    subset.any_high_above_gulp_calibration.sum()
                ),
                "n_sites_onset_measurement_concern": int(subset.measurement_concern.sum()),
                "long_72h": bool(event.duration_hours >= 72),
            }
        )
    return pd.DataFrame(rows)


def plot_selected_episodes(episodes, audit, rain, states, episode_ids, prefix):
    os.environ.setdefault("MPLCONFIGDIR", str(OUT / ".matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    selected_episodes = episodes.set_index("episode_id").loc[episode_ids].reset_index()
    for page, first in enumerate(range(0, len(selected_episodes), 4), start=1):
        selected = selected_episodes.iloc[first : first + 4]
        fig, axes = plt.subplots(8, 1, figsize=(17, 19), squeeze=False)
        for position, event in enumerate(selected.itertuples(index=False)):
            top, bottom = axes[2 * position : 2 * position + 2, 0]
            window = rain.loc[event.rain_start_utc : event.response_end_utc]
            regional = window.max(axis=1)
            top.bar(regional.index, regional.to_numpy(), width=0.03, color="steelblue")
            top.axvline(event.rain_end_utc, color="darkred", linestyle="--", linewidth=0.8)
            entry = audit.loc[audit.episode_id.eq(event.episode_id)].iloc[0]
            top.set_title(
                f"{event.episode_id}: {event.rain_start_utc:%Y-%m-%d} | "
                f"{event.duration_hours} h, {entry.rain_pulses_6h} rain pulses, "
                f"{entry.n_sites_high} sites high"
            )
            top.set_ylabel("regional max\nmm/h")
            for site in core.SITES:
                state = states[site].loc[event.rain_start_utc : event.response_end_utc]
                ratio = state.q.div(state.p99).where(state.valid)
                bottom.plot(ratio.index, ratio.clip(upper=2.5), label=site, linewidth=0.9)
            bottom.axhline(1, color="black", linestyle="--", linewidth=0.8)
            bottom.axvline(event.rain_end_utc, color="darkred", linestyle="--", linewidth=0.8)
            bottom.set_ylim(0, 2.55)
            bottom.set_ylabel("Q / p99\nclipped at 2.5")
            bottom.legend(ncol=6, fontsize=7, loc="upper right")
        for position in range(len(selected), 4):
            axes[2 * position, 0].axis("off")
            axes[2 * position + 1, 0].axis("off")
        fig.tight_layout()
        fig.savefig(OUT / f"{prefix}_{page:02d}.png", dpi=140)
        plt.close(fig)


def main():
    episodes = pd.read_csv(
        OUT / "rain_episodes.csv",
        parse_dates=["rain_start_utc", "rain_end_utc", "response_end_utc"],
    )
    sites = pd.read_csv(OUT / "site_footprints.csv")
    rain = core.read_hourly(core.DATA / "radolan_catchment_hourly.csv")[list(core.SITES)]
    discharge = core.read_hourly(core.DATA / "event_study_discharge_hourly.csv")
    ratings = pd.read_csv(core.DATA / "event_study_rating_eras.csv")
    states = core.site_states(discharge, ratings)
    audit = build_audit(episodes, sites, rain)
    audit.to_csv(OUT / "episode_measurement_audit.csv", index=False)
    long_ids = episodes.loc[episodes.duration_hours.ge(72)].episode_id.tolist()
    plot_selected_episodes(episodes, audit, rain, states, long_ids, "long_episode_review")
    prediction_path = OUT / "model_primary_predictions.csv"
    if prediction_path.exists():
        predictions = pd.read_csv(prediction_path)
        predictions["absolute_residual"] = (
            predictions.model_n_high - predictions.fitted_high_sites
        ).abs()
        top_ids = predictions.nlargest(8, "absolute_residual").episode_id.tolist()
        plot_selected_episodes(episodes, audit, rain, states, top_ids, "model_residual_review")
    summary = {
        "n_long_72h": int(audit.long_72h.sum()),
        "n_long_multipulse": int((audit.long_72h & audit.rain_pulses_6h.ge(2)).sum()),
        "n_site_high_without_new_onset": int(audit.n_high_without_reviewed_onset.sum()),
        "n_episodes_rating_domain_exceedance": int(
            audit.n_sites_high_outside_rating_domain.gt(0).sum()
        ),
        "n_episodes_gulp_above_calibration": int(
            audit.n_sites_high_above_gulp_calibration.gt(0).sum()
        ),
    }
    (OUT / "episode_measurement_audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
