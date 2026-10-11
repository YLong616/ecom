"""串口核心：打开/关闭、后台收发线程、字节计数。

设计要点：
- 读线程独立于 Tkinter 主线程，通过 ``queue.Queue`` 传递数据；
  GUI 用 ``root.after`` 周期调用 :meth:`SerialCore.drain` 取数，
  避免跨线程直接操作 Tk 控件。
- 计数：rx_count 仅读线程写入、tx_count 仅调用方（主线程）写入，
  读取侧不写，故无并发写冲突。
"""

from __future__ import annotations

import os
import queue
import threading
import time

import serial
from serial.tools import list_ports

UUCP_LOCK_DIR = "/var/lock"


class _LockInfo:
    """UUCP 锁文件检查结果。occupied=True 表示该端口被其它进程真占用。"""
    __slots__ = ("occupied", "path", "pid")

    def __init__(self, occupied, path, pid):
        self.occupied = occupied
        self.path = path
        self.pid = pid


def _uucp_lock_path(port):
    """
    计算 UUCP 锁文件路径（格式: /var/lock/LCK..<basename>）。
    仅在 POSIX 且端口形如 /dev/xxx 时返回路径，否则返回 None。
    busybox microcom / cu / uugetty 等工具通过该锁文件实现“占串口”。
    """
    if os.name != "posix":
        return None
    if not port or not port.startswith("/dev/"):
        return None
    base = os.path.basename(port)
    if not base:
        return None
    # UUCP 锁路径是固定的 POSIX 路径，显式用 "/" 拼接，避免 Windows 上
    # os.path.join 产出反斜杠。(真实设备只在 Linux 上自然为 "/")。
    return UUCP_LOCK_DIR + "/LCK.." + base


def _pid_alive(pid):
    """判断进程是否存活：kill(pid, 0) 不抛错=存活；无权限=存活。"""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _uucp_lock_info(port):
    """
    读取 UUCP 锁文件并判断该端口是否被占用。

    返回 _LockInfo：
      occupied=True  -> 锁文件存在且记录的活动进程仍存活（真占用）
      occupied=False -> 无锁 / 陈旧锁（PID 已死或无法解析）/ 非 POSIX
    """
    path = _uucp_lock_path(port)
    if not path or not os.path.exists(path):
        return _LockInfo(False, path, None)
    pid = None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        if content:
            pid = int(content.splitlines()[0].strip() or "0") or None
    except (OSError, ValueError):
        pid = None
    if pid is not None and _pid_alive(pid):
        return _LockInfo(True, path, pid)
    return _LockInfo(False, path, pid)




