# eCOM — 跨平台串口调试工具

> 本文件是项目进度的**唯一真相源**。
> 会话开始：先读本文件恢复上下文（重点看「下一步」「待办」「未决问题」）。
> 会话结束：把本轮进展**增量**写回，不覆盖历史，并在「变更日志」追加一条。

## 进度记忆规则（本项目约定）

1. 会话开始，用户提到「继续 eCOM」→ 先 `read_file` 本文件，再动手。
2. 会话结束或关键节点 → 增量更新：已完成移到「当前状态」勾选，新增写进「待办」，重要结论记「关键决策」，卡点记「未决问题」。
3. 关键决策**永远**落在「关键决策」章节，不能只留在聊天记录里。
4. 每次改动追加「变更日志」一条（带日期 + 一句话）。

## 项目目标

跨平台（Windows + Linux）轻量级串口调试 GUI 工具。
- 安装：`pip install ecom`
- 运行：`ecom start` 弹窗；Ctrl+C 或点窗口 "x" 结束
- 开发调试：`python main.py` 直接弹 GUI 预览

## 功能规格（9 项）

1. 输出窗口 + 输入窗口（GUI 图形窗口，非终端）
2. 串口配置：端口 / 波特率 / 数据位 / 停止位 / 校验位 / 流控
3. Log 保存：可开关 + 自定义保存路径与文件名
4. AT 快捷命令面板：命令组可保存 / 加载 / 一键清除
5. 文件加载发送：选本地文件，读取内容发送给模组
6. Send-on-Enter 后缀：None / CR / LF / CR-LF / Space / STX-ETX / Null
7. 发送数据类型：ASCII / HEX / Dec / Bin
8. 字节计数：发送 / 接收字节数，可清零
9. 显示选项：时间戳 / TX·RX 方向标志 / \r\n / 接收数据转 HEX 显示

## 技术栈（已锁定）

- Python 3.8+
- 串口：pyserial（用 `serial.serial_for_url`，兼容真实端口 + loop:// 自测）
- GUI 框架：**Tkinter**（标准库，零 pip 依赖；Linux 需系统包 python3-tk）
- 打包：pyproject.toml + setuptools，console_scripts: `ecom = ecom.cli:main`
- 运行时依赖目标：仅 pyserial + Tkinter；开发依赖 pytest / build / twine

## 目录结构

```
projects/eCOM/
├── PROGRESS.md
├── README.md
├── main.py               # 开发入口：python main.py 弹 GUI
├── pyproject.toml
├── requirements.txt
├── scripts/
│   └── install_deps.sh   # Linux 一键装 python3-tk（可选辅助）
├── ecom/
│   ├── __init__.py
│   ├── cli.py            # ecom start / --version；含 tkinter 检测
│   ├── app.py            # GUI 主窗口（菜单/配置卡/Notebook/状态栏）
│   ├── i18n.py           # 多语言资源：中文 / 英文 + get/lang_label
│   ├── serial_core.py    # 串口核心：收发线程 + 字节计数
│   ├── codec.py          # 编解码 + send-on-enter（M2）
│   ├── logger.py         # log 落盘（M4）
│   ├── config.py         # 配置持久化（M7，已提前落地）
│   ├── at_panel.py       # AT 命令面板（M5）
│   └── file_panel.py     # 文件发送面板（M6）
└── docs/
    └── ui_mockup.html    # UI 原型预览（方案A）
└── tests/
    └── test_serial_core.py
```

## 里程碑

- [x] M1 骨架 + 串口核心（开/关/收发线程）+ 最小 GUI（选端口、收发）
- [x] M2 四种编解码 + send-on-enter + 字节计数
- [x] M3 显示选项（时间/TX-RX/\r\n/接收 HEX）+ 输入输出窗口完善
- [x] M4 log 保存 + 自定义路径
- [x] M5 AT 命令面板（保存/加载/清除）
- [x] M6 文件加载发送
- [ ] M7 配置持久化 + 打包（pip install + ecom start）+ README
- [ ] M8 Win/Linux 双平台联调 + 上传 PyPI

## 当前状态

- [x] 项目初始化（目录 + PROGRESS.md + 记忆规则）
- [x] 功能规格确认
- [x] 技术选型确认（GUI 框架 = Tkinter）
- [x] M1 编码（骨架 + 串口核心 + 最小 GUI + 单元测试）
- [x] M1 增强：串口完整参数 + 菜单栏 + 中英语言切换
- [x] UI 美化（方案A：浅色界面 + 深色数据区，按 UI_DESIGN.md）
- [x] M2 编解码 + send-on-enter + 字节计数
- [x] M3 显示选项（时间戳/方向/\r\n/接收HEX）
- [x] M4 Log 落盘（文件菜单选择路径 + 开始/停止）
- [x] M5 AT 命令面板（命令组保存/加载/删除 + 快速发送）
- [x] M6 文件加载发送
- [x] UI 重排 v3（11 项：时间戳[date]格式/勾选✓/串口卡对称grid/端口全名/CR-LF/发送按钮置右/窗口加大/输出区白底/Log常驻整行/文件发送常驻整行/右栏仅留AT）
- [x] UI 走查修复 v4（8 项：窗口加高到1200x860/显示选项下移+类型后缀同区+DTR·RTS勾选/Log去外层线框/端口·停止位左侧间距收敛/4个参数下拉框缩短/命令组上移占右栏整列/头部菜单只留设置）
- [x] UI 走查修复 v5（11 项：右栏宽度按权重自适应40%/显示选项拆行/菜单字体放大/输入框矮+字体大/输出分帧聚合防断截/颜色统一黑/Ctrl+滚轮缩放/按钮竖排/Enter发送/默认值联动）
- [x] 剪贴板修复 v11（复制全部/选中改走「无 Tk 的独立子进程 + Win32 立即渲染」；只读框自接管 Ctrl+C/粘贴并 break，Tk 不再抢剪贴板；新增 ecom/clipboard.py + 6 条回归用例）
- [x] UI/交互修复 v12（4 项：复制不刷输入框 / 复制异步不卡主线程 / 顶部入口固定「串口模式切换」/ 预期结果对话框上窄示例+下宽输入）
- [x] v13 预期结果对话框「测试」区（带出该行 AT 命令可改 → 发送 → 显示返回 → 即时比对 → 绿/红渲染）
- [x] v14 宏定义（参数自定义）：`ecom/macro.py` 引擎 + `ecom/macro_panel.py` 窗口 + 顶部「宏定义」入口（在「帮助」左边）+ 四处发送前展开
- [x] v14.1 宏定义调整：表格铺满 / 三色按钮 / 引用语法改 `${name}` / 剪贴板子进程重试加固
- [x] v15 全局走查补强（测试区 6 项 + 宏面板 5 项 + i18n 全局审计测试）
- [x] v15.1 宏名解锁（数字/特殊字符/中文）+ 表头与数据行同网格对齐
- [x] v15.2 宏名禁止含空格（即时提示 + 保存拦截；i18n 审计加占位符一致性检查）
- [x] v15.3 预期对话框按钮双色（保存蓝/退出灰）+ 宏定义模糊搜索（不影响保存范围）
- [ ] v16 发布 PyPI：版本已升 0.2.0、手册已重写、干跑全通过、dist/ 已就绪 → **待用户用 token 上传**
- [x] v17 主窗口可缩小（minsize 560x420）+ 内容可滚动（Canvas+按需滚动条；默认尺寸观感不变）
- [x] v17.1 滚动条统一细/扁平（ecom/uikit.py：ttk 全局样式 + scrolledtext 经典条）
- [ ] M7 打包 + README（config 持久化已提前落地）

## 下一步

1. M7：补 pyproject.toml 打包配置 + README + 冒烟测试（pip install .）+ `ecom start` 验证。
2. M8：Win/Linux 双平台联调 + 上传 PyPI。
3. 用户本地跑 `python main.py` 走查 M2–M6 交互与 UI 观感，反馈后微调。
4. **用户验收剪贴板（本轮修复）**：彻底退出并重启 ecom → 输出框右键「复制全部」/选中后 Ctrl+C → 粘到记事本，应得到**完整**内容；**刻意在持续接收 Log（滚动刷屏）时复制**，也应为完整内容（这是旧实现必挂的场景）。若仍有问题，请告知：①「已复制 N 字符」提示是否出现 ②记事本里是完全空白还是仅一部分。
5. **教训（写进本项目规范）**：Tk `Text` 里要显示**字面量** `\r\n`，i18n 源必须写 `\\r\\n`；`\r` 会被 Text 当换行 → 文案被折行、窄框显示不全。**单测断言（height/内容）会通过而真实渲染是坏的**，这类"排版能否完整显示"必须用 `tools/shot_ui.py`（PrintWindow 抓窗口 → BMP）看一眼。文案宽度也要按窄条像素预算核对（1 单位 ≈ 1 个 ASCII 宽、CJK 记 2；9pt 等宽下窄条约可容 ~85 单位），超了就压文案或减字号。
6. 本轮新增可复用工具：`tools/g.py`（加密源码按正则查看/看行区间）、`tools/sync_sitepackages.py`、`tools/verify_installed*.py`、`tools/hw_clip_test.py`（COM105@921600 真机刷屏复制实测）、`tools/shot_ui.py` + `tools/win_grab.py`（窗口抓图）。

## 待办清单

（对齐里程碑，M2 起逐步填充）

## 关键决策

- 2026-09-29：**UI/交互 v12 的 4 条落地口径**：
  1. **复制提示**：成功一律静默（不写输入框）；「复制全部」保留一个确认弹框（用户此前要过"复制成功可确认"）；失败才写输入框。
  2. **复制的线程模型**：Windows 下由**常驻后台线程**（`_clip_worker` + `queue`）调进程外写入，主线程 put 完即返回；结果用 `root.after` 轮询的 `_drain_clip_results` 回主线程处理（**绝不在工作线程里碰 Tk**）。这样复制耗时与主线程解耦，右键菜单不再被长文本复制卡住。非 Windows / frozen 仍走主线程同步 Tk 回退。
  3. **顶部模式入口**固定文案「串口模式切换」（`mode_switch` 键 + `_register` 纳入语言刷新），切换模式只改 `_mode_var`，不再改按钮文字；下拉里的选项才表达"要切到哪个模式"。
  4. **预期结果对话框**：`上窄示例 + 下宽输入`，示例随匹配模式联动。**示例文案里的 `\r\n` 必须是字面量**（i18n 源里写 `\\r\\n`）——写成 `\r\n` 会变成真 CR/LF，插入 Tk `Text` 后被当成换行，示例被折行截断（本轮真出现过，见下方教训）。
- 2026-09-29：**剪贴板写入改为「进程外 + 立即渲染」（复制全部粘不出来问题的最终定案）**。用户反馈「复制粘贴还是不可取」，本轮先用 4 组独立进程实验定性，再改代码：
  - **实测根因（两条路都堵死）**：① 旧实现 `widget.clipboard_clear()/append()/update()` 是 **Tk 延迟渲染** —— 数据不进全局内存，等外部程序请求时才由主线程响应 `WM_RENDERFORMAT`；主线程忙于收 Log 时供给不上，Windows 丢弃该次请求。实测 40 万字符、主线程忙等 6s：外部 `OpenClipboard` 直接失败，忙完再读为 **0 字符**（记事本粘出来空白）。② 在**有 Tk 的进程里**直接 `SetClipboardData`（立即渲染）也不行：`CloseClipboard()` 之后我们写的内存块立刻被清零（同一句柄 len 180000 → 0），剪贴板被 Tk 未填充的数据顶掉；**无 Tk 的进程**做同样操作完全正常。
  - **定案方案**：新增 `ecom/clipboard.py`，`set_clipboard(text, widget)`：Windows 下把文本经 stdin 交给一个**不 import tkinter 的子进程**，用 Win32 立即渲染写入并在子进程内回读校验（`CREATE_NO_WINDOW` 避免黑框，20s 超时，失败回退）；其它平台回退 Tk（X11 剪贴板由持有者持续供给，短命子进程不适用）。实测：父进程（Tk GUI）存活且主线程忙等时写 40 万字符，外部进程完整读到 399996，**子进程退出后仍可读**。
  - **配套（关键，否则 Tk 会把数据抢回去）**：只读输出框/帮助查看器**自接管** `Ctrl+C` 与 `<<Copy>>`（执行复制并 `return "break"`）、`Ctrl+V`/`<<Paste>>`/`<<Cut>>` 一律 break；`app._clipboard_set()`（进程内 Win32 写）**删除**，避免有人再走回头路。
  - **证据链**：新增 `tests/test_clipboard.py`（6 例）全过；把 `set_clipboard` 换回旧实现后这 6 例中 2 例**必失败**（反向验证用例有效）；全量 `unittest discover tests` **93/93 通过**（基线 87）；安装版 site-packages 端到端验收（13.6 万字符 × 忙等 1.5s × 外部进程读）PASS。工具：`tools/sync_sitepackages.py`（源码↔运行版同步）、`tools/verify_installed.py`、`tools/verify_help_viewer.py`、`tools/verify_test_catches_bug.py`。
  - **注意**：Tk 的 `event_generate("<Control-c>")` **不会**派发物理按键绑定（实测 0 次命中），验证复制路径必须用虚拟事件 `event_generate("<<Copy>>")` 或真实按键注入 —— 这条坑让此前几轮排查得出过错误结论。
