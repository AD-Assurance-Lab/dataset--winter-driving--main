import os
import pandas as pd
import numpy as np
from PIL import Image

try:
    import torch
    from torch.utils.data import Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    Dataset = object

class WSPISynchronizedDataset(Dataset):
    """
    PyTorch-compatible dataset loader for the MCity-WSPI Winter Driving Dataset.
    Loads camera images synchronized with vehicle dynamics, GPS, IMU, and road conditions.
    """
    def __init__(self, metadata_csv_path, images_dir_path, transform=None):
        """
        Args:
            metadata_csv_path (str): Path to the synchronized CSV file (e.g. 'jan27-downtown-1_sync.csv').
            images_dir_path (str): Path to the folder containing raw images for this run.
            transform (callable, optional): Optional transform to be applied on a PIL image.
        """
        self.df = pd.read_csv(metadata_csv_path)
        self.images_dir = images_dir_path
        self.transform = transform
        
        # Fill missing values for numerical fields
        self.numeric_cols = [
            'latitude', 'longitude', 'altitude',
            'orientation_x', 'orientation_y', 'orientation_z', 'orientation_w',
            'angular_velocity_x', 'angular_velocity_y', 'angular_velocity_z',
            'linear_acceleration_x', 'linear_acceleration_y', 'linear_acceleration_z',
            'vehicle_speed_mps', 'vehicle_speed_mph',
            'wheel_speed_fl_rads', 'wheel_speed_fr_rads', 'wheel_speed_rl_rads', 'wheel_speed_rr_rads',
            'wheel_speed_fl_mph', 'wheel_speed_fr_mph', 'wheel_speed_rl_mph', 'wheel_speed_rr_mph',
            'avg_wheel_speed_mph', 'wheel_slip',
            'steering_angle_deg', 'throttle_pedal', 'brake_pedal', 'brake_torque_actual',
            'abs_active', 'esc_active', 'trac_active',
            'marwis_friction', 'marwis_surface_temp_c', 'marwis_ice_percent', 'marwis_water_film_height'
        ]
        self.df[self.numeric_cols] = self.df[self.numeric_cols].apply(pd.to_numeric, errors='coerce')

        # MARWIS telemetry is absent on 46% of frames (32 of 49 runs). These are
        # left as NaN rather than filled: a 0.0 friction reading is a physically
        # meaningful value, so filling would silently train a regressor on
        # "this surface has zero grip" for every unlogged frame. Callers must
        # mask on `marwis_valid` before using any marwis_* channel.
        self.marwis_cols = [c for c in self.numeric_cols if c.startswith('marwis_')]
        self.df['marwis_valid'] = self.df[self.marwis_cols].notna().all(axis=1)

        # Vehicle channels are dense, so a zero fill is safe there.
        vehicle_cols = [c for c in self.numeric_cols if not c.startswith('marwis_')]
        self.df[vehicle_cols] = self.df[vehicle_cols].fillna(0.0)

        self.df['marwis_road_condition'] = self.df['marwis_road_condition'].fillna('unknown')

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        if not HAS_TORCH:
            raise ImportError("PyTorch is required to use this dataset as a PyTorch Dataset.")
            
        row = self.df.iloc[idx]
        image_name = row['image_filename']
        image_path = os.path.join(self.images_dir, image_name)
        
        # Load image
        try:
            image = Image.open(image_path).convert('RGB')
        except FileNotFoundError:
            # Return placeholder/zero tensor if image is missing
            image = Image.new('RGB', (1920, 1080), color=(128, 128, 128))
            
        if self.transform:
            image = self.transform(image)
            
        # Extract physics variables as a dictionary of tensors
        physics = {
            'timestamp_ns': torch.tensor(row['timestamp_ns'], dtype=torch.int64),
            'timestamp_sec': torch.tensor(row['timestamp_sec'], dtype=torch.float32),
            
            # GPS / Pose
            'gps': torch.tensor([row['latitude'], row['longitude'], row['altitude']], dtype=torch.float32),
            'orientation': torch.tensor([row['orientation_x'], row['orientation_y'], row['orientation_z'], row['orientation_w']], dtype=torch.float32),
            
            # IMU. Accelerations are in the sensor frame WITH gravity present
            # (median a_z is -9.80 m/s^2); remove it before treating a_z as ride
            # response. The channels also carry isolated single-sample spikes -
            # see tools/analyze_friction.py for the median filter used.
            'angular_velocity': torch.tensor([row['angular_velocity_x'], row['angular_velocity_y'], row['angular_velocity_z']], dtype=torch.float32),
            'linear_acceleration': torch.tensor([row['linear_acceleration_x'], row['linear_acceleration_y'], row['linear_acceleration_z']], dtype=torch.float32),
            
            # Dynamics
            'speeds': torch.tensor([row['vehicle_speed_mph'], row['avg_wheel_speed_mph']], dtype=torch.float32),
            'wheel_slip': torch.tensor(row['wheel_slip'], dtype=torch.float32),
            'steering_angle_deg': torch.tensor(row['steering_angle_deg'], dtype=torch.float32),
            'controls': torch.tensor([row['throttle_pedal'], row['brake_pedal']], dtype=torch.float32),
            'safety_flags': torch.tensor([row['abs_active'], row['esc_active'], row['trac_active']], dtype=torch.float32),
            
            # MARWIS road condition. NaN where the sensor was not logging;
            # gate on marwis_valid before use.
            'marwis_valid': torch.tensor(bool(row['marwis_valid'])),
            'marwis_friction': torch.tensor(row['marwis_friction'], dtype=torch.float32),
            'marwis_surface_temp_c': torch.tensor(row['marwis_surface_temp_c'], dtype=torch.float32),
            'marwis_ice_percent': torch.tensor(row['marwis_ice_percent'], dtype=torch.float32),
        }

        return image, physics

# Example Usage
if __name__ == '__main__':
    print("WSPI Loader Module successfully defined.")
    if not HAS_TORCH:
        print("Note: PyTorch not found. Running WSPISynchronizedDataset in standalone mode (pandas only).")
    else:
        print("PyTorch integration active.")

    csv_path = os.path.join(os.path.dirname(__file__), "..", "metadata",
                            "mcity_wspi", "jan27-downtown-1_sync.csv")
    if os.path.exists(csv_path):
        dataset = WSPISynchronizedDataset(csv_path, "/dummy/path")
        print("Loaded synchronized CSV with", len(dataset.df), "rows.")
        print("MARWIS valid on", int(dataset.df['marwis_valid'].sum()), "of them.")
        print("Sample row:")
        print(dataset.df.iloc[1000][['image_filename', 'vehicle_speed_mph',
                                     'wheel_slip', 'marwis_road_condition',
                                     'marwis_friction']])
