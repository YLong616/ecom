"""配置持久化：串口参数 / 显示选项 / Log / 发送选项 / AT 命令组 -> JSON。

配置文件默认位于 ``~/.ecom/config.json``（跨项目共享，可被 M7 打包复用）。
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _deep_merge(base: dict, overlay: dict) -> dict:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


DEFAULT_CONFIG = {
    "language": "zh",
    "serial": {
        "port": "",
        "baudrate": "115200",
        "databits": "8",
        "stopbits": "1",
        "parity": "None (N)",
        "flow": "None",
    },
    "display": {
        "timestamp": True,
        "direction": True,
        "crlf": True,
        "hex": False,
    },
    "log": {"path": ""},
    "send": {"type": "ASCII", "suffix": "CR-LF"},
    "at_groups": {},
    "stress": {
        "name": "压力测试1",
        "end_mode": "count",
        "count": 1,
        "time": 1,           # 单位：分钟
        "interval_ms": 300,
        "timeout_ms": 2000,
        "at_log": "",
        "dos_log": "",
        "rows": [],
        "rules": [],
    },
}


class Config:
    def __init__(self, path: str | None = None):
        self.path = path or str(Path.home() / ".ecom" / "config.json")
        self.data = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                user = json.load(f)
            if isinstance(user, dict):
                _deep_merge(self.data, user)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        # 兼容旧配置：后缀 "CRLF" -> "CR-LF"
        send = self.data.get("send")
        if isinstance(send, dict) and send.get("suffix") == "CRLF":
            send["suffix"] = "CR-LF"

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, section: str, key: str | None = None, default=None):
        if key is None:
            return self.data.get(section, default)
        section_data = self.data.get(section)
        if isinstance(section_data, dict):
            return section_data.get(key, default)
        return default

    def set(self, section: str, key: str, value):
        self.data.setdefault(section, {})[key] = value

    def get_at_group(self, name: str, default=None):
        return self.data.get("at_groups", {}).get(name, default)

    def set_at_group(self, name: str, commands):
        self.data.setdefault("at_groups", {})[name] = commands

    def remove_at_group(self, name: str):
        self.data.setdefault("at_groups", {}).pop(name, None)
