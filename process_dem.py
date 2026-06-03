#!/usr/bin/env python3
"""
JK TREK EXPLORER - DEM Processing Script
Process Jammu & Kashmir DEM to extract peaks and generate map tiles
"""

import argparse
import json
import os
import sys
import sqlite3
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy
import geopandas as gpd
from scipy.ndimage import maximum_filter
from shapely.geometry import Point, box
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = "data"
DEM_PATH = os.path.join(DATA_DIR, "JK_COP_DEM_GLO30_mosaic_UTM_CLIP.tif")
SHAPEFILE_PATH = os.path.join(DATA_DIR, "DISTRICT_BOUNDARY.shp")
OUTPUT_DB = os.path.join(DATA_DIR, "peaks.db")
OUTPUT_JSON = os.path.join(DATA_DIR, "peaks.json")
OUTPUT_TILES = os.path.join(DATA_DIR, "tiles")

# Elevation bands for difficulty classification
ELEVATION_BANDS = {
    "Easy": (0, 2500),
    "Moderate": (2500, 3500),
    "Difficult": (3500, 4500),
    "Extreme": (4500, 10000)
}

# Best trekking months per elevation
SEASON_MAP = {
    "Easy": "Year-round",
    "Moderate": "March - November",
    "Difficult": "May - October",
    "Extreme": "June - September"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log(message, level="INFO"):
    """Print timestamped log messages"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "INFO": "✓",
        "WARN": "⚠",
        "ERROR": "✗",
        "PROGRESS": "→"
    }.get(level, "•")
    print(f"[{timestamp}] {prefix} {message}")

def check_files():
    """Verify input files exist"""
    log("Checking input files...")
    
    if not os.path.exists(DEM_PATH):
        log(f"DEM not found: {DEM_PATH}", "ERROR")
        sys.exit(1)
    
    if not os.path.exists(SHAPEFILE_PATH):
        log(f"Shapefile not found: {SHAPEFILE_PATH}", "ERROR")
        sys.exit(1)
    
    log(f"DEM: {os.path.getsize(DEM_PATH) / (1024**3):.2f} GB")
    log(f"Shapefile: {os.path.getsize(SHAPEFILE_PATH) / 1024:.2f} KB")

def create_output_dirs():
    """Create output directories if they don't exist"""
    os.makedirs(os.path.dirname(OUTPUT_DB), exist_ok=True)
    os.makedirs(OUTPUT_TILES, exist_ok=True)
    log(f"Output directories created")

def read_dem():
    """Read DEM raster file"""
    log("Reading DEM file...")
    try:
        with rasterio.open(DEM_PATH) as src:
            dem_data = src.read(1)
            dem_meta = src.meta
            dem_crs = src.crs
            dem_bounds = src.bounds
            dem_transform = src.transform
            
            log(f"DEM shape: {dem_data.shape}")
            log(f"DEM CRS: {dem_crs}")
            log(f"Elevation range: {np.nanmin(dem_data):.0f}m - {np.nanmax(dem_data):.0f}m")
            
            return dem_data, dem_meta, dem_crs, dem_bounds, dem_transform
    except Exception as e:
        log(f"Failed to read DEM: {e}", "ERROR")
        sys.exit(1)

def read_districts(shapefile_path):
    """Read district boundary shapefile."""
    log(f"Reading district boundaries from {shapefile_path}...")
    try:
        gdf = gpd.read_file(shapefile_path)
        log(f"Total districts: {len(gdf)}")
        log(f"Shapefile CRS: {gdf.crs}")

        name_columns = ['NAME', 'NAME_1', 'DISTRICT', 'District', 'district', 'NAME_EN', 'NAME_ENG']
        for col in name_columns:
            if col in gdf.columns:
                gdf['NAME'] = gdf[col].astype(str)
                break

        if 'NAME' not in gdf.columns:
            gdf['NAME'] = gdf.index.astype(str)
            log('Shapefile did not contain a standard name column, using index values.')

        return gdf
    except Exception as e:
        log(f"Failed to read shapefile: {e}", "ERROR")
        sys.exit(1)

def get_jk_districts(districts_gdf, dem_crs, dem_bounds):
    """Filter districts that intersect the DEM footprint."""
    log("Filtering districts that intersect the DEM footprint...")

    if districts_gdf.crs != dem_crs:
        districts_gdf = districts_gdf.to_crs(dem_crs)

    bounds_polygon = box(dem_bounds.left, dem_bounds.bottom, dem_bounds.right, dem_bounds.top)
    intersecting = districts_gdf[districts_gdf.intersects(bounds_polygon)].copy()

    log(f"Intersecting districts found: {len(intersecting)}")
    return intersecting

def extract_peaks_from_dem(dem_data, dem_transform, dem_crs, dem_bounds):
    """Extract peak locations using local maxima."""
    log("Extracting peak locations...")

    dem_clean = np.nan_to_num(dem_data, nan=-9999)
    local_max = maximum_filter(dem_clean, size=5) == dem_clean
    valid_peaks = np.where(local_max & (dem_clean > 1000))

    log(f"Initial peaks found: {len(valid_peaks[0])}")

    peaks = []
    for row, col in zip(valid_peaks[0], valid_peaks[1]):
        x, y = xy(dem_transform, row, col)
        elevation = float(dem_clean[row, col])
        peaks.append({
            'x': x,
            'y': y,
            'elevation': elevation,
            'row': int(row),
            'col': int(col)
        })

    return peaks

def peaks_to_gdf(peaks, crs):
    """Convert peaks list to GeoDataFrame"""
    from shapely.geometry import Point
    
    geometry = [Point(p['x'], p['y']) for p in peaks]
    data = {
        'elevation': [p['elevation'] for p in peaks],
        'x': [p['x'] for p in peaks],
        'y': [p['y'] for p in peaks]
    }
    
    gdf = gpd.GeoDataFrame(data, geometry=geometry, crs=crs)
    return gdf

def get_top_peaks_per_district(peaks_gdf, districts_gdf, top_n=10):
    """Get top N peaks per district."""
    log(f"Selecting top {top_n} peaks per district...")

    peaks_with_district = gpd.sjoin(
        peaks_gdf,
        districts_gdf[['geometry', 'NAME']],
        how='left',
        predicate='within'
    )

    top_peaks = []
    for district in districts_gdf['NAME'].unique():
        district_peaks = peaks_with_district[
            peaks_with_district['NAME'] == district
        ].nlargest(top_n, 'elevation')
        if len(district_peaks) > 0:
            log(f"  {district}: {len(district_peaks)} peaks (max: {district_peaks['elevation'].max():.0f}m)")
            top_peaks.append(district_peaks)

    if not top_peaks:
        log("No top peaks were found inside district boundaries.", "WARN")
        return gpd.GeoDataFrame(columns=peaks_gdf.columns, crs=peaks_gdf.crs)

    result = gpd.GeoDataFrame(pd.concat(top_peaks, ignore_index=True), crs=peaks_gdf.crs)
    return result

def get_difficulty_and_season(elevation):
    """Get difficulty class and best season for elevation"""
    for difficulty, (min_elev, max_elev) in ELEVATION_BANDS.items():
        if min_elev <= elevation < max_elev:
            return difficulty, SEASON_MAP[difficulty]
    return "Unknown", "Year-round"

def create_database(top_peaks_gdf):
    """Create SQLite database with peak data."""
    log("Creating SQLite database...")
    try:
        if os.path.exists(OUTPUT_DB):
            os.remove(OUTPUT_DB)

        conn = sqlite3.connect(OUTPUT_DB)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peaks (
                id INTEGER PRIMARY KEY,
                name TEXT,
                district TEXT,
                latitude REAL,
                longitude REAL,
                elevation REAL,
                difficulty TEXT,
                season TEXT,
                distance_from_town REAL,
                prominence REAL,
                first_ascent_verified INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                peak_id INTEGER,
                elevation_reached REAL,
                photo_url TEXT,
                gps_verified INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(peak_id) REFERENCES peaks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trails (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                name TEXT,
                gpx_url TEXT,
                distance_km REAL,
                elevation_gain REAL,
                difficulty TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        for idx, row in top_peaks_gdf.iterrows():
            difficulty, season = get_difficulty_and_season(row['elevation'])
            cursor.execute('''
                INSERT INTO peaks 
                (name, district, latitude, longitude, elevation, difficulty, season)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"Peak_{idx}",
                row.get('NAME', 'Unknown'),
                row.geometry.y,
                row.geometry.x,
                row['elevation'],
                difficulty,
                season
            ))

        conn.commit()
        log(f"Database created with {len(top_peaks_gdf)} peaks")
        cursor.execute('SELECT COUNT(*) FROM peaks')
        count = cursor.fetchone()[0]
        log(f"Total peaks in database: {count}")
        conn.close()
    except Exception as e:
        log(f"Database creation failed: {e}", "ERROR")
        sys.exit(1)

def generate_map_tiles(dem_data, dem_transform, dem_meta):
    """Generate map tiles for web display."""
    log("Generating map tiles...")
    try:
        nodata_value = dem_meta.get('nodata', None)
        if nodata_value is not None:
            valid_mask = dem_data != nodata_value
            valid_data = dem_data[valid_mask]
        else:
            valid_data = dem_data

        if valid_data.size == 0:
            raise ValueError('DEM contains no valid data values for tile generation.')

        min_val = np.nanmin(valid_data)
        max_val = np.nanmax(valid_data)
        if min_val == max_val:
            raise ValueError('DEM has constant elevation values; cannot normalize.')

        normalized = np.zeros_like(dem_data, dtype=np.uint8)
        normalized[valid_mask] = np.clip(((dem_data[valid_mask] - min_val) / (max_val - min_val) * 255), 0, 255).astype(np.uint8)

        output_path = os.path.join(OUTPUT_TILES, 'dem_preview.tif')
        tile_meta = dem_meta.copy()
        tile_meta.update({
            'dtype': 'uint8',
            'count': 1,
            'nodata': 0
        })

        with rasterio.open(output_path, 'w', **tile_meta) as dst:
            dst.write(normalized, 1)

        log(f"Map tiles generated in {OUTPUT_TILES}")
        log("Note: For production, use gdal2tiles.py for full Web Mercator tiles")
    except Exception as e:
        log(f"Tile generation warning: {e}", "WARN")
        # This is non-critical, continue anyway

def write_peaks_json(top_peaks_gdf):
    """Export peak data as a JSON file for the web app."""
    log("Exporting peaks to JSON...")
    peaks = []
    for _, row in top_peaks_gdf.iterrows():
        peaks.append({
            'name': f"Peak_{_}",
            'district': row.get('NAME', 'Unknown'),
            'latitude': float(row.geometry.y),
            'longitude': float(row.geometry.x),
            'elevation': float(row['elevation']),
            'difficulty': get_difficulty_and_season(row['elevation'])[0],
            'season': get_difficulty_and_season(row['elevation'])[1]
        })
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(peaks, f, indent=2)
    log(f"Peaks JSON written to: {OUTPUT_JSON}")


def verify_output():
    """Verify all output files were created."""
    log("Verifying output...")

    checks = {
        "Database": os.path.exists(OUTPUT_DB),
        "JSON export": os.path.exists(OUTPUT_JSON),
        "Output directory": os.path.exists(OUTPUT_TILES)
    }

    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        log(f"  {status} {check_name}")

    if os.path.exists(OUTPUT_DB):
        db_size = os.path.getsize(OUTPUT_DB) / (1024*1024)
        log(f"Database size: {db_size:.2f} MB")

    return all(checks.values())

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Process J&K DEM and district boundaries to extract peaks.')
    parser.add_argument('--dem', default=DEM_PATH, help='DEM file path')
    parser.add_argument('--shapefile', default=SHAPEFILE_PATH, help='Shapefile path')
    parser.add_argument('--output-db', default=OUTPUT_DB, help='Output SQLite database path')
    parser.add_argument('--output-json', default=OUTPUT_JSON, help='Output JSON file path')
    parser.add_argument('--output-tiles', default=OUTPUT_TILES, help='Output tiles directory')
    return parser.parse_args()


def main():
    """Main processing pipeline."""
    args = parse_args()

    global DEM_PATH, SHAPEFILE_PATH, OUTPUT_DB, OUTPUT_JSON, OUTPUT_TILES
    DEM_PATH = args.dem
    SHAPEFILE_PATH = args.shapefile
    OUTPUT_DB = args.output_db
    OUTPUT_JSON = args.output_json
    OUTPUT_TILES = args.output_tiles

    log("=" * 60)
    log("JK TREK EXPLORER - DEM PROCESSING")
    log("=" * 60)

    check_files()
    create_output_dirs()

    dem_data, dem_meta, dem_crs, dem_bounds, dem_transform = read_dem()
    districts_gdf = read_districts(SHAPEFILE_PATH)
    jk_districts = get_jk_districts(districts_gdf, dem_crs, dem_bounds)

    peaks = extract_peaks_from_dem(dem_data, dem_transform, dem_crs, dem_bounds)
    peaks_gdf = peaks_to_gdf(peaks, dem_crs)

    top_peaks = get_top_peaks_per_district(peaks_gdf, jk_districts, top_n=10)

    create_database(top_peaks)
    write_peaks_json(top_peaks)
    generate_map_tiles(dem_data, dem_transform, dem_meta)

    if verify_output():
        log("=" * 60)
        log("✓ PROCESSING COMPLETE!")
        log("=" * 60)
        log(f"Output DB: {OUTPUT_DB}")
        log(f"JSON: {OUTPUT_JSON}")
        log(f"Tiles: {OUTPUT_TILES}")
        print()
    else:
        log("Processing completed with warnings", "WARN")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Processing interrupted by user", "WARN")
        sys.exit(0)

        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
