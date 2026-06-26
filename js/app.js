/* ============================================================
 *  index.html（トップ／スタンプ一覧）の処理
 * ============================================================ */

(function () {
  "use strict";

  var CFG = window.STAMP_CONFIG;
  var Store = window.StampStore;

  /* デバッグ用リセット：URLに ?reset=1 を付けるとスタンプを消去 */
  var params = new URLSearchParams(location.search);
  if (params.get("reset") === "1") {
    Store.resetAll();
    location.replace(location.pathname);
    return;
  }

  /* LocalStorage が使えない場合は警告だけ出す */
  if (!Store.isAvailable()) {
    document.getElementById("noStorageWarn").classList.remove("warn--hidden");
  }

  /* 初回アクセス時：参加者ID生成＋スタンプ状況を初期化 */
  var pid = Store.getParticipantId();
  Store.ensureInitialized();

  /* ---- ヘッダー・説明文 ---- */
  document.title = CFG.eventName + " スタンプラリー";
  document.getElementById("eventName").textContent = CFG.eventName;
  document.getElementById("eventTagline").textContent = CFG.eventTagline || "";
  document.getElementById("descBox").textContent = CFG.description || "";
  document.getElementById("participantId").textContent = "ID: " + pid;

  /* ---- 進捗 ---- */
  var stamps = Store.getStamps();
  var now = Object.keys(stamps).length;
  var total = CFG.totalStamps;
  var need = CFG.clearThreshold;

  document.getElementById("countNow").textContent = now;
  document.getElementById("countTotal").textContent = total;

  var pct = total > 0 ? Math.round((now / total) * 100) : 0;
  document.getElementById("progressFill").style.width = pct + "%";

  var cleared = now >= need;
  var complete = now >= total;

  var hint = document.getElementById("progressHint");
  if (complete) {
    hint.textContent = "すべてのスタンプを集めました！";
  } else if (cleared) {
    hint.textContent = "クリア条件を達成しました（あと " + (total - now) + " 個でコンプリート）";
  } else {
    hint.textContent = "クリアまであと " + (need - now) + " 個（クリア条件：" + need + "個）";
  }

  /* ---- クリア／コンプリート バナー ---- */
  var banner = document.getElementById("statusBanner");
  if (complete) {
    banner.classList.remove("banner--hidden");
    banner.classList.add("banner--complete");
    banner.innerHTML =
      '<div class="banner__big">🎉 コンプリート！</div>' +
      '<div class="banner__sub">全' + total + "個のスタンプを集めました！</div>" +
      '<div class="banner__prize">' + (CFG.prizeMessage || "") + "</div>";
  } else if (cleared) {
    banner.classList.remove("banner--hidden");
    banner.classList.add("banner--clear");
    banner.innerHTML =
      '<div class="banner__big">✨ クリア！</div>' +
      '<div class="banner__sub">スタンプを' + need + "個以上集めました！</div>" +
      '<div class="banner__prize">' + (CFG.prizeMessage || "") + "</div>";
  }

  /* ---- スタンプ一覧 ---- */
  var grid = document.getElementById("stampGrid");
  CFG.areas.forEach(function (area) {
    var got = Object.prototype.hasOwnProperty.call(stamps, area.code);

    var cell = document.createElement("div");
    cell.className = "stamp" + (got ? " stamp--got" : " stamp--locked");

    var imgWrap = document.createElement("div");
    imgWrap.className = "stamp__imgwrap";

    var img = document.createElement("img");
    img.className = "stamp__img";
    img.src = area.image;
    img.alt = got ? area.title + "（取得済み）" : area.title + "（未取得）";
    img.loading = "lazy";
    imgWrap.appendChild(img);

    if (!got) {
      var lock = document.createElement("div");
      lock.className = "stamp__lock";
      lock.textContent = "?";
      imgWrap.appendChild(lock);
    }

    var label = document.createElement("div");
    label.className = "stamp__label";
    label.textContent = area.label + " " + area.title;

    cell.appendChild(imgWrap);
    cell.appendChild(label);
    grid.appendChild(cell);
  });
})();
