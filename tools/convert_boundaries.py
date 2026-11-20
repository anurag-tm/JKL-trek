#!/usr/bin/env python3
"""Make web/data/boundaries.json (WGS84 GeoJSON) from the SOI district shapefile.

Usage:
    python tools/convert_boundaries.py "F:/2/Administrative Boundary Database/DISTRICT_BOUNDARY.shp"

The input can also be an old projected GeoJSON with no CRS stored; then the
SOI Lambert projection is assumed (override with --src-crs).
"""
import argparse
import sys
from pathlib import Path

import geopandas as gpd

from common import SOI_LCC, TARGET_STATES, decode_soi, state_of

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "web" / "data" / "boundaries.json"


def find_col(gdf, *candidates):
    cols = {c.upper(): c for c in gdf.columns}
    for c in candidates:
        if c.upper() in cols:
            return cols[c.upper()]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="District shapefile or GeoJSON")
    ap.add_argument("-o", "--output", default=str(DEFAULT_OUT))
    ap.add_argument("--src-crs", default=None, help="CRS to assume if the file has none (default: SOI LCC)")
    ap.add_argument("--tolerance", type=float, default=0.001,
                    help="Simplify tolerance in degrees (0.001 ~ 100 m)")
    args = ap.parse_args()

    gdf = gpd.read_file(args.input)
    minx, miny, maxx, maxy = gdf.total_bounds
    looks_projected = max(abs(minx), abs(maxx)) > 180 or max(abs(miny), abs(maxy)) > 90
    if args.src_crs:
        gdf = gdf.set_crs(args.src_crs, allow_override=True)
    elif gdf.crs is None or (gdf.crs.is_geographic and looks_projected):
        # GeoJSON readers default to WGS84 even when the numbers are metres.
        gdf = gdf.set_crs(SOI_LCC, allow_override=True)
        print("CRS missing or wrong (coordinates are in metres): assuming SOI Lambert")

    state_col = find_col(gdf, "STATE", "ST_NM", "STATE_NAME")
    dist_col = find_col(gdf, "District", "DISTRICT", "DIST_NAME", "NAME")
    if not state_col or not dist_col:
        sys.exit(f"Could not find state/district columns in: {list(gdf.columns)}")

    gdf = gdf[gdf[state_col].map(state_of).isin(TARGET_STATES)].copy()
    if gdf.empty:
        sys.exit("No J&K / Ladakh districts found.")

    out = gpd.GeoDataFrame(
        {
            "name": gdf[dist_col].map(decode_soi),
            "state": gdf[state_col].map(lambda s: decode_soi(s).replace("And", "and")),
        },
        geometry=gdf.geometry.to_crs(4326).simplify(args.tolerance, preserve_topology=True),
        crs=4326,
    ).sort_values("name")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_file(args.output, driver="GeoJSON", COORDINATE_PRECISION=5)
    size_kb = Path(args.output).stat().st_size / 1024
    print(f"Wrote {len(out)} districts to {args.output} ({size_kb:.0f} KB)")
    print(", ".join(out["name"]))


if __name__ == "__main__":
    main()
