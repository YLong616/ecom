"""编解码：发送数据类型(ASCII/HEX/DEC/BIN) + send-on-enter 后缀 + 接收显示。

- ``encode``：把 GUI 输入的文本按类型 + 后缀转成待发送 bytes。
- ``decode_display``：把收到的 bytes 转成展示字符串（可选 HEX）。
"""

from __future__ import annotations

# 发送数据类型
SEND_TYPES = ["ASCII", "HEX", "DEC", "BIN"]

# send-on-enter 后缀
SUFFIXES = ["None", "CR", "LF", "CR-LF", "SPACE", "STX-ETX", "NULL"]

_SUFFIX_BYTES = {
    "CR": b"\r",
    "LF": b"\n",
    "CR-LF": b"\r\n",
    "SPACE": b" ",
    "NULL": b"\x00",
}


def _parse_hex(text: str) -> bytes:
    """解析 hex 字符串：忽略空格 / 换行 / 逗号 / 0x 前缀。"""
    cleaned = (
        text.replace(" ", "").replace("\n", "")
            .replace(",", "").replace("0x", "").replace("0X", "")
    )
    if len(cleaned) % 2 != 0:
        raise ValueError("HEX 长度必须为偶数（每 2 位十六进制对应 1 字节）")
    return bytes.fromhex(cleaned)


def encode(text: str, data_type: str = "ASCII", suffix: str = "None") -> bytes:
    """按类型与后缀把 GUI 输入转成待发送 bytes。"""
    data_type = (data_type or "ASCII").upper()
    suffix = suffix or "None"

    if data_type == "HEX":
        body = _parse_hex(text)
    elif data_type == "DEC":
        tokens = text.split()
        if not tokens:
            body = b""
        else:
            body = bytes(int(t) & 0xFF for t in tokens)
    elif data_type == "BIN":
        tokens = text.split()
        if not tokens:
            body = b""
        else:
            body = bytes(int(t, 2) & 0xFF for t in tokens)
    elif data_type == "ASCII":
        body = text.encode("utf-8")
    else:
        raise ValueError(f"未知发送类型: {data_type}")

    if suffix == "STX-ETX":
        return b"\x02" + body + b"\x03"
    extra = _SUFFIX_BYTES.get(suffix)
    if extra is not None:
        return body + extra
    return body


def decode_display(data: bytes, display_hex: bool = False) -> str:
    """把收到的 bytes 转成展示字符串。display_hex=True 时按 hex 展开。"""
    if display_hex:
        return " ".join(f"{b:02X}" for b in data) + " "
    return data.decode("utf-8", errors="replace")


def escape_control(text: str, show_crlf: bool = True) -> str:
    """把 \\r \\n 等控制字符转成可见的 \\r / \\n / \\t（用于显示选项）。"""
    if not show_crlf:
        return text
    return (
        text.replace("\r\n", "\\r\\n")
            .replace("\r", "\\r")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\x00", "\\0")
    )


def display_body(data: bytes, show_hex: bool = False, show_crlf: bool = True) -> str:
    """统一接收/发送显示：show_crlf=True 时把 \r\n 转义成字面量；
    关闭时去掉行尾裸 CR/LF（CR-LF/LF 终止符），交由换行表达，避免渲染成豆腐块。"""
    body = decode_display(data, show_hex)
    if show_crlf:
        return escape_control(body)
    return body.rstrip(chr(13) + chr(10))
