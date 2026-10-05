"""Convert the GeoJSON files in data/ to compressed GeoParquet files in parquet/.

Usage: python3 convert_to_parquet.py
Needs: pip install geopandas pyarrow
"""
import glob, os
import geopandas as gpd

HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "parquet"), exist_ok=True)
for f in sorted(glob.glob(os.path.join(HERE, "data", "*.geojson"))):
    out = os.path.join(HERE, "parquet", os.path.basename(f)[:-len(".geojson")] + ".parquet")
    if os.path.exists(out):
        continue
    gpd.read_file(f).to_parquet(out, compression="zstd")
    print(f"{os.path.getsize(out) / 1e6:7.1f} MB  {os.path.basename(out)}")
