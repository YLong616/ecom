"""开发入口：``python main.py`` 直接弹出 GUI。

与 ``ecom start`` 共用同一套代码，并在缺 tkinter 时给出友好提示。
"""

import os
import sys

# 兼容 sys.path 不含脚本目录的环境（如嵌入式 Python 的 ._pth 配置）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ecom.cli import _check_tkinter


def main():
    hint = _check_tkinter()
    if hint:
        print("[eCOM] 无法启动图形界面：" + hint, file=sys.stderr)
        return 1
    from ecom.app import run
    return run()


if __name__ == "__main__":
    sys.exit(main())
