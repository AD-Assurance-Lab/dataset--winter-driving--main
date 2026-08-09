# AD Winter Driving Dataset: Multimodal Perception & Physics

This repository hosts the metadata, documentation, loaders, and synchronization tools for the **AD Winter Driving Dataset**, a joint effort between the **AD Assurance Lab**, **Western Michigan University**, and **MCity**. 

The dataset is divided into two core modules:
1. **Module 1: REVA Perception (MI-Snow1000)**: A lane detection and semantic road understanding benchmark featuring 4,888 manually annotated lanes in TuSimple format, captured across 1,000 miles of winter driving in Michigan, Colorado, and Wyoming.

   > [!WARNING]
   > **Module 1 imagery is not yet hosted.** The annotations
   > (`metadata/reva_perception/`) and the trained checkpoints are published, but the
   > Hugging Face repository currently contains image packages for Module 2 only. The
   > MI-Snow1000 frames must be uploaded before the dataset can be described as
   > publicly available.
2. **Module 2: MCity-WSPI Physics**: Time-synchronized front-camera frames (~48 Hz January sessions, ~20 Hz February session) aligned directly with vehicle dynamics (CAN bus steering, wheel speeds, brake torque), high-grade IMU response (rotational rates, linear acceleration including vertical ride response), GPS/RTK trajectories, and mobile road weather information (MARWIS) optical surface parameters (friction coefficient, pavement temperature, ice percent, water film height).

---

## Repository Structure

```directory/
dataset--winter-driving--main/
├── docs/                     # Documentation landing page (hosted on GitHub Pages)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── metadata/                 # Tabular metadata and annotations
│   ├── reva_perception/      # Module 1: train.json, val.json, test.json
│   └── mcity_wspi/           # Module 2: jan27-downtown-1_sync.csv, ...
├── models/                   # Pre-trained lane detection benchmark checkpoints
│   ├── README.md             # Model info and Hugging Face weights download links
│   ├── onnx/                 # (Local only) ONNX .onnx checkpoints
│   └── pytorch/              # (Local only) PyTorch .pt / .pth checkpoints
├── tools/                    # Python loader and sync scripts
│   ├── download_wspi.py      # CLI tool to download raw image zips and sync CSVs
│   ├── download_models.py    # CLI tool to download pre-trained benchmarks
│   ├── wspi_sync.py          # CLI tool to perform nearest-neighbor sensor synchronization
│   ├── wspi_loader.py        # PyTorch-compatible dataset loader
│   ├── analyze_friction.py   # Optical vs. realized friction; friction-slip curve
│   └── make_sample_montage.py # Annotated sample-frame figure
├── README.md
├── LICENSE                   # Creative Commons Attribution 4.0 International
└── .gitignore
```

---

## Aligned Physics Variables

Each row in the synchronized metadata CSVs under `metadata/mcity_wspi/` matches a single camera frame (named with its index, e.g. `frame_00000.png`) to the temporally nearest telemetry signals. Key variables include:

| Group | Column Name | Source Sensor | Description |
| :--- | :--- | :--- | :--- |
| **Image** | `image_filename` | Windshield Camera | Name of the PNG image frame (`frame_xxxxx.png`). |
| **Time** | `timestamp_ns` | ROS Clock | Nanosecond epoch stamp. |
| **GPS** | `latitude`, `longitude`, `altitude` | RTK-GPS | Geographic coordinate. |
| **Pose** | `orientation_x` (y, z, w) | OxTS IMU | Orientation Quaternion. |
| **IMU** | `linear_acceleration_x` (y, z) | OxTS IMU | Acceleration in m/s² (Z-axis ride response). |
| **IMU** | `angular_velocity_x` (y, z) | OxTS IMU | Rotational velocity in rad/s. |
| **Speed** | `vehicle_speed_mph` | Vehicle CAN / Odo | Actual vehicle speed in mph (linear velocity X * 2.237). |
| **Wheel** | `wheel_speed_fl_rads` (fr, rl, rr)| Vehicle CAN | Individual wheel rotation rates in rad/s. |
| **Wheel** | `avg_wheel_speed_mph` | Calculated | Average speed of all wheels converted to mph. |
| **Physics**| `wheel_slip` | Calculated | Unsigned slip ratio, `abs(wheel_speed_mph - vehicle_speed_mph) / vehicle_speed_mph`. **See the caveat below — prefer `tools/analyze_friction.py`.** |
| **Control**| `steering_angle_deg` | Vehicle CAN | Steering wheel angle in degrees (observed range −491 to +488). |
| **Control**| `throttle_pedal` | Vehicle CAN | Throttle input in **percent** (observed range 0–90.4), not a 0–1 fraction. |
| **Control**| `brake_pedal` | Vehicle CAN | Brake input in **raw controller counts** (observed range 0–13,080), not a 0–1 fraction. |
| **Safety** | `abs_active`, `esc_active`, `trac_active` | Vehicle CAN | Binary flags. `trac_active` is identically 0 across the release. |
| **Road** | `marwis_road_condition` | MARWIS Sensor | Surface classification. Only `snow covered` and `snow/ice covered` occur. |
| **Road** | `marwis_friction` | MARWIS Sensor | Optical road friction estimate (observed range 0.196–0.317). |

### Known caveats

Read these before using the release; each is a real property of the current data.

