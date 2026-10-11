# eCOM 项目介绍

> 跨平台（Windows + Linux）轻量级串口调试工具，集 AT 命令调试、AT 命令集循环压测、文件发送与串口日志于一体。

---

## 1. 项目定位

eCOM 是一个基于 **Python + Tkinter** 的桌面级串口调试工具，面向嵌入式/模组调试场景，主打"轻量、够用、可压测"。核心能力：

- **AT 命令调试**：手动发送任意 AT 命令，支持 ASCII / HEX / DEC / BIN 多种编码与 send-on-enter 后缀，实时收发显示与落盘日志。
- **AT 命令集循环压测**：把一组 AT 命令组织成列表，按"次数 / 时长"循环执行，自动校验每条命令的**预期结果**，并对命中自定义 check 规则的响应判为异常，输出结构化运行统计。
- **文件发送**：把本地文件按块发送到串口，带进度与暂停。
- **串口日志**：AT 日志与 DOS 日志双通道落盘。

界面采用中英双语，可实时切换；状态与样式统一由全局配置驱动。

---

## 2. 技术架构

```
+--------------------------------------------------------------+
| Tkinter GUI 主线程 (root.after 轮询)                          |
|  ┌────────────┐ ┌──────────────┐ ┌─────────────┐ ┌─────────┐ |
|  │  app.py    │ │  at_panel.py │ │stress_panel │ │file_panel│ |
|  │ (EcomApp)  │ │  AT命令面板  │ │  压力面板   │ │ 文件发送 │ |
|  └─────┬──────┘ └──────┬───────┘ └──────┬──────┘ └────┬────┘ |
|        └──────┬────────┴────────┬────────┘             │      |
+───────────────┼─────────────────┼──────────────────────┼──────+
                │                 │                      │
        ┌───────▼────────┐ ┌──────▼───────┐      ┌───────▼───────┐
        │  serial_core   │ │ stress_*     │      │    codec      │
        │  串口读线程     │ │ 模型/IO/校验 │      │  编码/解码    │
        │  (queue 队列)  │ └──────┬───────┘      └───────┬───────┘
        └───────┬────────┘        │                      │
                │          ┌──────▼───────┐      ┌───────▼───────┐
                │          │  stress_io   │      │    logger     │
                │          │  CSV 导入导出 │      │   日志落盘    │
                │          └──────┬───────┘      └───────┬───────┘
                └───────────────┬─┴──────────────────────┘
                          ┌─────▼──────┐
                          │   config   │  ~/.ecom/config.json
                          │  持久化配置 │
                          └────────────┘
```

设计要点：

- **串口读线程独立于 GUI 主线程**：`serial_core` 用后台线程读取，数据通过 `queue.Queue` 交给 GUI，GUI 用 `root.after` 周期调用 `drain()` 取数，避免跨线程直接操作 Tk 控件。
- **主循环驱动**：收发、压测状态机（`send → wait → interval → next`）、统计刷新都由主线程 `after` 定时驱动，单线程无锁。
- **加密文件注意**：`ecom/*.py` 源码在部分环境被安全软件（E-SafeNet）加密，普通文本工具读为密文；**一切源码改动需用 Python 脚本做字节级替换并配合 `py_compile` 校验**（详见接口文档）。

---

## 3. 环境与依赖

### 3.1 运行环境

| 项 | 要求 |
|---|---|
| Python | **≥ 3.8** |
| 操作系统 | Windows 10+ / Linux 主流发行版 |
| GUI 依赖 | **tkinter**（系统级，pip 无法安装） |
| 串口依赖 | **pyserial ≥ 3.5** |

### 3.2 依赖清单（`requirements.txt` / `pyproject.toml`）

```
pyserial>=3.5
```

> tkinter 是 Python 自带的标准库，但在部分 Linux 发行版不随 Python 安装，需通过系统包管理器单独安装（见 §3.3）。

