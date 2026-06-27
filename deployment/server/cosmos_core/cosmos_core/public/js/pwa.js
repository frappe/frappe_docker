(function() {
  function addMeta(name, content) {
    var el = document.createElement("meta");
    el.name = name;
    el.content = content;
    document.head.appendChild(el);
  }
  function addLink(rel, href, extra) {
    var el = document.createElement("link");
    el.rel = rel;
    el.href = href;
    if (extra) Object.assign(el, extra);
    document.head.appendChild(el);
  }
  addLink("manifest", "/files/pwa/manifest.json");
  addMeta("theme-color", "#24963f");
  addLink("apple-touch-icon", "/files/pwa/cosmos-192.png");
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function() {
      navigator.serviceWorker.register("/service-worker.js").then(function(reg) {
        console.log("CosmOS PWA ready", reg.scope);
      }).catch(function(err) {
        console.log("CosmOS PWA error", err);
      });
    });
  }
})();
