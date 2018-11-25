CACHE_HASH = 'kjxqz-1543184507'

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_HASH).then(function(cache) {
            return cache.addAll([
                '/',
                '/index.html',
                '/dawg.js',
            ]);
        })
    );
});

self.addEventListener('message', function(event) {
    if (event.data == 'skipWaiting') {
        self.skipWaiting();
    }
});

self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(keys.map(function (key) {
                if (key !== CACHE_HASH) {
                    return caches.delete(key);
                }
            }));
        })
    );
});

self.addEventListener('fetch', function(event) {
    if (event.request.url.startsWith(self.location.origin)) {
        event.respondWith(
            caches.open(CACHE_HASH).then(function(cache) {
                return cache.match(event.request).then(function (response) {
                    return response || fetch(event.request).then(
                        function(response) {
                            cache.put(event.request, response.clone());
                            return response;
                        }
                    );
                });
            })
        );
    }
});