- 2026-08-24：**UI 走查修复 v5（11 项，响应「断截/布局/交互」反馈）**：
  1. 右栏命令组宽度过小 → `_build_body` 弃固定 `width=300`，改 `grid` 列权重 `columnconfigure`（左3右2），右栏占 **40%** 且随窗口拉伸自适应（实测 1200px 窗口：左 696 / 右 472）。
  2. 显示选项（时间戳/方向/\r\n/接收HEX）从与类型/后缀同行拆出，**单独换行**显示（第2行），并加 `流控引脚 DTR/RTS` 分组。
  3. 头部「设置」菜单字体放大：`menubar`/`settings_menu`/`lang_menu` 统一用 `font=self.ui_font`；`ui_font` 默认 9→10。
  4. 输入框：高度 `height=6`→`2`（只发一行 AT），`wrap="none"`，`mono_font` 默认 9→**12** 放大。
  5. **输出分帧防断截（核心）**：`_poll_rx` 不再逐段渲染，改 `_rx_buf` 累积 + 静默 `_rx_idle_ms=120ms` 超时后整体 `_flush_rx()` 渲染为一条完整 RX；`_append_line("TX")` 先 `_flush_rx()` 避免 TX 插到 RX 中间。实证：`RG/255C/GLACR…` 分片合成一条，响应不再被发回显打断。
  6. 输出数据颜色统一黑：`output.tag_configure("tx"/"rx", foreground="#1B2733")`，输出/输入区前景 `fg=#1B2733`。
  7. Ctrl+滚轮缩放：`_bind_events` 绑定 `<Control-MouseWheel>`/`<Control-Button-4/5>`，`_zoom_font`/`_apply_language_font` 同步输入输出框字号（上限28/下限8）。
  8. 「打开串口」按钮改竖排放「刷新」**下方**（`ops` 内 pack fill=x）；且左栏右侧空白舍弃，让给右布局。
  9. 输入框 Enter 发送：绑定 `<Return>`/`<KP_Enter>` → `_send()`（单行命令，无需回车换行）。
  10. 默认初始值联动：字体字号、输入框高度、右栏权重均为代码默认；已去掉右栏固定宽导致的不自适应。
  11. 全量回归：py_compile 通过 + 运行时 7 项（接收聚合/颜色/高度/缩放/Enter/loop回环TX/语言切换）+ 布局测量 + 截屏走查全过。
- 2026-08-24：**UI 走查修复 v4（8 项，响应「存疑/未修好」反馈）**：
  1. 窗口高度偏矮显示不全 → 初始 `1200x780` → `1200x860`，minsize `1020x680` → `1000x720`。
  2. 显示选项条从顶部移除，改放到**输入框下方、与类型/后缀同一条工具栏**；并新增 **DTR / RTS 复选**（`serial_core.set_dtr/set_rts`，勾选=拉低；在 `_toggle_port` 打开串口后应用，`_apply_dtr_rts` 回调即时生效）。
  3. Log 保存行的 `LabelFrame`(**线框**)改为普通 `Frame`，仅保留「Log Save」标签。
  4. 端口/停止位左侧间距过大 → `_field` 标签左 `padx=(12,4)` 收敛为 `(4,4)`，去掉标签列/控件列的 `uniform` 等宽拉伸。
  5. 波特率/数据位/校验位/流控输入框过长 → 去掉 `sticky="ew"` 拉伸 + 缩短 `width`（baud 7/databits 6/stopbits 6/parity 9/flow 9）。
  6. 命令组 UI 上移，整体改左右布局：左栏=串口配置卡 + 输入输出，右栏=AT 命令组（`AtPanel` 占满右侧整列，不再挤在窄侧栏）。
  7. 头部菜单删除「文件」，仅保留「设置」（语言 + 退出并入设置菜单）。
  8. 串口卡从 root 顶部移入左栏容器内部（`_build_serial_card(parent)` + `_populate_serial_card`），完成左右分栏。
- 2026-08-24：**UI 重排 v3（11 项细节打磨，响应走查反馈）**：
  1. 输出时间戳改 `[YYYY-MM-DD_HH:MM:SS:ms]`（带日期+方括号+毫秒），对齐 SSCOM 式干净格式。
  2. 勾选项用原生 `tk.Checkbutton`（`selected` 显示 ✓，替代 clam 主题默认 ✖）；`_apply_language` 与 file_panel 同步纳入该类型。
  3. 串口配置卡改 `grid` 两行对称布局（标签/控件列各自 `uniform` 等宽，上下对齐）。
  4. 端口下拉显示设备全名（`serial_core.list_ports()` 改返回 `(device, display)` 元组；combo 显示 display、打开时经 `_port_map` 反查 device）。
  5. 后缀标签 `CRLF` → `CR-LF`；`codec._SUFFIX_BYTES` 同步改键；旧配置 `.load()` 自动迁移。
  6. 「发送」按钮右移（最右），类型/后缀靠左。
  7. 窗口初始尺寸 1000x680 → 1200x780，minsize → 1020x680。
  8. 输出区背景黑 `#101A28` → 默认白 `#FFFFFF`。
  9. Log 保存配置改为**常驻整行**（AT 输入框下方，含路径框+选择+开始/停止+状态）。
  10. 文件发送配置改为**常驻整行**（输入框下方、Log 行**上方**，单行：路径+选择+大小+追加后缀+发送+清空）。
  11. 右栏仅保留 AT 快捷命令按钮网格（文件发送已移至左栏监控下方）。
- 2026-08-24：**GUI 框架选定 Tkinter**（轻量 + 跨平台 + 零 pip 依赖）。

- 2026-08-24：Linux 的 python3-tk 系统依赖**无法由 pip 携带**；采用「启动检测友好提示 + README 指引 + install_deps.sh 辅助脚本」方案。
- 2026-08-24：接收数据显示支持 ASCII + HEX 切换；log 收发都记（带时间戳 + TX/RX）；AT 命令组单独存 JSON，串口/显示选项另存全局配置。
- 2026-08-24：串口实例改用 `serial.serial_for_url`，对真实端口行为不变，同时支持 loop:// 虚拟端口做无硬件回环自测。
- 2026-08-24：串口读线程独立于 Tkinter 主线程，经 queue.Queue 传数据、GUI 用 root.after 轮询（drain），避免跨线程操作 Tk 控件；rx_count 仅读线程写、tx_count 仅主线程写，无并发写冲突。
- 2026-08-24：**开发机 Python 环境（最终敲定）**：使用标准完整版 `E:\software\python389\python.exe`（Python 3.8.9，带 tkinter 8.6 + pyserial 3.5，pip 20.2.3）。用户本地桌面 PATH `python` 已指向该环境，已验证 tkinter/pyserial 完整可用；项目所有的依赖安装、GUI 构建与单测均用此解释器。嵌入式精简版 `E:\software\python-3.8.10` 无 tkinter，仅作参考，不再使用。
- 2026-08-24：**UI 主题（方案A，浅色界面 + 深色数据区）**：按 UI_DESIGN.md 落地，用 ttk `clam` 基底 + 自定义样式（Color Token：主色 `#3B6FE0`、文本 `#1B2733`、终端底 `#101A28`）；数据区等宽字体 + TX/RX 着色 + 时间戳；Notebook 分页（监控 / AT 命令 / 文件发送）。
- 2026-08-24：**Tk 陷阱**：ttk.LabelFrame 默认样式名是 `TLabelframe`（小写 f），用 `Card.TLabelFrame`（大写）会报 `Layout … not found`；`scrolledtext` 不接受 `-underscore` 选项。均已规避。
- 2026-08-24：**Config API**：`.get(section)/get(section,key)` 两级访问，顶层标量（如 `language`）用 `get("language")`；`.set(section,key,value)` 只用于两级，顶层标量直接写 `config.data[...]`。务必用 `default=` 关键字，避免把默认值当 `key` 传。
- 2026-08-24：**面板与核心解耦**：at_panel / file_panel 经 `app._t/_register/send_text/send_bytes/config`（duck typing）交互，不 import app；核心收发方法暴露为公开 `send_text/send_bytes`；多面板同名文本用 `_text_widgets` **列表**注册，避免 dict key 互相覆盖。
- 2026-08-24：**UI 改版 v2（左右分栏，重排规整 + 侧边常驻AT栏）**：弃用 Notebook 分页，改「顶部配置卡 + 左=监控 / 右=常驻快捷AT命令+文件发送」左右分栏；右栏固定宽 300px；AT 命令改为**按钮网格**（单击即发送，右键弹「发送/删除」菜单），不再用 Listbox；监控区输入框固定 6 行高、输出区占主导（避免双 expand 平分不规整）。详见 UI_DESIGN.md v2。
- 2026-08-24：**E-SafeNet 加密文件处理（重要工程坑）**：`ecom/app.py` 被本机 DLP（透明加密 E-SafeNet）加密，`read_file`/`edit_file`/`write_file` 工具读写到密文、无法直接编辑；但 **`type` / `py`（白名单进程）可读明文**。因此对这类被加密文件**必须用 Python 脚本（`py -3.8 xxx.py`）做字节级替换**，且脚本内用 `\r\n` 做 CRLF 匹配；改完用 `py -m py_compile` 验证。

## 未决问题

- 2026-09-29：**宏定义（参数自定义）—— 已实现（v14），遗留三点待用户拍板**：
  1. **语法**：当前用 `{name}` + `{{`/`}}` 转义（按用户最初写法）。若他们的 AT 载荷里常出现**裸** `{x}`（无引号包裹），建议改 `${name}`（一行改动 + i18n 文案）。
  2. **可复现缺口（建议尽快补）**：压测「导出当前数据」**尚未带宏表** → 同一份导出文件在不同宏表下会跑出不同命令。建议导出时同时写出 `macros.json`（或写展开后的值），否则压测结论无法复算。
  3. **是否加「启用/停用」列**：宏多了以后想临时停用某个宏，现在只能删掉再补回来。

## （已归档）宏定义需求的原始分析

- 2026-09-29：**宏定义（参数自定义）功能 —— 用户提出，待拍板后再动工**。用户场景：`send_data = "1234567890"*150`（支持 Python 语法），命令里写 `AT+TCPSEND=1500,"{send_data}"`。
  可行性结论：**能做**，属"文本展开 + 受限表达式求值"，不动串口/协议层。待用户确认的三点：
  1. **宏语法**：推荐 `${name}`（`{name}` 与 AT 里常见的 JSON 载荷 `{...}` 冲突，需 `{{` 转义规则）；若坚持 `{name}` 需明确转义写法。
  2. **表达式能力边界**：推荐"AST 白名单求值"（只允许字面量、`+ - * // % **`、`join/split/str/int/len` 等少数函数，禁 import/属性访问/名字引用），并对**结果长度**设上限（如 1 MiB）+ 禁止超大幂；`random`/`time` 之类会使压测不可复现，默认禁。
  3. **落点与可复现**：宏表单独存 `configs/macros.json`（与命令组同目录，便于随项目走）；展开发生在**发送时**（UI 里保留符号形式），并在 AT list / 输入框显示**展开预览**；**压测「导出当前数据」必须同时写宏表或其展开值**，否则同一份导出文件在不同宏表下会跑出不同结果。
  计划：新增 `ecom/macro.py`（引擎+校验）、`ecom/macro_panel.py`（宏表管理对话框，设置菜单入口）、在 `at_panel`/`stress_panel._row_bytes`/`app.send_text` 三处发送前展开；`tests/test_macro.py`（含安全用例：无内置函数、无属性访问、结果长度上限、未知宏不发送）。工作量约 1 个工作日。


（无 —— 4 项选型已全部确认，见「关键决策」）

## 待用户确认（v14 之后）

1. 宏语法是否换成 `${name}`（避开 JSON 载荷里的裸花括号）。
2. 压测导出是否附带宏表（否则压测不可复算）—— 建议做。
3. 宏表是否加「启用/停用」列。

## 变更日志

