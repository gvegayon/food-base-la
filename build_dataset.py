"""Build the compact dataset in data/ from the raw GeoJSON downloads in raw/.

Most layers in Food Base LA reuse the exact same shapes (e.g., the 2020 census
tracts), so instead of repeating them in every file we store:

  data/geometries/<set>.parquet   each distinct set of shapes once (GeoParquet), keyed by geom_id
  data/attributes/<layer>.parquet one table per layer (no shapes), with a geom_id column
  data/catalog.csv                one row per layer: which attribute file goes with which geometry file

Joining a layer's attributes to its geometry set on geom_id gives back the
original layer exactly. See load_layer.py / load_layer.R.

Usage: python3 build_dataset.py
Needs: pip install geopandas pyarrow
"""
import csv, glob, hashlib, json, os, re
import geopandas as gpd
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(os.path.join(DATA, "geometries"), exist_ok=True)
os.makedirs(os.path.join(DATA, "attributes"), exist_ok=True)

def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:120]

def leaves(layers, path):
    for l in layers:
        if l.get("layers"):
            yield from leaves(l["layers"], path + [l.get("title", "")])
        else:
            yield path, l

webmap = json.load(open(os.path.join(HERE, "webmap.json")))
geom_sets = {}  # hash of the set of shapes -> geometry file name
catalog = []

for path, l in leaves(webmap["operationalLayers"], []):
    layer = slug("__".join(path + [l.get("title", "")]))
    gdf = gpd.read_file(os.path.join(HERE, "raw", layer + ".geojson"))
    wkb = gdf.geometry.to_wkb()

    # The distinct shapes in this layer, in a fixed order, identify its geometry set
    shapes = sorted(set(w for w in wkb if w is not None))
    key = hashlib.sha1(b"".join(shapes)).hexdigest()
    if key not in geom_sets:
        gtype = gdf.geom_type.dropna().iloc[0].lower() if gdf.geom_type.notna().any() else "none"
        name = f"{gtype}_{len(shapes)}_{key[:8]}.parquet"
        gpd.GeoDataFrame({"geom_id": range(len(shapes))},
                         geometry=gpd.GeoSeries.from_wkb(shapes, crs=gdf.crs)
                         ).to_parquet(os.path.join(DATA, "geometries", name), compression="zstd")
        geom_sets[key] = name

    ids = {w: i for i, w in enumerate(shapes)}
    attrs = pd.DataFrame(gdf.drop(columns="geometry"))
    # Store all-empty text columns as strings (otherwise Parquet writes an untyped "null" column)
    for c in attrs.columns[(attrs.dtypes == object) & attrs.isna().all()]:
        attrs[c] = attrs[c].astype("string")
    attrs.insert(0, "geom_id", pd.array([ids.get(w) if w is not None else None for w in wkb], dtype="Int32"))
    attrs.to_parquet(os.path.join(DATA, "attributes", layer + ".parquet"), compression="zstd", index=False)

    catalog.append({"layer": layer, "group": " / ".join(path), "title": l.get("title", ""),
                    "n_features": len(gdf), "attributes_file": layer + ".parquet",
                    "geometry_file": geom_sets[key], "source_url": l.get("url", "")})
    print(f"{len(gdf):>7}  {geom_sets[key]:<36} {layer}", flush=True)

with open(os.path.join(DATA, "catalog.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, catalog[0].keys())
    w.writeheader()
    w.writerows(catalog)
print(f"\n{len(catalog)} layers, {len(geom_sets)} geometry sets")
