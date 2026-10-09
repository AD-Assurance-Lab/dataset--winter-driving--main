# MCity-WSPI raw data: what exists beyond the public release

The public release (Hugging Face `AD-Assurance-Lab/winter-driving-dataset`) holds one PNG per
camera frame, renamed `frame_00000.png` onward per run, and one synchronized CSV per run under
`metadata/mcity_wspi/`. This note records the raw material those were made from, where it is,
and how the two naming schemes map. Written 2026-10-08 after the raw exports were recovered
from the project's Google Drive folder ("2025 - Snow Perception & Control Project"). The
CSV exports, the Jan 20 day and the bag were added to the Hugging Face dataset under
`raw/mcity_wspi/` on 2026-10-09, so everything below except the original-name frames is public:

    hf download AD-Assurance-Lab/winter-driving-dataset --repo-type dataset --include "raw/mcity_wspi/*" --local-dir ./data

## Inventory

| Item | Content | Size | Where |
|---|---|---|---|
| Per-topic CSV exports | For 62 runs over four days (jan27: 15, jan28: 13, jan29: 10, feb23: 24): `oxts_imu`, `oxts_odometry`, `oxts_velocity`, `oxts_nav_sat_fix`, `vehicle_brake_info`, `vehicle_brake_report`, `vehicle_throttle_info`, `vehicle_throttle_report`, `vehicle_steering_report`, `vehicle_wheel_speeds`, `vehicle_wheel_positions`; one `marwis_data.csv` per day for jan27 and jan28 (plus `marwis_data_test2.csv`). Each row is one ROS message with its receive timestamp (ns), the header stamp and every message field flattened | 285 MB, 688 files | Hugging Face `raw/mcity_wspi/csv/<day>/`; Google Drive `MCity Data/<day>_csv`; the lab's data root `~/datasets/mcity-wspi/raw/csv/<day>/`; cold SSD `mcity_wspi/raw/csv/` |
| Jan 20 shakedown day | Two drives (`wmu-jan20-downtown1`, `wmu-jan20-highwaysouth1`) with OxTS CSVs (imu, imu_bias, lever_arm, nav_sat_fix, nav_sat_ref, ncom, odometry), vehicle brake, wheel speeds and positions, a 29 s video, the bag metadata and a topic list | 22 MB | same four places, `raw/jan20/` |
| ROS 2 bag | `wmu-jan20-highwaysouth1_0.db3`: the only bag that survived, 29 s, 68,319 messages, 50 topics including `/arenacam6/images` (1,373 frames), `/oxts/*`, `/vehicle/*` (Dataspeed `ds_dbw_msgs`), `/can_bus_dbw/can_rx` | 3.5 GB | same four places, `raw/bags/` |
| Camera frames with original names | `real_camera_images/wmu-<run>/arenacam6/arenacam6_<timestamp_ns>.png` for the January days and `real_camera_images/feb23-2026_<run>/pylon_camera_<timestamp_ns>.png` for Feb 23; 54,173 files, the same pixels as the public `frame_NNNNN.png` files | 140 GB | Not on Hugging Face under these names (the public frames are the same pixels); Google Drive as four zips (`jan27-camera-images-corrected`, `jan28-camera-images`, `jan29-camera-images`, `feb23-2026-camera-images`); data root `raw/images/<zip name>/` |

The bags for the Jan 27, 28, 29 and Feb 23 runs have not been found anywhere (checked the lab
server, the lab's SSDs and the Drive folder). Only the CSV exports and the camera frames survive.

## Frame naming map

Each public `frame_NNNNN.png` is the raw frame whose capture timestamp is the `timestamp_ns`
column of that row in the run's `_sync.csv`. For example, `jan27-downtown-1/frame_00000.png`
has `timestamp_ns = 1769537064131462650`, and the raw file is
`wmu-jan27-downtown-1/arenacam6/arenacam6_1769537064131462650.png`. Frames are numbered in
timestamp order, so a run without a sync CSV maps by sorted order.

Run names: raw `wmu-jan27-test2` is public `jan27-test-2`; raw `wmu-jan28-northcircle4-no-tc`
is `jan28-northcircle-4-no-tc`; raw `feb23-2026_turn_mainstate_10` is `feb23-turn-mainstate-10`.
Underscores and the `wmu-` and `-2026` parts are the only differences.

## Making the synchronized CSVs again

`tools/wspi_sync.py` reads the per-topic CSVs above and the MARWIS file and writes the
`_sync.csv` files by nearest-timestamp matching. Point it at `raw/csv/<day>/`.
