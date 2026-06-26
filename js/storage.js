/* ============================================================
 *  LocalStorage 操作の共通処理
 *  - 参加者IDの自動生成
 *  - スタンプ取得状況の保存／読み出し
 * ============================================================ */

(function (global) {
  "use strict";

  var CFG = global.STAMP_CONFIG;
  var PREFIX = (CFG && CFG.storagePrefix) || "familyday_";

  var KEY_PID = PREFIX + "participantId";
  var KEY_STAMPS = PREFIX + "stamps";

  /* LocalStorage が使えるか（プライベートモード等の保険） */
  function isAvailable() {
    try {
      var t = "__t__";
      localStorage.setItem(t, t);
      localStorage.removeItem(t);
      return true;
    } catch (e) {
      return false;
    }
  }

  /* 参加者IDを生成（端末内でユニーク／個人情報は含めない） */
  function generateId() {
    var rnd = Math.random().toString(36).slice(2, 8);
    var time = Date.now().toString(36);
    return "P-" + time + "-" + rnd;
  }

  /* 参加者IDを取得。無ければ生成して保存 */
  function getParticipantId() {
    var id = null;
    try {
      id = localStorage.getItem(KEY_PID);
    } catch (e) {}
    if (!id) {
      id = generateId();
      try {
        localStorage.setItem(KEY_PID, id);
      } catch (e) {}
    }
    return id;
  }

  /* 取得済みスタンプを読み出す（{ areaCode: 取得時刻(ms) } 形式） */
  function getStamps() {
    try {
      var raw = localStorage.getItem(KEY_STAMPS);
      if (!raw) return {};
      var obj = JSON.parse(raw);
      return obj && typeof obj === "object" ? obj : {};
    } catch (e) {
      return {};
    }
  }

  /* スタンプ取得状況を初期化（空で保存） */
  function ensureInitialized() {
    try {
      if (localStorage.getItem(KEY_STAMPS) === null) {
        localStorage.setItem(KEY_STAMPS, JSON.stringify({}));
      }
    } catch (e) {}
  }

  /* スタンプを1つ追加。新規追加できたら true、既に持っていれば false */
  function addStamp(areaCode) {
    var stamps = getStamps();
    if (Object.prototype.hasOwnProperty.call(stamps, areaCode)) {
      return false; // 既に取得済み
    }
    stamps[areaCode] = Date.now();
    try {
      localStorage.setItem(KEY_STAMPS, JSON.stringify(stamps));
    } catch (e) {}
    return true;
  }

  function hasStamp(areaCode) {
    return Object.prototype.hasOwnProperty.call(getStamps(), areaCode);
  }

  function count() {
    return Object.keys(getStamps()).length;
  }

  /* すべてリセット（デバッグ用。?reset=1 で実行） */
  function resetAll() {
    try {
      localStorage.removeItem(KEY_STAMPS);
      localStorage.setItem(KEY_STAMPS, JSON.stringify({}));
    } catch (e) {}
  }

  global.StampStore = {
    isAvailable: isAvailable,
    getParticipantId: getParticipantId,
    getStamps: getStamps,
    ensureInitialized: ensureInitialized,
    addStamp: addStamp,
    hasStamp: hasStamp,
    count: count,
    resetAll: resetAll
  };
})(window);
