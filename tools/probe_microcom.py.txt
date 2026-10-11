"""逐字节复刻 busybox microcom：只设 raw、不动波特率、发 b"at\\r"、连续读。

用法（Linux，root）:
    sudo python3 tools/probe_microcom.py /dev/ttyUSB3

说明：
- microcom 在 9600（CDC-ACM 固定值）下仍能回 OK，证明波特率无关。
- microcom 你敲的是小写 at + 回车 -> 实际发送 b"at\\r"。
- 本脚本只调 libc cfmakeraw（设 raw，不写波特率），发 b"at\\r"，连续阻塞读 3s。
- 若这样收到 OK -> 根因是「我此前发的字节/读取方式不对」，eCOM 改发送/读取即可。
- 若仍空 -> 说明 Python 根本驱动不了该设备（须用 microcom 集成），我再换方案。
"""
import os
import sys
import time
import ctypes
import ctypes.util
import select
from ctypes import c_int, c_uint, POINTER, byref, c_ubyte


libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)


class Termios(ctypes.Structure):
    _fields_ = [
        ("c_iflag", c_uint),
        ("c_oflag", c_uint),
        ("c_cflag", c_uint),
        ("c_lflag", c_uint),
        ("c_line", c_ubyte),
        ("c_cc", c_ubyte * 32),
        ("c_ispeed", c_uint),
        ("c_ospeed", c_uint),
    ]


tcgetattr = libc.tcgetattr
tcgetattr.argtypes = [c_int, POINTER(Termios)]
tcgetattr.restype = c_int
tcsetattr = libc.tcsetattr
tcsetattr.argtypes = [c_int, c_int, POINTER(Termios)]
tcsetattr.restype = c_int
cfmakeraw = libc.cfmakeraw
cfmakeraw.argtypes = [POINTER(Termios)]
cfmakeraw.restype = None
tcflush = libc.tcflush
tcflush.argtypes = [c_int, c_int]
tcflush.restype = c_int

TCSANOW = 0
TCIFLUSH = 0


def probe(port, payload, read_secs=3.0, label=""):
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
    try:
        t = Termios()
        if tcgetattr(fd, byref(t)) != 0:
            print(f"[{label}] tcgetattr ERR {ctypes.get_errno()}")
            return b""
        cfmakeraw(byref(t))
        if tcsetattr(fd, TCSANOW, byref(t)) != 0:
            print(f"[{label}] tcsetattr ERR {ctypes.get_errno()}")
            return b""
        tcflush(fd, TCIFLUSH)
        os.write(fd, payload)
        time.sleep(0.3)
        acc = b""
        deadline = time.monotonic() + read_secs
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
                if b"OK" in acc or b"ERROR" in acc:
                    break
        return acc
    finally:
        os.close(fd)


def show(label, data):
    asc = data.decode("utf-8", "replace").replace(chr(13), "\\r").replace(chr(10), "\\n")
    print("[%s] hex=%r" % (label, data.hex()))
    print("[%s] asc=%r" % (label, asc))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    port = sys.argv[1]
    print("=" * 60)

    data = probe(port, b"at\r", label="LO1")
    show("LO1 at\\r", data)
    print("-" * 60)
    time.sleep(0.4)

    data = probe(port, b"at\n", label="LO2")
    show("LO2 at\\n", data)
    print("-" * 60)
    time.sleep(0.4)

    data = probe(port, b"AT\r\n", label="LO3")
    show("LO3 AT\\r\\n", data)
    print("-" * 60)
    time.sleep(0.4)

    data = probe(port, b"at", label="LO4")
    show("LO4 at", data)
    print("-" * 60)

    # 回读 speed，确认确实没改
    import subprocess
    sp = subprocess.run(["stty", "-F", port, "-a"], capture_output=True, text=True)
    for line in sp.stdout.splitlines():
        if "baud" in line:
            print("stty speed:", line.split(";")[0])
            break

    print("完成。看 LO1-LO4 是否有 OK/ERROR，发回。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
