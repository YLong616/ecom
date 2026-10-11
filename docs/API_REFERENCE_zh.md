# eCOM 接口说明（API Reference）

> 面向开发者/二次开发。覆盖 `ecom` 包全部模块：文件职责、公开类与方法、参数、返回值、以及调用者/被调用者关系。
> 所有签名基于源码实际提取，行号为当前版本。

---

## 0. 约定

- **命名前缀**：`_` 开头＝模块内部私有，仅在文件内使用；无 `_` 前缀＝对外可调用入口。
- **调用方向**：GUI 层（app / at_panel / stress_panel / file_panel）→ 核心层（serial_core / stress_model / stress_io / codec / logger / config / i18n / tooltip）。
- **线程模型**：除 `serial_core` 的后台读线程外，其余均运行在 Tkinter 主线程；跨线程仅通过 `queue.Queue` 传递。
- **行号**：以当前源码为准，仅供定位，不作为稳定 API 契约。

---

## 1. 模块依赖与调用关系总览

```
                    ┌─────────────────────────────┐
                    │        app.py (EcomApp)      │
                    │  主窗口 / 模式切换 / 显示/日志  │
                    └──────┬──────┬──────┬────────┘
                           │      │      │
          ┌────────────────┘      │      └────────────────┐
          ▼                       ▼                       ▼
 ┌──────────────┐        ┌───────────────┐        ┌──────────────┐
 │  at_panel.py │        │ stress_panel  │        │ file_panel   │
 │  AT命令面板   │        │  压力模式面板  │        │  文件发送     │
 └──────┬───────┘        └──────┬────────┘        └──────┬───────┘
        │                       │                         │
        └──────────┬────────────┴──────────┬──────────────┘
                   ▼                       ▼
        ┌────────────────────┐    ┌───────────────────┐
        │   serial_core.py   │    │  stress_model.py  │
        │    串口读线程/队列   │    │  模型/匹配/统计    │
        └───────┬────────────┘    └─────────┬─────────┘
                │                            │
   ┌────────────┼─────────────┐       ┌──────▼──────┐
   ▼            ▼             ▼       │ stress_io   │
┌──────┐  ┌─────────┐  ┌──────────┐  │  CSV 导入导出│
│codec │  │ logger  │  │  config  │  └──────┬──────┘
│ 编码 │  │  日志    │  │  持久化   │         │
└──────┘  └─────────┘  └──────────┘         │
           i18n.py（翻译表）─────────────┐   │
           tooltip.py（悬浮提示）──────────┐ │
┌─────────────┐  cli.py（命令行入口）      └─┴─ app.run()
│  __init__.py │  __version__ = "0.1.0"
└─────────────┘
```

**直接依赖（import）关系**：

| 模块 | import 了谁 |
|---|---|
| app | codec, i18n, at_panel, file_panel, stress_panel, config, logger, serial_core, tooltip, tkinter, datetime, time |
| at_panel | codec, pathlib, tkinter, json, math |
| stress_panel | codec, i18n, stress_io, stress_model, logger, serial_core, tooltip, tkinter, datetime, math, time |
| stress_model | dataclasses, datetime, re |
| stress_io | csv, io, os |
| file_panel | tkinter, tooltip, os, queue, threading |
| serial_core | serial, serial.tools.list_ports, queue, threading, time |
| codec | （无，纯函数模块） |
| logger | datetime, os |
| config | json, os, pathlib |
| i18n | （无） |
| tooltip | tkinter |
| cli | argparse, sys, platform, app.run, __version__ |

---

## 2. 各模块 API 详情

### 2.1 `serial_core.py` — 串口核心

