#!/usr/bin/env python3
"""
Build the sample-frame montage used in the SAE WCX paper.

Each tile is a real frame drawn from the middle of a run, annotated with the
MARWIS surface classification and optical friction recorded on that same frame.
Requires the image packages for the selected runs to be present locally
(see tools/download_wspi.py).

Usage:
    python3 tools/make_sample_montage.py --out figures/fig_sample_frames.png
"""

import argparse
import glob
import os

import pandas as pd

# Runs chosen for visual spread: bright packed snow with ruts, plowed asphalt,
# an overcast low-contrast surface, and deep manufactured snow.
RUNS = [
    ("jan28-downtown-1", "(a) packed snow, tire ruts"),
    ("jan28-highway-asphalt1", "(b) plowed asphalt, partial cover"),
    ("jan28-northcircle-1", "(c) cone-defined circle, cornering"),
    ("feb23-straightdeep-30", "(d) deep manufactured snow"),
]

TILE_W, TILE_H = 640, 400


def frame_for(run, images_root, metadata_dir):
    paths = sorted(glob.glob(os.path.join(images_root, run, "*.png")))
    if not paths:
        return None, None
    path = paths[len(paths) // 2]

    caption = ""
    csv_path = os.path.join(metadata_dir, f"{run}_sync.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        row = df[df["image_filename"] == os.path.basename(path)]
        if len(row):
            row = row.iloc[0]
            cond = row.get("marwis_road_condition")
            mu = row.get("marwis_friction")
            bits = []
            if isinstance(cond, str) and cond and pd.notna(mu):
                bits.append(f"{cond} · $\\mu_{{opt}}$ = {float(mu):.2f}")
            else:
                # 32 of 49 runs carry no MARWIS telemetry; say so rather than
                # leaving the reader to assume the sensor agreed.
                bits.append("MARWIS n/a")
            bits.append(f"{float(row['vehicle_speed_mph']):.0f} mph")
            caption = " · ".join(bits)
    return path, caption


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images_root", default="images/mcity_wspi")
    p.add_argument("--metadata_dir", default="metadata/mcity_wspi")
    p.add_argument("--out", default="figures/fig_sample_frames.png")
    args = p.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg

    plt.rcParams.update({"font.size": 6.5, "figure.dpi": 400, "savefig.dpi": 400})

    fig, axes = plt.subplots(2, 2, figsize=(3.35, 2.25))
    missing = []
    for ax, (run, label) in zip(axes.ravel(), RUNS):
        path, caption = frame_for(run, args.images_root, args.metadata_dir)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        if path is None:
            missing.append(run)
            ax.text(0.5, 0.5, f"{run}\nnot downloaded", ha="center", va="center",
                    fontsize=5, color="#9a9992", transform=ax.transAxes)
            continue
        ax.imshow(mpimg.imread(path))
        ax.set_title(label, fontsize=6, color="#0b0b0b", pad=2, loc="left")
        if caption:
            ax.text(0.015, 0.03, caption, transform=ax.transAxes, fontsize=4.6,
                    color="#ffffff", va="bottom", ha="left",
                    bbox=dict(boxstyle="square,pad=0.22", fc="#0b0b0b",
                              ec="none", alpha=0.65))

    fig.tight_layout(pad=0.25, h_pad=0.5, w_pad=0.3)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, bbox_inches="tight", pad_inches=0.02)
    print(f"wrote {args.out}")
    if missing:
        print("missing image packages for:", ", ".join(missing))


if __name__ == "__main__":
    main()
