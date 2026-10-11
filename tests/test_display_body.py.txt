# -*- coding: utf-8 -*-
"""display_body：CR-LF 终止符在关闭转义时不应残留裸 CR（豆腐块）。"""
import unittest

from ecom import codec


class TestDisplayBody(unittest.TestCase):
    def test_crlf_off_strips_trailing_cr(self):
        # b"AT\r\n" -> 关闭转义 -> 只剩 "AT"（无裸 CR）
        self.assertEqual(codec.display_body(b"AT\r\n", show_hex=False, show_crlf=False), "AT")

    def test_crlf_off_strips_trailing_cr_only_lf(self):
        self.assertEqual(codec.display_body(b"OK\r\n", show_hex=False, show_crlf=False), "OK")

    def test_crlf_off_blank_line_becomes_empty(self):
        self.assertEqual(codec.display_body(b"\r\n", show_hex=False, show_crlf=False), "")

    def test_crlf_off_keeps_mid_text(self):
        self.assertEqual(codec.display_body(b"AT+QGMR\r\n", show_hex=False, show_crlf=False), "AT+QGMR")

    def test_crlf_on_escapes_to_literal(self):
        self.assertEqual(codec.display_body(b"AT\r\n", show_hex=False, show_crlf=True), "AT\\r\\n")

    def test_hex_keeps_terminator_bytes(self):
        self.assertEqual(codec.display_body(b"\r\n", show_hex=True, show_crlf=False), "0D 0A ")

    def test_crlf_on_no_extra_strip(self):
        # show_crlf=True 时不应误删尾部数据
        self.assertEqual(codec.display_body(b"A\r", show_hex=False, show_crlf=True), "A\\r")


if __name__ == "__main__":
    unittest.main()