职责：打开/关闭串口、后台读线程、字节计数、端口枚举。**对外只暴露队列与计数，不进 Tk。**

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `class SerialCore` | — | — | 线程安全串口核心 |
| `__init__(self)` | — | — | 初始化 `_ser=None`、`_running=False`、读取队列、`rx_count/tx_count=0` |
| `is_open` (property) | — | bool | 端口是否已打开 |
| `open(self, port, baudrate=115200, bytesize=8, parity="N", stopbits=1, rtscts=False, xonxoff=False)` | port:串口名/URL（支持 `loop://`）；其余=串口参数 | None | 打开并启动读线程；已开则先 close；用 `serial_for_url` 兼容真实/虚拟端口 |
| `_read_loop(self)` | — | None | 读线程：轮询 `in_waiting` 读数据，put `(RX_DATA, bytes)`；异常 put `(RX_ERROR, str)`；意外退出补 `(RX_CLOSED, None)` |
| `write(self, data: bytes) -> int` | data:待发 bytes | 写入字节数 | 未打开抛 `RuntimeError("串口未打开")`；累加 `tx_count` |
| `set_dtr(self, low=True)` | low:True=拉低 | None | 勾选态->拉低 DTR；异常静默 |
| `set_rts(self, low=True)` | low:True=拉低 | None | 同上，RTS |
| `close(self)` | — | None | 停止读线程（join≤1s）并关闭串口 |
| `drain(self)` | — | `list[tuple]` | 取空队列所有事件，供 GUI `after` 调用 |
| `reset_counters(self)` | — | None | 清零 rx/tx 计数 |
| `list_ports()` (staticmethod) | — | `list[(device, display)]` | 枚举可用串口；`display` 含设备全名 |

**被调用者**：`app._toggle_port`、`stress_panel._toggle_port` 调 `open/close/drain/set_dtr/set_rts/reset_counters`；`app.send_bytes`、`stress_panel._send_current` 调 `write`。
**调用者**：`app._refresh_ports`、`stress_panel._refresh_ports` 调 `list_ports`。

---

### 2.2 `codec.py` — 编解码

纯函数，无状态。发前编码 + 收后显示。

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `_parse_hex(text)` | text:hex 字符串 | bytes | 忽略空格/换行/逗号/`0x`；长度非偶抛 `ValueError` |
| `encode(text, data_type="ASCII", suffix="None")` | text:原始输入; data_type:ASCII/HEX/DEC/BIN; suffix:None/CR/LF/CR-LF/SPACE/STX-ETX/NULL | bytes | 按类型+后缀构造待发数据；未知类型抛 `ValueError`；STX-ETX 会包 `\x02...\x03` |
| `decode_display(data, display_hex=False)` | data:接收 bytes; display_hex:是否按 hex 展开 | str | 显示字符串；`errors="replace"` 容错 |
| `escape_control(text, show_crlf=True)` | text; show_crlf | str | 把 `\r\n`→`\\r\\n` 等可见化，用于显示选项 |

**被调用者**：`app.send_text/send_bytes`、`at_panel._encode_row`、`stress_panel._row_bytes` 调 `encode`；`app._render_frame`、`stress_panel._render_line` 调 `decode_display`/`escape_control`。

---

### 2.3 `logger.py` — 日志落盘

把收发记录写入文本文件。格式与输出框**逐字节一致**：`[时间戳]  TX/RX  正文`。

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `class Logger` | — | — | 单文件日志器 |
| `__init__(self)` | — | — | `_f=None, _path=None, entries=0` |
| `active` (property) | — | bool | 是否处于记录中 |
| `path` (property) | — | str | 当前日志文件路径 |
| `start(self, path) -> bool` | path:日志文件路径 | 成功与否 | 先 stop；自动建目录；追加写；失败返回 False |
| `stop(self)` | — | None | flush + close |
| `log(self, line)` | line:整行（含时间戳前缀） | None | 写 `${line}\n`，active 才写；累加 `entries` |

**被调用者**：`app._log_start/_log_stop/_append_line`、`stress_panel._start_logs/_stop_logs/_render_line/_log_round_marker` 调 `start/stop/log`。

---

### 2.4 `config.py` — 配置持久化

