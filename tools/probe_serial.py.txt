#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""串口诊断：复刻 ecom 的打开/发送参数，验证 pyserial 能否读回 AT 响应。

用法（在项目根 projects/eCOM 下）：
    python3 tools/probe_serial.py                  # 默认 /dev/ttyUSB3 115200
    python3 tools/probe_serial.py /dev/ttyUSB3 115200
    python3 tools/probe_serial.py --no-excl        # 不用 exclusive=True

脚本会先以 exclusive=True 测一次，再以非 exclusive 测一次，便于对比。
输出 in_waiting 与接收字节的 hex / 文本。
"""
import sys
import time
import serial


def probe(port, baud, excl):
    kw = dict(
        baudrate=baud,
        bytesize=8,
        parity=serial.PARITY_NONE,
        stopbits=1,
        xonxoff=False,
        rtscts=False,
        timeout=0.5,
    )
    if excl:
        kw["exclusive"] = True
    try:
        ser = serial.serial_for_url(port, **kw)
    except Exception as e:
        print("OPEN FAIL port=%s exclusive=%s :: %r" % (port, excl, e))
        return
    print("OPENED      port=%s baud=%s exclusive=%s" % (port, baud, excl))
    try:
        ser.reset_input_buffer()
    except Exception:
        pass
    ser.write(b"at\r\n")
    time.sleep(0.8)
    n = ser.in_waiting
    print("  in_waiting =", n)
    data = ser.read(n) if n else b""
    print("  RX hex     :", data.hex(" ") if data else "(none)")
    print("  RX text    :", repr(data))
    ser.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    excl = "--no-excl" not in args
    rest = [a for a in args if not a.startswith("--") and not a.isdigit()]
    nums = [a for a in args if a.isdigit()]
    port = rest[0] if rest else "/dev/ttyUSB3"
    baud = int(nums[0]) if nums else 115200

    print("==== exclusive=True ====")
    probe(port, baud, True)
    print("\n==== exclusive=False ====")
    probe(port, baud, False)