- 2026-09-29：**v17.1 滚动条观感统一（用户要求：好看一些、细一些）**：新增 `ecom/uikit.py`：`slim_ttk()` 全局统一 ttk 滚动条样式（**宽 9px**、箭头 `arrowsize=11`、`relief=flat` + bevel 三色设成轨道色去掉立体边框、滑块 `#9AA4B1` / 轨道 `#ECEFF4`、hover/pressed 转 `#59657A`），**一处生效覆盖主窗口、压力面板、各对话框**；`slim_scrollbar()` 处理 `scrolledtext` 内置的**经典 tk.Scrollbar**（不走 ttk 样式）——已应用到主窗口输出框/输入框、压测输出框、排障手册查看器，保证全应用粗细一致。回归断言：`TScrollbar` 宽=9 且 `relief=flat`、主页面两条与输出/输入框的经典条宽=9 且 `bd=0`。
  验证：`unittest discover tests` **143 通过**；实拍 `ui_shot_win_small.bmp`（细/扁平、无立体边框）。

- 2026-09-29：**剪贴板用例在受限环境下改为「跳过」而非失败（环境问题，非代码问题）**：v17 收尾时全量测试出现 2 条剪贴板失败，排查结论＝**本机 shell 进程当前拿不到剪贴板**（`OpenClipboard` 连续 6 次失败、两次间隔重试仍失败；`GetOpenClipboardWindow` 返回空即**无人占用**、剪贴板序列号可正常读取）→ 属会话/沙箱限制（桌面会话被锁或远程会话），不是回归：该代码路径当天早些时候已用真实数据验证过（40 万字符外部读取、136000 字符忙等后读取）。
  处理：① `tests/test_clipboard.py` 与 `tests/test_ui_round2.py` 里**真正需要读写剪贴板**的 5 条用例改为「先用 `_clipboard_usable()` 探测，不可用则 `skipTest(剪贴板不可用…)`」，其余用例照跑；② `copy_fail` 文案补充原因（「剪贴板可能被其它程序占用，或被远程会话/系统策略限制」）。诊断脚本 `tools/who_holds_clipboard.py`（查占用者）保留备用。
  现状：`unittest discover tests` → **143 通过（5 跳过）**。**用户需在自己控制台里复跑 `tests/test_clipboard.py`**（或直接用 GUI 复制）来真正跑通那 5 条。

- 2026-09-29：**v17 主窗口可缩小 + 可滚动（用户反馈：缩到一定程度不能更小，且无法滚动查看被裁掉的内容）**：
  ① `root.minsize(960, 800)` → **`(560, 420)`**（旧下限比内容自然尺寸还大，是「缩不动」的根因；默认 `geometry("1080x900")` 不变）。
  ② 主内容从直接 pack 到 root 改为放进 **Canvas + 双向滚动条**：默认尺寸下内容仍铺满、**不出现滚动条**（观感与改动前一致），缩到比下限小才出现滚动条并可滚。尺寸策略：**宽下限 = `PAGE_MIN_W`(960，等于旧 minsize，正好在老限制处出现横向滚动条)**、**高下限 = 内容自然高**（窗口变矮时内容不被裁切，直接纵向滚动）。滚动条**按需显示/隐藏**。
  ③ 滚轮：主窗口内、指针不在自带滚动控件（Text/Canvas/Listbox/Treeview/Combobox/Spinbox/Scrollbar）上时翻主页；对话框内的滚轮不影响主页（`_page_wheel_target` 守卫）；**Shift+滚轮**横向滚动。
  ④ 测试：`test_gui_regression` 的 setUp 改为**全透明映射窗口**（`-alpha 0` + deiconify）——主内容进 Canvas 后，withdraw 下 Canvas 不给内容定尺寸、几何量不到（两个老用例因此失败）；并新增用例「窗口缩小后可滚动」（默认无滚动条 / 缩小出现双向滚动条 / 滚轮能翻页 / 不抢输出框滚轮 / minsize 已放开）。
  验证：`unittest discover tests` **143/143**；实拍 `ui_shot_win_default.bmp`（1080x900，无滚动条，content=1060x818）与 `ui_shot_win_small.bmp`（700x520，双向滚动条，content=960x772）。

- 2026-09-29：**v16 发布准备（Windows 直发 PyPI）**：① 版本升到 **0.2.0**（`pyproject.toml` 与 `ecom/__init__.py` 两处同步——`ecom --version` 读的是后者，PyPI 上 0.1.0 已存在故必须升）；② **发布手册 `docs/PUBLISH_WIN.md` 重写**（211 行）：修正包内手册名拼写（`TROUBLESHOT`→`TROUBLESHOOT`）、版本/测试数（66→142）、补 `clipboard/macro/macro_panel` 三个新模块、并新增「**版本号必须改两处**」「**产物明文自检**」「**sdist 解包跑测试**」「**wheel 用 --target 试装（别覆盖 site-packages 里日常在用的那份）**」四节。
  ③ **干跑验证（不含上传）全部通过**：`python -m build --no-isolation` 出 `ecom_serial_tool-0.2.0.{tar.gz,whl}`；`twine check` 两项 PASSED；wheel 内含 `ecom/docs/TROUBLESHOOT_{zh,en}.md`；**wheel 内源码是明文**（`findstr` 这类非白名单进程也能读到 `ecom/cli.py`、`ecom/macro.py` 条目，`ecom/macro.py` 里能读到中文注释）；sdist 解包后 `compileall` OK 且 **142/142 测试通过**；wheel `--target` 试装后 `import OK, 版本 0.2.0`。工具：`tools/dryrun_build.py`（清产物+build+twine check）、`tools/dryrun_verify.py`（解包测试+试装+明文检查）、`tools/check_pypi.py`（查 PyPI 已发布版本）。
  ④ **关键机制（已实测）**：白名单解释器 `E:\software\python389\python.exe` 对 E-SafeNet 密文源透明解密，**但必须加 `--no-isolation`**（否则 build 会新建隔离 venv，里面的 python.exe 不在白名单 → 把密文打进 wheel）；白名单进程**新写出的文件在磁盘上是明文**，所以 `dist/` 产物可直接上传/拷走。
  ⑤ 现状：`dist/` 里已是**验证过的 0.2.0 产物**，只差用 PyPI token 执行 `twine upload dist\*`（等用户上传）。

- 2026-09-29：**v15.3 预期结果对话框按钮配色 + 宏定义搜索（用户反馈）**：
  ① 「编辑预期结果」底部**保存=主色蓝（`ExpSave.TButton`）、退出=中性灰（`ExpExit.TButton`）** 两个不同底色（退出只是关窗、不丢已保存内容，故不用红，避免误读为危险操作）。
  ② 宏定义工具条在「一键删除」右侧加**搜索**：**模糊匹配**（宏名子序列，`dta`→`data`；也匹配宏值内容），带「×」清空；**只影响显示、不影响保存范围**（保存仍保存全部），搜索期间状态栏显示 `匹配 n/总数`，点「新增」自动清空搜索。
     实现：新增 `_fuzzy_match/_search_query/_filtered_indices/_visible_page/_on_search`，`_render/_pages/_toggle_all/_sync_all_var` 全部改走「过滤后的绝对行号」（表头/列宽逻辑不变）。
  **过程中修的三件事**：① i18n 审计的实参提取原来用正则 `[^)]*`，遇到 `n=len(x)` 这种嵌套括号会截断并**误报**「total 不是形参」→ 改为**括号配对扫描**（`_t_calls()`）；② 审计重构时**误删了 `DYNAMIC_KEYS`**（且我的输出过滤太窄没显示 ERROR，差点漏过）→ 已补回并纳入本轮新键；③ `shot_macro.py` 的搜索截图被追加到 `destroy` 之后 → TclError，已挪到销毁之前。
  验证：`unittest discover tests` **142/142**；实拍 `ui_shot_testarea_pass.bmp`（蓝/灰两按钮）与 `ui_shot_macros_search.bmp`（搜索 `dta` → 3/7 命中）。

- 2026-09-29：**v15.2 宏名禁止空格（用户拍板）**：`validate_key` 新增 `'space'` 错误码（含空格/制表符/全角空格即非法）；`}` 与换行仍判 `'bad'`，且**先判结构性非法再判空白**，避免换行被误报成空格；面板改为**输入时即时红字提示** + 保存拦截 + 聚焦选中出错行；新增文案 `macro_err_key_space`。
  **过程中被测试抓到的真 bug**：新文案里的字面 `${a b}`/`${ab}` 在带参渲染时被 `.format()` 当成占位符 → `KeyError` → `i18n.get` 兜底退回原文 → 界面显示**未替换的 `{name}`**（静默坏掉）；修法是字面花括号写 `${{a b}}`，并把提示文案缩短到窗口内可读。
  **i18n 审计再升级**：新增「**带参渲染的文案里每个 `{xxx}` 必须是该调用真的传进去的形参名**」（否则会被兜底吞掉、界面静默显示原文），扫描前先折叠 `{{ }}` 转义以免误报。
  验证：`unittest discover tests` **139/139**；实拍 `tools/ui_shot_macros.bmp`（含空格的行 + 红字提示 + 聚焦选中）。

- 2026-09-29：**v15.1 宏名解锁 + 表头对齐（用户反馈）**：
  ① **解开宏名输入限制**：去掉实时输入过滤（原来只允许标识符），宏名现在可用**数字开头/连字符/中文/点号**等任意字符；配套把引用语法从「标识符」放宽为 **`${...}` 取到 `}` 为止**（否则这类名字没法被引用），展开时名字**去首尾空白**；唯一保留的限制是**不能含 `}` 或换行**（会破坏引用定界），校验信息也改成解释这一点。
  ② **表头与数据行对齐**：根因是表头与行分别放在两个 Frame 里**各算各的列宽** → 合并到**同一个 grid**（列宽由同一套 `columnconfigure` 决定；`_render` 只重建数据行、表头保持不动），长度列右对齐、操作列正对按钮。
  ③ 过程中被测试/新审计抓到并修掉的两个真问题：**`macro_err_key_bad` 文案里的裸 `}` 会让 `.format()` 抛 `ValueError`**（保存失败时反而崩）→ 文案改「右花括号」措辞；**`i18n.get` 只捕获 IndexError/KeyError** → 补 `ValueError` 兜底，任何文案问题都不再把界面搞崩。i18n 审计相应升级：新增「**带参数渲染的键**必须是合法模板」（27 个）与「`get` 永不抛异常」。
  验证：`unittest discover tests` **137/137**；实拍 `tools/ui_shot_macros.bmp`（`1pkg`/`data-2`/`数据包` 可录入 + 表头对齐）。

- 2026-09-29：**v15 全局走查（预期结果测试区 + 宏定义）并逐项补强**。
  **预期结果「测试」区**：
  ① **真 bug**：匹配模式下拉的初值用的是模式码（`contains`）而不是本地化标签（`包含`）——界面显示成 `contains`，且**不动下拉直接保存会把该行的正则/全等静默降级成包含**；已改为用标签初始化 + 加回归用例（`dlg._ok()` 断言模式不变）。
  ② 静态提示写死「按 ASCII + CR-LF 发送」，与实际发送方式不符 → 改文案，并新增一行**动态提示**「发送方式：X + Y；串口：PORT/未打开」。
  ③ 发送方式不看行设置（HEX 行也按 ASCII 发）→ 改为跟随 `row.effective_type/effective_suffix`，与实际压测一致。
  ④ 结果框无滚动条、无法右键复制 → 加垂直滚动条 + 复用 app 的只读框右键菜单（复制/全选）。
  ⑤ 结论不显示匹配模式 → 结论带模式名；新增**「用返回填充预期」**按钮（全等模式尤其实用，只改对话框文本，保存才落盘）。
  ⑥ 串口错误/掉线要干等到超时 → 新增 `_mark_test_error`，掉线立即结束并给出原因。
  **宏定义面板**：① 宏名输入实时限制（`validatecommand`：字母/下划线开头 + 字母数字下划线）；② 保存校验加**大小写重名**（`Send_Data` vs `send_data`）；③ 保存失败时跳页并**聚焦/选中**出错那一行；④ 状态文字**按语义着色**（未保存=主色、已保存=绿、失败=红）；⑤ 编辑对话框加**展开预览（前 80 字符）**，长值一眼看清。
  **全局**：新增 `tests/test_i18n_keys.py` —— **i18n 全局审计**（代码里每个 `_t("…")` 键必须在 zh/en 都存在、两侧键集一致、占位符不得叫 `{key}`），正是为了防上轮「整段替换误删相邻键」那类事故（写完即发现并修正了自己扫描规则的一个误报）。
  **验证**：`unittest discover tests` **135/135**（新增 i18n 审计 4 例 + 宏 3 例 + 测试区 2 例）；实拍 `tools/ui_shot_testarea_pass.bmp` / `ui_shot_testarea_fail.bmp`（绿/红两态 + 动态提示 + 下拉本地化）。