JSON 配置存于 `~/.ecom/config.json`。

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `_deep_merge(base, overlay)` | 两个 dict | dict | 递归合并（含嵌套 dict） |
| `class Config` | — | — | 配置读写 |
| `__init__(self, path=None)` | path:配置路径，默认 `~/.ecom/config.json` | — | 深拷贝默认配置后 `load()` |
| `load(self)` | — | None | 读文件→`_deep_merge`；兼容旧 `"CRLF"→"CR-LF"` |
| `save(self)` | — | None | 写 JSON（`ensure_ascii=False, indent=2`） |
| `get(self, section, key=None, default=None)` | section; key; default | 任意 | 取配置；key=None 返回整个 section |
| `set(self, section, key, value)` | 同上 | None | 写入（不清空其它 key） |
| `get_at_group(self, name, default=None)` | name:AT组名 | 命令列表 | 读 AT 命令组 |
| `set_at_group(self, name, commands)` | name; commands | None | 写 AT 命令组 |
| `remove_at_group(self, name)` | name | None | 删除 AT 命令组 |

**被调用者**：`app._save_config/_on_close`、`at_panel._load_config/_save_config/_refresh_configs`、`stress_panel` 的配置项读写调用 `get/set`。

---

### 2.5 `i18n.py` — 中英翻译

只有两个对外函数。

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `get(lang, key, **fmt)` | lang:zh/en; key:翻译键; fmt:格式化参数 | str | 取翻译；缺 key 返回 key 原文；含 `{e}` 占位时用 fmt 格式化 |
| `lang_label(lang)` | lang | str | 返回语言本名（"中文"/"English"），不随当前语言翻译 |

**调用者**：几乎所有面板的 `_t()` 都调 `get`（`app._t`、`stress_panel._t` 等）。内部 `I18N = {"zh": {...}, "en": {...}}` 为两级字典：一级=语言，二级=键。

---

### 2.6 `tooltip.py` — 悬浮提示

鼠标悬停显示完整文本，用于被截断的路径控件。

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `class Tooltip` | — | — | 悬浮小窗 |
| `__init__(self, widget, text="")` | widget:绑定控件; text:字符串或可调用对象 | — | 绑定 Enter/Leave/Motion；`text` 可传 `lambda:` 返回动态文本 |
| `_schedule(self, _event=None)` | 事件 | None | 悬停 `_DELAY_MS`(350ms) 后显示 |
| `_show(self)` | — | None | 创建无边框置顶 Toplevel，`wraplength=560` 自动换行，靠屏幕边缘自动上翻/左移 |
| `_hide(self, _event=None)` | event | None | 取消调度并销毁小窗 |

**调用者**：`app`、`stress_panel`、`file_panel` 对路径类 Entry/Button 创建 `Tooltip`。

---

### 2.7 `stress_model.py` — 数据模型 / 匹配 / 统计 / 结束条件

纯逻辑模块（无 Tk），是压测的算法核心。

**常量**：`MATCH_CONTAINS`、`MATCH_EXACT`、`MATCH_REGEX`、`MATCH_MODES`；`TARGET_AT/TARGET_DOS/TARGET_BOTH`；`BUILTIN_RULES`（内置示例规则）。

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `class StressRow` (dataclass) | 字段见下方 | — | AT list 单行模型 |
| `__post_init__(self)` | — | None | 归一化 `match_mode`/`send_type` |
| `effective_type` (property) | — | str | HEX 勾选则强制 `"HEX"`，否则 `send_type` |
| `effective_suffix` (property) | — | str | 勾选 Enter 则 `"CR-LF"`，否则 `send_suffix` |
| `has_expected` (property) | — | bool | 预期非空 |
| `to_dict(self)` | — | dict | 序列化 → 配置/导出 |
| `from_dict(d)` (staticmethod) | d:dict | StressRow | 反序列化（容错） |
| `class CheckRule` (dataclass) | name/keyword/record_to/as_exception/enabled | — | 自定义 check 规则 |
| `parse_expected(expected)` | expected:字符串 | `list[str]` | 按换行/竖线拆成多个预期 |
| `match_expected(response_text, expected, mode)` | 响应/预期/模式 | bool | 多预期任一命中即过；**空预期→True（不校验）**；regex 非法退化为 contains |
| `run_check_rules(response_text, rules)` | 响应/规则列表 | `list[(rule, text)]` | 命中启用规则的记录 |
| `class RunStats` (dataclass) | sent_lines/errors/current_line/total_rounds/start_time/end_time | — | 统计对象 |
| `format_duration(seconds)` | 秒 | str | 如 `"0.0H"` |
| `format_window(start, end)` | 两个 datetime | str | `start~end` 含微秒 |
| `compute_end_condition(current_rounds, mode, target_count, elapsed_seconds, target_seconds)` | 当前轮数/结束模式/目标次数/已耗时/目标秒 | bool | time 模式按秒；否则按轮数 |

