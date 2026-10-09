# MARWIS drives around Kalamazoo, winter 2022-23

Twenty-one drives logged with the lab's Lufft MARWIS 10722 mobile road weather sensor between
2022-12-20 and 2023-01-30, during the NSF PFI project. They come before the MCity-WSPI
collection and use the same sensor, so they extend the dataset's road-surface record to
ordinary Kalamazoo roads (latitude 42.19 to 42.54, longitude -85.86 to -85.64). There is no
camera or vehicle data with them.

    hf download AD-Assurance-Lab/winter-driving-dataset --repo-type dataset --include "raw/marwis_kalamazoo_2022-23/*" --local-dir ./data

Each file is one drive as exported by the MARWIS app, named
`MARWIS 10722_<start>-<end>.csv` (local time, `YYYYMMDDhhmmss`). Columns: date, time,
latitude, longitude, altitude, course, speed, dew point (°C), ambient temperature (°C),
ambient relative humidity (%), surface temperature (°C), road condition (Lufft code),
friction, ice percent (%), water film height (µm). 1,972 rows in all, roughly one every
7 to 10 s. `SHA256SUMS` lists the files.

Copies: Hugging Face `raw/marwis_kalamazoo_2022-23/`; the lab's data root
`~/datasets/marwis-kalamazoo-2022-23/`; Google Drive, shared drive "Automated Driving
Assurance Lab", `Finished Projects/2022 NSF PFI Project/Data Collection/Marwis/`.