- 2026-09-29：**v14.2 匹配示例去真实数据（用户指出泄密风险）**：示例里的 `+QSTAAPINFO`、`+QVERSION: FCMA62NAAR03A02M08`、`+QGETIP: "10.1.2.3"` 都是本机模组的**真实回包**，已全部换成虚构样例 `ABCD123456\r\nOK\r\n`（正则示例用 `ABC\d+`、`OK\r\n\r\n\+DATA: 1`）；措辞由「实际接收内容」改为「**假设实际接收内容**」（en: Assumed received text）。测试新增**防泄密断言**：三种示例不得含 `+QSTAAPINFO/+QVERSION/+QGETIP/FCMA/10.1.2.3/Quectel`，且首行必须以「假设…」措辞开头。另做了**交付物泄露扫描**：`ecom/*.py`、`ecom/docs/*.md`、`docs/*.md` 内已无上述真实数据（仅 `docs/PUBLISH_WIN.md` 出现本机路径里的 EdisonCode）。
- 2026-09-29：**事故与教训（v14.2 过程中）**：做区间替换时把 `stress_ex_*` 到 `stress_no_rows` 之间的内容整段换掉，而 **12 个 `stress_test_*` 键正好落在该区间内 → 被误删**（界面把原始 key 名当文案渲染出来，测试与实拍立刻暴露）。已补回（zh/en 各 12 键）。**教训：改 i18n 分块前先确认区间内没有其他键；改完必须跑全量而不是只看目标用例。**
- 2026-09-29：顺带修 `tests/test_clipboard._external_read` 在剪贴板为空时抛 `ValueError`（`.strip()` 后只剩一个 token）→ 改为返回 `(0, "")` 交给断言。

- 2026-09-29：**v14.1 宏定义四处调整（用户反馈）**：① 顶部入口移到「帮助」**左边**（顺序：设置 | 串口模式切换 | 宏定义 | 帮助）；② 宏窗口表格**铺满**窗口宽度（`table.columnconfigure(0, weight=1)`——原来错配在 column 2 上，所以只有 ~72% 宽）；③ `新增`/`保存`/`一键删除` 改**三色**（新增=主色蓝、保存=成功绿、一键删除=危险红；本地 MacroAdd/MacroSave/MacroDel.TButton 样式，不依赖压力面板才定义的 Run.TButton）；④ 引用语法 `{name}` → **`${name}`**（带 `$` 前缀；AT 里的 JSON 花括号回归**普通字符、无需转义**，写字面 `$` 用 `$$`，`${1bad}` 这类非法宏名原样保留）。
- 2026-09-29：**剪贴板子进程写入加固**：全量跑测试时偶发「子进程启动被拖慢」导致 `test_stress_output_uses_same_copy_path` 假失败（单独跑必过）→ `clipboard._set_windows` 改为 **8s × 最多 2 次重试**（生产上同样避免用户复制静默失败），测试等待放宽到 30s 并带诊断信息。

- 2026-09-29：**v14 宏定义（参数自定义）落地**。新增 `ecom/macro.py`（引擎）+ `ecom/macro_panel.py`（窗口），顶部「帮助」旁加「宏定义」入口，**独立 Toplevel 居中于主窗口**（不动主界面布局）。
  - **值的语义（按用户表格反推确认）**：默认 = **字面量 + `*N` 重复**（`12345*10`→50 字节、`12345-1`→7 字节、`1234567890*150`→1500 字节，与其示例表完全一致，**不是数值运算**）；`=` 开头才走受限表达式（`=str(1500)+',x'`）。长度列实时显示 UTF-8 字节数。
  - **窗口**：说明行 → `新增/保存/一键删除` + 状态 → 表格（**只有横线**，无竖线；列 = 多选 | 宏名称 key（可编辑）| 宏值 value（可编辑）| 长度 | 编辑 | 删除）→ 分页（10 行/页，含表头全选）→ 关闭。`编辑` 打开大编辑框（长 value 用）+ 实时长度；删除/一键删除**不做二次确认**（未保存即作废，删了不点保存无损失）。
  - **保存语义**：只有点「保存」写 `~/.ecom/config.json` 的 `macros`（不放 `configs/`：那里是命令组，会串进命令组下拉）；未保存关闭即作废；保存前校验（空名/非法名/重名/值求值失败都会拦下并跳到出错页）。
  - **安全**：自写 AST 求值器（**不用 eval**），禁 import / 属性访问 / 下标 / 变量引用 / 推导式；结果上限 1 MiB，`'x'*10**9`、`10**100000` 直接拒绝（重复先算长度再构造）。
  - **接线**：AT 输入 `app.send_text`、AT list `at_panel._encode_row`、压力行 `stress_panel._row_bytes`、压力「测试」命令 —— 四处发送前展开；未知宏/值有误**阻止发送**并提示；`{{`/`}}` 为字面花括号转义。文件发送不展开。
  - **验证**：`unittest discover tests` **126/126**（新增 `tests/test_macro.py` 24 例：用户表格三条数值、TCP 1500 字节、表达式与安全拒绝、超限拒绝、展开/转义/未知宏、保存往返、四条发送链路、面板新增/删除/一键删除/分页/长度列/保存校验）；实拍 `tools/ui_shot_macros.bmp`（长度列 6/50/7/1500 byte 与用户表格一致）。
- 2026-09-29：**v13 预期结果对话框增加「测试」区（发送 + 即时比对，绿/红渲染）**。`_edit_expected` 对话框在预期输入框**下方**新增：测试命令框（默认带出该行 AT 命令，来自实时输入框 `_row_vars["txt"]`，可改）+「测试」按钮 + 只读结果框（5 行）+ 说明行「按 ASCII + CR-LF 发送；返回结果与上方预期按所选匹配模式即时比对」。
  - **读数据复用唯一读线程**：在 `_poll_rx` 的 RX_DATA 分支加捕获钩子（`self._test_cap`），不另开 read 口，避免和面板抢数据；响应同时照常显示在输出框。
  - **非阻塞判定**：对话框用 `after(POLL_MS)` 轮询——收到数据后静默 `RESP_IDLE_MS`(120ms) 即判定，或到「响应超时」(`timeout_var`，默认 2000ms) 判定；期间禁用测试按钮，对话框销毁即 `_stop_test_capture()`（`<Destroy>` 绑定），不泄漏捕获。
  - **判定与渲染**：用 `stress_model.match_expected(响应, 预期, 匹配模式)`；命中用 `P["success"]` 绿色加粗、未命中用 `P["danger"]` 红色加粗、原文用 `P["muted"]`；无返回/串口未开/命令为空/压测运行中各有独立提示（未开串口时不发数据）。
  - 对话框 560x470 → 620x640（minsize 470x560）。
  - i18n 新增 12 键（zh/en）：`stress_test_section/at/send/hint/wait/noresp/empty/pass/fail/noexp/busy/resp`。
  - **验证**：`unittest discover tests` **102/102**（新增 `TestExpectedDialogTestButton` 3 例：默认值+颜色、命中绿/未命中红（替身串口断言按 ASCII+CR-LF 发送 `b"AT+CSUB\r\n"`）、未开串口红色报错且不发数据）；**真机 COM105@921600**：`get_version` → 阶段1 预期故意写错 → 红「匹配失败」并显示模组真实返回 `get FCM100D version / FCM100DACR23A01M02_LIGHTBULB_D_FWT_M14.bin / heap=55704 / $`；阶段2 用真实返回行 `get FCM100D version` 作预期 → 绿「匹配成功」；实拍 `tools/ui_shot_dialog_contains.bmp`。脚本：`tools/hw_expected_test.py`。
- 2026-09-29：**匹配示例重做 v12.1（用户反馈「示例太粗糙」）**。把压力模式「编辑预期结果」对话框的示例区从「三种响应样例罗列」改为**按匹配模式给出「实际接收内容 → 预期这么写 → 命中/不命中」对照**（示例不再限定 AT 命令）：包含示例用 `+QSTAAPINFO OK`（教「照抄可见片段、不要写 `\r\n`」）、正则示例用 `+QGETIP: "10.1.2.3"\r\nOK\r\n`（教 `\r\n`/`\s` 是转义、跨行要 `(?m)`/`(?s)`、不能用真实换行或 `|`）、全等示例用 `+QVERSION: FCMA62NAAR03A02M08`（教无通配符、只适合单行）。示例区字号比输出框小一档、行高 6→7。**修了三个自己引入的问题**：① `\r\n` 在 i18n 源码里写 `\r\n` 得到真 CR/LF（插入 Text 被当换行）→ 必须写 `\\r\\n`（连错三次才收敛，已用 `chr(92)` 显式构造校验）；② 要点行超窄条宽度被折到第 7 行、第 6 行之后看不见 → 文案压到 ≤73 宽度单位 + 字号减一档 + 行高 7；③ 测试断言改为「与 i18n 文案逐字相同 + 6 行 + 无真 CR + 正则含字面量 `\r\n`/`\s`/`(?m)`」。验证：`unittest discover tests` **99/99**；三种模式实拍（tools/ui_shot_dialog_{contains,regex,exact}.bmp）逐条可见不折行；说明书 §7.6.3 同步。
- 2026-09-29：**UI/交互修复 v12（用户 4 项反馈）**。① 复制成功**不再往输入框写「已复制 N 字符」**（AT/压力模式共用同一实现；失败仍提示，复制全部仍弹确认框）。② 复制改为**后台线程异步**写剪贴板：长文本复制不再阻塞主线程 —— 实测真机 COM105@921600 刷屏中途复制全部主线程仅阻塞 **0.001s**（旧实现为同步等待子进程数百 ms 起步），右键菜单不再卡。③ 顶部模式入口文案固定为「**串口模式切换**」（原来会随当前模式改名 AT模式/压力模式），下拉菜单项仍是「AT 模式 / 压力模式」；同时纳入语言刷新。④ 压力模式「编辑预期结果」对话框：输入区拆成**上窄（匹配示例，6 行只读，随匹配模式联动）+ 下宽（输入框，可拉伸）**；示例按「包含/正则/全等」三种模式分别给出 (1) 只回 OK、(2) OK 前有数据、(3) OK 后有数据 三种响应样例与写法（含正则可区分 (2)(3) 的写法、全等只适合单行响应的注意事项）；对话框 520x360 → 560x470。验证：`unittest discover tests` **98/98 通过**（基线 93，新增 tests/test_ui_round2.py 4 例 + test_clipboard 1 例）；安装版 site-packages 端到端 7 项断言全过；两种模式的示例区实拍（tools/ui_shot_dialog_contains.bmp）确认；**须彻底退出并重启 ecom 生效**。
- 2026-09-29：**剪贴板修复 v11（复制全部/选中粘到外部为空）**。① 新增 `ecom/clipboard.py`：Windows 下用一个不 import tkinter 的子进程 + Win32 立即渲染写剪贴板，子进程内回读校验；非 Windows 回退 Tk；失败返回 False 并提示。② `app.py`：`_copy_to_clipboard` 改为委托 `set_clipboard`；`_install_select_menu` 自接管 `Ctrl+C`/`<<Copy>>`（复制后 return "break"）与 `Ctrl+V`/`<<Paste>>`/`<<Cut>>`（break），阻止 Tk 类绑定（tk_textCopy/tk_textPaste）再接管剪贴板；新增 `_on_copy_key/_on_paste_key/_on_select_all_key`；**删除**废弃的进程内 `_clipboard_set()`。③ `help_viewer.py`：复制同样改走 `set_clipboard` + break 绑定。④ 新增 `tests/test_clipboard.py` 6 例（含「复制全部 → 主线程忙等 1s → 独立进程读剪贴板」的复现用例，及 `<<Copy>>` 真实路径用例）。⑤ 新增 `tools/sync_sitepackages.py`（源码↔site-packages 同步，防止又改到不生效的那份）。验证：`unittest discover tests` 93/93 通过（基线 87）；旧实现下该 2 条用例必失败（反向验证）；site-packages 已同步（app/help_viewer/clipboard）并清 __pycache__，安装版端到端 136000 字符 PASS。**须彻底退出并重启 ecom 才生效。**
- 2026-08-30：输入/输出交互增强（AT+压力模式）。①输入框开启 `undo=True`(maxundo 2000) 支持 Ctrl+Z 撤回；Ctrl+←/→ 按「单词/分隔符」分段移动光标（`_move_word`，如 `AT+QPING="…"` 中 Ctrl+→ 从 A 前移到 `+` 前，不直跳首尾）；复制/粘贴（Tk 默认绑定）不受影响。②字体调大：`ui_font` 8→9、`in_font` 9→11、`out_font`(输出框 Log，AT/压力共用) 9→11 后按用户「小一号」降为 10；窗口 1000x850→1080x900(minsize 960x800)。③Log 开始/停止两按钮合并为单 toggle（`log_btn`），未记录=开始记录 Log、已记录=停止记录 Log，`_sync_log_state` 随 active 切换文字。④开始记录时把输出框已有 Log 一并写入文件并持续记录。新增 tests/test_input_features.py 6 用例；87/87 测试过。
- 2026-08-30：审计并修复「输出框复制全部大 Log 失败」。实测根因：Windows 剪贴板+Tk 对超大文本受限——Tk `clipboard_append` + `update_idletasks()` + `update()` 在约 2.7M 字符内外部(Win32)可完整读取，超 6.75M 外部 `OpenClipboard` 失败；Win32 手动 `SetClipboardData` 在有 Tk 的进程会写成空(陷阱)。最终方案：`_copy_to_clipboard` 回到可靠 Tk 方式(`append`+`update_idletasks`+`update`)，文本>3M 字符提示改用「另存 Log/分段」，避免静默失败；AT 与压力输出框共用。i18n 加 `copy_big`。tests/test_bug_copy_and_encode.py 5 用例；81/81 测试过。
- 2026-08-30：修复两个 BUG。BUG B：AT/压测发送 HEX/DEC/BIN 类型时输入非对应格式（如 BIN 里输入 AT 命令）抛 ValueError 崩溃；`app.send_text` 捕获并提示 `encode_bad`，返回 0。BUG A：输出框大文本复制在持续接收场景下不可靠；`_copy_selection/_copy_all` 统一走 `_copy_to_clipboard`（append 后 `update_idletasks()` 确保提交 + 异常兜底提示 `copy_fail`）；i18n 加 `encode_bad/copy_fail`。新增 tests/test_bug_copy_and_encode.py 5 用例，81/81 测试过。
- 2026-08-30：README（即 PyPI 简介 `readme`）移除「📝 维护者注意」段（E-SafeNet 加密、用脚本改源码、先读 PROGRESS 等内部信息不再外泄）。README 内「维护者注意」「E-SafeNet」字样清零。
- 2026-08-28：「关于」弹窗改版：相对主窗居中、`win`/标题/版本/简介底色统一为 `P["bg"]`（去白底灰块）、新增作者「EDISON」、删简介句号；Linux 排障手册正文行距加大（`spacing3=6`，标题 9/8/7）。66/66 测试过。
  - 2026-08-28：重建 Linux 明文同步包 `ecom_plain_src.zip`（41 文件），纳入厂商关键字清零 + 新增 `ecom/help_viewer.py`、`docs/TROUBLESHOOT_zh/en.md`，包内 vendor 残留 0。
  - 2026-08-24：初始化项目目录与进度文件，确立「PROGRESS.md 进度记忆规则」。
