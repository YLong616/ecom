# -*- coding: utf-8 -*-
"""Verify the 6 reported UI bug fixes on the stress panel."""
import datetime
import os
import sys
import tkinter as tk
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ecom.app import EcomApp
except Exception as exc:
    EcomApp = None
    _err = exc

from ecom.stress_panel import PAGE_SIZE, RULES_PER_PAGE


@unittest.skipIf(EcomApp is None, "no tkinter / GUI env")
class TestBugFixes(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = EcomApp(self.root)
        self.root.update()
        self.app._refresh_ports()
        self.app._apply_language()
        self.app._switch_mode("stress")
        self.root.update_idletasks()
        self.root.update()
        self.sv = self.app.stress_view

    def tearDown(self):
        try:
            self.sv._stop_run()
        except Exception:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_bug1_time_unit_hours(self):
        sv = self.sv
        sv.time_min_var.set("1")
        self.assertAlmostEqual(sv._target_seconds(), 3600.0)
        sv.time_min_var.set("0.5")
        self.assertAlmostEqual(sv._target_seconds(), 1800.0)
        self.assertIn(sv._t("stress_time_unit"), ("小时", "h", "H"))

    def test_bug2_run_btn_shows_round(self):
        sv = self.sv
        sv._running = True
        sv._rounds_done = 4
        sv._set_run_round()
        self.assertEqual(sv.run_btn.cget("text"), "5")
        sv._rounds_done = 0
        sv._set_run_round()
        self.assertEqual(sv.run_btn.cget("text"), "1")

    def test_bug3_add_rule_stable_height(self):
        sv = self.sv
        self.assertTrue(sv._rules_rows_h, "rules height must be pinned after init")
        y0 = sv.run_btn.winfo_rooty()
        h0 = sv._rules_rows.winfo_reqheight() if sv._rules_rows.winfo_exists() else 0
        sv._add_rule()
        self.root.update_idletasks()
        self.root.update()
        h1 = sv._rules_rows.winfo_reqheight()
        y1 = sv.run_btn.winfo_rooty()
        self.assertLess(abs(y1 - y0), 8, "add rule must not shift start/stop buttons")
        self.assertLessEqual(abs(h1 - h0), 10, "rules area height must stay stable")

    def test_bug4_atlist_interval_default_300(self):
        sv = self.sv
        self.assertTrue(sv._row_vars, "at-list rows expected")
        vals = [v["interval"].get() for v in sv._row_vars]
        self.assertTrue(all(x == "300" for x in vals),
                        "interval column should default to 300, got %s" % vals)

    def test_bug5_summary_multiline(self):
        sv = self.sv
        sv.name_var.set("stress-1")
        s = sv._stats
        s.start_time = datetime.datetime(2026, 8, 26, 10, 56, 20, 11779)
        s.end_time = datetime.datetime(2026, 8, 26, 10, 56, 24, 231304)
        s.sent_lines = 10
        s.errors = 0
        s.total_rounds = 5
        cap = []
        sv._render_note = lambda txt: cap.append(txt)
        sv._append_summary()
        text = "".join(cap)
        self.assertIn("== %s ==\n" % sv._t("stress_summary"), text)
        self.assertIn("%s: stress-1\n" % sv._t("stress_summary_name"), text)
        self.assertIn("%s: " % sv._t("stress_stats_duration"), text)
        self.assertIn("%s: " % sv._t("stress_summary_run"), text)
        self.assertIn("%s: 5\n" % sv._t("stress_stats_rounds"), text)
        self.assertIn("%s: 10\n" % sv._t("stress_stats_sent"), text)
        self.assertIn("%s: 0\n" % sv._t("stress_stats_err"), text)
        # fields must be on separate lines
        self.assertIn("\n%s: " % sv._t("stress_stats_rounds"), text)

    def test_bug6_stats_duration_and_rounds_separate(self):
        sv = self.sv
        sv._running = False
        sv._rounds_done = 5
        s = sv._stats
        s.sent_lines = 10
        s.errors = 0
        s.current_line = 0
        s.start_time = datetime.datetime(2026, 8, 26, 10, 56, 20, 11779)
        sv._update_stats()
        body = sv.stats_text.get("1.0", "end-1c")
        lines = [l for l in body.split("\n")]
        dur_lines = [i for i, l in enumerate(lines) if sv._t("stress_stats_duration") in l]
        rnd_lines = [i for i, l in enumerate(lines) if sv._t("stress_stats_rounds") in l]
        self.assertEqual(len(dur_lines), 1)
        self.assertEqual(len(rnd_lines), 1)
        self.assertNotEqual(dur_lines[0], rnd_lines[0],
                            "duration and rounds must be on separate lines")

    def test_language_switch_updates_stress_panel(self):
        sv = self.sv
        self.app._set_language("zh")
        self.root.update_idletasks(); self.root.update()

        def reg(key):
            for k, w in self.app._text_widgets:
                if k == key:
                    try:
                        return str(w.cget("text"))
                    except tk.TclError:
                        return None
            return None

        def regw(key):
            for k, w in self.app._text_widgets:
                if k == key:
                    return w
            return None

        # 静态控件（LabelFrame/Label/Button/Checkbutton）随语言刷新
        self.app._set_language("en")
        self.root.update_idletasks(); self.root.update()
        self.assertEqual(reg("stress_config"), self.app._t("stress_config"))
        self.assertEqual(reg("stress_serial"), self.app._t("stress_serial"))
        self.assertEqual(reg("stress_stats"), self.app._t("stress_stats"))
        self.assertEqual(reg("stress_check_rules"), self.app._t("stress_check_rules"))
        self.assertEqual(reg("stress_at"), self.app._t("stress_at"))
        self.assertEqual(reg("refresh"), self.app._t("refresh"))
        self.assertEqual(reg("clear_output"), self.app._t("clear_output"))
        self.assertEqual(reg("stress_rule_keyword"), self.app._t("stress_rule_keyword"))
        # Radiobutton 类被 _apply_language 支持刷新
        rb = regw("stress_end_count")
        self.assertIsNotNone(rb)
        self.assertEqual(str(rb.cget("text")), self.app._t("stress_end_count"))
        # 动态控件均由 _refresh_language 处理
        self.assertEqual(sv.run_btn.cget("text"), self.app._t("stress_start"))
        self.assertEqual(sv.name_btn.cget("text"), self.app._t("stress_edit"))
        self.assertEqual(sv.open_btn.cget("text"),
                         self.app._t("close") if sv.core.is_open else self.app._t("open"))
        # 切回中文
        self.app._set_language("zh")
        self.root.update_idletasks(); self.root.update()
        self.assertEqual(reg("stress_config"), self.app._t("stress_config"))
        self.assertEqual(sv.run_btn.cget("text"), self.app._t("stress_start"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
