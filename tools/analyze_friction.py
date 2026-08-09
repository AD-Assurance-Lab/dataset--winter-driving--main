#!/usr/bin/env python3
"""
Friction analysis for the MCity-WSPI module.

Reproduces the two dynamics figures in the SAE WCX paper:

  fig_friction_validation.png  Optical (MARWIS) road friction vs. the peak
                               longitudinal friction actually realised by the
                               vehicle during ABS-active braking, per event.
  fig_slip_friction.png        Friction-slip curve for a representative
                               full-ABS stop, using the corrected slip ratio.

Both are computed from the synchronized CSVs in metadata/mcity_wspi/ only, so
the figures can be regenerated without downloading the image packages.

Usage:
    python3 tools/analyze_friction.py --metadata_dir metadata/mcity_wspi \
                                      --out_dir figures
"""

import argparse
import glob
import os

import numpy as np
import pandas as pd

G = 9.80665           # m/s^2
MPH_TO_MPS = 0.44704
MIN_SPEED_MPH = 3.0   # slip ratio is undefined as the vehicle approaches rest
MEDIAN_WINDOW = 5     # samples; rejects isolated single-sample IMU spikes
MIN_EVENT_SAMPLES = 20

# Categorical slots 1-3 of the validated palette (see paper figure captions).
C_DYN = "#2a78d6"     # blue   - dynamics-derived friction
C_OPT = "#eb6834"     # orange - MARWIS optical friction
C_AUX = "#1baf7a"     # aqua   - binned mean / auxiliary


def load_runs(metadata_dir):
    """Load every *_sync.csv into one frame, tagged with its run name."""
    frames = []
    for path in sorted(glob.glob(os.path.join(metadata_dir, "*_sync.csv"))):
        df = pd.read_csv(path)
        df["run"] = os.path.basename(path).replace("_sync.csv", "")
        frames.append(df)
    if not frames:
        raise SystemExit(f"no *_sync.csv found under {metadata_dir}")
    return pd.concat(frames, ignore_index=True)


def despike(series, window=MEDIAN_WINDOW):
    """Rolling-median filter.

    The OxTS accelerations contain isolated single-sample outliers (up to
    -12.8 m/s^2, i.e. 1.3 g, on surfaces whose friction limit is near 0.3).
    Neighbouring samples are physically consistent, so a short median filter
    removes them without attenuating the braking transient.
    """
    return series.rolling(window, center=True, min_periods=1).median()


def corrected_slip(v_vehicle_mph, v_wheel_mph):
    """Signed SAE J670 slip ratio, gated at low speed.

    Braking  (wheel slower than body): s = (v_veh - v_wheel) / v_veh
    Driving  (wheel faster than body): s = (v_wheel - v_veh) / v_wheel

    Returns NaN below MIN_SPEED_MPH, where the denominator collapses. The
    published `wheel_slip` column instead used abs(...)/v_vehicle at all
    speeds, which is why 2.8% of its values exceed 1.0.
    """
    v_veh = np.asarray(v_vehicle_mph, dtype=float)
    v_whl = np.asarray(v_wheel_mph, dtype=float)
    s = np.full(v_veh.shape, np.nan)

    braking = (v_veh >= MIN_SPEED_MPH) & (v_whl <= v_veh)
    s[braking] = (v_veh[braking] - v_whl[braking]) / v_veh[braking]

    driving = (v_whl >= MIN_SPEED_MPH) & (v_whl > v_veh)
    s[driving] = (v_whl[driving] - v_veh[driving]) / v_whl[driving]

    return np.clip(s, -1.0, 1.0)