- 2026-08-24：需求从「Linux 串口工具」扩为「Win+Linux 跨平台 GUI 串口工具」；补充 9 项功能规格、架构规划、8 个里程碑；GUI 框架待确认。
- 2026-08-24：确认 Tkinter 为 GUI 框架，锁定全部选型；明确 python3-tk 无法由 pip 携带及三层兜底方案。
- 2026-08-24：M1 完成 —— 骨架（pyproject/main/cli/app/serial_core）+ 最小 GUI + 4 个单元测试（loop:// 回环）全部通过。
- 2026-08-24：修复 main.py 加 sys.path 兼容处理；定位开发机正确 Python 为 `C:\Python38`（py -3.8），GUI 弹窗待用户本地验证。
- 2026-08-24：M1 增强 —— 串口配置补齐数据位/停止位/校验位/流控（带默认值：8/1/None/None、波特率115200）+ 菜单栏（文件→退出、设置→语言）+ 语言切换（中文/English，I18N 资源独立 i18n.py）；serial_core.open 完整参数透传；新增 3 个 loop 回环参数化单测 + 1 个 stopbits=1.5 & parity=E 组合测试全部通过。
- 2026-08-24：开发解释器由 `C:\Python38` 切换为 `E:\software\python389`（用户新建的 Python 3.8.9 完整版）；技术坑：Tk 顶层 menubar 项不支持 `entryconfigure(label=…)` 更新标题，故语言切换时采用**重建菜单**方案（radiobutton 状态用共享 `_lang_var` 保留）。
- 2026-08-24：**M2–M6 一次性落地**：M2 编解码(ASCII/HEX/DEC/BIN)+send-on-enter；M3 显示选项(时间戳/方向/\r\n/接收HEX)；M4 Log 落盘(文件菜单选路径+开始/停止)；M5 AT 命令面板(命令组保存/加载/删除+快速发送)；M6 文件加载发送；UI 美化(方案A，Notebook 分页)；config 持久化提前落地。新增 codec/logger/config/at_panel/file_panel 五模块，单元+smoke 全通过（用 `E:\software\python389`）。
- 2026-08-24：**UI 重排 v2**（响应「太丑/不规整/缺侧边AT栏」反馈）：弃 Notebook → 左右分栏；右栏常驻「AT 命令（快捷）」按钮网格 + 文件发送；AT 单击即发送、右键管理；输出区主导/输入区固定高度。改 `ecom/app.py`（主布局）+ `ecom/at_panel.py`（按钮化）+ `i18n.py`（补 en/zh 键）+ UI_DESIGN.md（v2）+ ui_mockup.html（v2 预览）。中文构建 + 中英切换 + AT 按钮渲染 + send_text 无串口容错自测全通过，`py_compile` 通过。
- 2026-08-24：**UI 走查修复 v5（11 项）**——①右栏命令组改 grid 权重占40%自适应；②显示选项拆行显示；③菜单字体放大；④输入框矮化(height=2)+字体放大(12)；⑤输出分帧聚合（_rx_buf+静默120ms,避免断截/发回显打断）；⑥输出颜色统一黑；⑦Ctrl+滚轮缩放输入输出字体；⑧打开串口竖排到刷新下+左栏空白让给右栏；⑨输入框Enter发送；⑩默认值联动；⑪全量回归。涉及 `app.py`(menu/body/monitor/poll_rx/append_line/serial_card/events, E-SafeNet→py脚本字节级替换)、`i18n.py`(补 dtr_rts)。证据：py_compile 通过 + 运行时 7 项 + 布局测量(左696/右472) + 截屏走查。
- 2026-08-25：**用 PrintWindow 直接抓 eCOM 窗口位图验证**（桌面级截图被 QuecAgent 遮挡不可用；PIL 未装；改用 ctypes `PrintWindow`+`GetDIBits` 输出 BMP）。**实证核心结论：磁盘明文 app.py 共 746 行，布局 v5 已正确生效**——串口卡为三行 Frame（top(y=31)端口/波特率/数据位+右侧刷新·打开串口；row1(y=99)停止位/校验位/流控；row2(y=132)发送/接收计数+清零），`_build_body` 左列 weight=2/右列 weight=1。**技术坑（重要，E-SafeNet 加密的具体表现）**：`read_file`/`edit_file` 读到的 app.py 是**截断的 237 行密文、file_panel.py 是 29 行密文**，与磁盘真身（746/127 行）不一致——这正是此前多轮 "改不动布局" 的根因；对这类被 DLP 加密的文件，唯一可靠途径是 `py -3.8`（白名单进程）读明文 + 字节级替换，改后 `py_compile` 校验。遗留：`xbak/` 为更旧版本备份，暂留未动。
- 2026-08-25：**UI 走查修复 v6（5 项，响应截图反馈）**：
  1. **初始窗口高度不够、Log 显示不全** → `root.geometry("1200x860")`→`"1200x920"`；`minsize(1000,720)`→`(1000,780)`。
  2. **右栏命令组占比过大** → 弃 `columnconfigure` 权重（实测 weight=3:1 仍占 42%，因 weight 只分额外空间、受内容请求宽度影响），改**右栏固定宽度 320px**（`sidebar=ttk.Frame(width=320)`+`grid_propagate(False)`，`body.columnconfigure(0,weight=1)/columnconfigure(1,weight=0)`），实测右栏 27%。
  3. **串口配置文字与输入框太挤** → `_field_pack`：字段组 `f.pack(padx=(0,12))`→`(0,16)`；label 与控件 `padx=(0,4)`→`(0,6)`。
  4. **全部按钮宽度过大、一行放不下多个** → `TButton` padding `(12,5)`→`(8,4)`（全局所有按钮变窄；AT 命令按钮保持 `sticky="ew"` 撑两列，右栏收窄后自然更紧凑）。
  5. **输出 Log 只有首行有时间戳（核心）** → 根因是 `_flush_rx` 把整批字节**聚合为一条 RX** 渲染，`_render_frame` 只生成一次时间戳；改 `_flush_rx` 按 `\n` 拆行，逐行 `_render_frame("RX", ...)`（每行独立时间戳，空行也各自一条），末段无换行时补渲染一次。实测 7 行 RX 全部带时间戳。
  证据：py_compile 全过 + 布局测量（右栏 320px/27%、左列 71%）+ 输出框内容逐行时间戳（7/7）+ 窗口坐标验证 + PrintWindow 截图走查。
- 2026-08-25：**UI 走查修复 v7（5 项，响应截图反馈）**：
  1. **窗口尺寸 + Log 未显示** → `root.geometry("1200x920")`→`"900x950"`，`minsize(1000,780)`→`(820,860)`；同时给输出框设 `height=22`（固定行高不撑大）。实测 900×950 下 Log 行按钮（log_select/start/stop）窗口坐标 bottom=912 < 950，**全部可见**；文件发送按钮 bottom=877 可见。
  2. **输出/输入字体小一号** → 原共用 `mono_font`(12) 拆成 `out_font`/`in_font`(均 11)。
  3. **Ctrl+滚轮缩放独立 + 不撑大布局** → 拆 `out_font`/`in_font` 两个独立字体对象，缩放只作用鼠标所在框（`_bind_events` 用 `make_wheel(fontob, widget)` 分别绑输出/输入）；`_zoom_font(fontob, widget, delta)` 只改对应 widget 字体。新增 `_clamp_output` 在 `<Configure>` 时强制 `output.configure(height=22)`，字体变大不改变输出框尺寸。实测：out_font≠in_font（独立对象）；输出放大后 output 高度仍 22；缩放输出不动 in_font（始终 11）。
  4. **串口配置标签间距（上次理解反了）** → 需求：**标签紧贴自己的下拉框**、**上一个下拉框与下一个标签之间留大间距**。**根因**：`_field_pack` 里 `widget.pack(side="left")` 把控件 pack 到了 **parent（top）** 而非 field Frame `f`，导致 label 与 combo 不再同框、间距失控。改 `widget.pack(in_=f, side="left")` 让 label+combo 同进 `f`；`f.pack(side="left", padx=(0,20))` 保证组间大间距。实测：端口label→COM88 gap=2px（紧贴），COM88→波特率label gap=20px（大间距）。
  5. **文件发送/Log 保存间距过大** → file_panel row1 `pady=(6,2)`→`(3,1)`、row2 `pady=(2,6)`→`(1,3)`、发送/清空按钮 `padx=(8,6)/(0,6)`→`(8,2)/(0,2)`；`file_panel` 外层 `pady=(4,4)`→`(2,2)`；Log 行 `pady=(2,4)`→`(1,2)`、entry `pady=4`→`2`。
  证据：py_compile 全过 + 输出框逐行时间戳 + 字体独立/高度锁定实测 + field_pack 间距实测（label→combo=2px，combo→label=20px）+ PrintWindow 截图走查。
- 2026-08-25：**UI 走查修复 v8（响应「串口下拉框消失 + 窗口尺寸/字体/间距」严重回归）**：
  0. **核心 bug（严重回归）**：串口配置的 6 个下拉框（端口/波特率/数据位/停止位/校验位/流控）在真实 GUI 中全部不显示（只剩标签文字）。**根因**：`_field_pack` 用了 `widget.pack(in_=f, side="left")` 这种 `in_` reparent 写法——虽在 `winfo_ismapped` 单测中通过，但真实窗口渲染时 ttk.Combobox 经 `in_` reparent 会静默失效不显示（v7 第 4 项引入的修复反而制造了此 bug）。**修复**：弃用 `in_=`，改 `_field_pack` 直接 `self._label(parent, label_key).pack(side="left", padx=(0,3))` + `widget.pack(side="left")`，label 与 combo 在 parent 内同排。实测：6 combo 全部 mapped=1 且各 values 有值。
  1. **窗口默认尺寸** → `root.geometry("1000x850")`，`minsize(900,760)`（要求：默认初始窗口显示完整所有组件）。
  2. **数据字体缩小 2 号** → `out_font` 11→9、`in_font` 11→9、`ui_font` 10→8；输出框 `height` 22→18（缩小占用）。**头部「设置」语言字号不缩**：`menu_font` 保持 `size=12, weight="bold"`。
  3. **组件间距减小**：串口卡字段组间距 `(0,20)`→label 后 `(0,3)`；配合字体缩小整体更紧凑。
  证据：py_compile 全过 + 运行时测量（root 1000x850 / requested 901x793）+ 6 combo mapped 且带 values + overflow count=0（无组件超出窗口边界）+ 新进程 `py -3.8 main.py` 截图走查（下拉框恢复、布局完整）。
