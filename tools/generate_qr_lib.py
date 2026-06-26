# -*- coding: utf-8 -*-
"""
実績のあるライブラリ（qrcode）でQRを生成する版。
お使いのPCで実行してください（ネット接続が必要なのは初回の pip だけ）。

使い方:
    pip install qrcode pillow
    python tools/generate_qr_lib.py

config.js の areas（code / key）を読み込み、BASE_URL と組み合わせて
各エリアのQRを tools/qr/ に出力します。
- area-XX.png        … 通常サイズ
- area-XX_large.png  … 大きめ（画面/印刷でも読み取りやすい）
- print.html         … 印刷用（1ページ2枚・大きめ）
"""

import os
import re

# ▼ 本番URL（末尾スラッシュなし）。GitHub Pages のトップ。
BASE_URL = "https://koheikasahara.github.io/FamilyDayStampRally"

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
    except ImportError:
        raise SystemExit("先に実行してください:  pip install qrcode pillow")

    cfg = open(os.path.join(HERE, "..", "js", "config.js"), encoding="utf-8").read()
    pat = re.compile(r'code:\s*"([^"]+)"\s*,\s*key:\s*"([^"]+)"\s*,\s*label:\s*"([^"]*)"\s*,\s*title:\s*"([^"]+)"')
    areas = [{"code": a, "key": b, "label": c, "title": d} for a, b, c, d in pat.findall(cfg)]
    if not areas:
        raise SystemExit("config.js からエリアを読み取れませんでした。")

    out = os.path.join(HERE, "qr")
    os.makedirs(out, exist_ok=True)

    rows = []
    for a in areas:
        url = "{0}/stamp.html?area={1}&key={2}".format(BASE_URL, a["code"], a["key"])
        # box_size を大きく、border(余白)は最低4で確保
        for suffix, box in (("", 10), ("_large", 18)):
            qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=box, border=4)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(os.path.join(out, "area-{0}{1}.png".format(a["code"], suffix)))
        rows.append((a, url))
        print("生成: area-{0}  {1}".format(a["code"], url))

    cards = "\n".join(
        '<div class="card"><div class="t">{lab} {title}</div>'
        '<img src="area-{code}_large.png" alt=""><div class="c">{url}</div></div>'.format(
            lab=a["label"], title=a["title"], code=a["code"], url=url)
        for (a, url) in rows)
    html = ('<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">'
            '<title>スタンプQR 印刷用</title><style>'
            'body{font-family:sans-serif;margin:0;padding:16px;color:#222}'
            'h1{font-size:18px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}'
            '.card{border:2px dashed #bbb;border-radius:12px;padding:18px;text-align:center;page-break-inside:avoid}'
            '.card img{width:90%;max-width:340px}.t{font-size:22px;font-weight:bold;margin-bottom:8px}'
            '.c{color:#999;font-size:10px;margin-top:8px;word-break:break-all}'
            '@media print{.c{display:none}}</style></head><body>'
            '<h1>各エリア掲示用QRコード</h1><div class="grid">' + cards + '</div></body></html>')
    open(os.path.join(out, "print.html"), "w", encoding="utf-8").write(html)
    print("\n完了。tools/qr/print.html を開いて印刷してください。")


if __name__ == "__main__":
    main()
