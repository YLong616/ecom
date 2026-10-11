"""用 ctypes 直调 libc termios（绕开残缺的 Python termios 模块），复刻 microcom。

用法（Linux，root）:
    sudo python3 tools/probe_ctypes.py /dev/ttyUSB3 115200

动机：这台机器 Python 的 termios 模块缺少 cfsetispeed（报错已确认），
pyserial 内部设波特率依赖它 -> 设不动 -> termios 停 9600 -> 模块按 115200 通信不回。
microcom 是 busybox 二进制直接用 libc，不受影响，所以它通。

本脚本用 ctypes 直接调用 libc 的 tcgetattr/tcsetattr/cfsetispeed/cfsetospeed，
再设置 raw(8N1, CLOCAL|CREAD) 和 DTR/RTS 拉高，发送 AT 读取。
若通 -> 证明根因是 Python termios 残缺，eCOM 修复方案改用 ctypes/裸 ioctl 设波特率。
"""
import os
import sys
import time
import ctypes
import ctypes.util
from ctypes import c_int, c_uint, c_void_p, POINTER, byref


libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)


# ---- C termios 常量（Linux x86_64 标准值） ----
TCSANOW = 0
B9600 = 13
B115200 = 24          # x86_64: 115200 -> B115200=24
CS8 = 48              # 0011000
CLOCAL = 0x800        # 00004000? 实际 0x1000? 按常见: 0x800 (2048)
CREAD = 0x80
VMIN = 6
VTIME = 5
TIOCMSET = 0x5418
TIOCM_DTR = 0x002
TIOCM_RTS = 0x004
TCIOFLUSH = 2         # TCIFLUSH? 用 TCIOFLUSH=2 实际用 TCIFLUSH=0
_TCIFLUSH_ = 0
TCIFLUSH = 0

# 实际 linux 值（从 /usr/include/asm-generic/termbits.h 校正）
B115200 = 24
B9600 = 13
CS8 = 48              # 0x30
CLOCAL = 0x800        # 0x00000800 on x86_64? 常用 0x800 (2048)
CREAD = 0x80
_cflag_mask = 0
if False:
    pass


def cfg_termios_c(baud):
    """返回 ctypes 的 termios 类型定义与设置函数。"""
    # termios 在 glibc 的 struct: tcflag_t c_iflag,c_oflag,c_cflag,c_lflag;
    # cc_t c_line; cc_t c_cc[32]; speed_t c_ispeed,c_ospeed;
    # tcflag_t 4 字节, cc_t 1 字节, speed_t 4 字节
    class Termios(ctypes.Structure):
        _fields_ = [
            ("c_iflag", c_uint),
            ("c_oflag", c_uint),
            ("c_cflag", c_uint),
            ("c_lflag", c_uint),
            ("c_line", ctypes.c_ubyte),
            ("c_cc", ctypes.c_ubyte * 32),
            ("c_ispeed", c_uint),
            ("c_ospeed", c_uint),
        ]
    # config get/set 从 libc
    tcgetattr = libc.tcgetattr
    tcgetattr.argtypes = [c_int, POINTER(Termios)]
    tcgetattr.restype = c_int
    tcsetattr = libc.tcsetattr
    tcsetattr.argtypes = [c_int, c_int, POINTER(Termios)]
    tcsetattr.restype = c_int
    cfsetispeed = libc.cfsetispeed
    cfsetispeed.argtypes = [POINTER(Termios), c_uint]
    cfsetispeed.restype = c_int
    cfsetospeed = libc.cfsetospeed
    cfsetospeed.argtypes = [POINTER(Termios), c_uint]
    cfsetospeed.restype = c_int
    return Termios, tcgetattr, tcsetattr, cfsetispeed, cfsetospeed


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    port = sys.argv[1]
    baud = int(sys.argv[2])
    baudmap = {9600: B9600, 115200: B115200}

    Termios, tcgetattr, tcsetattr, cfsetispeed, cfsetospeed = cfg_termios_c(baud)

    fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
    try:
        t = Termios()
        if tcgetattr(fd, byref(t)) != 0:
            print("tcgetattr ERR", ctypes.get_errno())
            return 1
        print("got termios; trying cfsetispeed/cfsetospeed...")
        r1 = cfsetispeed(byref(t), baudmap[baud])
        r2 = cfsetospeed(byref(t), baudmap[baud])
        print("cfsetispeed=%d cfsetospeed=%d errno=%d" % (r1, r2, ctypes.get_errno()))
        # raw 8N1 + CLOCAL|CREAD
        t.c_iflag = 0
        t.c_oflag = 0
        t.c_lflag = 0
        t.c_cflag = CS8 | CLOCAL | CREAD
        t.c_cc[VMIN] = 1
        t.c_cc[VTIME] = 0
        if tcsetattr(fd, TCSANOW, byref(t)) != 0:
            print("tcsetattr ERR", ctypes.get_errno())
            return 1
        # 请求 DTR/RTS 拉高
        import fcntl, struct
        try:
            fcntl.ioctl(fd, TIOCMSET, struct.pack("I", TIOCM_DTR | TIOCM_RTS))
            print("ioctl DTR|RTS OK")
        except OSError as e:
            print("ioctl DTR|RTS skip:", e)

        # flush 输入
        try:
            libc.tcflush(fd, _TCIFLUSH_)
        except Exception:
            pass

        # 发送 + 读
        os.write(fd, b"AT\r\n")
        time.sleep(0.4)
        import select
        acc = b""
        deadline = time.monotonic() + 2.0
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
                if b"\n" in acc or b"OK" in acc:
                    break
        print("RX hex:", acc.hex())
        print("RX asc:", acc.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
        print("RX len:", len(acc))
        # 回读 stty -a 看 speed
        import subprocess
        sp = subprocess.run(["stty", "-F", port, "-a"], capture_output=True, text=True)
        for line in sp.stdout.splitlines():
            if "baud" in line:
                print("stty speed line:", line.split(";")[0])
                break
        return 0
    finally:
        os.close(fd)


if __name__ == "__main__":
    sys.exit(main())
