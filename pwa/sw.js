// Offline cache for Borrowed Time. Bump VERSION whenever index.html changes so phones pick up the new build.
const VERSION='borrowed-time-20261115-0151', CORE=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{ e.waitUntil(caches.open(VERSION).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())); });
self.addEventListener('activate',e=>{ e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener('fetch',e=>{ const r=e.request; if(r.method!=='GET') return;
  // the pinned Rapier build is cached too, so demolition physics keeps working offline after the first online launch
  const cacheable=u=>u.startsWith(self.location.origin)||/^https:\/\/fonts\.(googleapis|gstatic)\.com\//.test(u)||u.startsWith('https://cdn.jsdelivr.net/npm/@dimforge/rapier3d-compat@0.21.0/');
  e.respondWith(caches.match(r).then(hit=>{ const net=fetch(r).then(res=>{ if(res&&(res.ok||res.type==='opaque')&&cacheable(r.url)){ const cp=res.clone(); caches.open(VERSION).then(c=>c.put(r,cp)); } return res; }).catch(()=>hit);
    return hit||net; })); });
