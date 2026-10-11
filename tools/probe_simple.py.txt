"""简单串口通信测试：横向对比 bash 原生 vs pyserial vs os.open。

用法（Linux，root）:
    sudo python3 tools/probe_simple.py /dev/ttyUSB3 115200

每法都发送多种命令变体并读取，打印 十六进制(hex) 防止肉眼漏看。
  S0. 纯 bash 子进程（printf> + timeout cat）: 你已验证可通，作对照组
  S1. pyserial 单 fd 打开发送 b'AT' / b'AT\\r\\n' / b'at\\r\\n' / b'AT\\n'
  S2. pyserial + reset_input_buffer + 发送后长延时读
  S3. os.open 单 fd + raw termios + 发送 b'AT\\r\\n'
"""
import os
import sys
import time
import subprocess


def show(tag, data):
    hx = data.hex()
    asc = data.decode("utf-8", "replace")
    print(f"  [{tag} ] hex={hx!r}   asc={asc!r}")


def bash_control(port):
    """复刻你验证过的 bash 方式：printf> 写 + timeout cat 读。"""
    cmd = "( sleep 0.2; printf 'AT\\r\\n' > {p} ) & timeout 2 cat {p}".format(p=port)
    try:
        p = subprocess.run(["bash", "-c", cmd], capture_output=True,
                           timeout=4, shell=False)
        return p.stdout
    except Exception as e:
        return f"ERR {e}".encode()


def pyserial_send(port, baud, payloads, reset):
    import serial
    s = serial.serial_for_url(port, baudrate=baud, timeout=1.0)
    out = b""
    for idx, pay in enumerate(payloads):
        try:
            if reset:
                s.reset_input_buffer()
            s.write(pay)
            s.flush()
        except Exception as e:
            out += b"[%d write_err %s] " % (idx, str(e).encode())
            continue
        time.sleep(0.5)
        try:
            r = s.read(256)
        except Exception as e:
            r = b"[err %s]" % str(e).encode()
        out += b"[payload%d=%r len=%d read=%r] " % (idx, pay, len(r), r)
    s.close()
    return out


def osopen_send(port, baud):
    import termios as T
    BAUD_MAP = {9600: T.B9600, 19200: T.B19200, 38400: T.B38400,
                57600: T.B57600, 115200: T.B115200}
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
    try:
        attr = T.tcgetattr(fd)
        attr[0] = 0
        attr[1] = 0
        attr[3] = 0
        attr[2] = T.CS8 | T.CLOCAL | T.CREAD
        if baud in BAUD_MAP:
            attr[4] = BAUD_MAP[baud]
            attr[5] = BAUD_MAP[baud]
        T.tcsetattr(fd, T.TCSANOW, attr)
        os.write(fd, b"AT\r\n")
        time.sleep(0.5)
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
        return acc
    finally:
        os.close(fd)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    port = sys.argv[1]
    baud = int(sys.argv[2])

    print("=" * 62)
    print("[S0] bash 子进程 printf> + timeout cat (对照)")
    show("S0", bash_control(port))
    print("-" * 62)
    time.sleep(0.4)

    print("[S1] pyserial 单 fd 发送多种变体")
    payloads = [b"AT", b"AT\r\n", b"at\r\n", b"AT\n", b"AT\r"]
    show("S1", pyserial_send(port, baud, payloads, reset=False))
    print("-" * 62)
    time.sleep(0.4)

    print("[S2] pyserial + reset_input_buffer + 发送 b'AT\\r\\n'")
    show("S2", pyserial_send(port, baud, [b"AT\r\n"], reset=True))
    print("-" * 62)
    time.sleep(0.4)

    print(f"[S3] os.open + raw + 发送 b'AT\\r\\n'")
    show("S3", osopen_send(port, baud))
    print("-" * 62)

    print("完成。看 S0 是否非空(对照)，S1/S2/S3 是否非空，发回这四行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
