# ファミリーデー スタンプラリー（静的Webアプリ）

会場の各エリアに掲示したQRコードをスマホのカメラで読み取ると、スタンプが集まるWebアプリです。
**完全な静的サイト**（HTML / CSS / JavaScript のみ）で、サーバー・DB・ログインは使いません。
データはブラウザの LocalStorage に保存し、Service Worker でオフラインでも動作します（PWA対応）。

---

## フォルダ構成

```
60th FamilyDay スタンプラリー/
├─ index.html              … トップ／スタンプ一覧画面
├─ stamp.html              … QR読み取り後のスタンプ取得画面
├─ manifest.webmanifest    … PWA設定
├─ sw.js                   … Service Worker（オフライン対応）
├─ css/
│   └─ style.css
├─ js/
│   ├─ config.js           ★ 設定ファイル（ここだけ編集すればOK）
│   ├─ storage.js          … LocalStorage処理
│   ├─ app.js              … トップ画面の処理
│   └─ stamp.js            … スタンプ取得処理
├─ images/                 … スタンプ画像・ロゴ・アイコン（差し替え可）
│   ├─ logo.png
│   ├─ icon-192.png / icon-512.png
│   └─ stamp-1.png … stamp-8.png
├─ tools/                  … QRコード生成ツール（公開には不要）
│   ├─ generate_qr.py      … 各エリアのQRコード生成スクリプト（依存ライブラリ不要）
│   ├─ generate_qr_lib.py  … qrcodeライブラリ版の生成スクリプト（代替）
│   ├─ qr-generator.html   … ブラウザ上でQRを生成・確認するツール
│   ├─ qr-abtest.html      … QRの読み取り精度を比較する検証用ページ
│   └─ qr/                 … 生成物の出力先（area-*.svg/png, print.html など）
├─ tests/                  … 自動テスト（後述）
│   ├─ config.test.js      … config.js の整合性テスト（Vitest）
│   ├─ storage.test.js     … storage.js のテスト（Vitest）
│   ├─ python/
│   │   └─ test_generate_qr.py … generate_qr.py のテスト（pytest）
│   └─ README.md           … テストの実行方法
├─ package.json            … テスト用の設定（npm scripts / 開発依存）
├─ vitest.config.js        … Vitest 設定（jsdom 環境）
└─ README.md
```

> 画像はすべて**仮のプレースホルダー**です。記念ロゴ等に差し替えてください。

---

## 1. 設定を変える（js/config.js）

`js/config.js` を編集するだけで、内容を変更できます。HTMLは触りません。

- `eventName` … イベント名
- `description` … 説明文
- `totalStamps` … スタンプ総数（初期値 8）
- `clearThreshold` … クリアに必要な数（初期値 5）
- `areas` … 各エリアの `code`（QRのarea）/ `key`（QRのkey）/ `title`（エリア名）/ `image`（画像）

スタンプ数を変えたいときは `areas` を増減し、`totalStamps` をその数に合わせてください。

### QRコードの `key` について（重要）
このアプリは完全な静的サイトのため、`key` は技術的に「完全な秘密」にはできません
（ソースを見れば誰でも分かります）。
**QRを読み取らずに手入力でスタンプを増やす行為を防ぐ簡易チェック**としてのみ機能します。
不正対策が重要な場合は、景品交換所でのスタッフ確認で運用を担保してください。

---

## 2. スタンプ画像を差し替える

`images/` の中の画像を、同じファイル名で置き換えるだけです。

- スタンプ … `stamp-1.png` 〜 `stamp-8.png`（正方形・透過PNG推奨）
- ロゴ … `logo.png`
- アプリアイコン … `icon-192.png` / `icon-512.png`

ファイル名を変えたい場合は `config.js` の `image` も合わせて変更してください。
**画像を差し替えたら、`sw.js` の `CACHE_VERSION` の数字を1つ上げてください**（後述）。

---

## 3. QRコードを作る（tools/generate_qr.py）

GitHub Pages のURLが決まってから実行します。

1. `tools/generate_qr.py` の `BASE_URL` が本番URLになっているか確認する
   （現在 `https://koheikasahara.github.io/FamilyDayStampRally` に設定済み。
   公開先が変わる場合のみ書き換え。末尾スラッシュなし）
2. 実行（Python が必要）:
   ```
   pip install qrcode pillow
   python tools/generate_qr.py
   ```
3. `tools/qr/` に各エリアのQR画像（`area-A1.svg` / `area-A1.png` …）と、
   印刷用の `print.html` が生成されます。
   `print.html` をブラウザで開いてA4印刷し、各エリアに掲示してください。

QRの内容は `config.js` の `areas` から自動で読み込まれるので、
設定を変えたら再実行するだけです。

QRが指すURLの形式:
```
https://<...>/stamp.html?area=A1&key=g7k2
```

---

## 4. GitHub Pages に公開する

1. GitHub で新しいリポジトリを作成
2. このフォルダの中身を**すべて**アップロード（`tools/` は無くても動きます）
3. リポジトリの **Settings → Pages** を開く
4. **Source** で `main` ブランチ・`/ (root)` を選び保存
5. 数分後、`https://<ユーザー名>.github.io/<リポジトリ名>/` で公開されます
6. そのURLを `tools/generate_qr.py` の `BASE_URL` に設定し、QRを生成

> 補足：プロジェクトサイト（リポジトリ名がURLに入る形）でも動くように、
> アプリ内のパスはすべて相対パスにしてあります。

---

## 5. アプリを更新したとき（キャッシュ反映）

Service Worker が古いファイルをキャッシュし続けるのを防ぐため、
**HTML/CSS/JS/画像を更新したら `sw.js` の先頭の `CACHE_VERSION` を変更**してください。

```js
var CACHE_VERSION = "v1";  // → "v2" などに変更
```

利用者が次にアクセスしたときに、新しい内容が反映されます。

---

## 6. 動作の確認方法（ローカル）

`file://` で直接開くと Service Worker が動かないため、簡易サーバーで開きます。

```
cd "60th FamilyDay スタンプラリー"
python -m http.server 8000
```
ブラウザで `http://localhost:8000/` を開く。
スタンプ取得のテスト:
```
http://localhost:8000/stamp.html?area=A1&key=g7k2
```
スタンプをリセットしたいとき:
```
http://localhost:8000/index.html?reset=1
```

---

## 7. 自動テスト

ロジックの回帰を防ぐためのユニットテストを `tests/` に用意しています。詳細は
`tests/README.md` を参照してください。

```bash
npm install && npm test                 # JS（storage.js / config.js）
python -m pytest tests/python/ -q       # QR生成（generate_qr.py）
```

---

## 仕様まとめ

- 初回アクセス時に参加者IDを自動生成（家族名・人数などの入力は不要）
- スタンプ初期数 8 / クリア条件 5（`config.js` で変更可）
- 5個以上で「クリア！」、全部で「コンプリート！」表示
- 景品交換は景品交換所でスタッフが画面を確認して対応（交換済み管理・集計・管理画面なし）
- データはLocalStorageのみ。サーバー・DB・外部CDNは不使用
