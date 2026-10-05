"""Minimal example: load and map Food Base LA layers in Python.

Run from the repository root:  python3 examples/example.py
Needs: pip install geopandas pyarrow matplotlib
"""
import sys
sys.path.insert(0, ".")
from load_layer import catalog, load_layer

# 1. See which layers are available
layers = catalog()
print(layers[["layer", "title", "n_features"]].head())

# 2. Load one layer as a GeoDataFrame
tracts = load_layer("Resident_Health_Food_Insecurity_Food_Insecurity_2022")
restaurants = load_layer("Retail_Food_Outlets_Restaurants_Restaurants_2026_March")

# 3. Use it like any other GeoDataFrame
print(tracts.columns.tolist())
print(len(restaurants), "restaurants")

ax = tracts.plot(color="none", edgecolor="lightgrey", figsize=(8, 8))
restaurants.plot(ax=ax, markersize=0.5, color="firebrick")
ax.set_title("Restaurants, March 2026")
ax.figure.savefig("examples/restaurants.png", dpi=100)
