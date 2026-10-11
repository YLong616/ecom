"""压力模式核心逻辑（纯 Python，无 Tk，可单测）。

包含：
- StressRow：AT list 单行模型。
- CheckRule / BUILTIN_RULES：自定义 check 规则（内置示例）。
- parse_expected / match_expected：预期结果的解析与匹配（包含/正则/全等）。
- run_check_rules：对某次响应跑所有启用的自定义规则。
- EndCondition / RunStats / format_duration / format_window：结束条件与统计口径。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

# 预期结果匹配模式
MATCH_CONTAINS = "contains"   # 纯字符串包含匹配
MATCH_REGEX = "regex"         # 正则
MATCH_EXACT = "exact"         # 全等
MATCH_MODES = [MATCH_CONTAINS, MATCH_REGEX, MATCH_EXACT]

# 记录目标
TARGET_AT = "at"   # AT Log
TARGET_DOS = "dos"  # DOS Log
TARGET_BOTH = "both"
TARGETS = [TARGET_AT, TARGET_DOS, TARGET_BOTH]


@dataclass
class StressRow:
    """AT list 单行数据。"""

    txt: str = ""                 # AT 命令文本
    send_type: str = "ASCII"      # ASCII/HEX/DEC/BIN
    send_suffix: str = "CR-LF"    # None/CR/LF/CR-LF/SPACE/STX-ETX/NULL
    hex: bool = False             # HEX 快捷勾选（True 则该行强制按 HEX 发送）
    enter: bool = True            # Enter 快捷勾选（True 则该行强制追加 CR-LF）
    interval_ms: int = 0          # 单行间隔(ms)，0 = 用全局行间隔
    expected: str = "OK"          # 预期结果（多个用换行或 | 分隔），默认 OK
    match_mode: str = MATCH_CONTAINS
    enabled: bool = True          # 是否参与压测

    def __post_init__(self):
        if self.match_mode not in MATCH_MODES:
            self.match_mode = MATCH_CONTAINS
        if self.send_type not in ("ASCII", "HEX", "DEC", "BIN"):
            self.send_type = "ASCII"

    @property
    def effective_type(self) -> str:
        """实际发送类型：HEX 勾选优先。"""
        return "HEX" if self.hex else self.send_type

    @property
    def effective_suffix(self) -> str:
        """实际发送后缀：Enter 勾选（CR-LF）优先。"""
        return "CR-LF" if self.enter else self.send_suffix

    @property
    def has_expected(self) -> bool:
        return bool(str(self.expected or "").strip())

    def to_dict(self) -> dict:
        return {
            "txt": self.txt, "send_type": self.send_type,
            "send_suffix": self.send_suffix, "hex": self.hex,
            "enter": self.enter, "interval_ms": self.interval_ms,
            "expected": self.expected, "match_mode": self.match_mode,
            "enabled": self.enabled,
        }

    @staticmethod
    def from_dict(d: dict) -> "StressRow":
        return StressRow(
            txt=str(d.get("txt", "")),
            send_type=str(d.get("send_type", "ASCII")),
            send_suffix=str(d.get("send_suffix", "None")),
            hex=bool(d.get("hex", False)),
            enter=bool(d.get("enter", False)),
            interval_ms=int(d.get("interval_ms", 0) or 0),
            expected=str(d.get("expected", "")),
            match_mode=str(d.get("match_mode", MATCH_CONTAINS)),
            enabled=bool(d.get("enabled", True)),
        )


@dataclass
class CheckRule:
    """自定义 check 规则：命中关键字 → 判异常 → 记录到目标。"""

    name: str = ""
    keyword: str = ""
    record_to: str = TARGET_DOS   # at/dos/both
    as_exception: bool = True      # 命中是否计入异常数
    enabled: bool = False


# 内置示例规则（默认关闭，用户可开可改，作为发散参考）
BUILTIN_RULES = [
    CheckRule(name="模组异常重启", keyword="RDY",
              record_to=TARGET_DOS, as_exception=True, enabled=False),
    CheckRule(name="响应含ERROR", keyword="ERROR",
              record_to=TARGET_DOS, as_exception=True, enabled=False),
]


# ---------- 预期结果 ----------
def parse_expected(expected: str) -> list[str]:
    """把预期字符串拆成多个独立预期，分隔符：换行 / 竖线。"""
    s = str(expected or "")
    parts = re.split(r"[\n|]+", s)
    return [p.strip() for p in parts if p.strip()]


def match_expected(response_text: str, expected: str, mode: str) -> bool:
    """判断响应是否命中预期（多个预期任一命中即通过）。"""
    if mode not in MATCH_MODES:
        mode = MATCH_CONTAINS
    expects = parse_expected(expected)
    if not expects:
        return True  # 无预期结果 → 不校验，视为通过
    for exp in expects:
        if mode == MATCH_CONTAINS:
            if exp in response_text:
                return True
        elif mode == MATCH_EXACT:
            if response_text.strip() == exp:
                return True
        elif mode == MATCH_REGEX:
            try:
                if re.search(exp, response_text):
                    return True
            except re.error:
                # 非法正则：退化为包含匹配
                if exp in response_text:
                    return True
    return False


def run_check_rules(response_text: str, rules: list[CheckRule]) -> list[tuple]:
    """跑所有启用规则，返回命中记录 [(rule, response_text)]。"""
    hits = []
    for rule in rules:
        if not rule.enabled:
            continue
        if not rule.keyword:
            continue
        if rule.keyword in response_text:
            hits.append((rule, response_text))
    return hits


# ---------- 统计 ----------
@dataclass
class RunStats:
    """压测运行统计（口径：已发送数=发送行条数；异常数=不匹配+规则命中；当前行=行号）。"""

    sent_lines: int = 0          # 已发送行条数
    errors: int = 0              # 异常数（预期不匹配 + 规则命中）
    current_line: int = 0        # 当前正在发送的行号（1-based）
    total_rounds: int = 0        # 实际完成的轮数
    start_time: datetime | None = None   # 脚本运行时间段起点
    end_time: datetime | None = None     # 脚本运行时间段终点


def format_duration(seconds: float) -> str:
    """测试时长：按样本格式以 小时、1 位小数 展示（如 0.0H）。"""
    return f"{seconds / 3600.0:.1f}H"


def format_window(start: datetime, end: datetime) -> str:
    """脚本运行时间段：start~end（含微秒）。"""
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    return f"{start.strftime(fmt)}~{end.strftime(fmt)}"


def compute_end_condition(current_rounds: int, mode: str, target_count: int,
                          elapsed_seconds: float, target_seconds: float) -> bool:
    """是否满足结束条件（二选一，只判选中那种）。"""
    if mode == "time":
        return elapsed_seconds >= target_seconds
    return current_rounds >= target_count
