"""热插拔/端口消失检测 —— 打开串口后设备被移除，应自动断开并恢复“打开串口”。

覆盖三类路径：
  1) 虚拟端口(loop://)不死循环跳过探测；
  2) 真实端口从 list_ports 消失 -> _on_port_lost -> 按钮恢复“打开串口”；
  3) 读线程上报 RX_ERROR -> 同样触发自动断开。

运行（项目根目录 projects/eCOM 下）：
    python -m unittest tests.test_hotplug -v
"""
import os
import sys
import tkinter as tk
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ecom.app import EcomApp
except Exception as _exc:  # 无 tkinter 环境时 skipped
    EcomApp = None

from ecom.serial_core import SerialCore


@unittest.skipIf(EcomApp is None, "无 tkinter / GUI 环境")
class TestHotplug(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = EcomApp(self.root)
        self.root.update()
        self.app._refresh_ports()
        self.app._apply_language()
        self.root.update_idletasks()
        self.root.update()

    def tearDown(self):
        # 抑制 root.after 残留的 _poll_rx 回调
        self.app._poll_interval_ms = 10 ** 9
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        try:
            for cid in list(self.root.tk.call("after", "info") or []):
                pass
        except tk.TclError:
            pass

    # 1) 虚拟端口(loop://)不在 list_ports 中被枚举，必须跳过探测，避免误断开
    def test_presence_skips_virtual_loop(self):
        app = self.app
        app._active_port = "loop://"
        app._status_error = None
        # 即使枚举结果与 loop:// 不匹配，也不应触发断开
        app.core.list_ports = lambda: [("COM1", "COM1  USB Serial")]
        app._check_port_presence()
        self.assertEqual(app._active_port, "loop://")
        self.assertIsNone(app._status_error)

    # 2) 真实端口被拔出：从 list_ports 消失 -> 自动断开，按钮恢复“打开串口”
    def test_presence_port_removed_disconnects(self):
        app = self.app
        app.core.list_ports = lambda: [("COM1", "COM1  USB Serial"), ("COM3", "COM3  USB Serial")]
        app._active_port = "COM99"
        app._status_error = None
        app._check_port_presence()
        self.assertIsNone(app._active_port)
        self.assertEqual(app.open_btn["text"], app._t("open"))
        self.assertIsNotNone(app._status_error)
        self.assertEqual(app._status_error, app._t("port_lost"))
        self.assertFalse(app.core.is_open)

    # 2b) 端口仍在列表 -> 不应断开
    def test_presence_port_still_present_keeps_connected(self):
        app = self.app
        app.core.list_ports = lambda: [("COM1", "COM1  USB Serial")]
        app._active_port = "COM1"
        app._status_error = None
        app._check_port_presence()
        self.assertEqual(app._active_port, "COM1")
        self.assertIsNone(app._status_error)

    # 3) 读线程错误(RX_ERROR) -> 同样自动断开并恢复“打开串口”
    def test_rx_error_triggers_disconnect(self):
        app = self.app
        app._poll_interval_ms = 10 ** 9  # 避免 after 反复重入
        app._active_port = "COM3"
        app._status_error = None
        app.core._rx_queue.put((SerialCore.RX_ERROR, "boom"))
        app._poll_rx()
        self.assertIsNone(app._active_port)
        self.assertEqual(app._status_error, "boom")
        self.assertEqual(app.open_btn["text"], app._t("open"))

    # 3b) 读线程关闭信号(RX_CLOSED) -> 自动断开
    def test_rx_closed_triggers_disconnect(self):
        app = self.app
        app._poll_interval_ms = 10 ** 9
        app._active_port = "COM3"
        app._status_error = None
        app.core._rx_queue.put((SerialCore.RX_CLOSED, None))
        app._poll_rx()
        self.assertIsNone(app._active_port)
        self.assertEqual(app._status_error, app._t("port_lost"))
        self.assertEqual(app.open_btn["text"], app._t("open"))


if __name__ == "__main__":
    unittest.main()
