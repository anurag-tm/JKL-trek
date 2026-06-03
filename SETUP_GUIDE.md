# JK Trek Explorer - Complete Setup Guide
**Mountain Trekking & Elevation Explorer for Jammu & Kashmir and Ladakh**

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Phase 1: Initial Setup](#phase-1-initial-setup)
3. [Phase 2: DEM Processing](#phase-2-dem-processing)
4. [Phase 3: Deploy Web App](#phase-3-deploy-web-app)
5. [Phase 4: Android App](#phase-4-android-app)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need BEFORE Starting
- ✅ Windows/Mac/Linux PC
- ✅ VS Code installed
- ✅ Python 3.10+ installed
- ✅ GitHub account
- ✅ Firebase account (free)
- ✅ 2GB free disk space (for DEM processing)
- ✅ DEM file: `JK_COP_DEM_GLO30_mosaic_UTM_CLIP.tif` (1GB)
- ✅ Shapefile: `DISTRICT_BOUNDARY.shp` (with .shx, .dbf, .prj files)
- ✅ Android Studio (for Phase 4)

### Check Your Python Installation
Open VS Code Terminal and run:
```bash
python --version
```
Should show: `Python 3.10.x` or higher

If not installed, download from [python.org](https://python.org/downloads)

---

## Phase 1: Initial Setup (15 minutes)

### Step 1A: Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Fill in:
   - **Repository name**: `jk-trek-explorer`
   - **Description**: "Mountain Trekking Explorer for J&K & Ladakh"
   - **Public** (required for GitHub Pages)
   - **Add README.md** ✓
3. Click **Create Repository**
4. Copy the URL (you'll need it soon)

### Step 1B: Clone Repository to Your PC

In VS Code:
1. Open Terminal: `Ctrl + ~` (backtick)
2. Navigate to where you want the project:
   ```bash
   cd C:\Users\YourName\Documents
   # or on Mac/Linux:
   cd ~/Documents
   ```
3. Clone the repo:
   ```bash
   git clone https://github.com/YourGitHubUsername/jk-trek-explorer.git
   cd jk-trek-explorer
   ```

### Step 1C: Create Folder Structure

In your `jk-trek-explorer` folder, create these folders:
```
jk-trek-explorer/
├── data/              (for peaks.db and tiles)
├── scripts/           (for Python script)
├── assets/
│   ├── icons/        (app icons)
│   └── markers/      (color pin SVGs)
├── README.md         (already exists)
└── .gitignore        (create - see below)
```

Create `.gitignore` file in root folder with:
```
# Large files - don't push to GitHub
data/tiles/
data/*.db
node_modules/
*.tif
*.shp
*.shx
*.dbf
*.prj
.DS_Store
```

Push to GitHub:
```bash
git add .
git commit -m "Initial folder structure"
git push origin main
```

### Step 1D: Set Up Firebase (Free)

1. Go to [firebase.google.com](https://firebase.google.com)
2. Click **Get Started** → Sign in with Google
3. Create new project:
   - Name: `jk-trek-explorer`
   - Accept terms → Continue
   - Disable Google Analytics → Create Project
4. Wait for setup (~30 seconds)
5. Go to **Project Settings** (gear icon)
6. Under **Your Apps**, click **Web** icon
7. Register app as `jk-trek-explorer`
8. Copy the config object (looks like below):
   ```javascript
   const firebaseConfig = {
     apiKey: "AIz...",
     authDomain: "jk-trek-explorer-xxx.firebaseapp.com",
     projectId: "jk-trek-explorer-xxx",
     storageBucket: "jk-trek-explorer-xxx.appspot.com",
     messagingSenderId: "123...",
     appId: "1:123..."
   };
   ```
9. Keep this safe - you'll paste it into `firebase-config.js`

### Step 1E: Enable Firebase Services

In Firebase Console:
1. Go to **Build** menu
2. Click **Authentication** → Set Up Sign-In Method
   - Enable **Google** (first option)
   - Click Save
3. Go to **Firestore Database**
   - Click **Create Database**
   - Start in **Production Mode**
   - Choose region: `asia-south1` (India)
   - Click Enable
4. Go to **Storage**
   - Click **Create Bucket**
   - Name: `jk-trek-explorer.appspot.com`
   - Region: `asia-south1`
   - Click Create

### Step 1F: Install Python Libraries

In VS Code Terminal:
```bash
pip install rasterio geopandas numpy scipy simplekml folium pyproj gdal pandas pillow

# If GDAL fails, try:
pip install --upgrade GDAL
```

If you get GDAL errors on Windows, download the wheel file from [Christoph Gohlke's site](https://www.lfd.uci.edu/~gohlke/pythonlibs/) and install:
```bash
pip install GDAL‑3.7.0‑cp311‑cp311‑win_amd64.whl
```

Test installation:
```bash
python -c "import rasterio, geopandas; print('OK')"
```

---

## Phase 2: DEM Processing (45-120 minutes depending on DEM size)

### Step 2A: Prepare Your DEM Files

1. Place these files in your `jk-trek-explorer/data/` folder:
   - `JK_COP_DEM_GLO30_mosaic_UTM_CLIP.tif`
   - `DISTRICT_BOUNDARY.shp` (+ .shx, .dbf, .prj files - all required!)

2. Verify file paths are correct

### Step 2B: Run the Python Processing Script

1. Make sure `process_dem.py` is in the project root and your DEM/shapefile are available.
2. In VS Code Terminal, run this command with your actual file paths:
   ```bash
   python process_dem.py --dem "E:\J&K_aster_12.5\JK_COP_DEM_GLO30_mosaic_UTM_CLIP.tif" --shapefile "F:\2\Administrative Boundary Database\DISTRICT_BOUNDARY.shp"
   ```
3. The script now writes output to the local `data/` folder:
   - `data/peaks.db`
   - `data/peaks.json`
   - `data/tiles/`
4. **Wait** - this may take 30-120 minutes depending on DEM size.
5. You'll see progress messages like:
   ```
   Reading DEM...
   Clipping to J&K & Ladakh...
   Extracting peaks per district...
   Generating map tiles...
   Creating database...
   ✓ Complete!
   ```

### Step 2C: Verify Output

After script finishes, check that these files were created:
- `data/peaks.db` (should be ~8-15 MB)
- `data/tiles/` folder with many PNG files

If not created, check Terminal for error messages (see Troubleshooting section)

### Step 2D: Commit to GitHub

```bash
cd ..
git add data/peaks.db
git add .gitignore
git commit -m "Add DEM-processed peaks database"
git push origin main
```

**Note:** Map tiles (data/tiles/) are large - they stay on your PC only. We'll handle them separately.

---

## Phase 3: Deploy Web App (20 minutes)

### Step 3A: Create Firebase Config File

1. Create file: `firebase-config.js` in root folder
2. Paste this code and replace with YOUR Firebase config:
   ```javascript
   // Replace these values with your Firebase config from Step 1E
   const firebaseConfig = {
     apiKey: "YOUR_API_KEY",
     authDomain: "YOUR_AUTH_DOMAIN",
     projectId: "YOUR_PROJECT_ID",
     storageBucket: "YOUR_STORAGE_BUCKET",
     messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
     appId: "YOUR_APP_ID"
   };

   // Initialize Firebase
   if (!window.firebase) {
     const script = document.createElement('script');
     script.src = 'https://www.gstatic.com/firebasejs/10.5.0/firebase-app.js';
     document.head.appendChild(script);
   }

   export const firebaseConfig;
   ```

### Step 3B: Create Main App File

Create `index.html` in root folder with the complete app code (provided below)

### Step 3C: Create Supporting Files

Create these 3 additional files:

**`manifest.json`** - makes app installable on Android
```json
{
  "name": "JK Trek Explorer",
  "short_name": "Trek Explorer",
  "description": "Discover mountain peaks and plan treks in J&K and Ladakh",
  "start_url": "/jk-trek-explorer/",
  "scope": "/jk-trek-explorer/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "assets/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "assets/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    }
  ]
}
```

**`service-worker.js`** - enables offline mode
```javascript
const CACHE_NAME = 'trek-explorer-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.json',
  '/firebase-config.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) {
        return response;
      }
      return fetch(event.request)
        .then(response => {
          if (!response || response.status !== 200 || response.type === 'error') {
            return response;
          }
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });
          return response;
        })
        .catch(() => {
          return new Response('Offline - content not available');
        });
    })
  );
});
```

### Step 3D: Enable GitHub Pages

1. Go to your GitHub repo
2. Click **Settings** → **Pages**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main** / **root**
4. Click Save
5. Wait 2 minutes for deployment
6. Your app is now live at:
   ```
   https://YourGitHubUsername.github.io/jk-trek-explorer/
   ```

### Step 3E: Test on Your Phone

1. Open the URL from Step 3D on your phone
2. Tap the 3-dot menu → **Add to Home Screen**
3. The app should:
   - Load the map
   - Show your GPS location (allow permission)
   - Allow you to tap peaks and see info
   - Work even when WiFi is turned off

---

## Phase 4: Android App (Optional - for Better GPS & Play Store)

This requires Android Studio and knowledge of Kotlin/Java.

### Option A: Keep Using Web App
- No Android Studio needed
- Users access via browser
- All features work
- Free hosting forever

### Option B: Build Android APK
Follow the Android Studio section in this guide (add after testing Phase 3)

---

## File Checklist

Before pushing to GitHub, verify you have:

```
✓ jk-trek-explorer/
  ✓ index.html                  (main app)
  ✓ manifest.json               (PWA config)
  ✓ service-worker.js           (offline support)
  ✓ firebase-config.js          (with YOUR keys)
  ✓ README.md                   (already exists)
  ✓ .gitignore                  (created in Step 1C)
  ✓ scripts/
    ✓ process_dem.py            (DEM processing)
  ✓ data/
    ✓ peaks.db                  (generated by Python)
    ✓ tiles/                    (generated by Python)
  ✓ assets/
    ✓ icons/                    (app icons - create if needed)
    ✓ markers/                  (color pins - optional)
```

---

## Troubleshooting

### Problem: "GDAL not found"
**Solution:**
```bash
pip install --upgrade GDAL
# If still fails, download wheel from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
```

### Problem: "Shapefile not found"
**Solution:**
- Verify DISTRICT_BOUNDARY.shp is in `data/` folder
- Make sure ALL these files are present:
  - DISTRICT_BOUNDARY.shp
  - DISTRICT_BOUNDARY.shx
  - DISTRICT_BOUNDARY.dbf
  - DISTRICT_BOUNDARY.prj

### Problem: "DEM file is too large / runs out of memory"
**Solution:**
- Your DEM might be larger than expected
- Try processing in tiles (modify process_dem.py)
- Increase virtual memory on your PC

### Problem: "GitHub Pages not showing content"
**Solution:**
- Verify Settings → Pages shows "Deploy from branch - main"
- Wait 5 minutes for deployment
- Hard refresh browser: Ctrl + Shift + R

### Problem: "Peaks not showing on map"
**Solution:**
- Check browser console (F12 → Console tab)
- Verify peaks.db exists and is not empty
- Check that SQLite database can be read

### Problem: "Firebase authentication failing"
**Solution:**
- Verify firebase-config.js has correct config keys
- Check Firebase console → Authentication → Google is enabled
- Clear browser cache and try again

### Problem: "GPS not working"
**Solution:**
- Allow location permission when prompted
- Only works on HTTPS (GitHub Pages is HTTPS ✓)
- Needs actual GPS hardware (not available in browser on PC)
- Works on mobile devices with GPS

### Problem: "Offline mode not working"
**Solution:**
- Service worker needs HTTPS (GitHub Pages is HTTPS ✓)
- First visit must be online to cache files
- Check browser console for service worker errors

---

## Common Issues & Prevention

| Issue | Prevention |
|-------|-----------|
| Map tiles too large | Keep tiles in `/data/tiles/` - don't push to GitHub |
| Firebase quota exceeded | Free tier supports ~5000 users - plenty for start |
| DEM processing crashes | Make sure DEM file has .tif extension, not geoTIFF |
| App not responding | Check browser console (F12) for JavaScript errors |
| Database locked error | Close any other processes using peaks.db |
| GPS coordinates wrong | Verify DEM CRS matches WGS84 output |

---

## Success Checklist

You'll know it's working when:

- ✅ GitHub Pages shows your app at the URL
- ✅ Map displays terrain and peaks
- ✅ GPS shows your location (mobile)
- ✅ Clicking peaks shows elevation info
- ✅ Can draw trails on map
- ✅ Can save trail as .gpx file
- ✅ App works offline after first visit
- ✅ Firebase login works
- ✅ Friend location syncs when online
- ✅ Achievements appear on leaderboard

---

## Next Steps After Phase 3

### Step 1: Test thoroughly
- Test all features on mobile
- Test offline mode (turn off WiFi)
- Test GPS tracking

### Step 2: Gather feedback
- Share link with friends
- Get feedback on UX
- Fix any issues

### Step 3: Phase 4 - Android App (Optional)
- Build APK for Play Store
- Better GPS access
- Better offline storage

### Step 4: Scale
- Monitor Firebase usage
- Upgrade if needed (still very cheap)
- Market the app

---

## Support & Help

If you encounter issues:

1. **Check Terminal output** - read error messages carefully
2. **Check browser console** - F12 → Console tab
3. **Check Firebase console** - verify services are enabled
4. **Restart everything** - often fixes strange issues
5. **Clear cache** - Ctrl + Shift + Delete in Chrome

---

## File Size Reference

Expected sizes after processing:

```
peaks.db          ~8-15 MB    (varies by DEM resolution)
tiles/            ~60-80 MB   (map background images)
index.html        ~150 KB     (main app)
Overall app       ~90-110 MB  (quite normal)
```

---

## Production Checklist

When ready to launch:

- [ ] All 3 Firebase services enabled and tested
- [ ] Firebase config keys verified
- [ ] GitHub Pages deployed and live
- [ ] App tested on real mobile device
- [ ] GPS tested (allow permission when prompted)
- [ ] Trail drawing and export tested
- [ ] Achievement posting tested
- [ ] Leaderboard appears correctly
- [ ] Dark mode tested
- [ ] Offline mode tested (turn off WiFi)
- [ ] Battery saver mode works
- [ ] App icon appears on home screen
- [ ] Share to WhatsApp works
- [ ] Responsive design (mobile/tablet/desktop)

---

## You're Ready!

You have everything needed. Just follow the steps in order, and if you get stuck, check the Troubleshooting section.

**Next: Create the files and run process_dem.py**

---

*Last Updated: June 2025*
*Version: 1.0 - Complete Setup Guide*
