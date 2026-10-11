"""SerialCore 单元测试 —— 用 loop:// 虚拟端口回环，无需真实硬件。

运行方式（在项目根目录 projects/eCOM 下）：
    python -m unittest discover tests -v
"""

import time
import unittest

from ecom.serial_core import SerialCore


class TestSerialCore(unittest.TestCase):
    def setUp(self):
        self.core = SerialCore()

    def tearDown(self):
        self.core.close()

    def test_loopback_write_read_and_count(self):
        self.core.open("loop://", baudrate=115200)
        self.core.write(b"hello")
        time.sleep(0.3)
        items = self.core.drain()
        data = b"".join(p for k, p in items if k == SerialCore.RX_DATA)
        self.assertEqual(data, b"hello")
        self.assertEqual(self.core.rx_count, 5)
        self.assertEqual(self.core.tx_count, 5)

    def test_close_marks_not_open(self):
        self.core.open("loop://")
        self.assertTrue(self.core.is_open)
        self.core.close()
        self.assertFalse(self.core.is_open)

    def test_write_when_closed_raises(self):
        with self.assertRaises(RuntimeError):
            self.core.write(b"x")

    def test_reset_counters(self):
        self.core.open("loop://")
        self.core.write(b"abc")
        time.sleep(0.3)
        self.core.drain()
        self.core.reset_counters()
        self.assertEqual(self.core.rx_count, 0)
        self.assertEqual(self.core.tx_count, 0)




from unittest import mock

import serial

from ecom.serial_core import (
    _LockInfo,
    _uucp_lock_path,
    _pid_alive,
    _uucp_lock_info,
)


class TestUucpLock(unittest.TestCase):
    """UUCP 锁检测：识别 busybox microcom / cu / uugetty “占串口”。

    背景：pyserial 的 exclusive=True 走 flock()，与这类工具用的
    /var/lock/LCK..ttyUSBx 锁互不相干，因此必须单独检测锁文件。
    """

    def test_lock_path_posix(self):
        with mock.patch("ecom.serial_core.os.name", "posix"):
            self.assertEqual(_uucp_lock_path("/dev/ttyUSB3"),
                             "/var/lock/LCK..ttyUSB3")

    def test_lock_path_nt_returns_none(self):
        with mock.patch("ecom.serial_core.os.name", "nt"):
            self.assertIsNone(_uucp_lock_path("/dev/ttyUSB3"))

    def test_lock_path_non_dev_returns_none(self):
        with mock.patch("ecom.serial_core.os.name", "posix"):
            self.assertIsNone(_uucp_lock_path("loop://"))
            self.assertIsNone(_uucp_lock_path("COM3"))

    def test_pid_alive(self):
        with mock.patch("ecom.serial_core.os.kill", side_effect=None):
            self.assertTrue(_pid_alive(123))
        with mock.patch("ecom.serial_core.os.kill",
                        side_effect=ProcessLookupError):
            self.assertFalse(_pid_alive(123))
        with mock.patch("ecom.serial_core.os.kill", side_effect=PermissionError):
            self.assertTrue(_pid_alive(123))
        self.assertFalse(_pid_alive(None))

    def test_uucp_lock_info_occupied(self):
        with mock.patch("ecom.serial_core._uucp_lock_path",
                        return_value="/var/lock/LCK..ttyUSB3"), \
             mock.patch("ecom.serial_core.os.path.exists", return_value=True), \
             mock.patch("ecom.serial_core.os.kill", side_effect=None), \
             mock.patch("builtins.open",
                        mock.mock_open(read_data="4242\n")):
            info = _uucp_lock_info("/dev/ttyUSB3")
            self.assertTrue(info.occupied)
            self.assertEqual(info.pid, 4242)
            self.assertEqual(info.path, "/var/lock/LCK..ttyUSB3")

    def test_uucp_lock_info_stale(self):
        with mock.patch("ecom.serial_core._uucp_lock_path",
                        return_value="/var/lock/LCK..ttyUSB3"), \
             mock.patch("ecom.serial_core.os.path.exists", return_value=True), \
             mock.patch("ecom.serial_core.os.kill",
                        side_effect=ProcessLookupError), \
             mock.patch("builtins.open",
                        mock.mock_open(read_data="9999\n")):
            info = _uucp_lock_info("/dev/ttyUSB3")
            self.assertFalse(info.occupied)
            self.assertEqual(info.pid, 9999)

    def test_uucp_lock_info_no_lock(self):
        with mock.patch("ecom.serial_core._uucp_lock_path",
                        return_value="/var/lock/LCK..ttyUSB3"), \
             mock.patch("ecom.serial_core.os.path.exists", return_value=False):
            info = _uucp_lock_info("/dev/ttyUSB3")
            self.assertFalse(info.occupied)
            self.assertIsNone(info.pid)

    def test_open_raises_when_occupied(self):
        core = SerialCore()
        with mock.patch("ecom.serial_core.os.name", "posix"), \
             mock.patch("ecom.serial_core._uucp_lock_info") as m:
            m.return_value = _LockInfo(True, "/var/lock/LCK..ttyUSB3", 4242)
            with self.assertRaises(serial.SerialException):
                core.open("/dev/ttyUSB3")

    def test_open_ok_when_not_occupied(self):
        core = SerialCore()
        with mock.patch("ecom.serial_core.os.name", "posix"), \
             mock.patch("ecom.serial_core._uucp_lock_info") as m:
            m.return_value = _LockInfo(False, "/var/lock/LCK..ttyUSB3", None)
            core.open("loop://")
            self.assertTrue(core.is_open)
            core.close()
if __name__ == "__main__":
    unittest.main()
