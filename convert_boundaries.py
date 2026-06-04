import geopandas as gpd
import os

# Define paths
shp_path = r'F:\2\Administrative Boundary Database\DISTRICT_BOUNDARY.shp'
output_path = r'C:\Users\anura\Downloads\trek\data\boundaries.json'

print(f"Reading shapefile: {shp_path}...")

try:
    # 1. Load the shapefile
    gdf = gpd.read_file(shp_path)

    # 2. Filter for J&K and Ladakh
    # Note: Column names vary by dataset. Common ones are 'State_Name' or 'ST_NM'
    # We will search for common column patterns
    state_col = next((col for col in gdf.columns if 'STATE' in col.upper() or 'ST_NM' in col.upper()), None)

    if state_col:
        print(f"Filtering using column: {state_col}")
        # Standardize names to handle variations in spelling/case
        mask = gdf[state_col].str.upper().str.contains('JAMMU|KASHMIR|LADAKH', na=False)
        filtered_gdf = gdf[mask]
    else:
        print("Could not find State column. Available columns:", list(gdf.columns))
        print("Attempting to filter by checking all columns...")
        # Fallback: check all columns for the names
        filtered_gdf = gdf[gdf.apply(lambda row: row.astype(str).str.contains('Jammu|Kashmir|Ladakh', case=False).any(), axis=1)]

    # 3. Simplify the geometry to make it load fast in the mobile app
    # (0.01 is roughly 1km accuracy, good for mobile maps)
    print("Simplifying boundaries for mobile performance...")
    filtered_gdf['geometry'] = filtered_gdf.simplify(0.005, preserve_topology=True)

    # 4. Save to GeoJSON
    print(f"Saving filtered data to: {output_path}")
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    filtered_gdf.to_file(output_path, driver='GeoJSON')
    print("Successfully created boundaries.json!")
    print(f"Found {len(filtered_gdf)} districts in J&K/Ladakh.")

except Exception as e:
    print(f"\nERROR: {e}")
    print("\nMake sure you have geopandas installed: pip install geopandas")