### 3.3 tkinter 系统级安装（Linux）

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

Windows 下使用官方 python.org 安装器自带的 tkinter，无需额外处理。

---

## 4. 项目结构
```
eCOM/
├── main.py              使用    GUI 启动入口（python main.py）
├── run.bat              使用    Windows 一键启动脚本（python main.py）
├── requirements.txt     使用    Python 依赖清单（pyserial>=3.5）
├── pyproject.toml       使用    打包/元数据；[project.scripts] ecom = ecom.cli:main
├── README.md            使用    一页速览
├── PROGRESS.md          使用    开发/修复进度日志（维护文档）
├── UI_DESIGN.md         使用    UI 设计说明
├── docs/                使用    文档目录（本套中英双语文档）
│   ├── PROJECT_OVERVIEW_zh.md / _en.md   项目介绍
│   ├── API_REFERENCE_zh.md / _en.md      接口说明
│   ├── USER_GUIDE_zh.md / _en.md         使用说明书
│   ├── KNOWN_ISSUES_zh.md / _en.md       已知限制
│   ├── ui_mockup.html                    UI 原型（设计稿，非运行时依赖）
│   └── images/interface_mockup.png       界面原型图（设计稿，非运行时依赖）
├── configs/             使用    AT 命令组数据（at_panel 经 configs_dir()=项目根/configs 读取 *.json）
│   ├── config.json      使用    默认 AT 命令组（启动时加载）
│   └── config1.json     使用    备选/空示例命令组
├── scripts/             辅助
│   ├── install_deps.sh  使用    Linux 一键安装 python3-tk（部署辅助）
│   ├── shot_pw.bmp      未使用  调试截图（3.4MB，可清理）
│   └── stress_template_demo.xlsx  未使用/示例  压测导出模板示例（可选保留）
├── tests/               使用    单元/回归测试（6 个文件）
│   ├── test_fixes_verify.py      修复/回归验证
│   ├── test_gui_regression.py    GUI 布局回归（8 项防线）
│   ├── test_serial_core.py       串口核心单测
│   ├── test_stress.py            压测状态机/模型单测
│   ├── test_hotplug.py           串口热插拔检测
│   └── test_stress_features.py   压测新增特性（导出导入/全选/清空/批量下拉）
├── xbak/                未使用  旧版本源码备份（见 4.2）
└── ecom/                使用    核心源码包（见 4.3 / API_REFERENCE）
```

> `使用` = 被运行时或维护流程引用；`未使用` = 不参与运行、仅作备份/调试/示例/设计稿。凡标 `未使用` 的文件可在发布前清理（见 4.2 清单）。

### 4.1 各源码模块作用（`ecom/`）

| 模块 | 作用 | 被谁使用 |
|---|---|---|
| `__init__.py` | 包标识 + `__version__` | 引入即生效 |
| `app.py` | 主窗口 `EcomApp` + `run()` | `cli.py`、`main.py` |
| `cli.py` | 命令行入口 `main()`（`ecom start` / `--version`） | `main.py`、entrypoint |
| `at_panel.py` | AT 命令面板（命令组加载/分页/循环） | `app.py` |
| `stress_panel.py` | 压力模式面板 + 压测状态机 | `app.py` |
| `stress_model.py` | 数据模型/匹配/统计/结束条件 | `stress_panel.py` |
| `stress_io.py` | AT list CSV 模板/导入/导出 | `stress_panel.py` |
| `file_panel.py` | 文件发送面板 | `app.py` |
| `serial_core.py` | 串口封装（读线程/队列/计数/热插拔） | `app.py`、`stress_panel.py` |
| `codec.py` | 编解码（类型/后缀/显示转换） | `app.py`、`at_panel.py`、`stress_panel.py` |
| `logger.py` | 日志落盘 Logger | `app.py`、`stress_panel.py` |
| `config.py` | 配置持久化 `Config`（读写 `~/.ecom/config.json`） | `app.py` |
| `i18n.py` | 中英翻译表 + `get()` | `app.py`、`stress_panel.py` |
| `tooltip.py` | 悬浮提示 `Tooltip` | `app.py`、`file_panel.py`、`stress_panel.py` |

