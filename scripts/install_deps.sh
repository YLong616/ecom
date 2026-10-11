#!/usr/bin/env bash
# 一键安装 eCOM 在 Linux 下的系统级依赖（tkinter）。
set -e

if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3-tk
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3-tkinter
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm tk
elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y python3-tk
else
    echo "未识别发行版，请手动安装 tkinter 支持。"
    exit 1
fi

echo "tkinter 依赖安装完成。"
