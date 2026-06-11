const STATIC_CACHE = 'trek-static-v2';
const DYNAMIC_CACHE = 'trek-dynamic-v2';
const MAP_CACHE = 'trek-map-v2';
const OFFLINE_PAGE = '/offline.html';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  OFFLINE_PAGE,
  '/manifest.json',
  '/service-worker.js',
  '/data/peaks.json',
  '/data/boundaries.json',
  '/js/offline-storage.js',
  '/js/offline-manager.js',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png'
];

function isMapTileRequest(url) {
  const isGoogleTile = url.hostname.endsWith('.google.com') && url.pathname === '/vt' && url.searchParams.has('lyrs');
  const isOsmTile = url.hostname === 'tile.openstreetmap.org';
  return isGoogleTile || isOsmTile;
}

function isApiRequest(url) {
  return url.pathname.startsWith('/data/');
}

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  if (response && (response.ok || response.type === 'opaque')) {
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request, cacheName, requestUrl) {
  try {
    const response = await fetch(request);
    if (response && (response.ok || response.type === 'opaque')) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;

    if (request.destination === 'document') {
      return caches.match(OFFLINE_PAGE);
    }

    if (isApiRequest(requestUrl || new URL(request.url))) {
      return new Response('[]', { headers: { 'Content-Type': 'application/json' } });
    }

    return new Response('Offline', { status: 503, statusText: 'Offline' });
  }
}

self.addEventListener('install', event => {
  event.waitUntil(caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  const expected = [STATIC_CACHE, DYNAMIC_CACHE, MAP_CACHE];
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(key => !expected.includes(key)).map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);

  if (isMapTileRequest(requestUrl)) {
    event.respondWith(cacheFirst(event.request, MAP_CACHE));
    return;
  }

  if (isApiRequest(requestUrl)) {
    event.respondWith(networkFirst(event.request, DYNAMIC_CACHE, requestUrl));
    return;
  }

  if (['document', 'script', 'style', 'image'].includes(event.request.destination)) {
    event.respondWith(cacheFirst(event.request, STATIC_CACHE).catch(() => caches.match(OFFLINE_PAGE)));
    return;
  }

  event.respondWith(networkFirst(event.request, DYNAMIC_CACHE, requestUrl));
});
