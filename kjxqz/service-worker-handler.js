if ('serviceWorker' in navigator) {
    var refreshing = false;
    var sw = navigator.serviceWorker;
    sw.addEventListener('controllerchange', function() {
        // Reload when the new Service Worker starts activating.
        // Why do it this way? Because it works even if there are multiple
        // open tabs. All of the tabs will display the “OK to reload?”
        // prompt; when the user clicks the “reload” link in any one of
        // them, the new Service Worker will take control of all of the
        // tabs, causing all of them to reload to the new version.

        if (refreshing) {
            return;
        }

        // Use `refreshing` to make sure the page is reloaded only once.
        // Otherwise an infinite reload loop may occur when using the
        // Chrome Developer Tools "Update on Reload" feature.

        refreshing = true;
        window.location.reload();
    });
    sw.register('/service-worker.js').then(function (swr) {
        // When the user requests a reload, post a message to the waiting
        // Service Worker, asking it to skipWaiting(), which will fire the
        // controllerchange event, which is configured to reload the page.

        function promptForReload() {
            if (window.confirm('New version available! OK to reload?')) {
                swr.waiting.postMessage('skipWaiting');
            }
        }

        // Wait for an installed Service Worker, then prompt the user to
        // reload.

        function waitForInstalled() {
            if (swr.waiting) {
                return promptForReload();
            }

            swr.installing.addEventListener('statechange', function() {
                if (this.state === 'installed') {
                    promptForReload();
                }
            });
        }

        // Listen for a waiting ServiceWorker, which requires some
        // inconvenient boilerplate code.
        //
        // The registration fires an "updatefound" event when there’s a
        // new installing Service Worker.
        //
        // The installing Service Worker fires a "statechange" event once
        // it’s in the “installed” waiting state.

        if (!swr) {
            return;
        }
        else if (swr.waiting) {
            return promptForReload();
        }
        else if (swr.installing) {
            waitForInstalled();
        }
        swr.addEventListener('updatefound', waitForInstalled);
    });
}
