# テスト

このプロジェクトには2系統のテストがあります。**どちらも追加インストール不要**で、
Node と Python の標準機能だけで実行できます（pip / npm のパッケージ取得が制限された
環境でも動きます）。

## JS（フロント）— Node 内蔵テストランナー

`js/storage.js`（スタンプの保存・重複防止・リセット）と `js/config.js`（設定の整合性）を
検証します。`window` と `localStorage` はテスト側で最小実装しているため、
jsdom などのライブラリは不要です。

```bash
npm test                 # = node --test "tests/**/*.test.js"
npm run test:watch       # 変更監視

# npm を使わず node だけでも実行できます
node --test "tests/**/*.test.js"
```

対象: `tests/storage.test.js`, `tests/config.test.js`, `tests/helpers/load-app.js`（読み込み補助）

## QR生成（ツール）— Python 標準ライブラリ unittest

`tools/generate_qr.py` の符号化ロジックを、QR仕様に基づく不変条件で検証します。
画像デコーダ等の重い依存は使いません。

```bash
python -m unittest discover -s tests/python -v
# pytest がある環境なら pytest tests/python でも実行可
```

対象: `tests/python/test_generate_qr.py`

検証内容: GF(256)/Reed-Solomon、BCHフォーマット情報・バージョン情報（直近で
修正したビット順の回帰防止を含む）、バージョン選択、コードワード生成、行列サイズ・
ファインダパターン・決定性。
