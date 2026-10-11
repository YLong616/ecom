"""隔离「shell 明文读写能通、python 全空」的根因：到底差在哪个打开方式。

用法（Linux, root）:
    sudo python3 tools/probe_plain.py /dev/ttyUSB3

背景:test.txt 证明
    ( sleep 0.2; printf 'AT\\r\\n' > /dev/ttyUSB3 ) &   # 纯 O_WRONLY 打开写
    sudo timeout 3 cat /dev/ttyUSB3                      # 纯 O_RDONLY 打开读
    稳定返回  AT / OK。

本探针逐条复刻 & 做 4 个对照,定位唯一差异:
  V1  纯 O_WRONLY 写 + 纯 O_RDONLY 读(两次 open,不碰 termios/flock)  == test.txt 等价
  V2  单次 O_RDWR open,不碰 termios/flock(测:是不是"分开两次 open"才有效)
  V3  单次 O_RDWR + cfmakeraw raw(测:是不是"设termios"就废)
  V4  pyserial 控制组(预期空,复现 eCOM 现状)

若 V1 有 OK、V2/V3 全空 -> 根因=pyserial 的 O_RDWR+flock+termios 把 CDC-ACM 打废;
   eCOM 在 POSIX 须改为"纯 O_WRONLY 写 + 纯 O_RDONLY 读"两次独立 open(不设 termios/flock/非阻塞)。
"""
import os
import sys
import time
import select
import ctypes
import ctypes.util
from ctypes import c_int, c_uint, c_ubyte, POINTER, byref

libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)


class Termios(ctypes.Structure):
    _fields_ = [
        ("c_iflag", c_uint), ("c_oflag", c_uint), ("c_cflag", c_uint),
        ("c_lflag", c_uint), ("c_line", c_ubyte), ("c_cc", c_ubyte * 32),
        ("c_ispeed", c_uint), ("c_ospeed", c_uint),
    ]


tcgetattr = libc.tcgetattr
tcgetattr.argtypes = [c_int, POINTER(Termios)]
tcgetattr.restype = c_int
cfmakeraw = libc.cfmakeraw
cfmakeraw.argtypes = [POINTER(Termios)]
cfmakeraw.restype = None


def _read_fd(fd, secs=3.0, stop_on_ok=True):
    acc = b""
    deadline = time.monotonic() + secs
    while time.monotonic() < deadline:
        rdt, _, _ = select.select([fd], [], [], 0.1)
        if rdt:
            try:
                chunk = os.read(fd, 256)
            except BlockingIOError:
                continue
            if not chunk:
                break
            acc += chunk
            if stop_on_ok and (b"OK" in acc or b"ERROR" in acc):
                break
    return acc


def v1_split_open(port, payload):
    """V1 == test.txt 等价:纯 O_WRONLY 写,关闭;再纯 O_RDONLY 读。"""
    fd = os.open(port, os.O_WRONLY | os.O_NOCTTY)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)
    time.sleep(0.2)
    fd = os.open(port, os.O_RDONLY | os.O_NOCTTY)
    try:
        return _read_fd(fd)
    finally:
        os.close(fd)


def v2_single_rdwr(port, payload):
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
    try:
        os.write(fd, payload)
        time.sleep(0.2)
        return _read_fd(fd)
    finally:
        os.close(fd)


def v3_single_rdwr_raw(port, payload):
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
    try:
        t = Termios()
        if tcgetattr(fd, byref(t)) == 0:
            cfmakeraw(byref(t))
            # 不写回 tcsetattr? 复刻 microcom 会 tcsetattr。这里写回测试"设termios是否废"
            # 说明: 只测 raw,不碰速度
        os.write(fd, payload)
        time.sleep(0.2)
        return _read_fd(fd)
    finally:
        os.close(fd)


def v4_pyserial(port, payload):
    import serial
    s = serial.serial_for_url(port, baudrate=115200, timeout=0.5)
    try:
        s.reset_input_buffer()
        s.write(payload)
        time.sleep(0.3)
        return s.read(4096)
    finally:
        s.close()


def show(label, data):
    asc = data.decode("utf-8", "replace").replace(chr(13), "\\r").replace(chr(10), "\\n")
    print("[%s] hex=%r" % (label, data.hex()))
    print("[%s] asc=%r" % (label, asc))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    port = sys.argv[1]
    payload = b"AT\r\n"
    print("=" * 60)
    show("V1 split", v1_split_open(port, payload))
    print("-" * 60)
    time.sleep(0.3)
    show("V2 rdwr", v2_single_rdwr(port, payload))
    print("-" * 60)
    time.sleep(0.3)
    show("V3 rdwr_raw", v3_single_rdwr_raw(port, payload))
    print("-" * 60)
    time.sleep(0.3)
    show("V4 pyserial", v4_pyserial(port, payload))
    print("完成。看 V1 是否有 OK。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