> API 依赖（AST 分析）：`ecom/` 内 14 个模块均有被引用，**无死代码/废弃模块**；仅 `__init__.py` 为包标记非 import 目标属正常。

### 4.2 未使用 / 建议清理文件清单

| 路径 | 类型 | 建议 |
|---|---|---|
| `ecom/stress_panel.py.bak_addwobble` | 源码备份 | 清理 |
| `ecom/stress_panel.py.bak_addwobble2` | 源码备份 | 清理 |
| `ecom/stress_panel.py.bak_repaint3` | 源码备份 | 清理 |
| `ecom/stress_panel.py.bak_ui3` | 源码备份 | 清理 |
| `ecom/stress_panel.py.bak_ui4` | 源码备份 | 清理 |
| `xbak/app.py` | 源码备份 | 清理 |
| `xbak/app_v5.py` | 源码备份 | 清理 |
| `xbak/app_v6.py` | 源码备份 | 清理 |
| `xbak/file_panel.py` | 源码备份 | 清理 |
| `xbak/file_panel_v6.py` | 源码备份 | 清理 |
| `xbak/i18n.py` | 源码备份 | 清理 |
| `xbak/color_20260826_193203/`（app/at_panel/file_panel/stress_panel/tooltip.py + restore.bat/py） | 配色回退备份 | 如需保留配色备份可留，否则清理 |
| `scripts/shot_pw.bmp` | 调试截图（3.4MB） | 清理 |
| `scripts/stress_template_demo.xlsx` | 导出模板示例 | 可选保留 |
| `docs/ui_mockup.html`、`docs/images/interface_mockup.png` | 设计稿 | 可作资料保留，非运行时依赖 |

### 4.3 运行期与配置数据

- `configs/*.json`：AT 命令组（`at_panel` 启动时从 `项目根/configs` 加载全部 `*.json`，`config.json` 为默认组）。这是**项目内共享**的命令组数据。
- `~/.ecom/config.json`：由 `ecom/config.py` 持久化，保存串口/面板等全局设置，**位于用户家目录、跨项目共享**，不在本仓库内。
- `scripts/stress_template_demo.xlsx`：用 `stress_io.export_template` 生成的示例模板，仅作演示。

---


## 5. 运行与安装

### 5.1 直接运行（开发）

```bash
python main.py
```

### 5.2 安装为命令

```bash
pip install .
```

安装后可执行：

```bash
ecom start        # 启动图形界面（等价于 python main.py）
ecom --version    # 查看版本
```

> `ecom` 命令由 `pyproject.toml` 的 `[project.scripts] ecom = "ecom.cli:main"` 注册；CLI 启动前会检测 tkinter，缺失时打印对应发行版的安装指引后退出。

### 5.3 结束

- 关闭窗口（点击 "x"），或
- 在终端按 `Ctrl+C`。

---

## 6. 许可

项目以 **MIT License** 开源（见 `pyproject.toml` 的 `license` 字段）。

---

## 7. 相关文档索引

| 文档 | 说明 |
|---|---|
| [API_REFERENCE_zh.md](API_REFERENCE_zh.md) | 文件、方法、接口、参数、调用者/被调用者 |
| [USER_GUIDE_zh.md](USER_GUIDE_zh.md) | 用户使用说明书（图文） |
| [KNOWN_ISSUES_zh.md](KNOWN_ISSUES_zh.md) | 已知限制与遗留项 |
| [README.md](../README.md) | 一页速览 |

---

*版本：0.1.0 · 文档语言：中文（英文版见 `PROJECT_OVERVIEW_en.md`）*