def abs_events(df):
    """Split into contiguous ABS-active segments, one row per event."""
    events = []
    for run, g in df.groupby("run", sort=False):
        g = g.sort_values("timestamp_sec").reset_index(drop=True)
        active = g["abs_active"].astype(float).values > 0.5
        i = 0
        while i < len(active):
            if not active[i]:
                i += 1
                continue
            j = i
            while j + 1 < len(active) and active[j + 1]:
                j += 1
            seg = g.iloc[i : j + 1]
            i = j + 1

            if len(seg) < MIN_EVENT_SAMPLES:
                continue
            ax = despike(seg["linear_acceleration_x"])
            # Braking events only: reject segments that are net accelerating.
            if ax.mean() > -0.5:
                continue

            events.append(
                {
                    "run": run,
                    "n": len(seg),
                    "duration_s": seg["timestamp_sec"].iloc[-1] - seg["timestamp_sec"].iloc[0],
                    "v_entry_mph": seg["vehicle_speed_mph"].iloc[0],
                    # 5th percentile of the filtered signal = sustained peak
                    # deceleration, robust to the remaining transients.
                    "mu_dynamic": float(abs(ax.quantile(0.05)) / G),
                    "mu_marwis": float(seg["marwis_friction"].mean()),
                    "cornering": bool(seg["linear_acceleration_y"].abs().median() > 1.5),
                    "surface": (
                        seg["marwis_road_condition"].mode().iloc[0]
                        if seg["marwis_road_condition"].notna().any()
                        else None
                    ),
                }
            )
    return pd.DataFrame(events)


def _style():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 7,
            "axes.labelsize": 7.5,
            "axes.titlesize": 7.5,
            "legend.fontsize": 6.5,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#52514e",
            "axes.linewidth": 0.6,
            "grid.color": "#e2e1dd",
            "grid.linewidth": 0.5,
            "figure.dpi": 400,
            "savefig.dpi": 400,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
        }
    )
    return plt