- 2026-08-25：**UI 走查修复 v9（响应 7 项 BUG 反馈）**：
  1. **Bug2（严重 AttributeError）**：点击「选择Log文件」报 `AttributeError: 'EcomApp' object has no attribute '_log_path_var'`。根因：`_choose_log` 用 `self._log_path_var.set(...)`，而构建时变量名为 `self.log_path_var`（无下划线），笔误导致未定义。修：`_log_path_var` → `log_path_var`。已走全链路验证（`_log_start` 用中文名 `.log` 成功建文件+开始记录+`logger.active` 正确切换）。
  2. **Bug4（串口配置太挤）**：`_field_pack` 标签左 padding 由 `(0,3)` 改 `(14,3)` —— 标签左侧留 14px 与前置下拉框隔开，右侧 3px 紧贴自己的下拉框。实测：端口combo结束x=205 → 波特率label x=219（差14px），波特率combo结束x=328 → 数据位label x=342（差14px）；label 与自家 combo 紧贴。
  3. **Bug6（文件发送布局易误触）**：`file_panel._build` 重排 —— 「发送文件」放到「选择文件」**下方**（同列），「清空」放到「发送文件」**左边**。实测：选择文件 y=728 / 发送文件 y=756（下一行）；清空 x=18 / 发送文件 x=106（清空在左）。
  4. **Bug1/5/7（悬浮看完整路径）**：新建 `ecom/tooltip.py`（`Tooltip` 类）—— 无边框置顶小窗，悬停 350ms 弹出，文本可动态读取（`text` 可传入 callable），中英文/任意语言文件名完整显示，不改变组件尺寸。应用到：Log 路径入口 `log_entry` 与「选择Log文件」按钮、file_panel 路径入口 `path_entry` 与「选择文件」按钮。实测：Toplevel 成功弹出显示完整混名路径（427x27，viewable=1）。
  5. **Bug3（任意语言文件名）**：确认 `logger.start` 用 `open(abspath, "a", encoding="utf-8")` 原生支持任意 Unicode 文件名（中/俄/阿拉伯/日/英实测均 open 成功）；无改动，属于 Bug2 修复后即正常。
  证据：py_compile 全过（app/file_panel/tooltip/logger）+ 运行时各 bug 专项验证（log_path_var.set、串口间距像素、file_panel 按钮坐标、tooltip 弹出、多语言文件名 open）+ 真实 `py -3.8 main.py` 截图走查。
- 2026-08-25：**UI/Log 修复 v10（响应「文件发送布局理解 + Log 与输出框不一致」）**：
  1. **文件发送面板重排 v2（按用户明确意图）**：`file_panel._build` 改嵌套右对齐子 Frame —— `发送文件`在`选择文件`**正下方**（同列 x=560 对齐，y 下一行）；`清空`在`发送文件`**左边**（x=472）；`大小`也移入右侧区（x=438）；`已发送`状态留左侧。实测坐标：sel_x=send_x=560、clear_x=472<send_x=560、Checkbutton 数量=0。
  2. **彻底删除「发送后追加后缀」**：删 `append_var/apppend_chk/_suffix_lbl/_sync_suffix` 及 i18n 两键（zh/en `file_append_suffix`）；`_send_file` 不再追加 suffix（只读文件原文发送）；`app._on_suffix_changed` 改空实现（避免 trace 回调因 `_sync_suffix` 缺失而 AttributeError）；`_apply_language` 里的 `panel._sync_suffix()` 调用随方法删除一并清除。send-on-enter 后缀仍作用于输入框编码，不受影响。
  3. **Log 与输出框不一致（核心）**：`_render_frame` 原先只把 `body`（纯正文）传给 logger，logger 内部自己拼 `2026-08-25 11:19:52.459  TX  ...`（无方括号、时间点变点），与输出框 `[2026-08-25_11:19:52:459]  TX  ...` 完全不同。**改法：`_render_frame` 把渲染进输出框的那一行（含 `[时间戳] TX/RX 正文`）原样传给 logger，logger.log 改为直接写入整行**（不再自己拼格式）。实测：复用 loop:// 回环生成 TX+多条 RX，输出框内容与 Log 文件**逐字节一致**（都含方括号时间戳、每行独立时间戳）。
  4. Bug3（多语言文件名）维持：logger 用 `open(abspath,"a",encoding="utf-8")` 原生支持任意 Unicode 文件名。
  证据：py_compile 全过（app/file_panel/logger/i18n）+ 文件面板坐标校验（发送在正下方/清空在左/大小居右/无Checkbutton）+ Log 一致性逐字节断言 + 真实 `py -3.8 main.py` 截图走查。
- 2026-08-25：**建立 GUI 回归测试防线（复盘教训）** —— UI 反复出问题的根因是我长期"点对点补丁"、改 A 坏 B，且无自动化防线。本轮做三件事：
  1. **端到端走查**：用 loop:// 真实回环走查 打开串口→发送 AT→接收→Log→计数 全链路，输出框与 Log 逐字节一致（含 `[时间戳] TX/RX 正文`，2 行完全一致）；程序化测量 1000×850 窗口下所有业务组件无溢出（仅 Menu winfo 假象）。
  2. **新增 tests/test_gui_regression.py**（4 用例，`unittest`）：① 串口配置 6 下拉框存在且布局宽>0（v8 回归，防 pack(in_) 丢失控件）；② 串口字段标签与前置下拉框间距>=12px（v9 回归）；③ Log 与输出框逐字节一致（v10 核心）；④ 文件面板布局——发送在选择文件正下方/清空在发送文件左（v10 回归）。
  3. **全量回归**：`python -m unittest discover tests -v` → 8 测试全过（4 GUI 回归 + 4 serial_core），既有功能未破坏。
  **教训**：后续每次改 UI 必须跑 `tests/test_gui_regression.py`；跨文件改动先 `py_compile` 全量再测；无头 GUI 测试用 `winfo_width()>0` 而非 `winfo_ismapped()`（withdraw 下恒 0）。

- 2026-08-25：**AT 命令组改造为 configs/ 配置文件版（重做右栏 AT 面板）** —— 按用户原型图推翻旧命令组，改为基于配置文件存储。
  1. **存储**：项目根 `configs/<name>.json`，每个文件=一个命令组（JSON 命令数组）；新增 `configs_dir()` 定位（优先项目根，打包后回退 `~/.ecom/configs`），`project_root()` 由 `ecom/at_panel.py` 上上级推导。
  2. **默认配置**：`configs/config.json` 内容只含 `["AT"]`。
  3. **界面（对齐原型）**：顶部「命令组配置」下拉输入框(config1，`state=normal` 可下拉选已有/直接输入新名)+[刷新]+[保存]+[删除配置]；中部可滚动命令列表，**每条命令一行=多选复选框+命令按钮(单击即发送)→多选序号可多选**；底部小输入框+[添加]+[删除选中](弹确认)+[清空组]。
  4. **逻辑六点全对齐**：①configs 文件夹存命令组；②默认 config 只含 AT；③保存=直接替换当前配置文件(新名即新建)；④删除=弹确认框(确认则删/取消不删，含删除配置、删除选中命令两处)；⑤config1 为下拉+可输入，保存新名即新建；⑥多选复选框批量操作。
  5. **实现**：全新重写 `at_panel.py`（废弃旧 `at_groups` 内嵌 JSON 方案），`config.py` 的 `at_groups` 键保留但不影响；i18n 新增 `at_refresh/at_del_config/at_del_config_confirm/at_del_selected/at_del_confirm/at_saved/at_new_config/at_config_name/at_save_confirm`。
  证据：mock 弹框自动化验证 6 点逻辑全过（config 只含 AT、保存替换、新名新建+下拉刷新、删除确认/取消、多选批量、渲染结构=每命令一行复选框+按钮）；py_compile 全过；`py -3.8 main.py` 截图走查确认右栏新布局渲染正常。

- 2026-08-25：**AT 命令组按原型图二次重做（修复4问题）** —— 用户反馈"与原型图不一样"，本轮推翻上一版重做。
  1. **底部循环控制**（核心新功能）：底部改为「循环次数输入框 + Run(绿) + Stop(红)」；逻辑=勾选多条命令后，Run 按序循环发送 n 次（0 表示无限循环直到 Stop），Stop 立即停止（after_cancel）。用 after 定时 300ms/条。实测：有限2次=2命令×2轮=4条准确、无限+Stop 立即停止不再增加、未勾选默认整组。
  2. **命令输入框显示出来**：顶部改为「config1 下拉(可输入) + 命令输入框(可留空) + 添加 + 保存」，输入框不再缺失（原版本误删），回车/添加进列表。
  3. **去掉臆测按钮**：删除我自加的"刷新""删除配置"按钮（原型图没有，用户明确"不要臆测功能"），仅保留原型真实控件。
  4. **右栏可扩展宽度**：`_build_body` 布局改 `columnconfigure(0, weight=1, minsize=520)` + `columnconfigure(1, weight=2, minsize=340)`，右栏不再固定 320px；实测 1500 宽窗口下 sidebar=424px（更宽，左栏让渡占比）。
  5. **命令列表滚动修复**：canvas item 宽度从 56px 修复为撑满可用宽(394px)，命令按钮从 24px→362px 不再截断长命令；多命令(25条)时 yview 可滚动到 1.0。
  6. 命令列表每条命令=多选复选框+命令按钮(单击即发送)，超长滚动条显示。

- 2026-08-25：**命令列表改为可编辑输入框（用户纠偏）** —— 用户指出"右侧的AT是输入框，可以进行更改，不是把AT命令显示为按钮，用户直接点击AT命令"。本轮确认我此前把命令显示为 `ttk.Button` 是**理解偏差**，每个命令应当是**可编辑的 `ttk.Entry` 输入框**。
  1. `_render_list` 第2列：`ttk.Button` → `ttk.Entry`(textvariable=StringVar)，每行一个可编辑输入框。
  2. 编辑同步：绑定 `<KeyRelease>`/`<FocusOut>` 调 `_sync_cmd(i, svar)`，用户改输入框即时写回 `self._commands`。
  3. 发送：`<Double-Button-1>` 触发 `_send_at(idx)`；右键菜单新增 `_bind_menu(entry, idx)`（发送/删除该命令）。
  4. `__init__`/`_render_list` 新增 `_cmd_vars` 列表，随行构建/重置。
  证据：py_compile 全过；mock 验证「输入框数=3、按钮数=0、编辑 AT+QGMRI→AT+CGSN 同步成功、双击发送当前命令、Run 循环就绪 cmds=整组」；8 个回归测试全过。
  教训：命令列表定位是「可编辑配置项(输入框)」而非「快捷触发(按钮)」——用户可修改命令内容后再触发，编辑与触发是两件事。
  证据：循环逻辑 mock+真实 after 双测通过；布局测量(cmd_entry可见 w=146/sidebar=424/run-stop 按钮就位)；25条滚动(yview 0.15~1.0)；宽度修复(scrollregion 56→394, 按钮24→362)；py_compile 全过；8 个回归测试全过(4+4)；main.py 截图走查确认右栏对齐原型。
  教训：改 UI 前先放大原型图逐控件确认，勿臆测功能；循环用 after 定时要在真实事件循环下测试（withdraw 下 after 不触发易误判）。


