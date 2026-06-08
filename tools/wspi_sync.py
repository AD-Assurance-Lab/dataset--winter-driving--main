import os
import glob
import csv
import bisect
import argparse
from datetime import datetime, timedelta

def local_time_to_epoch_ns(local_time_str):
    try:
        dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    # EST is UTC-5, so add 5 hours for UTC
    utc_dt = dt + timedelta(hours=5)
    epoch_sec = (utc_dt - datetime(1970, 1, 1)).total_seconds()
    return int(epoch_sec * 1e9)

def load_csv_data(filepath, key_columns):
    if not os.path.exists(filepath):
        return []
    
    rows = []
    with open(filepath, mode='r') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return []
            
        indices = {}
        for k, col in key_columns.items():
            if col in header:
                indices[k] = header.index(col)
        
        for r in reader:
            if r and len(r) > max(indices.values(), default=-1):
                try:
                    ts = int(r[0])
                    row_data = {"timestamp": ts}
                    for k, idx in indices.items():
                        val = r[idx]
                        try:
                            row_data[k] = float(val)
                        except ValueError:
                            if val.lower() == 'true':
                                row_data[k] = 1.0
                            elif val.lower() == 'false':
                                row_data[k] = 0.0
                            else:
                                row_data[k] = val
                    rows.append(row_data)
                except ValueError:
                    continue
    rows.sort(key=lambda x: x["timestamp"])
    return rows

def load_marwis_data(csv_root_path, filenames):
    rows = []
    for fn in filenames:
        path = os.path.join(csv_root_path, fn)
        if os.path.exists(path):
            with open(path, mode='r') as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                except StopIteration:
                    continue
                
                cols = ['road_condition', 'friction', 'surface_temp', 'ice_percent', 'water_film_height']
                indices = {}
                for c in cols:
                    if c in header:
                        indices[c] = header.index(c)
                
                for r in reader:
                    if r:
                        ts_ns = local_time_to_epoch_ns(r[0])
                        if ts_ns:
                            row_data = {"timestamp": ts_ns}
                            for c, idx in indices.items():
                                val = r[idx]
                                try:
                                    row_data[c] = float(val)
                                except ValueError:
                                    row_data[c] = val
                            rows.append(row_data)
    rows.sort(key=lambda x: x["timestamp"])
    return rows

def find_nearest(sorted_rows, target_ts):
    if not sorted_rows:
        return {}
    timestamps = [r["timestamp"] for r in sorted_rows]
    idx = bisect.bisect_left(timestamps, target_ts)
    if idx == 0:
        return sorted_rows[0]
    if idx == len(sorted_rows):
        return sorted_rows[-1]
    
    before = sorted_rows[idx-1]
    after = sorted_rows[idx]
    if target_ts - before["timestamp"] <= after["timestamp"] - target_ts:
        return before
    else:
        return after

