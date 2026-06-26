# テスト

このプロジェクトには2系統のテストがあります。

## JS（フロント）— Vitest

`js/storage.js`（スタンプの保存・重複防止・リセット）と `js/config.js`（設定の整合性）を検証します。
`window` と `localStorage` を使うため jsdom 環境で実行します。

```bash
npm install      # 初回のみ（vitest, jsdom を取得）
npm test         # 1回実行
npm run test:watch   # 変更監視
```

対象: `tests/storage.test.js`, `tests/config.test.js`

## QR生成（ツール）— pytest

`tools/generate_qr.py` の符号化ロジックを、QR仕様に基づく不変条件で検証します。
画像デコーダ等の重い依存は使いません。

```bash
pip install pytest          # 初回のみ
python -m pytest tests/python/ -q
```

対象: `tests/python/test_generate_qr.py`

検証内容: GF(256)/Reed-Solomon、BCHフォーマット情報・バージョン情報（直近で
修正したビット順の回帰防止を含む）、バージョン選択、コードワード生成、行列サイズ・
ファインダパターン・決定性。