def figure_friction_validation(events, out_path):
    plt = _style()
    paired = events.dropna(subset=["mu_marwis"])
    paired = paired[~paired["cornering"]]

    fig, ax = plt.subplots(figsize=(3.35, 2.7))
    lim = [0.0, 0.6]
    ax.plot(lim, lim, color="#9a9992", lw=0.8, ls="--", zorder=1)
    ax.text(
        0.325, 0.318, "1:1 agreement", color="#52514e", fontsize=6,
        rotation=38, rotation_mode="anchor", ha="right", va="bottom",
    )

    ax.scatter(
        paired["mu_marwis"], paired["mu_dynamic"],
        s=26, color=C_DYN, edgecolor="#fcfcfb", linewidth=0.7, zorder=3,
    )

    ratio = (paired["mu_dynamic"] / paired["mu_marwis"]).median()
    ax.set_xlim(0.15, 0.35)
    ax.set_ylim(0.15, 0.55)
    ax.set_xlabel(r"MARWIS optical friction $\mu_{\mathrm{opt}}$")
    ax.set_ylabel(r"ABS-realised friction $\mu_{\mathrm{dyn}} = |a_x|/g$")
    ax.grid(True, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.text(
        0.03, 0.96,
        f"n = {len(paired)} ABS stops\nmedian $\\mu_{{dyn}}/\\mu_{{opt}}$ = {ratio:.2f}",
        transform=ax.transAxes, va="top", ha="left", fontsize=6.5, color="#0b0b0b",
    )
    fig.savefig(out_path)
    plt.close(fig)
    return paired, ratio


def slip_samples(df, events):
    """Per-sample (slip, mu) pairs pooled over all straight-line ABS events."""
    out = []
    for run in events[~events["cornering"]]["run"].unique():
        g = df[df["run"] == run].sort_values("timestamp_sec").reset_index(drop=True)
        idx = np.flatnonzero(g["abs_active"].astype(float).values > 0.5)
        if len(idx) < MIN_EVENT_SAMPLES:
            continue
        seg = g.iloc[idx[0] : idx[-1] + 1].copy()
        seg["mu"] = despike(seg["linear_acceleration_x"]).abs() / G
        seg["slip"] = corrected_slip(seg["vehicle_speed_mph"], seg["avg_wheel_speed_mph"])
        out.append(seg[["run", "slip", "mu"]].dropna())
    return pd.concat(out, ignore_index=True)


def figure_slip_friction(df, events, out_path):
    plt = _style()
    s = slip_samples(df, events)
    s = s[(s["slip"] >= 0) & (s["slip"] <= 0.6)]

    fig, ax = plt.subplots(figsize=(3.35, 2.7))
    ax.scatter(
        s["slip"], s["mu"],
        s=5, color=C_DYN, alpha=0.22, edgecolor="none", zorder=2,
        label=f"samples ({len(s)})",
    )

    # Binned mean +/- 1 s.d., equal-count bins so every marker is equally supported.
    q = np.quantile(s["slip"], np.linspace(0, 1, 11))
    q = np.unique(q)
    centres, means, sds = [], [], []
    for lo, hi in zip(q[:-1], q[1:]):
        m = s[(s["slip"] >= lo) & (s["slip"] < hi)]
        if len(m) >= 10:
            centres.append(m["slip"].median())
            means.append(m["mu"].mean())
            sds.append(m["mu"].std())
    centres, means, sds = np.array(centres), np.array(means), np.array(sds)

    ax.fill_between(centres, means - sds, means + sds, color=C_OPT, alpha=0.16,
                    lw=0, zorder=3)
    ax.plot(centres, means, color=C_OPT, lw=2.0, marker="o", ms=4,
            markeredgecolor="#fcfcfb", markeredgewidth=0.7, zorder=4,
            label=r"binned mean $\pm$ 1 s.d.")

    peak = int(np.argmax(means))
    ax.annotate(
        f"peak $\\mu$ = {means[peak]:.2f}\nat $s$ = {centres[peak]:.2f}",
        xy=(centres[peak], means[peak]),
        xytext=(centres[peak] + 0.10, means[peak] + 0.09),
        fontsize=6, color="#0b0b0b",
        arrowprops=dict(arrowstyle="->", color="#52514e", lw=0.6),
    )

    ax.set_xlabel(r"corrected slip ratio $s$")
    ax.set_ylabel(r"$\mu_{\mathrm{est}} = |a_x|/g$")
    ax.set_xlim(0, 0.6)
    ax.set_ylim(0, 0.6)
    ax.grid(True, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right")
    fig.savefig(out_path)
    plt.close(fig)
    return s, centres[peak], means[peak]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--metadata_dir", default="metadata/mcity_wspi")
    p.add_argument("--out_dir", default="figures")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    df = load_runs(args.metadata_dir)
    events = abs_events(df)

    print(f"loaded {len(df)} synchronized frames from {df['run'].nunique()} runs")
    print(f"detected {len(events)} ABS braking events "
          f"({int((~events['cornering']).sum())} straight-line)")

    f1 = os.path.join(args.out_dir, "fig_friction_validation.png")
    paired, ratio = figure_friction_validation(events, f1)
    print(f"\n[{f1}]")
    print(f"  paired straight-line ABS stops with MARWIS: {len(paired)}")
    print(f"  MARWIS  mu_opt : {paired['mu_marwis'].min():.3f} - {paired['mu_marwis'].max():.3f}"
          f"  (mean {paired['mu_marwis'].mean():.3f})")
    print(f"  dynamics mu_dyn: {paired['mu_dynamic'].min():.3f} - {paired['mu_dynamic'].max():.3f}"
          f"  (mean {paired['mu_dynamic'].mean():.3f})")
    print(f"  median ratio mu_dyn / mu_opt = {ratio:.2f}")

    f2 = os.path.join(args.out_dir, "fig_slip_friction.png")
    s, s_peak, mu_peak = figure_slip_friction(df, events, f2)
    print(f"\n[{f2}]")
    print(f"  pooled samples across straight-line ABS events: {len(s)}")
    print(f"  peak binned mu = {mu_peak:.3f} at slip s = {s_peak:.3f}")

    events.to_csv(os.path.join(args.out_dir, "abs_events.csv"), index=False)
    print(f"\nwrote {os.path.join(args.out_dir, 'abs_events.csv')}")


if __name__ == "__main__":
    main()
