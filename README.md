# Food Base LA: data and configuration export

This repository extracts the data and configuration behind the **Food Base LA** Food Systems Dashboard so it can be reused outside ArcGIS (R, Python, QGIS, Leaflet/MapLibre, Shiny, etc.).

- Live app: <https://experience.arcgis.com/experience/a4daa72b157b4b969a058909cef387cd/page/Dashboard>
- Built with ArcGIS Experience Builder by the USC Spatial Sciences Institute for the Los Angeles County Office of Food Systems (ArcGIS Online owner: `uscssi_research`).

## How the app is put together

An Experience Builder site has no custom source code. It's a set of settings stored as JSON items in ArcGIS Online, all publicly readable through the ArcGIS REST API:

1. **The Experience** (item `a4daa72b157b4b969a058909cef387cd`) holds the pages, layout, text, buttons, theme and widgets. There are 4 pages and 141 widgets.
2. **The web map** (item `2bc29891fc744b62b57de017897583e0`) holds the layer tree, symbology (renderers and class breaks), popups, basemap and extent. It contains **245 layers** in groups such as Food Assistance and Benefits, Retail Food Outlets, Resident Health and Resident Demographics.
3. **The data** lives in 192 hosted feature services: 178 polygon layers (mostly 2020 census tracts) and 67 point layers (restaurants, markets, CalFresh, WIC, farmers' markets). That's about 1 million features in total.

## What was extracted and how

| File | Contents | How it was obtained |
|---|---|---|
| `item.json` | App metadata (description, credits, tags) | `GET https://www.arcgis.com/sharing/rest/content/items/<id>?f=json` |
| `experience_config.json` | Full Experience Builder app definition | `GET .../content/items/a4daa72b157b4b969a058909cef387cd/data?f=json` |
| `webmap.json` | Full web map definition, including styles and popups | `GET .../content/items/2bc29891fc744b62b57de017897583e0/data?f=json` |
| `layers.csv` | Inventory of all 245 layers: group, title, geometry type, feature count, REST URL, item ID | Generated from `webmap.json` plus a `returnCountOnly` query to each layer |
| `export_layers.py` | Downloads every layer's features and styling | See below |
| `convert_to_parquet.py` | Converts the downloaded GeoJSON to compressed GeoParquet | See below |

Commands used to fetch the metadata:

```bash
curl -s "https://www.arcgis.com/sharing/rest/content/items/a4daa72b157b4b969a058909cef387cd?f=json" -o item.json
curl -s "https://www.arcgis.com/sharing/rest/content/items/a4daa72b157b4b969a058909cef387cd/data?f=json" -o experience_config.json
curl -s "https://www.arcgis.com/sharing/rest/content/items/2bc29891fc744b62b57de017897583e0/data?f=json" -o webmap.json
```

### Downloading the data

`export_layers.py` walks the layer tree in `webmap.json`. For each layer it:

- pages through the layer's `/query` endpoint (`where=1=1`, all fields, output in WGS84 / EPSG:4326) and saves a GeoJSON file to `data/`;
- saves the layer's styling to `styles/`, as a JSON file with the renderer (`drawingInfo`), popup configuration and field definitions. Overrides set in the web map take precedence over the service defaults.

It needs only the Python standard library:

```bash
python3 export_layers.py                 # everything, 8 layers at a time
python3 export_layers.py --only "SVI"    # only layers whose title contains "SVI"
python3 export_layers.py --workers 4     # change the number of parallel downloads
```

Rerunning the script skips layers that are already downloaded, so an interrupted run can be resumed. Files are written atomically, so a stopped run never leaves a partial file.

### Converting to GeoParquet

```bash
pip install geopandas pyarrow
python3 convert_to_parquet.py
```

GeoParquet with zstd compression is about 28% the size of GeoJSON. It can be read with `geopandas.read_parquet()` in Python, `sfarrow`/`geoarrow` or `arrow` + `sf` in R, DuckDB, and QGIS 3.32+.

## Data in this repository

The extracted data is not yet committed; it will be added in a follow-up commit.

## What isn't directly portable

- **Symbology** is stored in Esri's renderer JSON format (in `styles/` and `webmap.json`). Other tools need it translated, but the colors, class breaks and labels are all there.
- **Layout and widgets** in `experience_config.json` only run inside Experience Builder. Use the file as a blueprint (text, page structure, links) when rebuilding the site in another framework.

## Data sources and terms

Most layers are hosted by USC SSI. A few boundary layers come directly from LA County and City of LA GIS servers. The underlying datasets come from public sources such as the US Census ACS, CDC, and the LA County Department of Public Health. See the app's "About the Layers" page and the `accessInformation` / `licenseInfo` fields in `item.json` for credits and terms before republishing.
