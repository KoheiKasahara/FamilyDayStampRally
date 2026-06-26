# -*- coding: utf-8 -*-
"""依存ライブラリ不要の QR コード生成器（Model2, バイトモード, ECレベルM）。
   versions 1-10 対応。標準テストベクタで自己検証してから使用する。"""

# ---------- GF(256) ----------
EXP = [0] * 512
LOG = [0] * 256
x = 1
for i in range(255):
    EXP[i] = x
    LOG[x] = i
    x <<= 1
    if x & 0x100:
        x ^= 0x11D
for i in range(255, 512):
    EXP[i] = EXP[i - 255]

def gmul(a, b):
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]

def rs_generator(n):
    g = [1]
    for i in range(n):
        ng = [0] * (len(g) + 1)
        for j in range(len(g)):
            ng[j] ^= g[j]
            ng[j + 1] ^= gmul(g[j], EXP[i])
        g = ng
    return g

def rs_encode(data, n):
    g = rs_generator(n)  # length n+1, g[0]==1
    res = [0] * n
    for d in data:
        factor = d ^ res[0]
        res = res[1:] + [0]
        for i in range(n):
            res[i] ^= gmul(g[i + 1], factor)
    return res

# ---------- EC characteristics (level M) ----------
# version: (ec_per_block, [(num_blocks, data_per_block), ...])
EC_M = {
    1:  (10, [(1, 16)]),
    2:  (16, [(1, 28)]),
    3:  (26, [(1, 44)]),
    4:  (18, [(2, 32)]),
    5:  (24, [(2, 43)]),
    6:  (16, [(4, 27)]),
    7:  (18, [(4, 31)]),
    8:  (22, [(2, 38), (2, 39)]),
    9:  (22, [(3, 36), (2, 37)]),
    10: (26, [(4, 43), (1, 44)]),
}

ALIGN = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
}

def total_data_codewords(ver):
    _, groups = EC_M[ver]
    return sum(nb * dpb for nb, dpb in groups)

def char_count_bits(ver):
    return 8 if ver <= 9 else 16

def pick_version(nbytes):
    for v in range(1, 11):
        cap = total_data_codewords(v)
        overhead_bits = 4 + char_count_bits(v)
        if nbytes * 8 + overhead_bits <= cap * 8:
            return v
    raise ValueError("データが長すぎます（v10超）")

# ---------- encode data ----------
def encode_data(text, ver):
    data = text.encode("utf-8")
    cap = total_data_codewords(ver)
    bits = []
    def put(val, n):
        for i in range(n - 1, -1, -1):
            bits.append((val >> i) & 1)
    put(0b0100, 4)                       # byte mode
    put(len(data), char_count_bits(ver)) # char count
    for b in data:
        put(b, 8)
    # terminator
    rem = cap * 8 - len(bits)
    put(0, min(4, rem))
    # pad to byte boundary
    while len(bits) % 8 != 0:
        bits.append(0)
    # pad bytes
    codewords = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = [0xEC, 0x11]
    i = 0
    while len(codewords) < cap:
        codewords.append(pad[i % 2])
        i += 1
    return codewords

def make_codeword_stream(text, ver):
    data_cw = encode_data(text, ver)
    ec_per_block, groups = EC_M[ver]
    blocks = []
    idx = 0
    for nb, dpb in groups:
        for _ in range(nb):
            blk = data_cw[idx:idx + dpb]
            idx += dpb
            blocks.append((blk, rs_encode(blk, ec_per_block)))
    # interleave data
    stream = []
    maxd = max(len(b[0]) for b in blocks)
    for i in range(maxd):
        for blk, _ in blocks:
            if i < len(blk):
                stream.append(blk[i])
    for i in range(ec_per_block):
        for _, ec in blocks:
            stream.append(ec[i])
    return stream