- 2026-08-25：**右侧 AT list 整体重构（固定20行，每行=复选+输入框+HEX+Enter+发送）** —— 用户明确全新布局。
  1. 删除头部 AT 输入框/添加按钮，头部只有「config下拉(可输入) + 保存 + 一键清空」。
  2. 正文固定 ROWS=20 行 AT list，可为空但始终展示 20 行输入框（不因空而隐藏）。
  3. 每行组件：选择复选 | 输入框(可编辑) | HEX复选 | Enter复选 | 发送按钮。
  4. 首行上方「全选」总复选框：勾选=全部行勾选，去勾=全部取消（联动 _toggle_select_all）。
  5. 发送语义（_encode_row）：HEX勾选=codec.encode(HEX)；Enter勾选=ASCII+CR-LF；默认 ASCII 无后缀。发送按钮独立发送本行，与最前选择复选无关。
  6. Run：只发送勾选行（_selected_rows），循环次数=N 逐个循环；Stop 停止。
  7. 存储 configs/<name>.json 每条 = {text, hex, enter}；_collect_rows 按行号保留空行占位，保存/加载行位不被打乱；兼容旧纯字符串数组加载。
  证据：mock 全过(20行输入框/每行发送按钮/全选联动/ASCII+HEX+Enter 发送字节正确/Run只发勾选行就绪/保存加载roundtrip行位对齐)；py_compile 全过；8 回归全过。
  说明：at_hex/at_enter/at_select_all/at_clear_all 已加入 i18n(zh/en)。


- 2026-08-25：**AT list 分页版 v3（按用户 8 点需求重构）**
  1. 一键清空：清空所有输入框里的 AT 命令文本，**保留**勾选/HEX/Enter 状态（不再重建body丢勾选）。
  2. HEX/Enter 上方新增各自「全选」总复选框（HEX全选/Enter全选），联动本页；行全选依旧。
  3. 恢复序号：每行前显示 1..PAGE_SIZE。
  4. ROWS 改为 PAGE_SIZE=22。
  5. 删除滚动轮查看，改**分页**：上一页 | 页码输入框(回车跳转) | 下一页 | 添加下一页 | 第 x/n 页。
  6. 分页按"总行数(含空行)"算页数（_total_pages=ceil(len(_all_data)/22)）；默认1页22空行；「添加下一页」+22空行并跳到新页，即可操作下一页。
  7. 新增 delay time(mS)：_delay_var，Run 执行多条AT时每条间隔 delay ms（after 定时）。
  8. Run 后新增「当前轮次」显示（_round_lbl），每完成一轮递增，如 2 轮显示 第2轮。
  数据源重构：_all_data(所有页数据,含空行占位,页对齐) → _row_vars 实时 tk 变量。关键：_sync_all_from_pages 从 **_row_vars** 读实时值回写 _all_data（勿从 _pages 静态副本读，否则编辑丢失）；翻页前先 sync 旧页再改 _page（_go_prev/_go_next/_goto_page/_add_page 已处理）。
  证据：mock 全过（22行+序号1-22/行·HEX·Enter三组全选/一键清空只清txt保留勾选/分页添加下一页跳新页+回页数据保留+翻页按钮state正确/delay getter/Run 2轮=4条+轮次显示/分页保存加载roundtrip）；py_compile 全过；8 回归全过。
  i18n 新增：at_select_all_hex/at_select_all_enter/at_prev/at_next/at_add_page/at_page_goto/at_page_of/at_delay/at_round/at_no_prev/at_no_next/at_page_bad。

- 2026-08-25：**压力模式首版落地（独立于 AT 模式）+ 压测名称编辑控件** —— 进入压力模式开发。
  1. **模式切换**：`app.py`(E-SafeNet→py 字节级替换) 顶部「设置」旁新增「AT 模式/压力模式」菜单按钮（`_switch_mode`）；`_build_body` 内容包装成 `content` 容器，`at_view`(AT 视图) 与 `stress_view`(压力视图，懒加载) 同容器切换，互不销毁、各自状态保留。
  2. **独立连接**：`StressPanel` 自带独立 `SerialCore`，与 AT 模式不共享连接；打开失败弹提示，不打断 AT。`_switch_mode` 离开压力时停掉运行中的压测(不关串口)。
  3. **新模块**：`stress_io.py`(模版/导入/导出 CSV，`utf-8-sig` 双平台) + `stress_model.py`(纯逻辑：StressRow/CheckRule/预期匹配contains·regex·exact/check规则/统计/结束条件count·time/时长`0.0H`·时间段格式) + `stress_panel.py`(UI+`after` 状态机运行)。
  4. **UI**：上=串口配置(压测)+压测配置(次数/时间二选一·行间隔·响应超时·AT/DOS Log路径)；下=输出框(含DTR/RTS/清空/显示选项) | 导出模版·导入数据·导出当前数据+**压测名称(输入框+修改/保存按钮)** + 压测AT list(20行可滚动:复选·AT输入框·HEX·Enter·类型·后缀·间隔·预期结果·编辑) + 自定义check规则 + 开始/停止 + 统计块(已发送/异常/当前行/测试时长/总运行次数/脚本运行时间段)。
  5. **配置持久化**：`config.py` DEFAULT_CONFIG 新增 `stress` 段(name/end_mode/count/time/interval_ms/timeout_ms/at_log/dos_log/rows/rules)；本轮不做 GUI↔config 双向持久化（保持独立性，后续补）。
  6. **压测名称编辑**：`导出当前数据` 按钮后加名称输入框(默认禁用)+按钮(初始「修改」)；点「修改」→按钮变「保存」+输入框可编辑；点「保存」→按钮回「修改」+输入框禁用。名称写入 AT/DOS Log 头部与汇总行（对齐 P0「把压力名称写到日志」）。
  7. **验证**：`py -3.8 -m py_compile` 全过；新增 `tests/test_stress.py`(23 用例：预期匹配/规则/行模型/统计/CSV roundtrip/config·i18n·app 锚点) 全过；既有 `test_gui_regression`+`test_serial_core`(8 用例) 全过；`root.withdraw()` 离线冒烟(切模式+名称开关+收集行+预期编辑+模式往返)通过。
  说明：i18n 新增 mode_at/mode_stress/stress_* 共 40+ 键(zh/en)；app/stress_panel 因 E-SafeNet 加密，用 `py -3.8` 脚本做字节级替换后 `py_compile` 校验。

