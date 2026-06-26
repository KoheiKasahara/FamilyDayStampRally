# -*- coding: utf-8 -*-
"""generate_qr.py のユニットテスト（依存ライブラリ不要・pytest）。

QR の符号化ロジック（GF(256)/RS符号/BCHフォーマット・バージョン情報/
バージョン選択/コードワード生成/行列出力）を、QR仕様に基づく不変条件で検証する。
画像デコーダ等の重い依存は使わず、生成側の数学的性質をチェックする方針。
"""

import importlib.util
import os
import sys

import pytest

# tools/generate_qr.py を動的に読み込む
_HERE = os.path.dirname(__file__)
_QR_PATH = os.path.abspath(os.path.join(_HERE, "..", "..", "tools", "generate_qr.py"))
_spec = importlib.util.spec_from_file_location("generate_qr", _QR_PATH)
qr = importlib.util.module_from_spec(_spec)
sys.modules["generate_qr"] = qr
_spec.loader.exec_module(qr)


# ---------------- GF(256) / Reed-Solomon ----------------
class TestGaloisField:
    def test_gmul_identity(self):
        for a in (0, 1, 2, 87, 255):
            assert qr.gmul(a, 1) == a
            assert qr.gmul(1, a) == a

    def test_gmul_zero(self):
        assert qr.gmul(0, 123) == 0
        assert qr.gmul(123, 0) == 0

    def test_gmul_commutative(self):
        for a in (3, 17, 200):
            for b in (5, 99, 254):
                assert qr.gmul(a, b) == qr.gmul(b, a)

    def test_exp_log_inverse(self):
        # EXP/LOG が互いに逆対応であること（1..255）
        for a in range(1, 256):
            assert qr.EXP[qr.LOG[a]] == a


class TestReedSolomon:
    def test_generator_length(self):
        # n 次の生成多項式は係数 n+1 個、先頭は 1
        for n in (7, 10, 16):
            g = qr.rs_generator(n)
            assert len(g) == n + 1
            assert g[0] == 1

    def test_zero_data_gives_zero_ec(self):
        # 全ゼロのデータからは全ゼロのECコードワードになる
        ec = qr.rs_encode([0, 0, 0, 0], 10)
        assert ec == [0] * 10

    def test_ec_length_matches(self):
        ec = qr.rs_encode([32, 91, 11, 120], 10)
        assert len(ec) == 10


# ---------------- バージョン・容量 ----------------
class TestVersionCapacity:
    def test_total_data_codewords_matches_table(self):
        # EC_M テーブルから手計算した値（versions 1-10, level M）
        expected = {1: 16, 2: 28, 3: 44, 4: 64, 5: 86,
                    6: 108, 7: 124, 8: 154, 9: 182, 10: 216}
        for ver, cw in expected.items():
            assert qr.total_data_codewords(ver) == cw

    def test_char_count_bits(self):
        for ver in range(1, 10):
            assert qr.char_count_bits(ver) == 8
        assert qr.char_count_bits(10) == 16

    def test_pick_version_small_text(self):
        # 短い文字列は version 1 に収まる
        assert qr.pick_version(5) == 1

    def test_pick_version_monotonic(self):
        # 長くなるほどバージョンは下がらない
        prev = 0
        for n in (1, 16, 30, 60, 100, 150):
            v = qr.pick_version(n)
            assert v >= prev
            prev = v

    def test_pick_version_too_long_raises(self):
        with pytest.raises(ValueError):
            qr.pick_version(10000)


# ---------------- BCH（フォーマット情報・バージョン情報） ----------------
class TestBCHFormat:
    G_FORMAT = 0b10100110111
    MASK = 0b101010000010010  # QR 仕様のフォーマット情報マスク

    @staticmethod
    def _poly_mod(value, gen, value_bits):
        """value(value_bits ビット) を gen で割った剰余を返す（GF(2)多項式除算）"""
        gen_deg = gen.bit_length() - 1
        for i in range(value_bits - 1, gen_deg - 1, -1):
            if (value >> i) & 1:
                value ^= gen << (i - gen_deg)
        return value

    def test_mask0_is_known_constant(self):
        # data5=0 のとき、出力はマスク定数そのもの（仕様で確定値）
        assert qr.bch_format(0) == self.MASK

    def test_format_is_valid_bch_codeword(self):
        # マスクを外した 15bit は生成多項式で割り切れ、上位5bitがデータに一致する
        for data5 in range(32):
            code = qr.bch_format(data5) ^ self.MASK
            assert (code >> 10) == data5  # データ部
            assert self._poly_mod(code, self.G_FORMAT, 15) == 0  # 誤り訂正部が整合

    def test_format_is_15_bits(self):
        for data5 in range(32):
            assert 0 <= qr.bch_format(data5) <= 0x7FFF


class TestBCHVersion:
    G_VERSION = 0b1111100100101

    @staticmethod
    def _poly_mod(value, gen, value_bits):
        gen_deg = gen.bit_length() - 1
        for i in range(value_bits - 1, gen_deg - 1, -1):
            if (value >> i) & 1:
                value ^= gen << (i - gen_deg)
        return value

    def test_version_is_valid_bch_codeword(self):
        # バージョン情報は version 7 以上で使用。18bit、上位6bitがバージョン番号。
        for ver in range(7, 11):
            code = qr.bch_version(ver)
            assert (code >> 12) == ver
            assert self._poly_mod(code, self.G_VERSION, 18) == 0


# ---------------- コードワードストリーム ----------------
class TestCodewordStream:
    def test_stream_length_version1(self):
        # v1(level M): データ16 + EC10 = 26 コードワード
        stream = qr.make_codeword_stream("HELLO", 1)
        assert len(stream) == 16 + 10

    def test_encode_data_padded_to_capacity(self):
        cw = qr.encode_data("HI", 1)
        assert len(cw) == qr.total_data_codewords(1)
        # バイトモード(0100) + 文字数 のヘッダで始まる
        assert (cw[0] >> 4) == 0b0100


# ---------------- 行列生成（エンドツーエンド） ----------------
class TestGenerateMatrix:
    def test_matrix_size(self):
        m, ver = qr.generate("https://example.com/stamp")
        assert len(m) == 17 + 4 * ver
        assert all(len(row) == len(m) for row in m)

    def test_cells_are_binary(self):
        m, _ = qr.generate("TEST")
        for row in m:
            for cell in row:
                assert cell in (0, 1)

    def test_finder_patterns_present(self):
        # 3隅のファインダ中心(オフセット2,2)は黒、周囲リングは白
        m, _ = qr.generate("TEST")
        n = len(m)
        centers = [(2, 2), (2, n - 3), (n - 3, 2)]
        for (r, c) in centers:
            # 中央 3x3 は黒
            assert m[r][c] == 1
            # 1つ外のリングの一点は白（区切り）
            assert m[r - 1][c - 1] == 0

    def test_deterministic(self):
        a, va = qr.generate("DETERMINISTIC")
        b, vb = qr.generate("DETERMINISTIC")
        assert va == vb
        assert a == b