def _force_baud(port, baudrate):
    """POSIX 上重新强制设置串口波特率（仅改 speed，不动其它标志）。

    pyserial 的 open() 用 termios 配置波特率，但部分 USB-串口芯片(常见于
    CH340/CP210x 或山寨转接器)在该路径下不会真正生效，termios 仍停留在默认
    9600。此时模块(如蜂窝模组 AT 口)按 115200 通信，工具发 AT 实际以 9600
    发出 -> 只 TX 无 RX。

    这里改用外部 ``stty -F <port> <baud>`` 写回，与“用户终端已验证可通的
    stty 配置路径”完全一致。stty 在绝大多数 Linux 发行版(busybox/coreutils)
    均存在；失败时静默跳过，不影响其它功能。
    """
    if not port or not port.startswith("/dev/"):
        return
    try:
        import subprocess
        subprocess.run(
            ["stty", "-F", port, str(int(baudrate))],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


class SerialCore:
    """串口收发核心（线程安全，外部只需访问队列与计数）。"""

    RX_DATA = "data"
    RX_ERROR = "error"
    RX_CLOSED = "closed"

    def __init__(self):
        self._ser = None
        self._running = False
        self._thread = None
        self._rx_queue = queue.Queue()
        self.rx_count = 0  # 累计接收字节数
        self.tx_count = 0  # 累计发送字节数

    @property
    def is_open(self):
        return self._ser is not None and self._ser.is_open

    # ---- 打开 / 关闭 ----
    def open(self, port, baudrate=115200, bytesize=8, parity="N",
             stopbits=1, rtscts=False, xonxoff=False):
        if self.is_open:
            self.close()
        # Linux: 真正打开前检测 UUCP 锁文件，识别 microcom/cu 等工具“占用串口”。
        # pyserial 的 exclusive=True 走 flock()，与该套 /var/lock/LCK..* 锁互不相干，
        # 因此需单独检测这一机制，否则会被 microcom 占用的端口照样打开成功。
        if os.name == "posix":
            _uucp = _uucp_lock_info(port)
            if _uucp.occupied:
                raise serial.SerialException(
                    "串口被其它程序占用（锁文件: {path}, PID={pid}），"
                    "请先关闭占用该端口的程序（如 microcom）。".format(
                        path=_uucp.path, pid=_uucp.pid))
        # serial_for_url 对普通端口（COM3、/dev/ttyUSB0）与 serial.Serial 行为一致，
        # 且额外支持 loop:// 等虚拟端口，便于无硬件自测。
        kwargs = dict(
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            rtscts=rtscts,
            xonxoff=xonxoff,
            timeout=0.1,
        )
        try:
            # exclusive=True -> flock()（非阻塞独占，见 serialposix.py）；与 UUCP 锁互补
            self._ser = serial.serial_for_url(port, exclusive=True, **kwargs)
        except TypeError as _te:
            # 部分虚拟 URL 协议(如 loop://)不支持 exclusive 参数，降级重试
            if "exclusive" in str(_te) or "unexpected keyword" in str(_te):
                self._ser = serial.serial_for_url(port, **kwargs)
            else:
                raise
        # Linux: 部分 USB-串口芯片 pyserial open 后实际波特率未生效，termios
        # 可能停留在默认 9600 -> 用 stty 强制写回（仅改 speed，不动 raw）。
        if os.name == "posix" and self._ser is not None:
            _force_baud(port, baudrate)
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        while self._running and self.is_open:
            try:
                n = self._ser.in_waiting
                if n:
                    data = self._ser.read(n)
                    if data:
                        self.rx_count += len(data)
                        self._rx_queue.put((self.RX_DATA, data))
                else:
                    time.sleep(0.01)
            except (serial.SerialException, OSError) as exc:
                if self._running:
                    self._rx_queue.put((self.RX_ERROR, str(exc)))
                break
        # 因异常退出但外部尚未主动关闭时，补发关闭信号
        if self._running:
            self._rx_queue.put((self.RX_CLOSED, None))

    def write(self, data: bytes) -> int:
        if not self.is_open:
            raise RuntimeError("串口未打开")
        n = self._ser.write(data)
        self.tx_count += n
        return n

    # ---- 流控引脚（DTR / RTS），勾选=拉低 ----
    def set_dtr(self, low: bool = True):
        if self.is_open:
            try:
                self._ser.dtr = not low
            except (serial.SerialException, OSError, AttributeError):
                pass

    def set_rts(self, low: bool = True):
        if self.is_open:
            try:
                self._ser.rts = not low
            except (serial.SerialException, OSError, AttributeError):
                pass

    def close(self):
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    def drain(self):
        """取出当前队列中所有事件，供 GUI 主循环调用。"""
        items = []
        while True:
            try:
                items.append(self._rx_queue.get_nowait())
            except queue.Empty:
                break
        return items

    def reset_counters(self):
        self.rx_count = 0
        self.tx_count = 0

    # ---- 静态工具 ----
    @staticmethod
    def list_ports():
        """返回可用串口列表，每项为 (device, display_name)。

        display_name 形如 ``COM78  USB Serial Port``，保留完整描述，
        便于 GUI 下拉框展示设备全名；device 为底层可打开的端口名。
        """
        result = []
        for p in list_ports.comports():
            device = p.device
            desc = (p.description or "").strip()
            if desc:
                display = f"{device}  {desc}"
            else:
                display = device
            result.append((device, display))
        return result