- 2026-08-26：**全项目代码走查 + 合理性修缮（E-SafeNet 下用 py 脚本字节级修改）** —— 用户要求「直接根治 + 浏览整个项目，不合理的可修复都完善」。
  1. tooltip.py：docstring 示例 `Tooltip(entry, get_text=...)` → `text=lambda: entry.get()`（对齐真实签名，避免后人踩坑）；删除从未引用的死常量 `_WRAP_ON`；`_WIDTH=560` 通过 Label `wraplength=self._WIDTH` 真正生效（原注释声称"超出自动换行"但未实现，超长路径会把悬浮小窗无限拉宽甚至超出屏幕）。
  2. i18n.py：zh 里残留的英文重复键 `dtr_rts: "Flow Pins"` 删除（保留"流控引脚"）；en 补缺失的 `dtr_rts` / `at_save_confirm`；en `at_add_page` 半中文残留 `"添加Next"` → `"Add Page"`（否则 en 用户看到 key 原文/中英混搭）。
  3. at_panel.py：行发送按钮注册 key 由伪键 `at_row_send_{idx}` 改为真实 i18n key `at_send`；否则 `_apply_language`（语言切换/初始化）会对每个注册控件 `text=self._t(key)`，而 `at_row_send_0` 在 i18n 不存在 → 22 个行发送按钮文字被覆盖成 `"at_row_send_0"`。
  4. stress_panel.py：`_poll_rx` 收到 `RX_DATA` 时补 `self._rx_last = time.monotonic()`（原只 extend 显示缓冲却未更新静默时刻，`_flush_display` 的 `RESP_IDLE_MS` 判定依赖它 → 首次靠 `_rx_last=0.0` 立即刷新、压测持续发送时又依赖发送时刻，RX 显示会滞后积压；现改为真实接收时刻驱动聚合）。
  验证：`py_compile` 全过；`unittest discover tests` 41 用例全过（含既有回归）；`import ecom.*` 全模块 OK；自写校验脚本确认 4 处修复均生效。
  说明：`stress_panel` 控件未接入 `_register` 语言刷新（切换语言时压力面板文字不随动）为已知遗留项，因需大规模改动/易回归，本轮未强行修，留待后续。
 - 2026-08-26：**压力运行日志增加「每轮开始分隔标记」** —— 用户期望按 `=================== Runtimes N ===================` 标注每一轮（而非只输出头部`=== 名称...===`与汇总）。   1. stress_panel.py 新增 `_log_round_marker(n)`：拼接 `=================== Runtimes {n} ===================`，写入输出框(`_render_note`)与 AT Log(`logger_at.log`)——与 TX/RX 落点一致，从而 header→每轮标记→汇总 完整衔接。   2. `_send_current` 入口在 `self._row_idx == 0` 时调用 `self._log_round_marker(self._rounds_done + 1)`。首轮由 `_start_run` 直达(row_idx=0)触发 Runtimes 1；后续轮由 `_advance` 将 `_row_idx` 归零进入，触发 Runtimes N(N=_rounds_done+1)。   验证：py_compile 全过；`unittest discover tests` 41 用例全过；自写离线冒烟用 mock 串口驱动 2行×2轮，marker 序列 == [Runtimes 1, Runtimes 2]（每轮仅一次、无缺失多余）。  - 2026-08-26：**运行轮次数字 disabled 灰字看不清 → 改成白色加粗** —— 点击「开始」后 `_start_run` 将 run_btn 置为 `state="disabled"`（防重复点击），ttk 按钮 disabled 默认走系统灰字，导致轮次数字（`_set_run_round` 写入 run_btn 文本）看不清。   1. stress_panel.py `_ensure_styles`：为 Run.TButton 创建 bold 字体 `self._run_font`（基于 app.ui_font copy + weight=bold）并挂到 `style.configure` 的 `font=`。   2. `style.map("Run.TButton", background=[("disabled","#1E9E4A"),("active","#17833d")], foreground=[("disabled","#ffffff"),("active","#ffffff")])`——disabled 态强制绿底白字，覆盖系统灰。   依据：app.py L116 `theme_use("clam")`，clam 完整支持自定义色与状态映射，故映射必生效（此前 Run.TButton 绿色一直正常显示即为佐证）。   验证：py_compile 全过；离线冒烟（clam 主题+AppMock）确认 weight=bold、bg/fg map 含 disabled 白绿映射、run_btn 运行态 text=3 显示正确；`unittest discover tests` 41 用例全过。  - 2026-08-26：**压测行间隔改为「AT list 行自身间隔优先，未设置回落全局行间隔」** —— 用户反馈：AT list 每行单独设置的间隔(如 3000ms)不生效，全局压测配置【行间隔(ms)】300ms 反而一直覆盖。   根因：`_advance` 调度下一行发送时直接 `interval = self.interval_var.get()`（全局），无视行自身 `interval_ms`。   修改：`_advance` 中在调度前取「即将发送的下一行」（此时 `_row_idx` 已递增/归零，恒 `0<=idx<len`）的 `interval_ms`，若 >0 则覆盖全局；=0（未单独设置）回落全局行间隔。语义：行自身间隔=发送该行前的等待。   验证：py_compile 全过；离线冒烟(捕获 _schedule_follow delay)三场景：行3000>全局300→3000；行0→回落300；行500→500；`unittest discover tests` 41 用例全过。  - 2026-08-26：**间隔语义纠偏 + AT list 默认预期 OK** —— 用户反馈两点：   1. 间隔语义偏差：设置 AT+QGMR 间隔=3000，旧实现得到「AT 执行后 3000ms 再执行 AT+QGMR」（即下一行间隔生效），用户期望该 3000 用于「AT+QGMR 自身执行后」。改法：`_advance` 取「本次刚执行完的那一行」的 interval_ms（`_row_idx` 已递增/归零：正常时=idx-1，一轮结束归零时=最后一行 len-1），>0 则覆盖全局，=0 回落。效果：AT+QGMR(3000) 执行完后等 3000 再进下一轮；AT 后到 AT+QGMR 用 AT 的间隔（未设→全局300）。   2. 每条 AT list 预期值为空→工具未对比（空预期走 has_expected=False 恒通过）。改法：stress_model.StressRow.expected 默认 "OK"（新建行默认 OK）；stress_panel._collect_rows 对勾选且非空但预期为空的行兜底补 "OK"，且不覆盖已显式设预期的行。   两处均用 py 脚本字节级替换（E-SafeNet）。验证：py_compile 全过；离线冒烟：完成AT→delay300 / 完成QGMR→delay3000；StressRow() 默认 'OK'；空预期行补 OK、已设 'READY' 行保留；`unittest discover tests` 41 用例全过。
 - 2026-08-26：**压力模式实现中英切换（补齐此前「切换语言压力面板不随动」遗留项）** —— 诊断：i18n zh/en 的 `stress_*` key 全部齐全（各 171 个且内容键集一致），压力面板控件构建时都用 `self._t(key)`（语言正确），但**未登记到 `app._text_widgets`**，导致 `app._apply_language` 只刷新 AT 主界面、不刷新压力面板。
   1. **stress_panel.py（30 处字节级替换）**：给全部静态文本控件（名称/串口/压测配置/输出/统计/IO 条/AT list/Pager/规则表头与 Pager/run box/end 区等 LabelFrame·Label·Button·Checkbutton·Radiobutton）在创建处调用 `self.app._register(key, widget)`，从而被 `_apply_language` 自动重刷。
   2. **`_build_grid_header`/`_build_rules_editor` 表头重构**：`header_texts`（翻译后字符串数组）改为 `header_keys`（key 数组，非空才登记），第 0/9 列（序号/编辑列）与规则表空列不登记，可精确刷新。
   3. **新增 `StressPanel._refresh_language()`**（处理刻意**不登记**的动态控件）：open_btn 按 `core.is_open` 显 打开/关闭；name_btn 按编辑态显 修改/保存；run_btn 非运行态显 开始、运行态保持轮次数字；并重算 `_update_run_info/_update_pager/_update_rules_pager`，最后 `_render_page()` 重建当前页行（刷新行内"编辑/序号"等，数据取自 `_rows` 不丢）。
   4. **app.py（2 处）**：`_apply_language` 的 isinstance 判定加入 `ttk.Radiobutton`（否则登记后的 Radiobutton 不刷新）；`_apply_language` 末尾调用 `getattr(self,"stress_view",None)._refresh_language()`（lazy 创建前为 None 则跳过）。
   证据：py_compile 全过；端到端冒烟（zh→en→zh 往返）静态 18+ 控件与 Radiobutton(TRadiobutton) 全部随语言刷新、open_btn/name_btn/run_btn 动态正确、编辑态/关端口态 bounce 正确；新增回归测试 `test_language_switch_updates_stress_panel`（落入 tests/test_fixes_verify.py）。`unittest discover tests` 42 用例：41 过，仅**既有** `test_file_panel_layout`（file_panel 按钮 1px 度量对齐，与本次无关）失败。说明：默认语言逻辑本身正确（config.py 默认 `"language":"zh"`、app.py `or "zh"`）；此前会话所见 `config default language: en` 只是磁盘持久化 config 的旧值。 
 - 2026-08-26：**界面配色全面优化（可一键回退）** —— 用户要求「把配色优化建议全部实现，做好回退准备」。基于真实调色板 + WCAG 对比度实测 + 2025/26 现代配色趋势（功能性色角色/支持色须与品牌色 HSB 协调/限制色阶数）做全套修改（E-SafeNet 下 py 脚本字节级替换，改前已快照）。
   新调色板(app.py P)：primary #3B6FE0→#0B57D0(白字6.39/底色5.80)、primary_h→#0842A0；muted #6B7688→#59657A(底色5.34)；success #22A06B→#15803D、danger #E5533D→#B3261E；新增 success_h #146C33、danger_h #8E1E18；tx #7FC1FF→#0B57D0、rx #9BE3A4→#15803D；全部达 WCAG AA。
   1. A1 恢复TX/RX着色：output.tag tx→P.tx蓝、rx→P.rx绿（替代原统一黑，可分发送/接收）。
   2. A2+B3 统一绿红：at/stress 的 Run.TButton→P.success、Stop.TButton→P.danger，active/disabled→success_h/danger_h（白字AA，disabled 态走更暗）。
   3. B1/B2 muted 与主蓝加深（见 P）。
   4. C2 输入/输出框加描边：ScrolledText=flat+bw0+highlightthickness1+highlightbg/color=border（可见读域边界）。
   5. C1 文件进度条：fill #90EE90→P.success，新增 _pc(key,default) helper。
   6. C3 白卡内标签底色贴合：新增 MutedSurface.TLabel(bg=surface)；app(串口field/monitor)与stress(卡片/表头/rules)的白卡标签改用它；灰条/状态栏/at_panel/file_panel 保持 Muted.TLabel。
   7. C5 tooltip：#FFFDF5/#333 → #FFFFFF/#1B2733。
   验证：py_compile 18模块全过；unittest discover tests 42用例全过；端到端构建无异常、P键含 success_h/danger_h。
   回退：快照 xbak/color_20260826_193203/（含 restore.py/restore.bat 一键还原 app/at/stress/file/tooltip 5 文件）。

 - 2026-08-26：**串口热插拔检测（设备被移除自动断开并恢复“打开串口”）** —— 用户反馈：打开串口后按钮显示“关闭串口”，但拔出 USB 后仍保持连接态、发送无返回、按钮不恢复。
   根因：USB 拔出未必让 pyserial 读线程抛出 RX_ERROR/RX_CLOSED（部分驱动下设备残留，in_waiting 不报错），且即使抛出，旧 `_poll_rx` 也只设 status_error、未真正 close 串口；`_update_status` 依赖 `core.is_open`，而异常后 `_ser.is_open` 仍为 True，按钮无法复位。
   方案：两层失效检测 + 主动断开。
   1. **端口存在性周期探测**：`app.py` 打开时记录 `self._active_port`，在 `_poll_rx`(40ms) 内每 15 次(≈600ms)调 `_check_port_presence()`——用 `list_ports.comports()` 比对当前端口是否仍在系统串口列表；不在则 `_on_port_lost()`。虚拟端口(loop:// 含 ":")跳过探测，避免自测误断开。
   2. **读线程失效接管**：`RX_ERROR`/`RX_CLOSED` 路由到 `_on_port_lost()`（原先只弹错误/刷状态），真正 `core.close()`。
   3. `_on_port_lost`：关串口 + 清 active_port + flush_rx + 输入区提示 + `_set_status_error(port_lost)`（点红·状态栏报错·open_btn→“打开串口”）+ `_refresh_ports(flash=False)`（下拉框剔除失效端口，不再闪“刷新OK”干扰）。
   4. `stress_panel.py` 同样的独立 SerialCore 也同步加固（其 open/close 按钮、`_poll_rx` 相同的断开/探测），保证压力面板端口被拔同样恢复“打开串口”。
   5. i18n zh/en 各新增 `port_lost`（设备已断开（串口被移除），已自动关闭连接 / Device disconnected (port removed), closed automatically）。
   验证：py_compile 全过；新增 tests/test_hotplug.py 5 用例（虚拟端口跳过/端口消失断开/端口仍在不断开/RX_ERROR断开/RX_CLOSED断开）全过；`unittest discover tests` 47 用例全过。

 - 2026-08-26：**压测 导出模版/导入数据/导出当前数据 格式升级（CSV+TXT+XLSX）** —— 用户反馈：现 CSV 用 Excel 打开无下拉框、index 列意义不大、希望支持 csv 和 txt。
   明确方案：①A1 ②B1 ③C1 —— 模板导出真 .xlsx（带 Excel 下拉框）；txt=CSV 换扩展名；send_type 下拉单选。
   1. **stress_io.py 重写**：
      - 去掉展示用 index 列，HEADERS 改 9 列：enabled/at/send_type/send_suffix/hex/enter/interval_ms/expected/match_mode；
      - 新增 .xlsx 读写（openpyxl）：`_write_xlsx`/`_read_xlsx`/`_add_dropdowns`，模板用 openpyxl 给 enabled·send_type·send_suffix·hex·enter·match_mode 6 列加 DataValidation 下拉（应用到 2..2000 行）；
      - `export_template`：.xlsx→带下拉框模板；.csv/.txt→逗号分隔模板；`export_data`：按扩展名 .xlsx→xlsx 数据 / .csv/.txt→csv；`import_data`：按扩展名路由 csv/txt/xlsx；
      - 兼容旧 10 列（含 index 首列）：`_offset(header)` 依据表头首列文字是否 `index` 自动 +1，读旧文件不坏。
   2. **stress_panel.py**：`_export_template` 默认 `stress_template.xlsx`（filetypes 含 Excel/CSV/TXT）；`_import_data` filetypes 含 数据文件(*.csv *.txt *.xlsx)/CSV/TXT/Excel；`_export_data` 默认 `stress_data.csv`（filetypes CSV/TXT/Excel，可改 .txt/.xlsx）。
   3. **pyproject.toml**：dependencies 新增 `openpyxl>=3.0`（此前刻意「运行时仅 pyserial+Tk」的原则性变更，用户已拍板接受）。开发机 python389 已 `pip install openpyxl 3.1.5`。
   4. **tests/test_stress.py**：BOM 导入测试数据改 9 列（去 index）；新增 `test_data_export_txt_roundtrip` / `test_xlsx_template_has_dropdowns`（断言无 index 表头+send_type/suffix/match_mode 下拉在 C/D/I）/ `test_import_xlsx_data_roundtrip`。
   验证：py_compile 全过；`unittest discover tests` 50 用例全过（47 既有 + 3 新增）；真实导出模板验证：表头无 index、6 个下拉框(type=list)选项值正确（ASCII,HEX,DEC,BIN 等）。
   说明：openpyxl 为纯 Python，pip 即装；stress_io.py 内 openpyxl 在函数内按需 import，未装时 xlsx 导出返回 False（报错提示），csv/txt 不受影响。
- 2026-08-28：**Linux 串口排障手册 + 工具入口**（用户拍板「全按推荐实现」；结合 ModemManager 抢占 AT 口根因）。
  1. **新增 `docs/TROUBLESHOOT_zh.md` / `docs/TROUBLESHOOT_en.md`**：通用 Linux 串口排障手册（现象/根因/方案一 udev `ID_MM_DEVICE_IGNORE` 永久忽略/方案二 stop ModemManager 临时/其它坑：dialout 权限、UUCP 锁、E-SafeNet 密文、CDC-ACM 波特率摆设）+ 快速判断。
  2. **新增 `ecom/help_viewer.py`**：内嵌 Tk 只读查看器，自实现 md 子集解析（#/##/###/列表/引用/```代码块/**加粗**/内联`code`），只读可选可复制（右键菜单+Ctrl+A/C，拦截非 Ctrl 键入）。
  3. **`ecom/app.py`**：顶部新增「帮助」按钮 + `help_menu`（入口 Linux 串口排障手册）；`_open_help_guide()` 按当前语言打开查看器；新增 `_mm_holds_port(port)`（POSIX 下 `fuser -v` 检测 ModemManager 占用，非 POSIX 恒 False）；成功打开与打开失败两条路径均触发 `help_mm_hint` 提示。
  4. **`ecom/i18n.py`**：zh/en 新增 `menu_help`/`help_guide`/`help_close`/`help_mm_hint` 4 词条。
  验证：py_compile 全过（app/i18n/help_viewer 及全部模块）；`unittest discover` 66/66 全过无回归；Tk 冒烟：doc_path 解析正确、md 渲染含 ModemManager/方案一、app 导入正常。备份于 `xbak/help_20260828/`（app.py.bak、i18n.py.bak）。
- 2026-08-28：**「关于」对话框 + `ecom help` 子命令 + 厂商关键字全量清除**。
  1. **①「关于」**：`ecom/app.py` 设置菜单新增「关于」项 → `_open_about()` 弹窗（标题/版本`__version__`/简介 + 「打开排障手册」Primary 按钮 + 关闭）；`i18n.py` 增 `menu_about/about_desc/about_open_guide`（zh/en）。
  2. **② `ecom help`**：`ecom/cli.py` 子命令 `help`（`choices` 加 `help`；新增 `--lang/-l` zh|en，默认 zh），终端直接打印排障手册，**不依赖 tkinter**（无显示也能用）；`_md_to_text()` 简易 md→文本转换。
  3. **厂商关键字清除**（用户要求"不要提及任何厂商"，先判断对工具运行影响：均为纯展示文档/字符串，逻辑不读取，**零运行影响**）：`docs/TROUBLESHOOT_zh/en.md` 删目标厂商名→"蜂窝模组"、删 厂商 USB VID→`<idVendor>:<idProduct>`、udev 例子用 `<VID>/<PID>` 占位；`docs/USER_GUIDE_zh/en.md` 示例串 设备全名→"USB Serial Port"；`docs/ui_mockup.html` `module.bin` 归一。`ecom/serial_core.py` 注释、`tests/test_hotplug.py` 测试替身中的厂商名亦全清（纯注释/测试替身，零运行影响），`__pycache__` 旧 .pyc 烘焙串同步删除重建。
  验证：vendor 扫描 md/html **零残留**；全包 py_compile 过；`unittest discover` 66/66 全过；`ecom help -l zh` 终端实测打印正常；实机构造 EcomApp + `_open_about()` 弹窗成功打开（title=关于）。Linux 明文包已重新导出至 `linux_patch_20260828/`（含 cli.py、清理后 docs）。
