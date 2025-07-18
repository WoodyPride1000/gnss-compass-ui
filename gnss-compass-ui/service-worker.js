self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.open('tile-cache').then(function(cache) {
      return cache.match(event.request).then(function (response) {
        return response || fetch(event.request).then(function(networkResponse) {
          if (event.request.url.includes('/tiles/')) {
            cache.put(event.request, networkResponse.clone());
          }
          return networkResponse;
        });
      });
    })
  );
});