// Kirkland Thermography PWA — offline-capable service worker.
// Bump CACHE on any data/app change to force a refresh.
const CACHE = 'kirkland-thermo-v5';

// Same-origin app shell + data. These are precached so the app works fully
// offline once it has been opened online once.
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './data/overlays.json',
  './data/overlay_jour.png',
  './data/buildings_scored.geojson',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
];

// Cross-origin assets cached at runtime (MapLibre lib + basemap tiles).
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Geocoder (Nominatim): always network, never cache — addresses must be live.
  if (/nominatim\.openstreetmap\.org/.test(url.host)) return;

  // HTML navigations: network-first, so the newest app shell always wins when
  // online (prevents being stuck on a stale cached page). Falls back to cache
  // offline. This is the key fix for "I still see the old version".
  if (req.mode === 'navigate' || req.destination === 'document') {
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(req).then((h) => h || caches.match('./index.html')))
    );
    return;
  }

  // Basemap tiles + CDN: cache-first, fall back to network, then cache the result.
  const isTile = /basemaps\.cartocdn\.com/.test(url.host);
  const isCdn = /unpkg\.com|demotiles\.maplibre\.org/.test(url.host);

  if (isTile || isCdn) {
    e.respondWith(
      caches.open(CACHE).then(async (c) => {
        const hit = await c.match(req);
        if (hit) return hit;
        try {
          const res = await fetch(req);
          if (res && (res.ok || res.type === 'opaque')) c.put(req, res.clone());
          return res;
        } catch (err) {
          return hit || Response.error();
        }
      })
    );
    return;
  }

  // Same-origin: cache-first with network fallback.
  e.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match('./index.html')))
  );
});
