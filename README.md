# EcoSense Dashboard

EcoSense is a Smart Agriculture / Polyhouse monitoring dashboard built with Python (Flask) and a modern HTML/CSS frontend. It helps users track, analyze, and visualize real-time and historical telemetry (such as temperature and humidity) as well as live camera feeds.

## Overview

The system collects data from multiple IoT sensory modules deployed across different layers of a polyhouse (e.g., Top Layer, Middle Layer, Bottom Layer). It seamlessly integrates with Google services:
- **Google Sheets API**: Retrieves continuous historical and live sensor data.
- **Google Drive API**: Retrieves the latest camera shots to provide real-time visual feedback of crop growth.

### Key Features
- **Interactive Dashboard**: View historical data on interactive modules, calculate daily averages, min/max values, and render chronological temperature & humidity trend charts via `matplotlib`.
- **Live Data Feed**: A separate Live Data view processes distinct remote Google Sheets to present the absolute most recent metrics and daily running averages.
- **Live Camera Pipeline**: Fetches the newest images directly from predetermined Google Drive folders.
- **Performance Optimized**: Includes local LRU caching, disk-based image caching for rendered plots, and a background daemon thread that prevents UI-blocking network load times by prefetching global data asynchronously.

## Project Structure

```text
eco_final/
├── app.py                   # Main Flask backend, route definitions, and data processing
├── sensor_data.csv          # Local backup cache of the global historical dataset
├── service_account.json     # (Required) GCP Service account credentials for APIs
├── requirements.txt         # Python package dependencies
├── templates/
│   └── index.html           # Main frontend layout and UI logic
└── static/
    ├── styles.css           # Vanilla CSS styling
    ├── graphs/              # Locally cached matplotlib visualizations
    └── deepwater/           # Static assets for Deep Water Culture references
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- [Google Cloud Platform Service Account](https://cloud.google.com/iam/docs/service-accounts-create) credentials formatted as `service_account.json` with permissions to read from the specified Google Drive folders.

### 1. Clone & Environment
```bash
# Clone the repository (if applicable)
# cd eco_final

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install pandas  # (If not implicitly listed)
```

### 3. Setup Credentials
Ensure you place your valid Google Service Account key inside the project root and name it exactly `service_account.json`.

### 4. Run the Server
```bash
python3 app.py
```
By default, the application will spin up a background worker thread immediately to start downloading cache data and then host the webserver at `http://localhost:5000`.

## Architecture Details
- **Threading**: `app.py` employs a lightweight background thread (`background_update_task`) to synchronize the primary Google Sheet into `sensor_data.csv` every 5 minutes, significantly speeding up route response times.
- **Graph Caching**: To minimize redundant matplotlib processing, graphs are deterministically cached to the disk (`/static/graphs/`) utilizing the date and hardware module as unique keys.
- **Frontend Logic**: Single Page Application (SPA) feel achieved through pure JavaScript dynamically swapping visibility tabs (`#dashboard`, `#live-data`, `#camera`) without hard reloads.

## Environment Variables / Config Constants
Inside `app.py`, you'll find top-level variables controlling the API targets:
- `SHEET_ID`: Target historical Google Sheet IDs.
- `DRIVE_FOLDER_ID`: Default drive folder string for camera APIs.
*(You can modify these variables in `app.py` to point to a different greenhouse deployment).*
