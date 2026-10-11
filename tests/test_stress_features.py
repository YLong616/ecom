# -*- coding: utf-8 -*-
"""压力模式遗漏功能回归：
- HEX / Enter 列顶格全选/去全选 master
- 一键清空 AT list
"""
import unittest
import tkinter as tk
from unittest import mock

from ecom.stress_panel import PAGE_SIZE
from ecom.app import EcomApp
from ecom import stress_model


class TestStressSelectAllClear(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = EcomApp(self.root)
        self.root.update()
        self.app._refresh_ports()
        self.app._apply_language()
        try:
            self.app._switch_mode("stress")
        except Exception:
            self.app = None
            return
        self.root.update_idletasks()
        self.root.update()
        self.sv = self.app.stress_view

    def tearDown(self):
        if getattr(self, "app", None) is None:
            try:
                self.root.destroy()
            except tk.TclError:
                pass
            return
        try:
            self.sv._stop_run()
        except Exception:
            pass
        try:
            self.app._poll_interval_ms = 10 ** 9
        except Exception:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_hex_all_toggles_type(self):
        sv = self.sv
        rows = sv._rows
        # 给前 3 行填上非 HEX 内容，便于观察切换
        for i in range(min(3, len(rows))):
            rows[i].txt = "AT+CPIN?"
            rows[i].hex = False
            rows[i].send_type = "ASCII"
        sv._render_page()
        # 全选 HEX
        sv.hex_all_var.set(True)
        sv._toggle_hex_all()
        self.assertTrue(all(v["hex"].get() for v in sv._row_vars))
        self.assertTrue(all(v["type"].get() == "HEX" for v in sv._row_vars))
        # 去全选 HEX
        sv.hex_all_var.set(False)
        sv._toggle_hex_all()
        self.assertFalse(any(v["hex"].get() for v in sv._row_vars))
        self.assertTrue(all(v["type"].get() == "ASCII" for v in sv._row_vars))

    def test_enter_all_toggles_suffix(self):
        sv = self.sv
        rows = sv._rows
        for i in range(min(3, len(rows))):
            rows[i].enter = False
            rows[i].send_suffix = "None"
        sv._render_page()
        sv.enter_all_var.set(True)
        sv._toggle_enter_all()
        self.assertTrue(all(v["enter"].get() for v in sv._row_vars))
        self.assertTrue(all(v["suffix"].get() == "CR-LF" for v in sv._row_vars))
        sv.enter_all_var.set(False)
        sv._toggle_enter_all()
        self.assertFalse(any(v["enter"].get() for v in sv._row_vars))
        self.assertTrue(all(v["suffix"].get() == "None" for v in sv._row_vars))

    def test_clear_at_list(self):
        sv = self.sv
        rows = sv._rows
        for i in range(len(rows)):
            rows[i].txt = "AT+CIMI"
            rows[i].hex = True
            rows[i].enter = True
            rows[i].enabled = True
        sv._render_page()
        with mock.patch("ecom.stress_panel.messagebox.askyesno", return_value=True):
            sv._clear_at_list()
        for r in sv._rows:
            self.assertFalse(r.enabled)
            self.assertEqual(r.txt, "")
            self.assertFalse(r.hex)
            self.assertTrue(r.enter)
            self.assertEqual(r.send_type, "ASCII")
            self.assertEqual(r.send_suffix, "CR-LF")
            self.assertEqual(r.interval_ms, 300)
            self.assertEqual(r.expected, "")
        self.assertEqual(sv._page, 1)

    def test_clear_cancelled_keeps_rows(self):
        sv = self.sv
        rows = sv._rows
        rows[0].txt = "AT+CPIN?"
        rows[0].enabled = True
        sv._render_page()
        with mock.patch("ecom.stress_panel.messagebox.askyesno", return_value=False):
            sv._clear_at_list()
        self.assertEqual(sv._rows[0].txt, "AT+CPIN?")

    def test_type_all_sets_column(self):
        sv = self.sv
        rows = sv._rows
        for i in range(min(4, len(rows))):
            rows[i].send_type = "ASCII"
            rows[i].hex = False
        sv._render_page()
        sv.type_all_var.set("HEX")
        sv._apply_type_all()
        self.assertTrue(all(v["type"].get() == "HEX" for v in sv._row_vars))
        # HEX 联动 → 行 hex 勾选被置真
        self.assertTrue(all(v["hex"].get() for v in sv._row_vars))
        # 改回 ASCII
        sv.type_all_var.set("ASCII")
        sv._apply_type_all()
        self.assertTrue(all(v["type"].get() == "ASCII" for v in sv._row_vars))
        self.assertFalse(any(v["hex"].get() for v in sv._row_vars))

    def test_suffix_all_sets_column(self):
        sv = self.sv
        rows = sv._rows
        for i in range(min(4, len(rows))):
            rows[i].send_suffix = "None"
            rows[i].enter = False
        sv._render_page()
        sv.suffix_all_var.set("CR-LF")
        sv._apply_suffix_all()
        self.assertTrue(all(v["suffix"].get() == "CR-LF" for v in sv._row_vars))
        self.assertTrue(all(v["enter"].get() for v in sv._row_vars))
        sv.suffix_all_var.set("None")
        sv._apply_suffix_all()
        self.assertTrue(all(v["suffix"].get() == "None" for v in sv._row_vars))
        self.assertFalse(any(v["enter"].get() for v in sv._row_vars))

    def test_type_empty_does_nothing(self):
        sv = self.sv
        sv.type_all_var.set("")
        before = [v["type"].get() for v in sv._row_vars]
        sv._apply_type_all()
        self.assertEqual([v["type"].get() for v in sv._row_vars], before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
