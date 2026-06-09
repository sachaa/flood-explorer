"""Diagnostic: sample JRC flood data at the target coordinates."""
import os
from pathlib import Path

from dotenv import load_dotenv

import ee

load_dotenv()
project = os.getenv("EE_PROJECT", "")

# Reuse your existing credentials
try:
    kwargs = {}
    if project:
        kwargs["project"] = project
    ee.Initialize(**kwargs)
    print(f"✅ EE initialized (project: {project or 'default'})\n")
except Exception as e:
    print(f"❌ EE init failed: {e}")
    exit(1)

col = ee.ImageCollection("JRC/CEMS_GLOFAS/FloodHazard/v2_1")
img = col.first()

# List all bands available
print("Bands in dataset:", img.bandNames().getInfo())
print()

# Sample at user's coordinates
LAT, LON = -25.634023, -57.072363
point = ee.Geometry.Point(LON, LAT)

for band in ["RP10_depth", "RP50_depth", "RP75_depth", "RP100_depth", "RP200_depth", "RP500_depth"]:
    try:
        val = img.select(band).reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=90,
            maxPixels=1,
        ).get(band).getInfo()
        if val is not None:
            print(f"  {band}: {val:.2f} m")
        else:
            print(f"  {band}: null — no river modelled at this point")
    except Exception as ex:
        print(f"  {band}: ERROR — {ex}")

# Also try sampling nearby points in a small radius
print("\n--- Sampling nearby points (100m radius) ---")
for offset_lat, offset_lon in [(0.001, 0), (-0.001, 0), (0, 0.001), (0, -0.001)]:
    p = ee.Geometry.Point(LON + offset_lon, LAT + offset_lat)
    val = img.select("RP100_depth").reduceRegion(
        reducer=ee.Reducer.first(), geometry=p, scale=90, maxPixels=1
    ).get("RP100_depth").getInfo()
    print(f"  ({LAT+offset_lat:.5f}, {LON+offset_lon:.5f}): {val}")

# Check tile URL validity
print("\n--- Tile URL check ---")
viz = img.select("RP100_depth").visualize(
    min=0.0, max=2.0,
    palette=["#ffffff00", "#cce5ff", "#99c2ff", "#6699ff", "#3366ff", "#0033cc"],
)
map_id = viz.getMapId()
print(f"MapID: {map_id['mapid']}")
print(f"Token: {map_id['token'][:20]}...")
print(f"Tile URL: {map_id['tile_fetcher'].url_format[:80]}...")
print("✅ Tile URL generated successfully")
