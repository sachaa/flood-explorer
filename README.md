# 🌊 Flood Explorer — Escobar, Paraguarí, Paraguay

Interactive web app to explore **JRC Global River Flood Hazard Maps v2.1**
for a specific land parcel in Escobar, Paraguarí, Paraguay
(`-25.634, -57.072`).

Built with Streamlit + Google Earth Engine + Folium.

## What it shows

- **6 flood return periods** (10, 20, 50, 100, 200, 500 year)
- **Flood depth** in meters — modelled, not observed
- **90 m resolution** — the highest global flood hazard dataset available free
- **Click-to-sample** — click any point on the map to get the flood depth at that exact location
- **Satellite basemap** — toggle between OpenStreetMap and Google Satellite

## Data source

The [JRC Global River Flood Hazard Maps v2.1](https://developers.google.com/earth-engine/datasets/catalog/JRC_CEMS_GLOFAS_FloodHazard_v2_1)
are produced by the Joint Research Centre of the European Commission,
using GLOFAS (Global Flood Awareness System) hydrological models.

> ⚠️ **Important:** These are **modelled** flood depths, not observed floods.
> The model simulates river flooding from rainfall-runoff and streamflow.
> It does **not** account for:
> - Local drainage or culverts
> - Flash floods from heavy rainfall (pluvial flooding)
> - Groundwater flooding
> - Human modifications (levees, dams, channels)
>
> Always verify with **ground surveys**, local flood history, and
> neighbours' accounts before committing to a land purchase.

## Quick start

### 1. Clone the repo

```bash
git clone git@github.com:saroz/flood-explorer.git
cd flood-explorer
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Google Earth Engine access

You need a Google Earth Engine account. Two options:

#### Option A: Service account (recommended for repeat use)

1. Go to [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)
2. Create a service account
3. Download the JSON key
4. Save it as `ee-service-account.json` in this directory
5. [Register the service account](https://signup.earthengine.google.com/#!/) for Earth Engine access

#### Option B: Personal OAuth (simplest)

1. Sign up at [signup.earthengine.google.com](https://signup.earthengine.google.com)
2. On first run, the app will open a browser window for OAuth
3. Follow the prompts — credentials are cached to `~/.config/earthengine/`

### 5. Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` in your browser.

## How to read the map

| Color | Depth (m) | Meaning |
|-------|-----------|---------|
| Transparent (no blue) | 0.0 | No flooding at this return period |
| Light blue | 0.1 – 0.5 | Shallow flooding — ankle to knee deep |
| Medium blue | 0.5 – 1.0 | Moderate — knee to waist deep |
| Dark blue | 1.0 – 2.0+ | Deep — chest height or higher |

**Return period explained:** A "100-year flood" does **not** mean "once per
century." It means a **1% annual probability** — a 1-in-100 chance in any
given year. Over a 30-year mortgage, that's roughly a **26% chance** of
experiencing at least one such event.

## Customising the location

Edit these variables in `.env` (copy from `.env.example`):

```bash
CENTER_LAT=-25.634
CENTER_LON=-57.072
ZOOM_START=13
```

Or change the coordinates directly in `app.py`.

## Project structure

```
flood-explorer/
├── app.py                    # Main Streamlit app
├── requirements.txt           # Python dependencies
├── .env.example              # Configuration template
├── .gitignore
├── ee-service-account.json   # (optional) GCP service account key
└── README.md                 # This file
```

## FAQ

### Why do I see "No data" when I click some points?

The JRC flood model only covers areas along the river network. If your
point is on high ground far from a mapped watercourse, the model doesn't
produce a flood value there — which is actually **good news**.

### Is this as good as a FEMA flood map?

**No.** FEMA maps are based on detailed local hydrology, surveyed
channel cross-sections, and calibrated hydraulic models. This global dataset
is a first-pass screening tool. For a land purchase decision, you should
supplement it with:
- Local flood history (ask neighbours, local government)
- On-site elevation survey
- Consult a local *escribano* or SEN (Secretaría de Emergencia Nacional)

### Can I use this for any other location?

Yes — the JRC dataset has global coverage. Change the coordinates and
zoom level in the sidebar or `.env` file.

## License

MIT — the app code. The JRC flood hazard data is © European Union and
[freely available for non-commercial use](https://data.jrc.ec.europa.eu).
