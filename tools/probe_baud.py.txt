"""一次性定位「发送 AT 无返回」的根因（在 Linux 上用 sudo 跑）。

用法:
    sudo python3 tools/probe_baud.py /dev/ttyUSB3 115200

依次测 4 种组合，打印每种组合下 stty 读回的波特率与收到的数据：
  1. pyserial 默认打开（复刻 eCOM：exclusive=True + 拉高 DTR/RTS）
  2. 默认打开 + 强制 stty 写回波特率 (115200)
  3. 默认打开 + 不碰 DTR/RTS（拉低 → 模块 AT 口更常见）
  4. 默认打开 + 强制 stty + 不碰 DTR/RTS

每步会打印 stty -a 的 speed，并在发 AT 后读 in_waiting 与内容。
结论：哪一步能收到 OK，就说明是那一步对应的参数在作祟。
"""
import sys
import time
import subprocess
import serial


def run_stty(port, args):
    """执行 stty -F <port> <args>，返回 stdout 文本。"""
    try:
        p = subprocess.run(["stty", "-F", port] + args,
                           capture_output=True, text=True, timeout=5)
        return p.stdout + (p.stderr and (" [stderr]" + p.stderr) or "")
    except Exception as e:
        return f"[stty error] {e}"


def speed_of(port):
    """从 stty -a 输出里提取 speed <n> baud。"""
    out = run_stty(port, ["-a"])
    for line in out.splitlines():
        if "baud" in line:
            return line.split(";")[0].strip(), out
    return "?", out


def try_open(port, baud, exclusive, touch_dtr):
    """打开并发送一次 AT，返回 (描述, speed_before, speed_after, in_waiting, rxd)。"""
    s = serial.serial_for_url(port, baudrate=baud, timeout=1.0,
                              exclusive=exclusive)
    if touch_dtr:
        # eCOM 默认行为：dtr 勾选=拉低(False)，未勾选时 set_dtr(False)->dtr=True(拉高)
        try:
            s.dtr = True
            s.rts = True
        except Exception as e:
            pass
    sp_before, _ = speed_of(port)
    # 强制写回波特率（模拟上一轮 serial_core 里的 _force_baud）
    run_stty(port, [str(baud)])
    sp_after, _ = speed_of(port)
    try:
        s.write(b"AT\r\n")
    except Exception as e:
        s.close()
        return ("write error", sp_before, sp_after, 0, f"err:{e}")
    time.sleep(1.0)
    n = 0
    rxd = b""
    try:
        n = s.in_waiting
        if n:
            rxd = s.read(n)
    except Exception as e:
        rxd = f"[read err {e}]".encode()
    s.close()
    return (f"exclusive={exclusive} dtr={touch_dtr}", sp_before, sp_after, n, rxd)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    port = sys.argv[1]
    baud = int(sys.argv[2])
    cases = [
        (True, True),    # eCOM 原样
        (True, False),   # eCOM 但 DTR/RTS 不动
        (False, True),   # 非独占 + DTR 拉高
        (False, False),  # 最保守：非独占 + 不动 DTR/RTS
    ]
    for exclusive, touch_dtr in cases:
        desc, before, after, n, rxd = try_open(port, baud, exclusive, touch_dtr)
        # 清理可能残留的 UUCP/DBus 锁之外的临时 stty 影响
        print("-" * 50)
        print(f"[{desc}]")
        print(f"  speed before stty : {before}")
        print(f"  speed after  stty : {after}")
        print(f"  in_waiting        : {n}")
        text = rxd.decode("utf-8", errors="replace") if isinstance(rxd, bytes) else rxd
        print(f"  RX                : {text!r}")
        # 让串口空闲，避免干扰下一例
        time.sleep(0.5)
    print("-" * 50)
    print("完成。请把整段输出发回，据此定位是波特率、DTR/RTS 还是读取问题。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
