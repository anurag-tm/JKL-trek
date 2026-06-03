# JK Trek Explorer

Interactive web app for Jammu & Kashmir / Ladakh trek peaks.

## What is included

- `index.html` — main app UI with Leaflet map and peak explorer
- `data/peaks.json` — extracted peak data from DEM processing
- `process_dem.py` — Python pipeline for DEM peak extraction
- `manifest.json` and `service-worker.js` — PWA support
- `assets/icons/` — app icon files for installable web app
- `debug.html` — diagnostics page for local testing

## Local development

Run a local web server from the project folder:

```powershell
cd "C:\Users\anura\Downloads\trek"
python -m http.server 8000
```

Open `http://localhost:8000` in your browser.

## GitHub Deployment

1. Open GitHub Desktop.
2. Choose `File` → `Add local repository` and select this folder.
3. Click `Publish repository`.
4. Use a repository name like `jk-trek-explorer`.
5. After publishing, open the repo on GitHub.
6. Go to `Settings` → `Pages` and publish from the `main` branch.

Then your app will be available as a GitHub Pages site.

## Next step

After publishing the web site, we can build an Android app wrapper that loads the GitHub Pages URL in a WebView.