# ---------- matrix ----------
class Matrix:
    def __init__(self, ver):
        self.ver = ver
        self.size = 17 + 4 * ver
        n = self.size
        self.m = [[0] * n for _ in range(n)]      # module value 0/1
        self.f = [[False] * n for _ in range(n)]  # function/reserved

    def set(self, r, c, v, func=True):
        self.m[r][c] = v & 1
        self.f[r][c] = func

    def place_finder(self, r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                rr, cc = r + dr, c + dc
                if 0 <= rr < self.size and 0 <= cc < self.size:
                    if dr in (-1, 7) or dc in (-1, 7):
                        self.set(rr, cc, 0)            # separator
                    else:
                        inring = (dr in (0, 6) or dc in (0, 6))
                        incore = (2 <= dr <= 4 and 2 <= dc <= 4)
                        self.set(rr, cc, 1 if (inring or incore) else 0)

    def place_alignment(self, r, c):
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                edge = max(abs(dr), abs(dc))
                self.set(r + dr, c + dc, 1 if edge != 1 else 0)

    def build_function(self):
        n = self.size
        self.place_finder(0, 0)
        self.place_finder(0, n - 7)
        self.place_finder(n - 7, 0)
        # timing
        for i in range(8, n - 8):
            v = 1 if i % 2 == 0 else 0
            self.set(6, i, v)
            self.set(i, 6, v)
        # alignment
        centers = ALIGN[self.ver]
        for r in centers:
            for c in centers:
                if (r < 8 and c < 8) or (r < 8 and c > n - 9) or (r > n - 9 and c < 8):
                    continue
                self.place_alignment(r, c)
        # dark module
        self.set(4 * self.ver + 9, 8, 1)
        # reserve format areas
        for i in range(9):
            if i != 6:
                self.reserve(8, i)
                self.reserve(i, 8)
        for i in range(8):
            self.reserve(8, n - 1 - i)
            self.reserve(n - 1 - i, 8)
        # reserve version areas (v>=7)
        if self.ver >= 7:
            for r in range(6):
                for c in range(n - 11, n - 8):
                    self.reserve(r, c)
                    self.reserve(c, r)

    def reserve(self, r, c):
        self.f[r][c] = True

    def place_data(self, stream):
        n = self.size
        bitlist = []
        for cw in stream:
            for i in range(7, -1, -1):
                bitlist.append((cw >> i) & 1)
        idx = 0
        upward = True
        col = n - 1
        while col > 0:
            if col == 6:
                col -= 1  # skip timing column
            rows = range(n - 1, -1, -1) if upward else range(n)
            for r in rows:
                for c in (col, col - 1):
                    if not self.f[r][c]:
                        bit = bitlist[idx] if idx < len(bitlist) else 0
                        self.m[r][c] = bit
                        idx += 1
            upward = not upward
            col -= 2

    def apply_mask(self, mask):
        n = self.size
        out = Matrix(self.ver)
        out.m = [row[:] for row in self.m]
        out.f = [row[:] for row in self.f]
        for r in range(n):
            for c in range(n):
                if self.f[r][c]:
                    continue
                if mask == 0: cond = (r + c) % 2 == 0
                elif mask == 1: cond = r % 2 == 0
                elif mask == 2: cond = c % 3 == 0
                elif mask == 3: cond = (r + c) % 3 == 0
                elif mask == 4: cond = (r // 2 + c // 3) % 2 == 0
                elif mask == 5: cond = (r * c) % 2 + (r * c) % 3 == 0
                elif mask == 6: cond = ((r * c) % 2 + (r * c) % 3) % 2 == 0
                else: cond = ((r + c) % 2 + (r * c) % 3) % 2 == 0
                if cond:
                    out.m[r][c] ^= 1
        return out

    def penalty(self):
        n = self.size
        m = self.m
        score = 0
        # rule 1: runs
        for line in list(m) + [list(col) for col in zip(*m)]:
            run = 1
            for i in range(1, n):
                if line[i] == line[i - 1]:
                    run += 1
                else:
                    if run >= 5:
                        score += 3 + (run - 5)
                    run = 1
            if run >= 5:
                score += 3 + (run - 5)
        # rule 2: 2x2 blocks
        for r in range(n - 1):
            for c in range(n - 1):
                if m[r][c] == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                    score += 3
        # rule 3: finder-like patterns
        pat1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
        pat2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
        for line in list(m) + [list(col) for col in zip(*m)]:
            for i in range(n - 10):
                seg = line[i:i + 11]
                if seg == pat1 or seg == pat2:
                    score += 40
        # rule 4: dark ratio
        dark = sum(sum(row) for row in m)
        pct = dark * 100.0 / (n * n)
        score += int(abs(pct - 50) // 5) * 10
        return score

# ---------- format & version info ----------
def bch_format(data5):
    g = 0b10100110111
    v = data5 << 10
    for i in range(14, 9, -1):
        if (v >> i) & 1:
            v ^= g << (i - 10)
    return ((data5 << 10) | v) ^ 0b101010000010010

def bch_version(ver):
    g = 0b1111100100101
    v = ver << 12
    for i in range(17, 11, -1):
        if (v >> i) & 1:
            v ^= g << (i - 12)
    return (ver << 12) | v

EC_BITS_M = 0b00  # level M

def place_format(mat, mask):
    n = mat.size
    bits = bch_format((EC_BITS_M << 3) | mask)
    arr = [(bits >> (14 - i)) & 1 for i in range(15)]  # MSB first（実機スキャナ準拠）
    # copy 1 (around top-left)
    coords1 = [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
               (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8)]
    for (r, c), b in zip(coords1, arr):
        mat.m[r][c] = b
        mat.f[r][c] = True
    # copy 2
    coords2 = [(n - 1, 8), (n - 2, 8), (n - 3, 8), (n - 4, 8), (n - 5, 8), (n - 6, 8), (n - 7, 8),
               (8, n - 8), (8, n - 7), (8, n - 6), (8, n - 5), (8, n - 4), (8, n - 3), (8, n - 2), (8, n - 1)]
    for (r, c), b in zip(coords2, arr):
        mat.m[r][c] = b
        mat.f[r][c] = True

def place_version(mat):
    if mat.ver < 7:
        return
    n = mat.size
    bits = bch_version(mat.ver)
    arr = [(bits >> i) & 1 for i in range(18)]  # LSB..MSB index
    k = 0
    for c in range(6):
        for r in range(n - 11, n - 8):
            mat.m[r][c] = arr[k]
            mat.f[r][c] = True
            mat.m[c][r] = arr[k]
            mat.f[c][r] = True
            k += 1

# ---------- top level ----------
def generate(text):
    ver = pick_version(len(text.encode("utf-8")))
    stream = make_codeword_stream(text, ver)
    base = Matrix(ver)
    base.build_function()
    base.place_data(stream)
    best = None
    for mask in range(8):
        cand = base.apply_mask(mask)
        place_format(cand, mask)
        place_version(cand)
        p = cand.penalty()
        if best is None or p < best[0]:
            best = (p, cand)
    return best[1].m, ver

def matrix_to_png(m, path, box=10, border=4, dark=(58, 42, 34)):
    from PIL import Image
    n = len(m)
    size = (n + border * 2) * box
    img = Image.new("RGB", (size, size), (255, 255, 255))
    px = img.load()
    for r in range(n):
        for c in range(n):
            if m[r][c]:
                for dy in range(box):
                    for dx in range(box):
                        px[(c + border) * box + dx, (r + border) * box + dy]
def matrix_to_svg(m, path, box=10, border=4, dark="#3a2a22"):
    n = len(m)
    dim = (n + border * 2) * box
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d" shape-rendering="crispEdges">' % (dim, dim, dim, dim)]
    parts.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (dim, dim))
    for r in range(n):
        for c in range(n):
            if m[r][c]:
                parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>'
                             % ((c + border) * box, (r + border) * box, box, box, dark))
    parts.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(parts))

