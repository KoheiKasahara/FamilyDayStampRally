/* ============================================================
 *  stamp.html（QR読み取り後のスタンプ取得処理）
 *  URL形式:  stamp.html?area={areaCode}&key={secretKey}
 * ============================================================ */

(function () {
  "use strict";

  var CFG = window.STAMP_CONFIG;
  var Store = window.StampStore;

  var el = {
    icon: document.getElementById("resultIcon"),
    title: document.getElementById("resultTitle"),
    msg: document.getElementById("resultMsg"),
    stampWrap: document.getElementById("stampWrap"),
    stamp: document.getElementById("resultStamp"),
    progress: document.getElementById("resultProgress"),
    rCount: document.getElementById("rCount"),
    rTotal: document.getElementById("rTotal"),
    status: document.getElementById("resultStatus"),
    card: document.getElementById("resultCard")
  };

  function render(opts) {
    el.icon.textContent = opts.icon || "";
    el.title.textContent = opts.title || "";
    el.msg.textContent = opts.msg || "";
    el.card.className = "card result " + (opts.cls || "");

    if (opts.area) {
      el.stamp.src = opts.area.image;
      el.stamp.alt = opts.area.title;
      el.stampWrap.hidden = false;
    } else {
      el.stampWrap.hidden = true;
    }

    if (opts.showProgress) {
      el.rCount.textContent = Store.count();
      el.rTotal.textContent = CFG.totalStamps;
      el.progress.hidden = false;
    } else {
      el.progress.hidden = true;
    }

    el.status.textContent = opts.status || "";
  }

  /* ---- パラメータ取得 ---- */
  var params = new URLSearchParams(location.search);
  var areaCode = params.get("area");
  var key = params.get("key");

  /* LocalStorage 不可 */
  if (!Store.isAvailable()) {
    render({
      icon: "⚠️",
      title: "スタンプを保存できません",
      msg: "ブラウザの設定でデータ保存が無効になっています。プライベートモードを解除してお試しください。",
      cls: "result--error"
    });
    return;
  }

  /* 初回でもIDを用意し、初期化 */
  Store.getParticipantId();
  Store.ensureInitialized();

  /* ---- パラメータ検証 ---- */
  var area = null;
  for (var i = 0; i < CFG.areas.length; i++) {
    if (CFG.areas[i].code === areaCode) {
      area = CFG.areas[i];
      break;
    }
  }

  if (!areaCode || !key) {
    render({
      icon: "❓",
      title: "QRコードを読み取ってください",
      msg: "この画面は、会場のQRコードを読み取ると表示されます。お手数ですが各エリアのQRコードを読み取ってください。",
      cls: "result--error"
    });
    return;
  }

  if (!area || area.key !== key) {
    render({
      icon: "⚠️",
      title: "このQRコードは無効です",
      msg: "正しいスタンプQRコードではないようです。お近くのスタッフにお声がけください。",
      cls: "result--error"
    });
    return;
  }

  /* ---- スタンプ付与 ---- */
  var added = Store.addStamp(area.code);
  var cleared = Store.count() >= CFG.clearThreshold;
  var complete = Store.count() >= CFG.totalStamps;

  var statusText = "";
  if (complete) {
    statusText = "🎉 コンプリート！ 全てのスタンプを集めました！";
  } else if (cleared) {
    statusText = "✨ クリア！ 景品交換ができます。";
  }

  if (added) {
    render({
      icon: "✅",
      title: "スタンプGET！",
      msg: "「" + area.title + "」のスタンプを獲得しました！",
      area: area,
      cls: "result--success",
      showProgress: true,
      status: statusText
    });
  } else {
    render({
      icon: "ℹ️",
      title: "取得済みです",
      msg: "「" + area.title + "」のスタンプはすでに獲得しています。",
      area: area,
      cls: "result--info",
      showProgress: true,
      status: statusText
    });
  }
})();
