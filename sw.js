/* ============================================================
 *  Service Worker（オフライン対応）
 *
 *  アプリの内容（HTML/CSS/JS/画像）を更新したら、
 *  下の CACHE_VERSION の数字を1つ上げてください。
 *  これで利用者の端末に新しいファイルが反映されます。
 * ============================================================ */

var CACHE_VERSION = "v1";
var CACHE_NAME = "stamprally-" + CACHE_VERSION;

/* オフラインでも動くように事前キャッシュするファイル一覧 */
var PRECACHE = [
  "./",
  "./index.html",
  "./stamp.html",
  "./manifest.webmanifest",
  "./css/style.css",
  "./js/config.js",
  "./js/storage.js",
  "./js/app.js",
  "./js/stamp.js",
  "./images/logo.png",
  "./images/icon-192.png",
  "./images/icon-512.png",
  "./images/stamp-1.png",
  "./images/stamp-2.png",
  "./images/stamp-3.png",
  "./images/stamp-4.png",
  "./images/stamp-5.png",
  "./images/stamp-6.png",
  "./images/stamp-7.png",
  "./images/stamp-8.png"
];

/* インストール：必要ファイルをキャッシュ */
self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      /* 1ファイルでも失敗すると全体が失敗するため個別に追加 */
      return Promise.all(
        PRECACHE.map(function (url) {
          return cache.add(url).catch(function () {});
        })
      );
    })
  );
  self.skipWaiting();
});

/* 有効化：古いキャッシュを削除 */
self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.map(function (k) {
          if (k !== CACHE_NAME) return caches.delete(k);
        })
      );
    })
  );
  self.clients.claim();
});

/* 取得：キャッシュ優先（無ければネットワーク→取得できたらキャッシュ） */
self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;

  event.respondWith(
    caches.match(req).then(function (cached) {
      if (cached) return cached;
      return fetch(req)
        .then(function (res) {
          /* 同一オリジンの成功レスポンスのみキャッシュ */
          if (res && res.status === 200 && res.type === "basic") {
            var copy = res.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(req, copy);
            });
          }
          return res;
        })
        .catch(function () {
          /* オフラインでHTMLが見つからない場合はトップを返す */
          if (req.mode === "navigate") {
            return caches.match("./index.html");
          }
        });
    })
  );
});