**StressRow 字段**：`txt`(str="")、`send_type`(str="ASCII")、`send_suffix`(str="CR-LF")、`hex`(bool=False)、`enter`(bool=True)、`interval_ms`(int=0，0=用全局行间隔)、`expected`(str="OK"，默认预期)、`match_mode`(str=contains)、`enabled`(bool=True)。

**被调用者**：`stress_panel`、`stress_io` 大量使用；`test_stress.py` 直接单测。

---

### 2.8 `stress_io.py` — AT list CSV 模版 / 导入 / 导出

跨平台：写 `utf-8-sig`（带 BOM），读兼容带/不带 BOM。

| 签名 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `HEADERS` | — | list | 列头（英文码值，稳定）：index/enabled/at/send_type/send_suffix/hex/enter/interval_ms/expected/match_mode |
| `export_template(path)` | path | bool | 导出带示例行的模版 |
| `export_data(path, rows)` | path; rows | bool | 导出当前全量 AT list |
| `import_data(path)` | path | `list[dict]` | 从 CSV 导入（可为空列表） |
| `_write_csv`/`_read_csv`/`_row_to_list`/`_row_from_list` | 私有 | — | 具体读写/行解析 |

**被调用者**：`stress_panel._export_template/_export_data/_import_data`。

---

### 2.9 `app.py` — 主窗口（`EcomApp`）

职责：主窗口、模式切换（AT / 压力 / 文件）、串口开合、收发显示、状态栏、菜单、配置保存、日志开关、语言切换、字体缩放。

| 签名 | 说明 |
|---|---|
| `__init__(self, root, language="zh")` | 构建全部界面与变量 |
| `_t(self, key, **fmt)` | 翻译（i18n.get 封装） |
| `_register(self, key, widget)` | 注册控件以便语言切换时刷新文字 |
| `_setup_style(self)` | ttk 主题（`theme_use("clam")`）+ 全局样式 |
| `_build_vars(self)` | 创建串口/显示/发送等变量 |
| `_switch_mode(self, mode)` | 切换 AT / 压力 / 文件面板 |
| `_build_serial_card/_build_body/_build_monitor/_build_statusbar` | 左串口卡/主体/收发区/状态栏 |
| `send_text(self, text)` / `send_bytes(self, raw)` | 发送入口（编码/写串口） |
| `_poll_rx(self)` / `_flush_rx(self)` / `_append_line(self, direction, raw)` | 接收轮询/刷新/渲染行 |
| `_render_frame(self, direction, raw)` | 按帧渲染（协议帧分帧展示） |
| `_open_log/_log_start/_log_stop` | 日志开关 |
| `_save_config(self)` / `_on_close(self)` | 保存/退出 |
| `_set_language(self, code)` / `_apply_language(self)` | 中英切换 |
| `_set_dot/_set_status_error/_update_status/_flash_status` | 状态指示 |
| `_update_counters/_clear_counters` | 收发计数 |
| `_choose_log(self)` | 选日志文件 |

**对外入口**：`run()`（模块级，创建 Tk root 并运行 `mainloop`）。`cli._start()` 调用 `app.run()`。

---

### 2.10 `at_panel.py` — AT 命令面板

职责：可编辑的 AT 列表（分页/全选/编码/后缀/HEX/Enter）、保存/加载命令组、单行发送、循环发送（次数+间隔）。

