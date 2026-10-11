# eCOM

> 跨平台（Windows + Linux）轻量级串口调试工具 —— 集 **AT 命令调试、AT 命令集循环压测、文件发送、串口日志** 于一体。

---

## ✨ 特性

- **AT 命令调试**：ASCII / HEX / DEC / BIN 多种编码，send-on-enter 后缀，TX/RX 实时显示（蓝/绿）。
- **AT list 循环压测**：把一组 AT 命令组织成列表，按**次数 / 时长**循环执行；自动校验每条命令的**预期结果**（contains / regex / exact），命中自定义 check 规则判为异常；输出按轮分段的结构化日志与汇总统计。
- **文件发送**：分块写串口，带进度条与暂停/恢复。
- **串口日志**：AT 日志与 DOS 日志双通道落盘（与输出框逐字节一致）。
- **中英双语**：菜单实时切换。
- **配置持久化**：串口参数、显示选项、AT 命令组等存于 `~/.ecom/config.json`。
- **自定义 check 规则** + **AT list 导入/导出 CSV**。

---

## 🚀 快速开始

### 环境要求

| 依赖 | 说明 |
|---|---|
| Python | **≥ 3.8** |
| pyserial | `pip install pyserial`（或 `pip install .`） |
| tkinter | Windows 自带；**Linux 需系统包**（见下） |

Linux 下 tkinter 是系统级依赖，pip 无法安装：

```bash
# Ubuntu / Debian
sudo apt install python3-tk
# Fedora
sudo dnf install python3-tkinter
# Arch
sudo pacman -S tk
# openSUSE
sudo zypper install python3-tk
```

### 运行

```bash
python main.py          # 开发运行
# 或安装后：
pip install .
ecom start              # 启动图形界面
ecom --version          # 查看版本
```

结束：关闭窗口（点 "x"）或在终端按 `Ctrl+C`。

---

## 📚 文档索引

| 文档 | 中文 | English |
|---|---|---|
| **项目介绍**（定位 / 架构 / 依赖 / 结构） | [项目介绍](docs/PROJECT_OVERVIEW_zh.md) | [Project Overview](docs/PROJECT_OVERVIEW_en.md) |
| **接口说明**（文件 / 方法 / 参数 / 调用关系） | [接口说明](docs/API_REFERENCE_zh.md) | [API Reference](docs/API_REFERENCE_en.md) |
| **使用说明书**（图文 / 操作步骤） | [使用说明书](docs/USER_GUIDE_zh.md) | [User Guide](docs/USER_GUIDE_en.md) |
| **已知限制与遗留项** | [已知限制](docs/KNOWN_ISSUES_zh.md) | [Known Issues](docs/KNOWN_ISSUES_en.md) |

> 完整接口与调用关系请看**接口说明**；界面截图见**使用说明书**的「截图需求清单」（本地运行后补图）。

---

## 🗂 项目结构（简）

```
eCOM/
├── main.py                 # GUI 入口
├── ecom/                   # 源码包
│   ├── app.py              # 主窗口 + run()
│   ├── cli.py              # 命令行入口
│   ├── at_panel.py         # AT 命令面板
│   ├── stress_panel.py     # 压力模式面板（压测状态机）
│   ├── stress_model.py     # 数据模型 / 匹配 / 统计 / 结束条件
│   ├── stress_io.py        # AT list CSV 模版/导入/导出
│   ├── file_panel.py       # 文件发送
│   ├── serial_core.py      # 串口封装（读线程/队列/计数）
│   ├── codec.py            # 编解码
│   ├── logger.py           # 日志落盘
│   ├── config.py           # 配置持久化
│   ├── i18n.py             # 中英翻译表
│   └── tooltip.py          # 悬浮提示
├── tests/                  # 单元/回归测试
├── docs/                   # 文档 + 界面示意
└── PROGRESS.md             # 开发/修复进度日志
```

---

## 🧪 测试

```bash
python -m unittest discover tests
```

---

## 📄 许可

以 **MIT License** 开源（见 `pyproject.toml` 的 `license` 字段）。
