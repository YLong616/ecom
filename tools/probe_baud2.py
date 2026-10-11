"""一次性定位「pyserial 发 AT 无返回」：区分是写不通/读不通/open 动作问题。

用法（Linux 上，root 或 dialout 组）:
    sudo python3 tools/probe_baud2.py /dev/ttyUSB3 115200

会依次做 5 个实验并打印结果：
  A. shell 写 + shell 读          (对照组，你手动已验证能通)
  B. pyserial 写 + pyserial 读    (复现当前 eCOM 的失败)
  C. shell 写 + pyserial 读      (若通 -> pyserial 读没问题, 是写的问题)
  D. pyserial 写 + shell 读      (若通 -> pyserial 写没问题, 是读的问题)
  E. pyserial 写 + pyserial 主动 read(等读)  (排除 in_waiting 不可靠)

结论定位：哪个组合通/不通，即指向对应环节。
"""
import os
import sys
import time
import subprocess
import serial


def stty_raw(port):
    # 设 raw（echo 关、规范模式关），成功与否不重要的模块自动忽略
    subprocess.run(["stty", "-F", port, "raw", "-echo"],
                   capture_output=True, text=True, timeout=5)


def shell_send(port, data):
    # 用 shell 重定向写（与手动 printf 完全一致）
    try:
        with open(port, "ab", buffering=0) as f:
            f.write(data)
        return True
    except Exception as e:
        return f"err:{e}"


def shell_recv(port, seconds=2):
    # 用 shell 读设备（等同 timeout cat）
    try:
        p = subprocess.run(["timeout", str(seconds), "cat", port],
                           capture_output=True, timeout=seconds + 2)
        return p.stdout
    except Exception as e:
        return f"[recv err {e}]".encode()


def py_send(s, data):
    try:
        s.reset_input_buffer()
        s.write(data)
        s.flush()
        return True
    except Exception as e:
        return f"err:{e}"


def py_recv_inwaiting(s, seconds=1.5):
    """轮询 in_waiting；同时用主动 read 兜底，排除 in_waiting 不可靠。"""
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
        time.sleep(0.1)
    if not acc:
        # 兜底：直接 read(阻塞到 timeout)
        try:
            acc = s.read(64)
        except Exception:
            acc = b""
    return acc


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    port = sys.argv[1]
    baud = int(sys.argv[2])
    AT = b"AT\r\n"

    stty_raw(port)
    print("=" * 56)

    # A: shell 写 + shell 读 (对照组)
    print("[A] shell 写 + shell 读 (对照组)")
    shell_send(port, AT)
    r = shell_recv(port, 2)
    print("    RX:", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    print("-" * 56)
    time.sleep(0.5)

    # B: pyserial 写 + pyserial 读 (复现 eCOM)
    print("[B] pyserial 写 + pyserial 读 (复现 eCOM)")
    s = serial.serial_for_url(port, baudrate=baud, timeout=1.0)
    w = py_send(s, AT)
    r = py_recv_inwaiting(s, 1.5)
    print("    write:", "OK" if w is True else w)
    print("    RX  :", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    s.close()
    print("-" * 56)
    time.sleep(0.5)

    # C: shell 写 + pyserial 读 (写用 shell, 读用 pyserial)
    print("[C] shell 写 + pyserial 读")
    s = serial.serial_for_url(port, baudrate=baud, timeout=1.0)
    w = shell_send(port, AT)
    r = py_recv_inwaiting(s, 1.5)
    print("    write:", "OK" if w is True else w)
    print("    RX  :", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    s.close()
    print("-" * 56)
    time.sleep(0.5)

    # D: pyserial 写 + shell 读 (写用 pyserial, 读用 shell)
    print("[D] pyserial 写 + shell 读")
    s = serial.serial_for_url(port, baudrate=baud, timeout=1.0)
    w = py_send(s, AT)
    print("    write:", "OK" if w is True else w)
    r = shell_recv(port, 2)
    print("    RX  :", r.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    s.close()
    print("-" * 56)
    time.sleep(0.5)

    # E: pyserial 写 + pyserial 主动 read (打开读线程式)
    print("[E] pyserial 写 + 主动 read(读线程式)")
    s = serial.serial_for_url(port, baudrate=baud, timeout=2.0)
    w = py_send(s, AT)
    print("    write:", "OK" if w is True else w)
    time.sleep(0.5)
    acc = b""
    try:
        acc = s.read(64)
    except Exception as e:
        acc = f"[{e}]".encode()
    print("    RX  :", acc.decode("utf-8", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    s.close()
    print("-" * 56)

    print("完成。分别记录 A/B/C/D/E 的 RX，发回定位环节。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