| 签名 | 说明 |
|---|---|
| `__init__(self, master, app)` | 构建面板 |
| `_send_row(self, idx)` | 发送指定行 |
| `_encode_row(self, v)` | 按行编码为 bytes |
| `_selected_rows(self)` | 取勾选行 |
| `_run_loop(self)` | 启动循环发送 |
| `_loop_step(self)` | 循环步进（按间隔发送下一行） |
| `_stop_loop(self)` | 停止循环 |
| `_load_config(self)` / `_save_config(self)` | 加载/保存命令组 |
| `_read_config(self, name)` / `_write_config(self, name, commands)` | 读/写命名命令组 |
| `_refresh_configs(self, select=None, keep=True)` | 刷新命令组下拉 |
| `project_root()` / `configs_dir()`（模块级） | 项目根/配置目录路径 |

**被调用者**：`app`（面板作为子控件）；其运行串口写经 `app.send_bytes` 或 `app.core`。

---

### 2.11 `stress_panel.py` — 压力模式面板（压测状态机核心）

职责：压测配置（次数/时长、行间隔、响应超时、AT/DOS Log）、AT list 循环校验、自定义 check 规则、运行统计与日志标注。

**压测状态机**（见 §3）：`_start_run` → `_send_current`(send) → `_wait_tick`(wait) → `_finish_response` → `_advance`(interval→next)。

关键方法（节选，完整见源码）：

| 签名 | 说明 |
|---|---|
| `__init__(self, master, app)` | 构建所有子区 |
| `_collect_rows(self)` | 勾选非空行 → `_rows_run`；**空预期行自动补 `"OK"`** |
| `_start_run(self)` | 初始化运行态、置 run_btn disabled、启动首轮发送 |
| `_start_logs(self)` / `_stop_logs(self)` | 打开/关闭 AT/DOS 日志 |
| `_header_line(self)` | 生成 `=== 名称 | 次数 | 行间隔 | 响应超时 ===` |
| `_row_bytes(self, row)` | 按行编码（codec.encode） |
| `_send_current(self)` | 发送当前行；**每轮首行(row_idx==0)打印 `Runtimes N` 分隔标记** |
| `_schedule_wait(self, delay)` | 调度响应收集 |
| `_wait_tick(self)` | 依据静默/超时判定收流，调 `_finish_response` |
| `_finish_response(self)` | 匹配预期/规则，记异常；`_row_idx+=1` 后 `_advance` |
| `_advance(self)` | 轮数/结束判定；**行间隔取"刚执行完的那一行"的 `interval_ms`（>0 覆盖全局，0 回落全局）**；调度下一行 |
| `_stop_run(self, finished=False)` | 停止、写汇总、恢复按钮 |
| `_append_summary(self)` | 输出 `== 汇总 ==`（名称/时长/运行时间/总次数/已发送/异常） |
| `_update_stats(self)` / `_tick_stats(self)` | 统计刷新 |
| `_log_round_marker(self, n)` | 写 `== Runtimes N ==` 到输出框+AT Log |
| `_edit_expected(self, gidx)` / `_sync_expected(self, gidx)` | 预期结果编辑 |
| `_add_rule(self)` / `_del_rule(self, idx)` / `_collect_rules_ui(self)` | check 规则管理 |
| `_export_template/_export_data/_import_data` | CSV 模版/导出/导入 |
| `_toggle_hex_all(self)` | HEX 顶格复选框：把当前页所有行的 `hex` 设为同值（`hex_all_var`） |
| `_toggle_enter_all(self)` | Enter 顶格复选框：把当前页所有行的 `enter` 设为同值（`enter_all_var`） |
| `_apply_type_all(self, _evt=None)` | 类型批量下拉：把当前页所有行的 `type` 设为选中值（空则忽略，`type_all_var`） |
| `_apply_suffix_all(self, _evt=None)` | 后缀批量下拉：把当前页所有行的 `suffix` 设为选中值（空则忽略，`suffix_all_var`） |
| `_clear_at_list(self)` | 一键清空当前 AT list 全部命令（仅清内存行、保留行结构，不涉模板/待导入文件；确认后 `_rows` 重建为默认空白行并回第 1 页） |
| `_choose_log(self, tag)` | 选 AT/DOS 日志文件 |

