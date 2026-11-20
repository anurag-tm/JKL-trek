# JKL Trekker

Offline-friendly web app for exploring summits and recording GPS tracks in the
Jammu & Kashmir and Ladakh Himalayas.

**Live app:** https://jkl-trekker.web.app

## Features

- Topo, satellite and street basemaps with J&K / Ladakh district boundaries
- 70 summits extracted from the Copernicus GLO-30 DEM, filterable by district and elevation
- GPS track recording (distance, elevation gain, time), route sketching, GPX export
- Works offline after the first visit: app, data and recently viewed map tiles are cached
- Installable on phones (Add to Home Screen), or as an Android app (APK) with background GPS recording
- Community photo feed (Google sign-in, Firestore + Supabase storage)

## Repository layout

```
web/                  the app (this folder is what gets deployed)
  index.html          UI and app logic
  config.js           public Firebase / Supabase client config
  service-worker.js   offline caching (bump VERSION after changing app files)
  data/peaks.json     summits (WGS84)
  data/boundaries.json district boundaries (WGS84 GeoJSON)
  vendor/leaflet/     Leaflet 1.9.4, bundled for offline use
tools/                Python scripts that build web/data
firestore.rules       Firestore security rules
supabase-storage-policies.sql   storage limits for the photo bucket
android/              Android app project (Capacitor), see BUILD_ANDROID.md
capacitor.config.json Android app settings
```

## Run locally

```bash
cd web
python -m http.server 8000
```

Open http://localhost:8000.

## Deploy (Firebase Hosting)

```bash
npm install -g firebase-tools
firebase login
firebase deploy --only hosting,firestore
```

Only the `web/` folder is uploaded. After deploying:

1. Firebase Console → Authentication → Settings → **Authorized domains**: make sure
   `jkl-trekker.web.app` (and `localhost` for testing) are listed.
2. Google Cloud Console → APIs & Services → Credentials → restrict the browser API key
   to `https://jkl-trekker.web.app/*` and `http://localhost/*`.
3. Supabase → SQL Editor → run `supabase-storage-policies.sql`.

GitHub Pages also deploys `web/` on every push to `master`, but Google sign-in
redirects only work on the Firebase domain, so use https://jkl-trekker.web.app as the main link.

## Android app

See [BUILD_ANDROID.md](BUILD_ANDROID.md). Short version:

```bash
npm install
npx cap sync android
npx cap open android   # then press Run in Android Studio
```

## Rebuild the data

Requires `pip install geopandas rasterio scipy`.

```bash
# District boundaries from the SOI Administrative Boundary Database
python tools/convert_boundaries.py "path/to/DISTRICT_BOUNDARY.shp"

# Summits from a projected (UTM) DEM
python tools/process_dem.py --dem path/to/JK_COP_DEM_GLO30_mosaic_UTM_CLIP.tif \
    --districts "path/to/DISTRICT_BOUNDARY.shp"
```

Options: `--min-sep 3000` (minimum distance between summits in metres),
`--top 10` (summits per district), `--window 1000` (local-maximum search window).

## Known limits

- In the browser version, phones pause GPS when the screen is off. Keep the screen
  on while recording, or use the Android app, which records in the background.
- Peak names are placeholders (`Peak 5,821 m`). Adding names from OpenStreetMap
  (`natural=peak`) is the next data step.
- Difficulty is an altitude class only, not a route grade.
- Google sign-in inside the Android app needs a one-time Firebase setup
  (BUILD_ANDROID.md, step 4).
