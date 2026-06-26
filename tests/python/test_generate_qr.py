# -*- coding: utf-8 -*-
"""generate_qr.py のユニットテスト（標準ライブラリの unittest のみ・インストール不要）。

実行:  python -m unittest discover -s tests/python -v
（pytest があれば pytest tests/python でも実行可能）

QR の符号化ロジックを、QR仕様に基づく不変条件で検証する。画像デコーダ等の重い
依存は使わず、生成側の数学的性質をチェックする方針。
"""

import importlib.util
import os
import sys
import unittest

# tools/generate_qr.py を動的に読み込む
_HERE = os.path.dirname(__file__)
_QR_PATH = os.path.abspath(os.path.join(_HERE, "..", "..", "tools", "generate_qr.py"))
_spec = importlib.util.spec_from_file_location("generate_qr", _QR_PATH)
qr = importlib.util.module_from_spec(_spec)
sys.modules["generate_qr"] = qr
_spec.loader.exec_module(qr)


def poly_mod(value, gen, value_bits):
    """value(value_bits ビット) を gen で割った剰余（GF(2)多項式除算）。"""
    gen_deg = gen.bit_length() - 1
    for i in range(value_bits - 1, gen_deg - 1, -1):
        if (value >> i) & 1:
            value ^= gen << (i - gen_deg)
    return value


# ---------------- GF(256) / Reed-Solomon ----------------
class TestGaloisField(unittest.TestCase):
    def test_gmul_identity(self):
        for a in (0, 1, 2, 87, 255):
            self.assertEqual(qr.gmul(a, 1), a)
            self.assertEqual(qr.gmul(1, a), a)

    def test_gmul_zero(self):
        self.assertEqual(qr.gmul(0, 123), 0)
        self.assertEqual(qr.gmul(123, 0), 0)

    def test_gmul_commutative(self):
        for a in (3, 17, 200):
            for b in (5, 99, 254):
                self.assertEqual(qr.gmul(a, b), qr.gmul(b, a))

    def test_exp_log_inverse(self):
        for a in range(1, 256):
            self.assertEqual(qr.EXP[qr.LOG[a]], a)


class TestReedSolomon(unittest.TestCase):
    def test_generator_length(self):
        for n in (7, 10, 16):
            g = qr.rs_generator(n)
            self.assertEqual(len(g), n + 1)
            self.assertEqual(g[0], 1)

    def test_zero_data_gives_zero_ec(self):
        self.assertEqual(qr.rs_encode([0, 0, 0, 0], 10), [0] * 10)

    def test_ec_length_matches(self):
        self.assertEqual(len(qr.rs_encode([32, 91, 11, 120], 10)), 10)


# ---------------- バージョン・容量 ----------------
class TestVersionCapacity(unittest.TestCase):
    def test_total_data_codewords_matches_table(self):
        # EC_M テーブルから手計算した値（versions 1-10, level M）
        expected = {1: 16, 2: 28, 3: 44, 4: 64, 5: 86,
                    6: 108, 7: 124, 8: 154, 9: 182, 10: 216}
        for ver, cw in expected.items():
            self.assertEqual(qr.total_data_codewords(ver), cw)

    def test_char_count_bits(self):
        for ver in range(1, 10):
            self.assertEqual(qr.char_count_bits(ver), 8)
        self.assertEqual(qr.char_count_bits(10), 16)

    def test_pick_version_small_text(self):
        self.assertEqual(qr.pick_version(5), 1)

    def test_pick_version_monotonic(self):
        prev = 0
        for n in (1, 16, 30, 60, 100, 150):
            v = qr.pick_version(n)
            self.assertGreaterEqual(v, prev)
            prev = v

    def test_pick_version_too_long_raises(self):
        with self.assertRaises(ValueError):
            qr.pick_version(10000)


# ---------------- BCH（フォーマット情報・バージョン情報） ----------------
class TestBCHFormat(unittest.TestCase):
    G_FORMAT = 0b10100110111
    MASK = 0b101010000010010  # QR 仕様のフォーマット情報マスク

    def test_mask0_is_known_constant(self):
        # data5=0 のとき、出力はマスク定数そのもの（仕様で確定値）
        self.assertEqual(qr.bch_format(0), self.MASK)

    def test_format_is_valid_bch_codeword(self):
        # マスクを外した 15bit は生成多項式で割り切れ、上位5bitがデータに一致
        for data5 in range(32):
            code = qr.bch_format(data5) ^ self.MASK
            self.assertEqual(code >> 10, data5)
            self.assertEqual(poly_mod(code, self.G_FORMAT, 15), 0)

    def test_format_is_15_bits(self):
        for data5 in range(32):
            self.assertGreaterEqual(qr.bch_format(data5), 0)
            self.assertLessEqual(qr.bch_format(data5), 0x7FFF)


class TestBCHVersion(unittest.TestCase):
    G_VERSION = 0b1111100100101

    def test_version_is_valid_bch_codeword(self):
        # バージョン情報は version 7 以上で使用。18bit、上位6bitがバージョン番号。
        for ver in range(7, 11):
            code = qr.bch_version(ver)
            self.assertEqual(code >> 12, ver)
            self.assertEqual(poly_mod(code, self.G_VERSION, 18), 0)


# ---------------- コードワードストリーム ----------------
class TestCodewordStream(unittest.TestCase):
    def test_stream_length_version1(self):
        # v1(level M): データ16 + EC10 = 26 コードワード
        self.assertEqual(len(qr.make_codeword_stream("HELLO", 1)), 16 + 10)

    def test_encode_data_padded_to_capacity(self):
        cw = qr.encode_data("HI", 1)
        self.assertEqual(len(cw), qr.total_data_codewords(1))
        # バイトモード(0100)で始まる
        self.assertEqual(cw[0] >> 4, 0b0100)


# ---------------- 行列生成（エンドツーエンド） ----------------
class TestGenerateMatrix(unittest.TestCase):
    def test_matrix_size(self):
        m, ver = qr.generate("https://example.com/stamp")
        self.assertEqual(len(m), 17 + 4 * ver)
        self.assertTrue(all(len(row) == len(m) for row in m))

    def test_cells_are_binary(self):
        m, _ = qr.generate("TEST")
        for row in m:
            for cell in row:
                self.assertIn(cell, (0, 1))

    def test_finder_patterns_present(self):
        # 3隅のファインダ中心(オフセット2,2)は黒、区切りは白
        m, _ = qr.generate("TEST")
        n = len(m)
        for (r, c) in [(2, 2), (2, n - 3), (n - 3, 2)]:
            self.assertEqual(m[r][c], 1)
            self.assertEqual(m[r - 1][c - 1], 0)

    def test_deterministic(self):
        a, va = qr.generate("DETERMINISTIC")
        b, vb = qr.generate("DETERMINISTIC")
        self.assertEqual(va, vb)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