**被调用者**：`app` 创建 `StressPanel` 并作为右列；内部调用 `serial_core`、`stress_model`、`stress_io`、`codec`、`Logger`、`Tooltip`。

---

### 2.12 `file_panel.py` — 文件发送面板

职责：选择文件、分块发送、进度/暂停/取消、后台线程 + 队列反馈进度。

| 签名 | 说明 |
|---|---|
| `__init__(self, master, app)` | 构建面板 |
| `_choose_file(self)` | 选择文件 |
| `_send_file(self)` | 启动发送（起后台线程） |
| `_send_worker(self, path)` | 后台分块发送线程 |
| `_start_poll(self)` / `_poll_progress(self)` | 进度轮询 |
| `_toggle_pause(self)` / `_update_pause_btn(self)` | 暂停/恢复 |
| `_finish_send(self)` / `_stop_old_send(self)` | 结束/取消旧发送 |
| `_set_progress(self, frac)` | 更新进度条 |

**被调用者**：`app`；后台线程经 `queue` 与主线程通信，主线程用 `root.after` 取进度。

---

### 2.13 `cli.py` — 命令行入口

| 签名 | 说明 |
|---|---|
| `main(argv=None)` | argparse 解析 `command(start)` 与 `--version`；其返回值作为进程退出码 |
| `_start()` | 检测 tkinter；缺失打印安装指引并返回 1；否则 `app.run()` |
| `_check_tkinter()` | 返回 None 或安装提示 |
| `_tk_install_hint()` | 按平台返回安装指引 |

---

## 3. 压测运行状态机

```
_start_run
   │  init stats/rounds, run_btn=disabled, _start_logs, header
   ▼
_send_current ───────────────┐  (row_idx==0 → _log_round_marker(N))
   │  write(row) → RX 显示    │
   ▼                          │
_wait_tick ──────────────────┤  (静默/超时判定收流)
   ▼                          │
_finish_response ─────────────┤  (匹配预期/规则, 记异常)
   │  _row_idx+=1              │
   ▼                          │
_advance ─────────────────────┘
   │  rows 跑完? ──会──> _rounds_done+=1, _row_idx=0
   │  结束条件? ──会──> _stop_run(finished=True)
   │  否则: interval = 上一行.interval_ms(>0)? * : 全局间隔
   ▼
_schedule_follow(interval, _send_current)  →  回到 _send_current
```

**行间隔优先级**：AT list 中「即将作为等待依据的那一行（刚执行完）」若 `interval_ms>0` 用其值；否则回落「压测配置的行间隔(ms)」。

**预期结果规则**：某行预期为空时 `_collect_rows` 自动补 `"OK"`，故 `has_expected=True`，参与对比；`match_expected` 命中即通过，不命中计异常。

---

## 4. 关键调用链（示例）

- **发送 AT**：`app.send_text(text)` → `codec.encode(...)` → `app.core.write(raw)` → `serial_core.write`。
- **接收显示**：`serial_core` 读线程 put 队列 → `app._poll_rx`（`after`）→ `drain()` → `_flush_rx` → `_render_frame` → `_append_line`（输出框 + `Logger.log`）。
- **压测一轮**：`stress_panel._start_run` → `_send_current` → `core.write` + `_render_line`；收流经 `_wait_tick/_finish_response`；`_advance` 调度下一行。
- **语言切换**：`app._set_language` → `_apply_language` → 对注册控件 `_register` 逐个 `_t` 刷新文字。

---

## 5. ⚠️ 开发注意：E-SafeNet 加密

- `ecom/*.py` 在用户环境被安全软件（E-SafeNet）加密，**用文本工具/`read_file` 读到的可能是密文**（如下方曾出现"读到 237 行密文而磁盘真身 746 行"）。
- **一切源码改动**：用 Python 脚本（`open(..., encoding='utf-8')` 读明文 → 字符串替换 → 重新写回）做**字节级替换**，随后 `python -m compileall -q ecom` 校验语法，并跑 `unittest discover tests` 回归。
- 不要用文本编辑器直接保存加密文件；备份文件 `*.bak_*` 仅作参考，勿改。
