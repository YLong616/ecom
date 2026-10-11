"""命令行入口：``ecom start`` / ``ecom --version``。

启动时检测 tkinter；缺失则打印带发行版适配的安装指引。
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__


def _tk_install_hint():
    import platform

    system = platform.system()
    if system == "Windows":
        return "Windows 下请使用 python.org 官方安装器重装 Python（安装器自带 tkinter）。"
    if system == "Linux":
        return (
            "缺少 tkinter（系统级依赖，pip 无法安装）。请执行：\n"
            "  Ubuntu/Debian: sudo apt install python3-tk\n"
            "  Fedora:        sudo dnf install python3-tkinter\n"
            "  Arch:          sudo pacman -S tk\n"
            "  openSUSE:      sudo zypper install python3-tk"
        )
    if system == "Darwin":
        return "macOS 下请使用 python.org 安装器，或 brew install python-tk。"
    return "缺少 tkinter，请安装系统对应的 Tk 支持。"


def _check_tkinter():
    try:
        import tkinter  # noqa: F401
        return None
    except ImportError:
        return _tk_install_hint()


def _md_to_text(text):
    """把排障手册的 md 子集粗略转成终端可读文本（不去依赖 markdown 库）。"""
    out = []
    in_code = False
    for raw in text.split("\n"):
        line = raw.rstrip("\n")
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            out.append(line)
            continue
        if not s:
            out.append("")
            continue
        if s.startswith("#### "):
            out.append("    " + s[5:])
        elif s.startswith("### "):
            out.append("\n  " + s[4:])
        elif s.startswith("## "):
            out.append("\n" + s[3:])
        elif s.startswith("# "):
            out.append("\n" + s[2:] + "\n" + "=" * len(s[2:]))
        elif s.startswith("- "):
            out.append("  * " + s[2:])
        elif s.startswith(">"):
            out.append(s[2:])
        else:
            out.append(s.replace("**", "").replace("`", ""))
    return "\n".join(out)


def _help(lang="zh"):
    doc = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "docs",
                     "TROUBLESHOOT_%s.md" % ("zh" if lang == "zh" else "en")))
    if not os.path.exists(doc):
        print("[eCOM] 排障手册文件不存在：%s" % doc, file=sys.stderr)
        return 1
    try:
        with open(doc, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print("[eCOM] 读取排障手册失败：%s" % e, file=sys.stderr)
        return 1
    print(_md_to_text(content))
    print("\n（手册原文：%s）" % doc)
    return 0


def _start():
    hint = _check_tkinter()
    if hint:
        print("[eCOM] 无法启动图形界面：" + hint, file=sys.stderr)
        return 1
    from .app import run
    return run()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ecom",
        description="eCOM — 跨平台串口调试工具",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="start",
        choices=["start", "help"],
        help="start=启动 GUI；help=在终端显示 Linux 串口排障手册（默认 start）",
    )
    parser.add_argument(
        "--lang", "-l",
        default="zh",
        choices=["zh", "en"],
        help="帮助手册语言（默认 zh）",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="ecom " + __version__,
    )
    args = parser.parse_args(argv)

    if args.command == "help":
        return _help(args.lang)
    if args.command == "start":
        return _start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