def main():
    parser = argparse.ArgumentParser(description="Synchronize camera images with vehicle telemetry CSVs.")
    parser.add_argument("--images_dir", required=True, help="Path to the directory containing raw camera images for a run.")
    parser.add_argument("--csv_dir", required=True, help="Path to the folder containing telemetry CSVs.")
    parser.add_argument("--run_name", required=True, help="Name of the run (e.g. 'jan27-downtown-1').")
    parser.add_argument("--marwis_files", nargs="*", default=[], help="Filenames of MARWIS CSV files in the csv_dir.")
    parser.add_argument("--output_file", required=True, help="Path to save the output synchronized CSV.")
    parser.add_argument("--tire_radius", type=float, default=0.363, help="Tire radius in meters (default: 0.363m).")
    
    args = parser.parse_args()
    
    # 1. Find images
    png_files = glob.glob(os.path.join(args.images_dir, "**", "*.png"), recursive=True)
    if not png_files:
        print(f"Error: No PNG images found in {args.images_dir}")
        return
        
    image_list = []
    for pf in png_files:
        filename = os.path.basename(pf)
        parts = filename.split('_')
        if parts:
            ts_part = parts[-1].split('.')[0]
            if ts_part.isdigit():
                image_list.append((int(ts_part), filename))
                
    image_list.sort()
    print(f"Loaded {len(image_list)} camera image frames.")
    
    # 2. Load MARWIS if specified
    marwis_data = load_marwis_data(args.csv_dir, args.marwis_files)
    if marwis_data:
        print(f"Loaded {len(marwis_data)} MARWIS weather sensor entries.")
        
    # 3. Load other CSVs
    prefix = args.run_name
    
    def find_csv_path(suffix):
        paths = [
            os.path.join(args.csv_dir, f"{prefix}{suffix}"),
            os.path.join(args.csv_dir, f"{prefix.replace('downtown-', 'downtown')}{suffix}"),
            os.path.join(args.csv_dir, f"{prefix.replace('downtown', 'downtown-')}{suffix}"),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return paths[0]
        
    imu_path = find_csv_path("_oxts_imu.csv")
    gps_path = find_csv_path("_oxts_nav_sat_fix.csv")
    odo_path = find_csv_path("_oxts_odometry.csv")
    wheel_path = find_csv_path("_vehicle_wheel_speeds.csv")
    brake_path = find_csv_path("_vehicle_brake_info.csv")
    steering_path = find_csv_path("_vehicle_steering_report.csv")
    throttle_path = find_csv_path("_vehicle_throttle_report.csv")
    if not os.path.exists(throttle_path):
        throttle_path = find_csv_path("_vehicle_throttle_info.csv")
        
    imu_data = load_csv_data(imu_path, {
        "orientation_x": "_orientation._x", "orientation_y": "_orientation._y", "orientation_z": "_orientation._z", "orientation_w": "_orientation._w",
        "ang_vel_x": "_angular_velocity._x", "ang_vel_y": "_angular_velocity._y", "ang_vel_z": "_angular_velocity._z",
        "lin_accel_x": "_linear_acceleration._x", "lin_accel_y": "_linear_acceleration._y", "lin_accel_z": "_linear_acceleration._z"
    })
    
    gps_data = load_csv_data(gps_path, {
        "latitude": "_latitude", "longitude": "_longitude", "altitude": "_altitude"
    })
    
    odo_data = load_csv_data(odo_path, {
        "lin_vel_x": "_twist._twist._linear._x", "lin_vel_y": "_twist._twist._linear._y", "lin_vel_z": "_twist._twist._linear._z"
    })
    
    wheel_data = load_csv_data(wheel_path, {
        "wheel_speed_fl": "_front_left", "wheel_speed_fr": "_front_right", "wheel_speed_rl": "_rear_left", "wheel_speed_rr": "_rear_right"
    })
    
    brake_data = load_csv_data(brake_path, {
        "brake_pedal": "_brake_torque_pedal", "brake_torque_actual": "_brake_torque_actual",
        "abs_active": "_abs_active", "esc_active": "_esc_active", "trac_active": "_trac_active"
    })
    
    steering_data = load_csv_data(steering_path, {
        "steering_angle": "_steering_wheel_angle"
    })
    
    throttle_data = load_csv_data(throttle_path, {
        "throttle_pedal": "_percent_input" if "report" in throttle_path else "_throttle_pedal"
    })
    
    print(f"Loaded sensor streams: IMU ({len(imu_data)}), GPS ({len(gps_data)}), Odo ({len(odo_data)}), Wheel ({len(wheel_data)}).")
    
    # 4. Synchronize
    sync_rows = []
    M_S_TO_MPH = 2.23694
    
    for ts, filename in image_list:
        imu_row = find_nearest(imu_data, ts)
        gps_row = find_nearest(gps_data, ts)
        odo_row = find_nearest(odo_data, ts)
        whl_row = find_nearest(wheel_data, ts)
        brk_row = find_nearest(brake_data, ts)
        str_row = find_nearest(steering_data, ts)
        thr_row = find_nearest(throttle_data, ts)
        mrw_row = find_nearest(marwis_data, ts)
        
        veh_speed_mps = odo_row.get("lin_vel_x", 0.0)
        veh_speed_mph = abs(veh_speed_mps) * M_S_TO_MPH
        
        fl_rads = whl_row.get("wheel_speed_fl", 0.0)
        fr_rads = whl_row.get("wheel_speed_fr", 0.0)
        rl_rads = whl_row.get("wheel_speed_rl", 0.0)
        rr_rads = whl_row.get("wheel_speed_rr", 0.0)
        
        fl_mph = abs(fl_rads) * args.tire_radius * M_S_TO_MPH
        fr_mph = abs(fr_rads) * args.tire_radius * M_S_TO_MPH
        rl_mph = abs(rl_rads) * args.tire_radius * M_S_TO_MPH
        rr_mph = abs(rr_rads) * args.tire_radius * M_S_TO_MPH
        
        avg_wheel_speed_mph = (fl_mph + fr_mph + rl_mph + rr_mph) / 4.0
        wheel_slip = abs(avg_wheel_speed_mph - veh_speed_mph) / veh_speed_mph if veh_speed_mph > 1.0 else 0.0
        
        row_dict = {
            "image_filename": filename,
            "timestamp_ns": ts,
            "timestamp_sec": ts / 1e9,
            "latitude": gps_row.get("latitude", ""),
            "longitude": gps_row.get("longitude", ""),
            "altitude": gps_row.get("altitude", ""),
            "orientation_x": imu_row.get("orientation_x", ""),
            "orientation_y": imu_row.get("orientation_y", ""),
            "orientation_z": imu_row.get("orientation_z", ""),
            "orientation_w": imu_row.get("orientation_w", ""),
            "angular_velocity_x": imu_row.get("ang_vel_x", ""),
            "angular_velocity_y": imu_row.get("ang_vel_y", ""),
            "angular_velocity_z": imu_row.get("ang_vel_z", ""),
            "linear_acceleration_x": imu_row.get("lin_accel_x", ""),
            "linear_acceleration_y": imu_row.get("lin_accel_y", ""),
            "linear_acceleration_z": imu_row.get("lin_accel_z", ""),
            "vehicle_speed_mps": veh_speed_mps,
            "vehicle_speed_mph": veh_speed_mph,
            "wheel_speed_fl_rads": fl_rads,
            "wheel_speed_fr_rads": fr_rads,
            "wheel_speed_rl_rads": rl_rads,
            "wheel_speed_rr_rads": rr_rads,
            "wheel_speed_fl_mph": fl_mph,
            "wheel_speed_fr_mph": fr_mph,
            "wheel_speed_rl_mph": rl_mph,
            "wheel_speed_rr_mph": rr_mph,
            "avg_wheel_speed_mph": avg_wheel_speed_mph,
            "wheel_slip": wheel_slip,
            "steering_angle_deg": str_row.get("steering_angle", ""),
            "throttle_pedal": thr_row.get("throttle_pedal", ""),
            "brake_pedal": brk_row.get("brake_pedal", ""),
            "brake_torque_actual": brk_row.get("brake_torque_actual", ""),
            "abs_active": brk_row.get("abs_active", 0.0),
            "esc_active": brk_row.get("esc_active", 0.0),
            "trac_active": brk_row.get("trac_active", 0.0),
            "marwis_road_condition": mrw_row.get("road_condition", "") if mrw_row and abs(ts - mrw_row["timestamp"]) < 5e9 else "",
            "marwis_friction": mrw_row.get("friction", "") if mrw_row and abs(ts - mrw_row["timestamp"]) < 5e9 else "",
            "marwis_surface_temp_c": mrw_row.get("surface_temp", "") if mrw_row and abs(ts - mrw_row["timestamp"]) < 5e9 else "",
            "marwis_ice_percent": mrw_row.get("ice_percent", "") if mrw_row and abs(ts - mrw_row["timestamp"]) < 5e9 else "",
            "marwis_water_film_height": mrw_row.get("water_film_height", "") if mrw_row and abs(ts - mrw_row["timestamp"]) < 5e9 else "",
        }
        sync_rows.append(row_dict)
        
    # Write output CSV
    os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)
    with open(args.output_file, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sync_rows[0].keys())
        writer.writeheader()
        writer.writerows(sync_rows)
        
    print(f"Successfully saved synchronized data to {args.output_file}")

if __name__ == '__main__':
    main()
