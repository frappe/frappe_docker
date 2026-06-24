const CACHE_NAME = "cosmos-cache-v1";
const STATIC_ASSETS = [
  "/assets/frappe/dist/css/desk.bundle.css",
  "/assets/frappe/dist/js/desk.bundle.js",
  "/assets/erpnext/dist/css/erpnext.bundle.css",
  "/assets/erpnext/dist/js/erpnext.bundle.js",
  "/assets/hrms/dist/css/hrms.bundle.css",
  "/assets/hrms/dist/js/hrms.bundle.js",
  "/assets/cosmos_core/css/cosmos.css",
  "/assets/cosmos_core/images/cosmos-logo.png",
  "/assets/cosmos_core/images/cosmos-icon.png",
  "/assets/frappe/icons/timeless/icons.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Cache-first for static assets
  if (url.pathname.startsWith("/assets/")) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return cached || fetch(event.request).then((response) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, response.clone());
            return response;
          });
        });
      })
    );
    return;
  }

  // Network-first for everything else
  event.respondWith(
    fetch(event.request).then((response) => {
      return caches.open(CACHE_NAME).then((cache) => {
        cache.put(event.request, response.clone());
        return response;
      });
    }).catch(() => {
      return caches.match(event.request);
    })
  );
});
