#!/usr/bin/env python3
"""
Download utility for the MCity-WSPI module of the AD Winter Driving Dataset.

Image packages are hosted on Hugging Face; the synchronization CSVs live in this
GitHub repository. Run names are shared between the two, so `--run <name>` works
for either.

Examples:
    python3 tools/download_wspi.py --list
    python3 tools/download_wspi.py --run jan27-downtown-1 --dest_dir ./data
    python3 tools/download_wspi.py --run all_metadata --dest_dir ./data
"""

import argparse
import os
import urllib.error
import urllib.request

HF_BASE = ("https://huggingface.co/datasets/AD-Assurance-Lab/"
           "winter-driving-dataset/resolve/main")
GH_BASE = ("https://raw.githubusercontent.com/AD-Assurance-Lab/"
           "dataset--winter-driving--main/main")

# Every run with an image package published on Hugging Face.
IMAGE_RUNS = [
    'feb23-straight-10', 'feb23-straight-15', 'feb23-straight-20',
    'feb23-straight-25', 'feb23-straight-30', 'feb23-straightdeep-10',
    'feb23-straightdeep-15', 'feb23-straightdeep-20', 'feb23-straightdeep-25',
    'feb23-straightdeep-30', 'feb23-turn-mainstate-10', 'feb23-turn-mainstate-15',
    'feb23-turn-mainstate-20', 'feb23-turn-mainstate-25', 'feb23-turn-mainstatedeep-10',
    'feb23-turn-mainstatedeep-15', 'feb23-turn-mainstatedeep-20', 'feb23-turn-statemain-10',
    'feb23-turn-statemain-15', 'feb23-turn-statemain-20', 'feb23-turn-statemaindeepright-10',
    'feb23-turn-statemaindeepright-15', 'feb23-turn-statemaindeepright-20',
    'feb23-turn-statemaindeepright-25',
    'jan27-downtown-1', 'jan27-highway-1', 'jan27-highway-2',
    'jan27-highway-3', 'jan27-icehighway-20mph', 'jan27-icehighway-3',
    'jan27-icehighway-asphalt', 'jan27-southcircle-1', 'jan27-southcircle-2',
    'jan27-southcircle-3', 'jan27-southcircle-4', 'jan27-southcircle-5',
    'jan27-southcircle-6', 'jan27-test-2', 'jan27-test-3',
    'jan28-downtown-1', 'jan28-downtown-2', 'jan28-downtown-3',
    'jan28-highway-asphalt1', 'jan28-highway-asphalt2', 'jan28-highway-asphalt3',
    'jan28-highway-concrete1', 'jan28-highway-concrete2', 'jan28-highway-concrete3',
    'jan28-northcircle-1', 'jan28-northcircle-2', 'jan28-northcircle-3',
    'jan28-northcircle-4-no-tc', 'jan29-circle-10mph-1', 'jan29-circle-10mph-2',
    'jan29-circle-15mph-1', 'jan29-circle-15mph-2', 'jan29-circle-20mph-1',
    'jan29-circle-20mph-2', 'jan29-circle-25mph-1', 'jan29-circle-25mph-2',
    'jan29-circle-30mph-1', 'jan29-circle-30mph-2',
]

# 13 runs ship imagery but have no synchronization CSV. Downloading images for
# these gives you frames with no aligned dynamics or road weather telemetry.
RUNS_WITHOUT_SYNC = {
    'jan27-highway-3', 'jan27-icehighway-20mph', 'jan27-icehighway-3',
    'jan27-icehighway-asphalt', 'jan27-southcircle-1', 'jan27-southcircle-2',
    'jan27-southcircle-3', 'jan27-southcircle-4', 'jan27-southcircle-5',
    'jan27-southcircle-6', 'jan27-test-3', 'jan29-circle-10mph-2',
    'jan29-circle-20mph-1',
}

SYNC_RUNS = [r for r in IMAGE_RUNS if r not in RUNS_WITHOUT_SYNC]


def image_url(run):
    return f"{HF_BASE}/images/mcity_wspi/{run}_images.zip"


def sync_url(run):
    return f"{GH_BASE}/metadata/mcity_wspi/{run}_sync.csv"


def download_file(url, dest_path):
    """Download url to dest_path. Returns True on success."""
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    print(f"Downloading {url}\n         -> {dest_path}")

    def report_progress(block_num, block_size, total_size):
        read_so_far = block_num * block_size
        if total_size > 0:
            pct = min(read_so_far * 100 / total_size, 100.0)
            print(f"\r  {pct:5.1f}%  ({read_so_far / 1e6:.1f} / {total_size / 1e6:.1f} MB)",
                  end="")
        else:
            print(f"\r  {read_so_far / 1e6:.1f} MB", end="")

    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print("\n  done.")
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"\n  ERROR: {e}")
        # Do not leave a truncated file behind that looks like a valid download.
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", help="run name, 'all_images', 'all_metadata', or 'all'")
    p.add_argument("--dest_dir", default="./data", help="output directory (default ./data)")
    p.add_argument("--metadata_only", action="store_true",
                   help="fetch only the sync CSV for --run, not the image package")
    p.add_argument("--list", action="store_true", help="list available runs and exit")
    args = p.parse_args()

    if args.list:
        print(f"{len(IMAGE_RUNS)} runs with image packages "
              f"({len(SYNC_RUNS)} of them also have a synchronization CSV):\n")
        for r in IMAGE_RUNS:
            flag = "" if r in SYNC_RUNS else "   [images only - no sync CSV]"
            print(f"  {r}{flag}")
        return

    if not args.run:
        p.error("--run is required (or use --list)")

    img_dir = os.path.join(args.dest_dir, "images", "mcity_wspi")
    meta_dir = os.path.join(args.dest_dir, "metadata", "mcity_wspi")
    ok = failed = 0

    if args.run in ("all_metadata", "all"):
        print(f"Fetching {len(SYNC_RUNS)} synchronization CSVs...")
        for r in SYNC_RUNS:
            if download_file(sync_url(r), os.path.join(meta_dir, f"{r}_sync.csv")):
                ok += 1
            else:
                failed += 1

    if args.run in ("all_images", "all"):
        print(f"\nFetching {len(IMAGE_RUNS)} image packages (~140 GB total)...")
        for r in IMAGE_RUNS:
            if download_file(image_url(r), os.path.join(img_dir, f"{r}_images.zip")):
                ok += 1
            else:
                failed += 1

    if args.run not in ("all", "all_images", "all_metadata"):
        if args.run not in IMAGE_RUNS:
            print(f"Error: unknown run '{args.run}'. Use --list to see available runs.")
            raise SystemExit(1)

        if args.run in SYNC_RUNS:
            if download_file(sync_url(args.run),
                             os.path.join(meta_dir, f"{args.run}_sync.csv")):
                ok += 1
            else:
                failed += 1
        else:
            print(f"Note: '{args.run}' has no synchronization CSV "
                  f"(images only, no aligned telemetry).")

        if not args.metadata_only:
            if download_file(image_url(args.run),
                             os.path.join(img_dir, f"{args.run}_images.zip")):
                ok += 1
            else:
                failed += 1

    print(f"\n{ok} file(s) downloaded, {failed} failed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
