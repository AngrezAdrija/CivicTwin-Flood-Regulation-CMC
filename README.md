# CivicTwin: AI-Enabled Digital Twin for Predictive Urban Infrastructure Resilience

A React & Leaflet spatial digital twin platform for real-time urban drainage monitoring, storm simulation, and dynamic flood risk assessment.

## Key Features

* **Dynamic Risk Engine:** Recalculates conduit flood risk dynamically based on real-time rainfall intensity controls ($20\text{ mm/hr}$ to $200\text{ mm/hr}$).
* **Spatial Mapping:** Renders PostGIS drainage geometries on an interactive Leaflet map with dynamic threat-based color coding.
* **OpenStreetMap Geocoding:** Converts human-readable address entries into geographic coordinates automatically.
* **Maintenance & Queue System:** Supports work-ticket dispatching and "what-if" desilting simulations to evaluate systemic risk reduction.

## Tech Stack

* **Frontend:** React, React-Leaflet, Lucide Icons
* **GIS Backend:** PostGIS, OpenStreetMap Nominatim API

## Getting Started

1. Clone the repository:
   ```bash
   git clone [https://github.com/AngrezAdrija/CivicTwin-Flood-regulation-for-CMC-area.git](https://github.com/AngrezAdrija/CivicTwin-Flood-regulation-for-CMC-area.git)
