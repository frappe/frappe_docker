// Register service worker and manifest for Cosmos ERP PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/assets/cosmos_core/sw.js')
      .then(function (reg) {
        console.log('Cosmos PWA service worker registered.', reg);
      })
      .catch(function (err) {
        console.error('Cosmos PWA service worker registration failed:', err);
      });
  });
}

// Inject manifest link if not present
(function () {
  if (!document.querySelector('link[rel="manifest"]')) {
    var link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/assets/cosmos_core/manifest.json';
    document.head.appendChild(link);
  }
})();