**Wheel speed units are rad/s.** Prior student analyses assumed RPM. Regressing the
angular against the linear wheel-speed channels over 134,496 samples gives an
effective rolling radius of **R = 0.362 m**, consistent with the nominal Mach-E value
of 0.363 m and confirming the rad/s interpretation. Tire speed is `v = ω · R`.

**The shipped `wheel_slip` column is not the SAE slip ratio.** It applies
`abs(v_wheel − v_veh) / v_veh` at all speeds. It is unsigned, so braking and driving
slip are indistinguishable, and it diverges as the vehicle approaches rest
(`vehicle_speed_mph` reaches 5.7e-6). **2.8% of its values exceed 1.0 and are
non-physical.** Use the mode-correct, speed-gated formulation in
`tools/analyze_friction.py` until this column is regenerated.

**MARWIS covers only part of the release.** Road weather telemetry is present on
53.7% of frames, spanning 17 of 49 runs. `marwis_ice_percent` is saturated at 100 for
every reading and carries no information. The loader leaves absent MARWIS values as
`NaN` and exposes a `marwis_valid` mask — do not fill them with 0.0, which reads as
"zero grip."

**Sampling rate varies by session.** The January runs are ~48 Hz and the February 23
runs ~20 Hz; no run is at 25 Hz. Four runs (`jan29-circle-10mph-1`,
`jan29-circle-30mph-1`, `jan29-circle-30mph-2`, and `jan27-downtown-1` in part) have
extended dropouts. Resample from `timestamp_sec` rather than assuming a fixed rate.

**Accelerations include gravity and contain spikes.** Values are in the sensor frame;
median `linear_acceleration_z` is −9.80 m/s². Isolated single-sample outliers reach
−12.8 m/s² (1.3 g), which is unattainable on these surfaces; a 5-sample rolling median
bounds the same run at −4.88 m/s².

**Coverage is uneven.** 13 of the 62 published image packages have no synchronization
CSV (all `jan27-icehighway-*` and `jan27-southcircle-*` runs among them), and
`jan27-downtown-1` is synchronized for 2,294 of its 5,065 frames. `tools/download_wspi.py --list`
marks which runs lack telemetry.

**Run names encode commanded, not achieved, speed.** The median speed of
`jan29-circle-30mph-1` is 17.2 mph. Always use the logged speed.

---

## Python Tools

### 1. Downloading Data
The image packages total roughly **140 GB** across 62 run archives. To list what is
available and fetch a single run (its sync CSV and its images) without pulling
everything:
```bash
python3 tools/download_wspi.py --list
python3 tools/download_wspi.py --run jan27-downtown-1 --dest_dir ./data

# metadata only (a few hundred KB per run)
python3 tools/download_wspi.py --run all_metadata --dest_dir ./data
```

To download the pre-trained lane detection models:
```bash
python3 tools/download_models.py --model all --dest_dir ./models
```

### 2. Loading Aligned Data in PyTorch
Use the PyTorch-compatible `WSPISynchronizedDataset` class in `tools/wspi_loader.py` to easily stream images and physics values during model training:

```python
from tools.wspi_loader import WSPISynchronizedDataset
from torch.utils.data import DataLoader

dataset = WSPISynchronizedDataset(
    metadata_csv_path="metadata/mcity_wspi/jan27-downtown-1_sync.csv",
    images_dir_path="data/mcity_wspi/jan27-downtown-1"
)
dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

for images, physics in dataloader:
    # Get synchronized RTK-GPS trajectory and MARWIS road friction
    coords = physics['gps']                # [Latitude, Longitude, Altitude]
    frictions = physics['marwis_friction'] # Aligned optical road friction (NaN where unlogged)
    valid = physics['marwis_valid']        # Mask on this before using any marwis_* channel
    slips = physics['wheel_slip']          # See caveat above; prefer analyze_friction.py

    # Train physics-informed NeRFs / Gaussian Splatting / friction estimators
```

> [!TIP]
> When training on this data, split by **run**, not by frame. At 20–48 Hz consecutive
> frames are near-duplicates, so a random frame-level split leaks training images into
> validation and inflates accuracy substantially.

### 3. Reproducing the Friction Analysis
`tools/analyze_friction.py` regenerates the dynamics results from the metadata alone —
no image download required. It detects ABS-active braking events, applies the corrected
slip ratio, and compares optical against realized friction:

```bash
python3 tools/analyze_friction.py --metadata_dir metadata/mcity_wspi --out_dir figures
```

Across the 12 straight-line ABS stops that have concurrent MARWIS telemetry, the
friction realized by the vehicle (`|a_x|/g`, 0.269–0.376) exceeds the optical estimate
(0.214–0.278) on **every** event, with a median ratio of **1.34**. The pooled
friction–slip characteristic peaks at μ ≈ 0.29 near a slip ratio of s ≈ 0.16.

---

## Citation

If you use this dataset, please cite the following publications:

> [!IMPORTANT]
> The MI-Snow1000 paper is **still under review**. Do not cite volume, issue, or page
> numbers for it until it is accepted — update this entry at that point.

```bibtex
@unpublished{tye2026misnow1000,
  title={MI-Snow1000: A Comprehensive Dataset and Benchmark for Lane Detection in Adverse Winter Conditions},
  author={Tye, Eugene and Clinton, Catherine and Asher, Zachary and Fong, Alvis},
  note={Manuscript submitted to the SAE International Journal of Connected and Autonomous Vehicles},
  year={2026}
}
```

---

## License
The dataset metadata, scripts, and documentation in this repository are licensed under the [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/) License.