# ============================================================
#  以下、コマンド実行部（依存ライブラリ不要）
#  PNGは Pillow があれば生成、無くても SVG は必ず生成します。
# ============================================================
def render_png(m, path, box=12, border=4, dark=(58, 42, 34)):
    from PIL import Image
    n = len(m); size = (n + border * 2) * box
    img = Image.new("RGB", (size, size), (255, 255, 255)); px = img.load()
    for r in range(n):
        for c in range(n):
            if m[r][c]:
                for dy in range(box):
                    for dx in range(box):
                        px[(c + border) * box + dx, (r + border) * box + dy] = dark
    img.save(path)


if __name__ == "__main__":
    import os, re

    # ▼▼▼ GitHub Pages 公開後、本番URLに書き換えてください（末尾スラッシュなし）▼▼▼
    BASE_URL = "https://koheikasahara.github.io/FamilyDayStampRally"
    # ▲▲▲ 例: https://<ユーザー名>.github.io/<リポジトリ名> ▲▲▲

    HERE = os.path.dirname(os.path.abspath(__file__))
    cfg = open(os.path.join(HERE, "..", "js", "config.js"), encoding="utf-8").read()
    pat = re.compile(r'code:\s*"([^"]+)"\s*,\s*key:\s*"([^"]+)"\s*,\s*label:\s*"([^"]*)"\s*,\s*title:\s*"([^"]+)"')
    areas = [{"code": a, "key": b, "label": c, "title": d} for a, b, c, d in pat.findall(cfg)]
    if not areas:
        raise SystemExit("config.js からエリアを読み取れませんでした。")

    OUT = os.path.join(HERE, "qr")
    os.makedirs(OUT, exist_ok=True)
    have_pil = True
    try:
        import PIL  # noqa
    except ImportError:
        have_pil = False
        print("※ Pillow が無いため SVG のみ生成します（PNGが必要なら: pip install pillow）")

    rows = []
    for a in areas:
        url = "{0}/stamp.html?area={1}&key={2}".format(BASE_URL, a["code"], a["key"])
        m, ver = generate(url)
        matrix_to_svg(m, os.path.join(OUT, "area-{0}.svg".format(a["code"])))
        if have_pil:
            render_png(m, os.path.join(OUT, "area-{0}.png".format(a["code"])))
        rows.append((a, url))
        print("生成: area-{0} (v{1})  {2}".format(a["code"], ver, url))

    ext = "png" if have_pil else "svg"
    cards = "\n".join(
        '<div class="card"><div class="t">{lab} {title}</div>'
        '<img src="area-{code}.{ext}" alt=""><div class="c">area={code} / key={key}</div></div>'.format(
            lab=a["label"], title=a["title"], code=a["code"], key=a["key"], ext=ext)
        for (a, url) in rows)
    sample = " ※サンプルURLのままです。BASE_URLを本番に変えて再実行してください。" if "example.github.io" in BASE_URL else ""
    html = ('<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>スタンプQR 印刷用</title>'
            '<style>body{font-family:sans-serif;margin:0;padding:16px;color:#3a2a22}'
            'h1{font-size:18px}.note{color:#a33;font-size:13px;margin:4px 0 14px}'
            '.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}'
            '.card{border:2px dashed #ccc;border-radius:12px;padding:14px;text-align:center;page-break-inside:avoid}'
            '.card img{width:78%;max-width:300px}.t{font-size:19px;font-weight:bold;margin-bottom:6px}'
            '.c{color:#888;font-size:11px;margin-top:6px}@media print{.note{display:none}}</style></head><body>'
            '<h1>各エリア掲示用QRコード（A4印刷推奨）</h1>'
            '<div class="note">QRの内容: ' + BASE_URL + '/stamp.html?area=...&key=...' + sample + '</div>'
            '<div class="grid">' + cards + '</div></body></html>')
    open(os.path.join(OUT, "print.html"), "w", encoding="utf-8").write(html)
    print("\n完了。tools/qr/print.html をブラウザで開いて印刷してください。")
