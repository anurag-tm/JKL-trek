#!/usr/bin/env python3
"""Extract summit points from a DEM and write web/data/peaks.json (WGS84).

Normal use (needs the DEM and the SOI district shapefile):
    python tools/process_dem.py --dem JK_COP_DEM_GLO30_mosaic_UTM_CLIP.tif \
        --districts DISTRICT_BOUNDARY.shp

Repair an old peaks.json whose "latitude/longitude" are really UTM metres:
    python tools/process_dem.py --from-json old_peaks.json --src-crs EPSG:32643 \
        --districts web/data/boundaries.json
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Point

from common import SOI_LCC, TARGET_STATES, decode_soi, state_of

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "web" / "data" / "peaks.json"

# Altitude class -> best months (a rough guide, not a route grade)
ALTITUDE_CLASSES = [
    (2500, "Easy", "Year-round"),
    (3500, "Moderate", "March - November"),
    (4500, "Difficult", "May - October"),
    (99999, "Extreme", "June - September"),
]


def altitude_class(elev):
    for upper, label, season in ALTITUDE_CLASSES:
        if elev < upper:
            return label, season
    return "Extreme", "June - September"


def load_districts(path):
    gdf = gpd.read_file(path)
    minx, miny, maxx, maxy = gdf.total_bounds
    if gdf.crs is None or (gdf.crs.is_geographic and max(abs(minx), abs(maxx)) > 180):
        gdf = gdf.set_crs(SOI_LCC, allow_override=True)
    cols = {c.upper(): c for c in gdf.columns}
    name_col = cols.get("NAME") or cols.get("DISTRICT")
    state_col = cols.get("STATE") or cols.get("ST_NM")
    if not name_col:
        sys.exit(f"No district name column in {list(gdf.columns)}")
    if state_col:
        gdf = gdf[gdf[state_col].map(state_of).isin(TARGET_STATES)]
    return gpd.GeoDataFrame({"district": gdf[name_col].map(decode_soi)}, geometry=gdf.geometry, crs=gdf.crs)


def candidates_from_dem(dem_path, window_m, min_elev, min_relief):
    """Local maxima of the DEM (in the DEM's own CRS).

    A pixel counts as a summit if it is the highest point in the search window
    and stands at least min_relief metres above the lowest point of that window
    (this removes flat plateaus, lakes and valley floors).
    """
    import rasterio
    from scipy.ndimage import maximum_filter, minimum_filter

    with rasterio.open(dem_path) as src:
        if src.crs is None or src.crs.is_geographic:
            sys.exit("Use a projected DEM (e.g. UTM) so the search window is in metres.")
        dem = src.read(1, masked=True).astype("float32").filled(np.nan)
        transform, crs = src.transform, src.crs
        px = abs(transform.a)

    size = max(3, int(round(window_m / px)) | 1)  # odd window, in pixels
    print(f"DEM {dem.shape}, pixel {px:.0f} m, search window {size} px")
    filled = np.nan_to_num(dem, nan=-9999)
    local_max = maximum_filter(filled, size=size)
    local_min = minimum_filter(np.nan_to_num(dem, nan=99999), size=size)
    is_peak = (local_max == filled) & (filled > min_elev) & (filled - local_min >= min_relief)
    rows, cols = np.nonzero(is_peak)
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    return gpd.GeoDataFrame({"elevation": filled[rows, cols]},
                            geometry=gpd.points_from_xy(xs, ys), crs=crs)


def candidates_from_json(path, src_crs):
    """Old peaks.json where 'latitude' held northing and 'longitude' easting."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return gpd.GeoDataFrame(
        {"elevation": [float(p["elevation"]) for p in data]},
        geometry=[Point(p["longitude"], p["latitude"]) for p in data],
        crs=src_crs,
    )


def thin_peaks(gdf, min_sep_m):
    """Keep the highest point and drop any lower point within min_sep_m of a kept one.

    Uses a grid of min_sep_m cells so it stays fast with many candidates.
    """
    gdf = gdf.sort_values("elevation", ascending=False).reset_index(drop=True)
    xs, ys = gdf.geometry.x.to_numpy(), gdf.geometry.y.to_numpy()
    grid, kept = {}, []
    sep2 = min_sep_m ** 2
    for i in range(len(gdf)):
        cx, cy = int(xs[i] // min_sep_m), int(ys[i] // min_sep_m)
        near = False
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for j in grid.get((gx, gy), ()):
                    if (xs[i] - xs[j]) ** 2 + (ys[i] - ys[j]) ** 2 < sep2:
                        near = True
                        break
                if near:
                    break
            if near:
                break
        if not near:
            kept.append(i)
            grid.setdefault((cx, cy), []).append(i)
    return gdf.loc[kept]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dem", help="Projected DEM GeoTIFF")
    src.add_argument("--from-json", help="Old peaks.json to repair")
    ap.add_argument("--src-crs", default="EPSG:32643", help="CRS of --from-json coordinates")
    ap.add_argument("--districts", required=True, help="District shapefile or boundaries.json")
    ap.add_argument("-o", "--output", default=str(DEFAULT_OUT))
    ap.add_argument("--window", type=float, default=1000, help="Local-maximum search window (m)")
    ap.add_argument("--min-elev", type=float, default=1000)
    ap.add_argument("--min-relief", type=float, default=150, help="Minimum height above the window's lowest point (m)")
    ap.add_argument("--min-sep", type=float, default=3000, help="Minimum distance between peaks (m)")
    ap.add_argument("--top", type=int, default=10, help="Peaks kept per district")
    args = ap.parse_args()

    if args.dem:
        cands = candidates_from_dem(args.dem, args.window, args.min_elev, args.min_relief)
    else:
        cands = candidates_from_json(args.from_json, args.src_crs)
    print(f"Candidate summits: {len(cands)}")

    # Work in a metric CRS for distances (UTM 43N covers J&K and most of Ladakh well enough).
    metric = cands.crs if cands.crs.is_projected else "EPSG:32643"
    cands = cands.to_crs(metric)
    districts = load_districts(args.districts).to_crs(metric)

    cands = gpd.sjoin(cands, districts, how="inner", predicate="within").drop(columns="index_right")
    print(f"Inside J&K / Ladakh: {len(cands)}")

    cands = thin_peaks(cands, args.min_sep)
    print(f"After removing duplicates within {args.min_sep / 1000:.1f} km: {len(cands)}")

    top = (cands.sort_values("elevation", ascending=False)
                .groupby("district", group_keys=False).head(args.top)
                .to_crs(4326)
                .sort_values(["district", "elevation"], ascending=[True, False]))

    peaks = []
    for i, row in enumerate(top.itertuples()):
        elev = int(round(row.elevation))
        label, season = altitude_class(elev)
        peaks.append({
            "id": i + 1,
            "name": f"Peak {elev:,} m",
            "district": row.district,
            "latitude": round(row.geometry.y, 5),
            "longitude": round(row.geometry.x, 5),
            "elevation": elev,
            "difficulty": label,
            "season": season,
        })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(peaks, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(peaks)} peaks in {top['district'].nunique()} districts to {args.output}")


if __name__ == "__main__":
    main()
