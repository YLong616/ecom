"""最终定位：隔离「pyserial 问题」 vs 「波特率设不进去」。

用法（Linux，root）:
    sudo python3 tools/probe_baud3.py /dev/ttyUSB3 115200

依次做 4 个实验，打印每段 RX 与 stty 回读的 speed：

  X1. 先 stty -F <port> 115200 raw -echo 强制写回，再 pyserial 打开+写+读
  X2. pyserial 裸打开（不先 stty）+ 写 + 读        （复现 eCOM，应失败）
  X3. 纯 os.open + termios 设置 B115200（不用 pyserial）写+读
  X4. 同 X1，但读取用【阻塞】(VMIN=1) 而非轮询

判定：
  - 若 X1/X3 能收到 OK 而 X2 收不到 -> 是 pyserial 打开/参数问题（改 eCOM 打开方式）
  - 若 X1/X3 也收不到，且 stty 回读恒 9600 -> 波特率在驱动层设不进去，需换打开策略
"""
import os
import sys
import time
import subprocess
import serial
import termios as T


def stty_force(port, baud):
    r = subprocess.run(
        ["stty", "-F", port, str(baud), "raw", "-echo"],
        capture_output=True, text=True, timeout=8,
    )
    return r.returncode, (r.stderr or "").strip()


def stty_speed(port):
    """回读当前 speed 字段。"""
    try:
        r = subprocess.run(["stty", "-F", port, "-a"],
                           capture_output=True, text=True, timeout=8)
        for line in r.stdout.splitlines():
            if "baud" in line:
                return line.split(";")[0].strip()
    except Exception as e:
        return f"err:{e}"
    return "?"


def py_recv(s, seconds=1.5):
    deadline = time.monotonic() + seconds
    acc = b""
    while time.monotonic() < deadline:
        try:
            n = s.in_waiting
            if n:
                acc += s.read(n)
                break
        except Exception:
            pass
        time.sleep(0.05)
    if not acc:
        try:
            acc = s.read(64)
        except Exception:
            acc = b""
    return acc


def py_try(port, baud, pre_stty):
    """pyserial 打开 + 写 + 读；可选先 stty 强制波特率。"""
    if pre_stty:
        stty_force(port, baud)
    s = serial.serial_for_url(port, baudrate=baud, timeout=1.0)
    w = None
    try:
        s.reset_input_buffer()
        s.write(b"AT\r\n")
        s.flush()
        w = "OK"
    except Exception as e:
        w = f"err:{e}"
    r = py_recv(s, 1.5)
    spd = stty_speed(port)
    s.close()
    return w, r, spd


def raw_termios_try(port, baud):
    """纯 os.open + termios 设置 B115200，不经过 pyserial。"""
    baud_map = {9600: T.B9600, 19200: T.B19200, 38400: T.B38400,
                57600: T.B57600, 115200: T.B115200}
    if baud not in baud_map:
        return "unsupported-baud", b"", ""
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        attr = T.tcgetattr(fd)
        attr[0] = 0                    # iflag
        attr[1] = 0                    # oflag
        attr[2] = T.CS8 | T.CLOCAL     # cflag: 8N1, no modem ctl
        attr[3] = 0                    # lflag
        attr[6][T.VMIN] = 0
        attr[6][T.VTIME] = 0
        T.cfsetispeed(attr, baud_map[baud])
        T.cfsetospeed(attr, baud_map[baud])
        T.tcsetattr(fd, T.TCSANOW, attr)
        os.write(fd, b"AT\r\n")
        time.sleep(0.3)
        try:
            data = os.read(fd, 256)
        except BlockingIOError:
            data = b""
            # 阻塞读兜底
            T.tcsetattr(fd, T.TCSANOW, attr)  # reset
            attr[6][T.VMIN] = 1
            T.tcsetattr(fd, T.TCSANOW, attr)
            try:
                data = os.read(fd, 64)
            except Exception:
                data = b""
        spd = stty_speed(port)
        return "OK", data, spd
    finally:
        os.close(fd)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    port = sys.argv[1]
    baud = int(sys.argv[2])

    print("=" * 60)

    # X1: 先 stty 强制波特率，再 pyserial
    rc, err = stty_force(port, baud)
    print(f"[X1] stty {baud} raw -echo (rc={rc}) + pyserial 写读")
    print("    stty stderr:", err or "(none)")
    w, r, spd = py_try(port, baud, pre_stty=False)  # 已 stty，不再重复
    print("    speed after :", spd)
    print("    write:", w)
    print("    RX  :", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    print("-" * 60)
    time.sleep(0.5)

    # X2: pyserial 裸打开（复现 eCOM）
    print("[X2] pyserial 裸打开 + 写读 (复现 eCOM)")
    w, r, spd = py_try(port, baud, pre_stty=False)
    print("    speed after :", spd)
    print("    write:", w)
    print("    RX  :", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    print("-" * 60)
    time.sleep(0.5)

    # X3: 纯 os.open + termios B<baud>（不用 pyserial）
    print(f"[X3] 纯 os.open + termios B{baud} (不用 pyserial) 写读")
    w, r, spd = raw_termios_try(port, baud)
    print("    speed after :", spd)
    print("    write:", w)
    print("    RX  :", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    print("-" * 60)
    time.sleep(0.5)

    # X4: 先 stty 强制 + pyserial，读取用阻塞(VMIN=1)
    print(f"[X4] stty {baud} 强制 + pyserial 写读(阻塞读)")
    stty_force(port, baud)
    s = serial.serial_for_url(port, baudrate=baud, timeout=2.0)
    w = "OK"
    try:
        s.reset_input_buffer()
        s.write(b"AT\r\n")
        s.flush()
    except Exception as e:
        w = f"err:{e}"
    time.sleep(0.4)
    try:
        r = s.read(64)
    except Exception as e:
        r = f"[{e}]".encode()
    spd = stty_speed(port)
    print("    speed after :", spd)
    print("    write:", w)
    print("    RX  :", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    s.close()
    print("-" * 60)

    print("完成。发回 X1/X2/X3/X4 的 RX 与 speed，即可定位。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
