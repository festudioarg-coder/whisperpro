// Guarda los archivos de la app para que abra al instante y sin conexión.
// (Dictar sí necesita internet: el audio se transcribe en Groq.) Nunca guarda ni toca las llamadas a Groq.
const CACHE = "wp-v1";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png",
  "fonts/Bricolage.woff2", "fonts/MartianMono.woff2"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;   // Groq y todo lo externo: directo, sin pasar por acá
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)));
});
