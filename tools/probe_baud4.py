"""纯 termios 复刻 microcom：验证「pyserial 打开改了不该改的 termios 位」这一根因。

用法（Linux，root）:
    sudo python3 tools/probe_baud4.py /dev/ttyUSB3 115200

V1: os.open(port) 后【不动波特率、不设 termios 模式】直接写 AT + 读  -> 复刻 bash printf>cat
V2: os.open(port) 后设 raw(8N1, CLOCAL|CREAD) 写 AT + 读           -> 复刻 microcom
V3: 同 V2，但再额外 assert DTR 拉高（TIOCM_DTR）写 AT + 读          -> 排查 DTR 影响

判定：
  - V1 通 -> 波特率/模式都不是问题，纯粹 pyserial open 设了不该设的位（或 exclusive/flock）
  - V1 不通、V2 通 -> 需要 raw 模式微调（我据此改 serial_core）
  - V2 通、V1 不通 -> 确认是 pyserial 参数问题
  - 全不通 -> 说明设备根本不能被 os.open 触发，需换方向
"""
import os
import sys
import time
import struct
import fcntl
import termios as T


BAUD_MAP = {9600: T.B9600, 19200: T.B19200, 38400: T.B38400,
            57600: T.B57600, 115200: T.B115200}


def _speed(port, fd):
    """用子进程 stty -a 回读 speed（与 pyserial 时代一致的观察口径）。"""
    if not port:
        return "?"
    try:
        r = subprocess.run if False else None
    except Exception:
        pass
    return None


def read_rx(fd, seconds=1.5):
    """从 fd 阻塞读一段时间；V2/V3 里 min=0 时用 select 等。"""
    import select
    deadline = time.monotonic() + seconds
    acc = b""
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
    return acc


def v1(port, baud):
    """完全按 bash 方式：os.open 写到 fd，sleep 后读。先不设 termios。"""
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
    try:
        os.write(fd, b"AT\r\n")
        time.sleep(0.3)
        return read_rx(fd)
    finally:
        os.close(fd)


def _set_raw(port, baud, set_speed=True):
    """设置 8N1 raw + CLOCAL|CREAD；set_speed 时直接赋 attr[4]/[5]。"""
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
    try:
        attr = T.tcgetattr(fd)
        attr[0] = 0                       # iflag
        attr[1] = 0                       # oflag
        attr[3] = 0                       # lflag
        cflag = T.CS8 | T.CLOCAL | T.CREAD
        attr[2] = cflag
        if set_speed and baud in BAUD_MAP:
            attr[4] = BAUD_MAP[baud]
            attr[5] = BAUD_MAP[baud]
        T.tcsetattr(fd, T.TCSANOW, attr)
        return fd
    except Exception:
        os.close(fd)
        raise


def v2(port, baud, dtr=False):
    """设 raw 8N1 CLOCAL|CREAD（microcom 同款）写 + 读。"""
    fd = _set_raw(port, baud, set_speed=True)
    try:
        if dtr:
            # TIOCMOD: modulo control via ioctl
            TIOCMSET = 0x5418
            TIOCM_DTR = 0x002
            state = TIOCM_DTR
            try:
                fcntl.ioctl(fd, TIOCMSET, struct.pack("I", state))
            except OSError:
                pass
        # 写前先冲掉 leftover
        try:
            T.tcflush(fd, T.TCIFLUSH)
        except OSError:
            pass
        os.write(fd, b"AT\r\n")
        time.sleep(0.3)
        return read_rx(fd)
    finally:
        os.close(fd)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    port = sys.argv[1]
    baud = int(sys.argv[2])

    print("=" * 58)
    print("[V1] os.open 不动 termios 直接写读 (复刻 bash printf>cat)")
    try:
        r = v1(port, baud)
        print("    RX:", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    except Exception as e:
        print("    ERR:", e)
    print("-" * 58)
    time.sleep(0.4)

    print(f"[V2] os.open + raw 8N1 CLOCAL|CREAD(B{baud}) 写读 (microcom 同款)")
    try:
        r = v2(port, baud)
        print("    RX:", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    except Exception as e:
        print("    ERR:", e)
    print("-" * 58)
    time.sleep(0.4)

    print(f"[V3] 同 V2 + DTR 拉高 写读")
    try:
        r = v2(port, baud, dtr=True)
        print("    RX:", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    except Exception as e:
        print("    ERR:", e)
    print("-" * 58)

    print("完成。发回 V1/V2/V3 的 RX 与是否有 ERR，即可定论。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
