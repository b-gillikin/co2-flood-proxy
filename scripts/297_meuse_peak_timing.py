"""Audit and plot the recent Borgharen-anchored tributary timing cases."""

from __future__ import annotations

import argparse
import json
import sys
from itertools import pairwise
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.geoglows_experiment import sha, write_json  # noqa: E402

RAW = ROOT / "data/raw/discharge"
OUT = ROOT / "results/meuse_peak_timing_2026_11_23"
EXTENDED_OUT = ROOT / "results/meuse_peak_timing_with_venlo_2026_11_23"
WINDOW = pd.Timedelta(days=3)
HOUR = pd.Timedelta(hours=1)
MEASUREMENT_STEP = pd.Timedelta(minutes=10)
ANCHORS = [
    "2024-10-11 08:50",
    "2024-11-20 11:10",
    "2025-01-10 04:20",
    "2025-01-27 01:00",
    "2026-02-13 18:10",
    "2026-02-23 12:00",
]
MAIN = "Meuse · Borgharen Dorp"
VENLO = "Meuse · Venlo"
GAUGES = {
    "Gulp · Azijnfabriek": "gulp_azijnfabriek_238.json",
    "Geul · Meerssen": "geul_meerssen_1394.json",
    "Wurm · Randerath": "worm_randerath_1715.json",
    "Roer · Stah": "roer_stah_222.json",
    "Wurm · Rimburg": "worm_rimburg_242.json",
    "Geleenbeek · Oud Roosteren": "geleenbeek_oud_roosteren_481.json",
    "Geleenbeek · Brommelen": "geleenbeek_brommelen_227.json",
    "Voer · Mesch": "voer_voer_mesch_239.json",
    "Eyserbeek · Eys": "eyserbeek_eys_235.json",
}
CHAINS = {
    "Gulp → Geul → Meuse": ("Gulp · Azijnfabriek", "Geul · Meerssen"),
    "Wurm → Roer → Meuse": ("Wurm · Randerath", "Roer · Stah"),
}


def load_rws(files, station, method):
    rows = []
    for path in files:
        payload = json.loads(path.read_text())
        for block in payload["WaarnemingenLijst"]:
            meta = block["AquoMetadata"]
            if (
                meta["Grootheid"]["Code"] != "Q"
                or meta["Eenheid"]["Code"] != "m3/s"
                or meta["ProcesType"] != "meting"
                or meta["WaardeBepalingsMethode"]["Code"] != method
                or meta["WaardeBewerkingsMethode"]["Code"] != "NVT"
            ):
                continue
            if block["Locatie"]["Naam"] != station:
                raise ValueError(f"Unexpected RWS location in {path}")
            for obs in block["MetingenLijst"]:
                status = obs["WaarnemingMetadata"]
                rows.append(
                    (
                        obs["Tijdstip"],
                        obs["Meetwaarde"]["Waarde_Numeriek"],
                        status["Kwaliteitswaardecode"],
                        status["Statuswaarde"],
                    )
                )
    main = pd.DataFrame(rows, columns=["time", "q", "code", "status"])
    main["time"] = pd.to_datetime(main.time, utc=True)
    main = main.loc[np.isfinite(main.q) & main.q.between(0, 1e8, inclusive="left")]
    return main.drop_duplicates().sort_values("time")


def controlled_discharge(rows):
    strict = rows.loc[rows.code.eq("00") & rows.status.eq("Gecontroleerd"), ["time", "q"]]
    return single_series(strict, "q")


def load_inputs(include_venlo=False):
    files = [
        RAW / "rws" / f"maastricht.borgharen.maas.beneden_{year}.json"
        for year in (2024, 2025, 2026)
    ]
    main = load_rws(files, "Borgharen Dorp", "other:F006")

    series = {}
    for gauge, name in GAUGES.items():
        path = RAW / "waterschap" / name
        files.append(path)
        rows = pd.DataFrame(json.loads(path.read_text())["value"])
        rows["time"] = pd.to_datetime(rows.DateTime, utc=True)
        valid = np.isfinite(rows.Value) & rows.Value.between(0, 1e8, inclusive="left")
        series[gauge] = single_series(rows.loc[valid, ["time", "Value"]], "Value")
    series[MAIN] = controlled_discharge(main)
    if include_venlo:
        venlo_path = RAW / "rws" / "venlo_2024.json"
        files.append(venlo_path)
        series[VENLO] = controlled_discharge(load_rws([venlo_path], "Venlo", "other:F103"))
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in files}
    return series, main, hashes


