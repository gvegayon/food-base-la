"""Load Food Base LA layers in Python.

    from load_layer import catalog, load_layer
    catalog()                       # list of all 245 layers
    gdf = load_layer("Retail_Food_Outlets_Restaurants_Restaurants_2026_March")

Needs: pip install geopandas pyarrow
"""
from pathlib import Path
import geopandas as gpd
import pandas as pd

DATA = Path(__file__).parent / "data"

def catalog():
    """Table of all layers (name, group, title, number of features, files)."""
    return pd.read_csv(DATA / "catalog.csv")

def load_layer(layer):
    """Return one layer as a GeoDataFrame (EPSG:4326)."""
    info = catalog().set_index("layer").loc[layer]
    attrs = pd.read_parquet(DATA / "attributes" / info["attributes_file"])
    shapes = gpd.read_parquet(DATA / "geometries" / info["geometry_file"])
    gdf = attrs.merge(shapes, on="geom_id", how="left").drop(columns="geom_id")
    return gpd.GeoDataFrame(gdf, geometry="geometry", crs=shapes.crs)
