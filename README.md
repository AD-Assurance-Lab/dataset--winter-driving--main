# AD Winter Driving Dataset: Multimodal Perception & Physics

This repository hosts the metadata, documentation, loaders, and synchronization tools for the **AD Winter Driving Dataset**, a joint effort between the **AD Assurance Lab**, **Western Michigan University**, and **MCity**. 

The dataset is divided into two core modules:
1. **Module 1: REVA Perception (MI-Snow1000)**: A lane detection and semantic road understanding benchmark featuring 4,888 manually annotated lanes in TuSimple format, captured across 1,000 miles of winter driving in Michigan, Colorado, and Wyoming.
2. **Module 2: MCity-WSPI Physics**: Time-synchronized front-camera frames (25Hz) aligned directly with vehicle dynamics (CAN bus steering, wheel speeds, brake torque), high-grade IMU response (rotational rates, linear acceleration including vertical ride response), GPS/RTK trajectories, and mobile road weather information (MARWIS) optical surface parameters (friction coefficient, pavement temperature, ice percent, water film height).

---

## Repository Structure

```directory/
winter-driving-dataset/
├── docs/                     # Documentation landing page (hosted on GitHub Pages)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── metadata/                 # Synchronized master CSV telemetry files for MCity runs
│   ├── wmu-jan27-downtown-1_sync.csv
│   ├── feb23-2026_straight_10_sync.csv
│   └── ... (49 runs total)
├── tools/                    # Python loader and sync scripts
│   ├── download_wspi.py      # CLI tool to download raw image zip files and bags
│   ├── wspi_sync.py          # CLI tool to perform nearest-neighbor sensor synchronization
│   └── wspi_loader.py        # PyTorch-compatible dataset loader
├── README.md
├── LICENSE                   # Creative Commons Attribution 4.0 International
└── .gitignore
```

---

## Aligned Physics Variables

Each row in the synchronized metadata CSVs under `metadata/` matches a single camera frame (named with its nanosecond Epoch timestamp) to the temporally nearest telemetry signals. Key variables include:

| Group | Column Name | Source Sensor | Description |
| :--- | :--- | :--- | :--- |
| **Image** | `image_filename` | Windshield Camera | Name of the PNG image frame. |
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
python3 tools/download_wspi.py --run wmu-jan27-downtown-1_images --dest_dir ./data
```

### 2. Loading Aligned Data in PyTorch
Use the PyTorch-compatible `WSPISynchronizedDataset` class in `tools/wspi_loader.py` to easily stream images and physics values during model training:

```python
from tools.wspi_loader import WSPISynchronizedDataset
from torch.utils.data import DataLoader

dataset = WSPISynchronizedDataset(
    metadata_csv_path="metadata/wmu-jan27-downtown-1_sync.csv",
    images_dir_path="data/wmu-jan27-downtown-1/arenacam6"
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

If you use this dataset, please cite the following publications:

```bibtex
@article{tye2026misnow1000,
  title={MI-Snow1000: A Comprehensive Dataset and Benchmark for Lane Detection in Adverse Winter Conditions},
  author={Tye, Eugene and Clinton, Catherine  and Asher, Zachary and Fong, Alvis},
  journal={SAE International Journal of Connected and Autonomous Vehicles},
  volume={9},
  number={2},
  pages={112--128},
  year={2026},
  publisher={SAE International}
}
```

---

## License
The dataset metadata, scripts, and documentation in this repository are licensed under the [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/) License.
