# AD Winter Driving Dataset: MI-Snow1000 Lane Detection and MCity-WSPI Physics

This repository hosts the metadata, documentation, loaders, and synchronization tools for the **AD Winter Driving Dataset**, a joint effort between the **AD Assurance Lab**, **Western Michigan University**, and **MCity**. 

The dataset is divided into two core modules:
1. **Module 1: MI-Snow1000 lane detection**: 4,888 dashcam frames (1280x720) from over 1,000 miles of winter driving in Michigan, Colorado and Wyoming, each annotated with the left and right boundaries of the ego lane in TuSimple format. Where snow buries the paint, the boundaries follow the drivable corridor shown by tire tracks and plow lines. See [MI-Snow1000](#mi-snow1000-lane-detection) below.
2. **Module 2: MCity-WSPI Physics**: Time-synchronized front-camera frames (25Hz) aligned directly with vehicle dynamics (CAN bus steering, wheel speeds, brake torque), high-grade IMU response (rotational rates, linear acceleration including vertical ride response), GPS/RTK trajectories, and mobile road weather information (MARWIS) optical surface parameters (friction coefficient, pavement temperature, ice percent, water film height).

---

## Repository Structure

```directory/
winter-driving-dataset/
├── docs/                     # Documentation landing page (hosted on GitHub Pages)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── metadata/                 # Tabular metadata and annotations
│   ├── reva_perception/      # Module 1: train.json, val.json, test.json (frame-level split)
│   ├── sequence_disjoint/    # Module 1: train.json, val.json, test.json (benchmark split)
│   ├── sequence_disjoint_split.json  # How the benchmark split was built
│   ├── condition_tags.json   # Module 1: per-frame curvature, glare, snow severity tags
│   └── mcity_wspi/           # Module 2: jan27-downtown-1_sync.csv, ...
├── models/                   # Pre-trained lane detection benchmark checkpoints
│   ├── README.md             # Model info and Hugging Face weights download links
│   ├── onnx/                 # (Local only) ONNX .onnx checkpoints
│   └── pytorch/              # (Local only) PyTorch .pt / .pth checkpoints
├── tools/                    # Python loader and sync scripts
│   ├── download_wspi.py      # CLI tool to download raw image zips
│   ├── download_models.py    # CLI tool to download pre-trained benchmarks
│   ├── wspi_sync.py          # CLI tool to perform nearest-neighbor sensor synchronization
│   └── wspi_loader.py        # PyTorch-compatible dataset loader
├── README.md
├── LICENSE                   # Creative Commons Attribution 4.0 International
└── .gitignore
```

---

## MI-Snow1000 Lane Detection

MI-Snow1000 is a lane detection dataset for snow-covered roads. Each of its 4,888 frames carries at most two lanes, the left and right boundaries of the ego lane, in TuSimple format: one JSON object per line, where `raw_file` names the frame, `h_samples` lists 56 image rows from 160 to 710, and `lanes` gives one x position per row for each boundary, with -2 where the boundary is absent.

**Frames with no lane boundaries are intentional.** Where the annotators judged that no boundary could be placed with confidence, for example on a fully snow-covered road with no tracks, the frame was kept with no lanes labeled, so that a detector learns to output nothing rather than guess. These are 535 of the 4,888 frames (11%). Treat them as frames whose correct output is no lane, not as missing labels.

| Split | Train | Validation | Test | Use |
|---|---|---|---|---|
| `metadata/sequence_disjoint/` | 3,105 | 887 | 337 | The benchmark split. No drive is shared between partitions, and test frames showing the same place as a training frame are removed. |
| `metadata/reva_perception/` | 3,421 | 977 | 490 | Frame-level random split. Neighboring frames of one drive fall on both sides, so use the benchmark split to measure accuracy on roads not seen in training. |

Per-frame condition tags (curvature, glare, snow severity, single boundary) are in `metadata/condition_tags.json`; its `split` field refers to the frame-level split. The checkpoints listed in [`models/README.md`](models/README.md) are trained on the training partition of the benchmark split. The images, scoring scripts and per-seed predictions behind the paper's tables are released on Zenodo with the paper.

```python
import json

records = [json.loads(line) for line in open("metadata/sequence_disjoint/test.json")]
for r in records:
    image_path = r["raw_file"]        # reva_perception/labeled_set/images/frame_NNNNN.jpg
    rows = r["h_samples"]
    lanes = [[(x, y) for x, y in zip(lane, rows) if x >= 0] for lane in r["lanes"]]
    lanes = [l for l in lanes if len(l) >= 2]   # empty list: the correct output is no lane
```

To ask for an image to be removed, for example one that shows your face or license plate, open an issue on this repository with the frame name.

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
| **Physics**| `wheel_slip` | Calculated | Physically correct slip ratio: `abs(wheel_speed_mph - vehicle_speed_mph) / vehicle_speed_mph`. |
| **Control**| `steering_angle_deg` | Vehicle CAN | Steering wheel angle in degrees. |
| **Control**| `throttle_pedal`, `brake_pedal` | Vehicle CAN | Driver inputs (0.0 to 1.0). |
| **Safety** | `abs_active`, `esc_active`, `trac_active` | Vehicle CAN | Binary safety system activation flags. |
| **Road** | `marwis_road_condition` | MARWIS Sensor | Surface classification (dry, wet, snow, ice covered). |
| **Road** | `marwis_friction` | MARWIS Sensor | Optical road friction estimation coefficient (0.0 to 1.0). |

> [!NOTE]
> **Corrected Wheel Slip Units**: Prior studies (e.g., student class projects) incorrectly assumed vehicle wheel speed logs were in RPM. We verified they are recorded in **radians per second (rad/s)**. Using a standard Ford Mustang Mach-E tire radius ($R \approx 0.363$m), tire speed is computed as $v = \omega \cdot R$. This repository implements the physically correct slip ratio, eliminating the heavy skew present in earlier revisions.

---

## Python Tools

### 1. Downloading Data
To download specific run packages (e.g., raw images or bags) without fetching the entire 85 GB dataset, use the download utility:
```bash
python3 tools/download_wspi.py --run jan27-downtown-1_images --dest_dir ./data
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
    coords = physics['gps']              # [Latitude, Longitude, Altitude]
    frictions = physics['marwis_friction'] # Aligned optical road friction
    slips = physics['wheel_slip']        # Calculated tire slip ratio
    
    # Train physics-informed NeRFs / Gaussian Splatting / friction estimators
```

---

## Citation

If you use MI-Snow1000, please cite:

```bibtex
@misc{tye2026misnow1000,
  title={MI-Snow1000: A Comprehensive Dataset and Benchmark for Lane Detection in Adverse Winter Conditions},
  author={Tye, Eugene and Fanas Rojas, Johan and Masterson, Alex and Kadav, Parth and Hong, Guan Yue and Asher, Zachary D.},
  year={2026},
  note={Manuscript under review}
}
```

---

## License
The dataset metadata, scripts, and documentation in this repository are licensed under the [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/) License.
