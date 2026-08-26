const SW_VERSION='6.0.2';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil((async()=>{const k=await caches.keys();await Promise.all(k.map(x=>caches.delete(x)));await self.clients.claim()})()));
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==location.origin)return;e.respondWith((async()=>{try{return await fetch(r,{cache:'no-store'})}catch(x){return fetch(r)}})())});
