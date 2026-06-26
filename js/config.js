/* ============================================================
 *  スタンプラリー 設定ファイル
 *  ここを編集するだけで、イベント名・エリア・クリア条件などを
 *  変更できます。HTML/CSS を触る必要はありません。
 * ============================================================ */

const STAMP_CONFIG = {
  /* ---- イベント基本情報（index.html に表示されます） ---- */
  eventName: "創立60周年 ファミリーデー",
  eventTagline: "会場をまわってスタンプを集めよう！",
  description:
    "会場の各エリアに設置されたQRコードを、スマートフォンのカメラで読み取るとスタンプが押されます。" +
    "スタンプを5個以上集めると「クリア」、8個すべて集めると「コンプリート」です。",

  /* ---- クリア条件 ----
   * totalStamps   : スタンプの総数（areas の数と一致させてください）
   * clearThreshold: クリアに必要なスタンプ数
   */
  totalStamps: 8,
  clearThreshold: 5,

  /* ---- 景品交換の案内文（クリア時に表示） ---- */
  prizeMessage: "この画面を景品交換所のスタッフにお見せください。",

  /* ---- LocalStorage のキー接頭辞（通常は変更不要） ---- */
  storagePrefix: "familyday60_",

  /* ---- アプリのバージョン ----
   * Service Worker のキャッシュ更新に使います。
   * 内容を更新したら数字を上げてください（例: "1.0.1"）。
   */
  appVersion: "1.0.0",

  /* ---- エリア定義 ----
   * code  : QR の area パラメータ（重複しない英数字）
   * key   : QR の key パラメータ（手入力での不正取得を防ぐ簡易キー）
   * label : 一覧での番号表示
   * title : エリア名（スタンプの名前）
   * image : スタンプ画像のパス（images/ 配下に差し替え可能）
   *
   * ※ 完全な静的アプリのため key は「完全な秘密」にはできません。
   *   QRを読まずに手入力でスタンプを増やす行為を防ぐ簡易チェック用です。
   */
  areas: [
    { code: "A1", key: "g7k2", label: "①", title: "うけつけ広場",   image: "images/stamp-1.png" },
    { code: "A2", key: "m4q9", label: "②", title: "ステージ前",     image: "images/stamp-2.png" },
    { code: "A3", key: "x1p6", label: "③", title: "キッズコーナー", image: "images/stamp-3.png" },
    { code: "A4", key: "t8b3", label: "④", title: "工場見学入口",   image: "images/stamp-4.png" },
    { code: "A5", key: "v5w0", label: "⑤", title: "ふれあい動物園", image: "images/stamp-5.png" },
    { code: "A6", key: "n2c7", label: "⑥", title: "キッチンカー前", image: "images/stamp-6.png" },
    { code: "A7", key: "j9r4", label: "⑦", title: "ゲームひろば",   image: "images/stamp-7.png" },
    { code: "A8", key: "h6s1", label: "⑧", title: "写真スポット",   image: "images/stamp-8.png" }
  ]
};

/* 他スクリプトから参照できるように公開 */
window.STAMP_CONFIG = STAMP_CONFIG;