def single_series(rows, col):
    clean = rows.drop_duplicates()
    if clean.time.duplicated().any():
        raise ValueError("Conflicting values at a shared timestamp")
    return clean.set_index("time")[col].sort_index()


def window(series, anchor):
    return series.loc[anchor - WINDOW : anchor + WINDOW]


def audit_events(series, main):
    strict = series[MAIN]
    events = []
    for anchor in pd.to_datetime(ANCHORS, utc=True):
        reported = main.loc[main.time.eq(anchor) & main.q.ge(1000)]
        if reported.empty:
            raise ValueError(f"No recorded crest at {anchor}")
        support = window(strict, anchor)
        has_quality = anchor in support.index
        native = reported.sort_values(["code", "status"]).iloc[0]
        core = support.loc[anchor - HOUR : anchor + HOUR]
        continuous = (
            len(core) == 13
            and core.index.to_series().diff().dropna().eq(pd.Timedelta(minutes=10)).all()
        )
        if has_quality and (support.idxmax() != anchor or not continuous):
            raise ValueError(f"Recheck controlled crest and support at {anchor}")
        # Keep quality-code and status fields separate. An unchecked 00 is not controlled.
        events.append(
            {
                "event": str(anchor.date()),
                "anchor_utc": anchor,
                "reported_q_m3s": native.q,
                "rws_code": native.code,
                "rws_status": native.status,
                "controlled_observations_in_window": len(support),
                "included": has_quality,
                "reason": (
                    "controlled code 00 crest"
                    if has_quality
                    else "interpolated crest"
                    if native.code == "25"
                    else "unchecked crest"
                ),
            }
        )
    selected = [record for record in events if record["included"]]
    for first, second in pairwise(selected):
        duration = second["anchor_utc"] - first["anchor_utc"]
        trough = strict.loc[first["anchor_utc"] : second["anchor_utc"]].min()
        drop = min(first["reported_q_m3s"], second["reported_q_m3s"]) - trough
        if duration < pd.Timedelta(days=1) or drop < 300:
            raise ValueError("Selected crests do not satisfy published separation")
        second["hours_since_previous_selected"] = duration / HOUR
        second["drop_from_lower_crest_m3s"] = drop
    return pd.DataFrame(events)


def timing(series, anchor, gauge, event):
    q = window(series, anchor)
    delta = (
        MEASUREMENT_STEP
        if gauge in (MAIN, VENLO)
        else series.index.to_series().diff().mode().iloc[0]
    )
    expected = pd.date_range(anchor - WINDOW, anchor + WINDOW, freq=delta).size
    base = {
        "event": event,
        "gauge": gauge,
        "anchor_utc": anchor,
        "sample_interval_minutes": delta / pd.Timedelta(minutes=1),
        "records": len(q),
        "expected_records_approx": expected,
    }
    if q.empty:
        return {**base, "peak_status": "missing"}
    at_peak = q.loc[q.eq(q.max())]
    near_peak = q.loc[q.ge(0.99 * q.max())]
    peak = at_peak.index[0]
    span = q.index.to_series().diff().max()
    edge = min(peak - q.index[0], q.index[-1] - at_peak.index[-1]) <= HOUR
    neighbourhood = q.loc[peak - HOUR : at_peak.index[-1] + HOUR]
    complete_neighbourhood = neighbourhood.index.to_series().diff().dropna().eq(delta).all()
    status = (
        "window_edge"
        if edge
        else "gap_near_peak"
        if not complete_neighbourhood
        else "interior_peak"
    )
    # Compare native maxima with fully sampled hourly means for aggregation sensitivity.
    per_hour = q.resample("h")
    hourly = per_hour.mean().where(per_hour.count().eq(HOUR / delta)).dropna()
    hours = hourly.idxmax() + HOUR / 2 if len(hourly) else None
    return {
        **base,
        "peak_status": status,
        "observed_max_q_m3s": q.max(),
        "first_max_utc": peak,
        "last_max_utc": at_peak.index[-1],
        "first_at_99_percent_of_max_utc": near_peak.index[0],
        "last_at_99_percent_of_max_utc": near_peak.index[-1],
        "hours_from_borgharen_crest": (peak - anchor) / HOUR,
        "max_gap_minutes": span / pd.Timedelta(minutes=1),
        "hourly_mean_peak_bin_midpoint_utc": hours,
    }


