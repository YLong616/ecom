"""Log 落盘：把收发记录写入文本文件。

日志行格式与输出框逐字节一致：``[2026-08-25_11:19:52:459]  TX  AT+QGMR``
"""

from __future__ import annotations

import datetime
import os


class Logger:
    def __init__(self):
        self._f = None
        self._path = None
        self.entries = 0

    @property
    def active(self) -> bool:
        return self._f is not None

    @property
    def path(self) -> str:
        return self._path

    def start(self, path: str) -> bool:
        """开始记录到 path；重复调用会先关闭旧的。"""
        self.stop()
        abspath = os.path.abspath(path)
        os.makedirs(os.path.dirname(abspath), exist_ok=True)
        try:
            self._f = open(abspath, "a", encoding="utf-8")
        except OSError:
            self._f = None
            return False
        self._path = abspath
        self.entries = 0
        return True

    def stop(self):
        if self._f is not None:
            try:
                self._f.flush()
                self._f.close()
            except OSError:
                pass
            self._f = None
            self._path = None

    def log(self, line: str):
        """写一条记录，直接写入与输出框一致的整行（含 [时间戳]  TX/RX  正文）。

        与输出框逐字节一致：输出框渲染什么，Log 就保存什么。
        """
        if not self.active:
            return
        try:
            self._f.write(line + "\n")
            self._f.flush()
            self.entries += 1
        except OSError:
            pass
