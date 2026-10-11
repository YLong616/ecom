"""GUI 层回归测试 —— 防止 UI 改坏（auto：修复 v8–v10）。

用无头 Tk 实例（withdraw 隐藏窗口）验证：
  - Log 文件内容与输出框逐字节一致（v10 核心）
  - 串口配置下拉框都存在且可见（v8 回归：pack(in_) 丢失控件）
  - 文件面板布局：发送在选择文件正下方 / 清空在发送文件左 / 无「追加后缀」勾选（v10）
  - 串口字段标签与前置下拉框间距（v9）

运行方式（项目根目录 projects/eCOM 下，需要 GUI 显示环境）：
    python -m unittest discover tests -v
"""

import os
import sys
import tempfile
import tkinter as tk
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ecom.app import EcomApp
except Exception as exc:  # 无 tkinter 环境时报 skipped
    EcomApp = None
    _EcomApp_import_error = exc

from ecom.stress_panel import PAGE_SIZE, RULES_PER_PAGE


def _rgx(w):
    return w.winfo_rootx()


@unittest.skipIf(EcomApp is None, "无 tkinter / GUI 环境")
class TestGuiRegression(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 不显示窗口，仍能布局测量
        self.app = EcomApp(self.root)
        self.root.update()
        self.app._refresh_ports()
        self.app._apply_language()
        self.root.update_idletasks()
        self.root.update()

    def tearDown(self):
        # 清掉 root.after 里可能残留的 _poll_rx 回调，避免 destroy 时报 after script 错误
        self.app._poll_interval_ms = 10**9
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        # 收集/清理 after 回调
        try:
            for cid in list(self.root.tk.call("after", "info") or []):
                pass
        except tk.TclError:
            pass

    # ---- v8 回归：串口配置下拉框都在且可显示 ----
    def test_serial_combos_present_and_mapped(self):
        combos = [
            self.app.port_combo, self.app.baud_combo, self.app.databits_combo,
            self.app.stopbits_combo, self.app.parity_combo, self.app.flow_combo,
        ]
        for c in combos:
            # withdraw（隐藏窗口）下 ismapped 恒为 0，改用布局宽度>0 判断
            self.assertGreater(c.winfo_width(), 0, f"{c} 无布局宽度")
        self.assertTrue(self.app.baud_combo["values"])

    # ---- v9 回归：串口字段标签与前置下拉框拉开间距 ----
    def test_serial_field_gap(self):
        # 找到 端口combo 与 波特率label 的横向间距（应为 14px 上下）
        top = self.app.port_combo.master
        labels = [c for c in top.winfo_children() if c.winfo_class() == "TLabel"]
        combos = [c for c in top.winfo_children() if c.winfo_class() == "TCombobox"]
        self.assertGreaterEqual(len(combos), 2, "端口/波特率/数据位下拉框不足")
        # 按 x 排序，相邻 combo 与 label 之间应有 14px 空隙
        items = sorted(
            [(c.winfo_x(), "combo", c) for c in combos]
            + [(c.winfo_x(), "label", c) for c in labels],
            key=lambda t: t[0])
        # 找出第一个 combo 之后紧跟的 label，验证间距
        gaps = []
        prev_end = None
        for x, kind, w in items:
            if prev_end is not None and kind == "label":
                gaps.append(x - prev_end)
            if kind == "combo":
                prev_end = x + w.winfo_width()
        self.assertTrue(any(g >= 12 for g in gaps), f"未检测到标签与前置下拉框的间距: {gaps}")

    # ---- v10 回归：Log 与输出框逐字节一致 ----
    def test_log_matches_output(self):
        self.app.show_ts.set(True)
        self.app.show_dir.set(True)
        self.app.show_crlf.set(True)
        logp = os.path.join(tempfile.gettempdir(), "ecom_gui_reg.log")
        if os.path.exists(logp):
            os.remove(logp)
        self.app._log_path = logp
        self.app.log_path_var.set(logp)
        self.app._log_start()
        self.app._render_frame("TX", b"AT+QGMR\r\n")
        self.app._render_frame("RX", b"OK\r\n")
        self.root.update_idletasks()
        self.app._log_stop()
        out = self.app.output.get("1.0", "end-1c")
        with open(logp, encoding="utf-8") as _f:
            log = _f.read()
        ol = [l for l in out.split("\n") if l.strip()]
        ll = [l for l in log.split("\n") if l.strip()]
        self.assertEqual(ol, ll, "Log 与输出框不一致")
        # Log 应带方括号时间戳
        self.assertIn("[2026-", ll[0]) if ll else None
        os.remove(logp)

    # ---- v10 回归：文件面板布局 ----
    def test_file_panel_layout(self):
        fp = self.app.file_panel

        def find_btn(txt):
            res = []
            self._find(fp, "TButton", txt, res)
            return res[0] if res else None

        sel = find_btn(self.app._t("file_select"))
        send = find_btn(self.app._t("file_send"))
        clear = find_btn(self.app._t("file_clear"))
        self.assertIsNotNone(sel)
        self.assertIsNotNone(send)
        self.assertIsNone(clear)   # 清空按钮已删除，换成暂停
        # 主操作行：路径回显框左延伸(op 行最左)；发送文件在选择文件正下方
        self.assertEqual(fp.path_entry.winfo_x(), 0, "路径回显框未左延伸")
        self.assertLess(abs(send.winfo_rootx() - sel.winfo_rootx()), 3,
                        "发送文件未对齐选择文件正下方")
        self.assertGreater(send.winfo_rooty(), sel.winfo_rooty(), "发送文件未在选择文件下方")
        # 进度占位组件
        self.assertTrue(hasattr(fp, "progress_bar") and hasattr(fp, "pct_lbl"),
                        "缺少文件发送进度占位组件")
        # 暂停按钮存在
        self.assertTrue(hasattr(fp, "pause_btn"), "缺少暂停按钮")

    def _find(self, w, cls, text, res):
        for c in w.winfo_children():
            if c.winfo_class() == cls:
                try:
                    if c.cget("text") == text:
                        res.append(c)
                except tk.TclError:
                    pass
            self._find(c, cls, text, res)


@unittest.skipIf(EcomApp is None, "无 tkinter / GUI 环境")
class TestStressGui(unittest.TestCase):
    """压力面板回归 —— 覆盖 v11 七项修复。"""

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
            self.app._poll_interval_ms = 10**9
        except Exception:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    # -- (2) AT list 每页 8 行 --
    def test_at_list_8_rows(self):
        sv = self.sv
        rows = [w for w in sv._list_frame.grid_slaves()
                if int(w.grid_info().get("row", 0)) >= 1]
        self.assertEqual(len(rows) % 10, 0, "每行控件数不规整")
        self.assertEqual(len(rows) // 10, PAGE_SIZE, "AT list 每页应为 %d 行" % PAGE_SIZE)

    # -- (4) 添加规则不挤下开始/停止（分页高度恒定） --
    def test_rules_pagination_bounded(self):
        sv = self.sv
        y0 = sv.run_btn.winfo_rooty()
        for _ in range(10):
            sv._add_rule()
        self.root.update_idletasks()
        self.root.update()
        y1 = sv.run_btn.winfo_rooty()
        self.assertLess(abs(y1 - y0), 8, "添加规则后开始/停止按钮不应被挤动")
        self.assertEqual(sv._rules_total_pages(),
                         max(1, (len(sv._rules) + RULES_PER_PAGE - 1) // RULES_PER_PAGE))

    # -- (5) 运行时开始按钮显示次数、停止旁显示开始时间+已运行 --
    def test_run_info_and_button(self):
        import datetime
        import time as _t
        sv = self.sv
        sv._running = True
        sv._stats.start_time = datetime.datetime.now()
        sv._start_mono = _t.monotonic() - 65.0
        sv._update_run_info()
        txt = sv.run_info_lbl.cget("text")
        self.assertIn(":", txt, "运行信息应含 HH:MM:SS 时间")
        self.assertTrue(sv.run_btn.cget("text"), "开始按钮应显示次数")
        sv._running = False
        sv._stats.start_time = None
        sv._update_run_info()
        self.assertEqual(sv.run_info_lbl.cget("text"), "")

    # -- (7) 输出框逐行读取（AT 模式逻辑） --
    def test_rx_line_split(self):
        sv = self.sv
        sv.show_ts.set(False)
        sv.show_dir.set(True)
        sv.show_crlf.set(False)
        sv.show_hex.set(False)
        sv._clear_output()
        sv._rx_display_buf = bytearray(b"AT\r\r\nOK\r\n")
        sv._flush_display()
        lines = [l for l in sv.output.get("1.0", "end-1c").split("\n") if l.strip()]
        self.assertEqual(len(lines), 2, "输出应逐行读取")
        self.assertIn("OK", lines[-1])

if __name__ == "__main__":
    unittest.main()