def mainstem_hourly(series, anchor):
    native_index = pd.date_range(anchor - WINDOW, anchor + WINDOW, freq=MEASUREMENT_STEP)
    # The boundary samples contribute a half interval. For F103 this represents
    # its centred 10-minute support; for F006 it integrates the reported labels.
    weights = np.array([0.5, 1, 1, 1, 1, 1, 0.5]) / 6
    hourly = (
        series.reindex(native_index)
        .rolling(len(weights))
        .apply(lambda samples: samples @ weights, raw=True)
    )
    return hourly.loc[hourly.index.minute == 0].dropna()


def mainstem_comparison(series, events, table):
    records = []
    for event in events.itertuples(index=False):
        pair = table.loc[table.event.eq(event.event)].set_index("gauge")
        upstream, downstream = pair.loc[MAIN], pair.loc[VENLO]
        hourly_up = mainstem_hourly(series[MAIN], event.anchor_utc)
        hourly_down = mainstem_hourly(series[VENLO], event.anchor_utc)
        paired_hours = hourly_up.index.intersection(hourly_down.index)
        hourly_up = hourly_up.loc[paired_hours]
        hourly_down = hourly_down.loc[paired_hours]
        records.append(
            {
                "event": event.event,
                "borgharen_peak_utc": upstream.first_max_utc,
                "venlo_peak_utc": downstream.first_max_utc,
                "borgharen_peak_m3s": upstream.observed_max_q_m3s,
                "venlo_peak_m3s": downstream.observed_max_q_m3s,
                "venlo_minus_borgharen_hours": (downstream.first_max_utc - upstream.first_max_utc)
                / HOUR,
                "venlo_minus_borgharen_peak_m3s": (
                    downstream.observed_max_q_m3s - upstream.observed_max_q_m3s
                ),
                "complete_paired_hours": len(paired_hours),
                "hourly_peak_offset_hours": (hourly_down.idxmax() - hourly_up.idxmax()) / HOUR,
                "hourly_peak_difference_m3s": hourly_down.max() - hourly_up.max(),
            }
        )
    return pd.DataFrame(records)


