# -*- coding: utf-8 -*-
"""AtPanel 配置组：enter 往返保存、默认配置播种、删除按钮。"""
import os
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ecom import at_panel as ap
    from ecom.at_panel import AtPanel
    from ecom import i18n
except Exception as exc:  # 无 tkinter 环境
    AtPanel = None
    _err = exc


class _StubApp:
    def __init__(self):
        self.P = {"success": "#2e9e6b", "danger": "#c0392b", "success_h": "#27a06b",
                  "danger_h": "#a83220", "surface": "#ffffff", "text": "#1b2733",
                  "bg": "#eef1f5", "muted": "#6b7a8d", "primary": "#3b82f6"}
        self.lang = "zh"

    def _t(self, key, **fmt):
        return i18n.get(self.lang, key, **fmt)

    def _register(self, key, w):
        pass

    def send_bytes(self, raw):
        return len(raw)


@unittest.skipIf(AtPanel is None, "无 tkinter / GUI 环境")
class TestAtPanelConfig(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.td = tempfile.mkdtemp()
        self._orig = ap.configs_dir
        ap.configs_dir = lambda: Path(self.td)
        self.app = _StubApp()
        self.panel = AtPanel(self.root, self.app)
        self.root.update()

    def tearDown(self):
        ap.configs_dir = self._orig
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_default_config_seeded_when_empty(self):
        # 目录为空 -> 构造时自动播种默认 config 组
        names = self.panel._list_config_names()
        self.assertIn("config", names)

    def test_enter_roundtrip_preserved(self):
        """BUG2 回归：保存写 'enter'，加载必须能读回 'enter'（否则 Enter 全变未勾选）。"""
        p = self.panel
        v = p._row_vars[0]
        v["txt"].set("ATQ")
        v["hex"].set(False)
        v["ent"].set(True)
        cols = p._collect_rows()
        self.assertTrue(any(c.get("enter") and c["text"] == "ATQ" for c in cols))

        p.config_name.set("cfg1")
        self.assertTrue(p._write_config("cfg1", cols))
        p.config_name.set("cfg1")
        p._load_config()
        found = [r for r in p._all_data if r["txt"] == "ATQ"]
        self.assertTrue(found, "加载后应仍有 ATQ 行")
        self.assertTrue(found[0]["ent"], "Enter 状态应在保存+加载后保持勾选")

    def test_delete_config_removes_file(self):
        p = self.panel
        p._ensure_default_config()
        self.assertIn("config", p._list_config_names())
        oy, oi, oe = ap.messagebox.askyesno, ap.messagebox.showinfo, ap.messagebox.showerror
        ap.messagebox.askyesno = lambda *a, **k: True
        ap.messagebox.showinfo = lambda *a, **k: None
        ap.messagebox.showerror = lambda *a, **k: None
        try:
            p.config_name.set("config")
            p._delete_config()
        finally:
            ap.messagebox.askyesno, ap.messagebox.showinfo, ap.messagebox.showerror = oy, oi, oe
        self.assertNotIn("config", p._list_config_names())


if __name__ == "__main__":
    unittest.main()
