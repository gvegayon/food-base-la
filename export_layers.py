"""Download every layer in the Food Base LA web map as GeoJSON, plus its styling.

Usage: python3 export_layers.py [--only "substring of title"] [--workers 8]
Outputs: raw/<group>__<title>.geojson and styles/<same>.json (renderer + popup from the web map)
Needs only the Python standard library.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
webmap = json.load(open(os.path.join(HERE, "webmap.json")))
only = sys.argv[sys.argv.index("--only") + 1].lower() if "--only" in sys.argv else None
workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 8

def get(url, params):
    q = urllib.parse.urlencode(params).encode()
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(url, data=q, timeout=120))
        except Exception:
            if attempt == 3: raise
            time.sleep(2 ** attempt)

def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:120]

def leaves(layers, path):
    for l in layers:
        if l.get("layers"):
            yield from leaves(l["layers"], path + [l.get("title", "")])
        else:
            yield path, l

def export(url, out):
    meta = get(url, {"f": "json"})
    page = min(meta.get("maxRecordCount") or 1000, 2000)
    oid_field = meta.get("objectIdField") or "OBJECTID"
    features, offset = [], 0
    while True:
        d = get(url + "/query", {"where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson",
                                 "resultOffset": offset, "resultRecordCount": page, "orderByFields": oid_field})
        if "error" in d: raise RuntimeError(d["error"])
        batch = d.get("features", [])
        features += batch
        offset += len(batch)
        if not batch or (len(batch) < page and not d.get("properties", {}).get("exceededTransferLimit")):
            break
    dump({"type": "FeatureCollection", "features": features}, out)
    return len(features), meta

def dump(obj, out, **kw):
    # Write to a temp file and rename, so an interrupted run never leaves a partial file
    with open(out + ".tmp", "w") as f:
        json.dump(obj, f, **kw)
    os.replace(out + ".tmp", out)

os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
os.makedirs(os.path.join(HERE, "styles"), exist_ok=True)
def run(job):
    path, l = job
    title = l.get("title", "")
    name = slug("__".join(path + [title]))
    out = os.path.join(HERE, "raw", name + ".geojson")
    style_out = os.path.join(HERE, "styles", name + ".json")
    if os.path.exists(out) and os.path.exists(style_out):
        return f"skip (exists) {name}"
    try:
        n, meta = export(l["url"], out)
        # Web-map overrides win over the service's default drawingInfo
        style = {"title": title, "group": path, "url": l["url"],
                 "drawingInfo": l.get("layerDefinition", {}).get("drawingInfo") or meta.get("drawingInfo"),
                 "popupInfo": l.get("popupInfo"), "fields": meta.get("fields")}
        dump(style, style_out, indent=1)
        return f"{n:>8}  {name}"
    except Exception as e:
        return f"FAILED {name} {e}"

jobs = [(p, l) for p, l in leaves(webmap["operationalLayers"], [])
        if not only or only in l.get("title", "").lower()]
with ThreadPoolExecutor(workers) as ex:
    for fut in as_completed([ex.submit(run, j) for j in jobs]):
        print(fut.result(), flush=True)