def draw_figure(series, events, table, out, mainstem=None):
    fig, grid = plt.subplots(
        len(events),
        len(CHAINS) + int(mainstem is not None),
        sharex=True,
        sharey=mainstem is None,
        squeeze=False,
        figsize=(13.5, 6.0) if mainstem is not None else (9.2, 6.0),
        layout="constrained",
    )
    palette = ("#146a95", "#bd512d", "#2f3743")
    for row, event in enumerate(events.itertuples(index=False)):
        for column, (title, chain) in enumerate(CHAINS.items()):
            ax = grid[row, column]
            if row == 0:
                ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
            if column == 0:
                ax.set_ylabel(f"{event.anchor_utc:%d %b %Y}\nFraction of gauge maximum")
            ax.axvline(0, color="#959da7", linestyle=":", linewidth=1)
            for i, (gauge, color) in enumerate(zip((*chain, MAIN), palette, strict=True)):
                q = window(series[gauge], event.anchor_utc)
                record = table.loc[table.event.eq(event.event) & table.gauge.eq(gauge)].iloc[0]
                step = pd.Timedelta(minutes=record.sample_interval_minutes)
                q = q.asfreq(step)
                x = (q.index - event.anchor_utc) / HOUR
                ax.plot(x, q / record.observed_max_q_m3s, color=color, linewidth=1.35)
                ax.scatter(record.hours_from_borgharen_crest, 1, color=color, s=18, zorder=3)
                label = gauge.split(" · ", 1)[1]
                ax.text(
                    0.985,
                    0.98 - i * 0.075,
                    f"{label}  {record.hours_from_borgharen_crest:+.0f} h",
                    color=color,
                    transform=ax.transAxes,
                    ha="right",
                    va="top",
                    fontsize=8.5,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "pad": 1},
                )
            ax.set(
                xlim=(-72, 72),
                ylim=(-0.01, 1.22),
                xticks=[-72, -48, -24, 0, 24, 48, 72],
                yticks=np.linspace(0, 1, 6),
            )
            ax.grid(axis="y", color="#e4e8ec", linewidth=0.7)
            ax.spines[["top", "right"]].set_visible(False)
            if mainstem is not None and column > 0:
                ax.tick_params(labelleft=False)
        if mainstem is not None:
            ax = grid[row, -1]
            ax.axvline(0, color="#959da7", linestyle=":", linewidth=1)
            for gauge, color in ((MAIN, palette[2]), (VENLO, "#6b438d")):
                q = window(series[gauge], event.anchor_utc).asfreq(MEASUREMENT_STEP)
                record = table.loc[table.event.eq(event.event) & table.gauge.eq(gauge)].iloc[0]
                ax.plot(
                    (q.index - event.anchor_utc) / HOUR,
                    q,
                    color=color,
                    linewidth=1.35,
                    label=gauge.split(" · ", 1)[1],
                )
                ax.scatter(
                    record.hours_from_borgharen_crest,
                    record.observed_max_q_m3s,
                    color=color,
                    s=18,
                    zorder=3,
                )
            if row == 0:
                ax.set_title(
                    "Meuse: Borgharen Dorp and Venlo", loc="left", fontsize=11, fontweight="bold"
                )
                ax.legend(loc="upper left", frameon=False, fontsize=8)
            ax.set(ylim=(0, 1.15 * mainstem.borgharen_peak_m3s.max()), ylabel="Discharge (m³/s)")
            ax.yaxis.set_label_position("right")
            ax.yaxis.tick_right()
            ax.grid(axis="y", color="#e4e8ec", linewidth=0.7)
            ax.spines[["top", "left"]].set_visible(False)
    fig.supxlabel("Hours from the observed Meuse crest at Borgharen Dorp (UTC)")
    fig.suptitle("From tributary high water to the Meuse", fontsize=14, fontweight="bold")
    for suffix in ("png", "pdf"):
        fig.savefig(
            out / f"meuse_peak_timing.{suffix}",
            dpi=200,
            metadata={"CreationDate": None, "ModDate": None} if suffix == "pdf" else None,
        )
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["audit", "run"])
    parser.add_argument("--include-venlo", action="store_true")
    args = parser.parse_args()
    out = EXTENDED_OUT if args.include_venlo else OUT
    series, mainstem, hashes = load_inputs(args.include_venlo)
    events = audit_events(series, mainstem)
    selected = events.loc[events.included].copy()
    identity = {
        "code_sha256": sha(Path(__file__)),
        "input_sha256": hashes,
        "selection": "Controlled code 00 F006 observed crest among fixed candidate windows",
        "candidate_anchors_utc": ANCHORS,
        "comparison_window_hours_each_side": WINDOW / HOUR,
        "primary_events": selected.event.to_list(),
    }
    audit_path = out / "audit.json"

    if args.stage == "audit":
        out.mkdir(parents=True, exist_ok=True)
        events.to_csv(out / "event_audit.csv", index=False)
        write_json(audit_path, {**identity, "event_audit_sha256": sha(out / "event_audit.csv")})
        print(events.to_string(index=False))
        return

    receipt = json.loads(audit_path.read_text())
    if receipt != {**identity, "event_audit_sha256": sha(out / "event_audit.csv")}:
        raise ValueError("Inputs or design changed after the audit")
    table = pd.DataFrame(
        [
            timing(q, event.anchor_utc, gauge, event.event)
            for event in selected.itertuples(index=False)
            for gauge, q in series.items()
        ]
    )
    critical = {MAIN, *(gauge for chain in CHAINS.values() for gauge in chain)}
    if args.include_venlo:
        critical.add(VENLO)
    primary = table.loc[table.gauge.isin(critical)]
    if not primary.peak_status.eq("interior_peak").all():
        raise ValueError("A figure gauge has an unsupported maximum")
    if not table.loc[table.gauge.eq(MAIN), "hours_from_borgharen_crest"].eq(0).all():
        raise ValueError("Mainstem reference deviates from the audited crest")
    outputs = ["gauge_peak_timing.csv", "meuse_peak_timing.png", "meuse_peak_timing.pdf"]
    comparison = None
    if args.include_venlo:
        comparison = mainstem_comparison(series, selected, table)
        comparison.to_csv(out / "mainstem_peak_comparison.csv", index=False)
        outputs.append("mainstem_peak_comparison.csv")
    table.to_csv(out / "gauge_peak_timing.csv", index=False)
    draw_figure(series, selected, table, out, comparison)
    write_json(
        out / "manifest.json",
        {
            **identity,
            "status": "completed",
            "audit_sha256": sha(audit_path),
            "outputs_sha256": {name: sha(out / name) for name in outputs},
        },
    )
    print(
        table[["event", "gauge", "hours_from_borgharen_crest", "peak_status"]].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
