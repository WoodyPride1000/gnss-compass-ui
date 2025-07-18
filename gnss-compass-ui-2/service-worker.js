const CACHE_NAME = "gnss-ui-cache-v1";
const OFFLINE_URLS = [
  "/",
  "/index.html",
  "/app.js",
  "/utm.min.js",
  "/tiles/"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(OFFLINE_URLS);
    })
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request);
    })
  );
});
