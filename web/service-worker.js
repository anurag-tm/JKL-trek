/* JKL Trekker service worker: offline app shell, data and recently viewed map tiles.
   Bump VERSION whenever app files change so phones pick up the new version. */
const VERSION = 'v4';
const SHELL_CACHE = `jkl-shell-${VERSION}`;
const RUNTIME_CACHE = `jkl-runtime-${VERSION}`;
const TILE_CACHE = 'jkl-tiles';          // kept across versions
const MAX_TILES = 3000;                   // roughly 50-60 MB

// Relative paths so this works on Firebase Hosting and under a GitHub Pages sub-path.
const SHELL = [
  './',
  'index.html',
  'config.js',
  'manifest.json',
  'vendor/leaflet/leaflet.js',
  'vendor/leaflet/leaflet.css',
  'vendor/leaflet/images/layers.png',
  'vendor/leaflet/images/layers-2x.png',
  'vendor/leaflet/images/marker-icon.png',
  'vendor/leaflet/images/marker-shadow.png',
  'data/peaks.json',
  'data/boundaries.json',
  'assets/icons/icon-192.png',
  'assets/icons/icon-512.png'
];

const TILE_HOSTS = ['server.arcgisonline.com', 'tile.opentopomap.org', 'tile.openstreetmap.org'];
const LIB_HOSTS = ['www.gstatic.com', 'cdn.jsdelivr.net'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL_CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys
        .filter(k => k !== SHELL_CACHE && k !== RUNTIME_CACHE && k !== TILE_CACHE)
        .map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function trimCache(name, max) {
  const cache = await caches.open(name);
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - max; i++) await cache.delete(keys[i]);
}

// Network first, fall back to cache (pages and data: always fresh when online).
async function networkFirst(request, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (e) {
    return (await cache.match(request, { ignoreSearch: true }))
        || (await caches.match(request, { ignoreSearch: true }))
        || (fallbackUrl && await caches.match(fallbackUrl))
        || Response.error();
  }
}

// Cache first (map tiles and versioned libraries rarely change).
async function cacheFirst(request, cacheName, maxEntries) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok || response.type === 'opaque') {
      const cache = await caches.open(cacheName);
      await cache.put(request, response.clone());
      if (maxEntries) trimCache(cacheName, maxEntries);
    }
    return response;
  } catch (e) {
    return Response.error();
  }
}

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  if (url.origin === self.location.origin) {
    if (request.mode === 'navigate') {
      event.respondWith(networkFirst(request, SHELL_CACHE, 'index.html'));
    } else {
      event.respondWith(networkFirst(request, SHELL_CACHE));
    }
    return;
  }
  if (TILE_HOSTS.some(h => url.hostname.endsWith(h))) {
    event.respondWith(cacheFirst(request, TILE_CACHE, MAX_TILES));
    return;
  }
  if (LIB_HOSTS.includes(url.hostname)) {
    event.respondWith(cacheFirst(request, RUNTIME_CACHE));
  }
  // Everything else (Firebase, Firestore, Supabase APIs) goes straight to the network.
});
