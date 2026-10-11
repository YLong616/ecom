"""GUI 主窗口（Tkinter）。

M1：端口 / 波特率 + 完整串口参数 + 打开关闭 + 收发 + 字节计数。
M1增强：菜单栏(文件/设置) + 中英语言切换。
M2：编解码(ASCII/HEX/DEC/BIN) + send-on-enter 后缀。
M3：显示选项（时间戳 / 方向 / \\r\\n / 接收HEX）。
M4：Log 落盘（菜单「文件 → Log」控制）。
M5：AT 命令面板（命令组保存/加载/清除）。
M6：文件加载发送。

视觉主题：浅色界面 + 深色数据区（见 UI_DESIGN.md，方案A）。
"""

from __future__ import annotations

import datetime
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import scrolledtext
from tkinter import ttk
from tkinter import filedialog

from . import codec, i18n
from .serial_core import SerialCore
from .logger import Logger
from .config import Config
from .at_panel import AtPanel
from .file_panel import FileSendPanel

BAUDRATES = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
DATABITS = ["8", "7", "6", "5"]
PARITY_OPTIONS = ["None (N)", "Even (E)", "Odd (O)", "Mark (M)", "Space (S)"]
STOPBITS = ["1", "1.5", "2"]
FLOW_OPTIONS = ["None", "RTS/CTS", "XON/XOFF"]

PARITY_MAP = {
    "None (N)": "N", "Even (E)": "E", "Odd (O)": "O", "Mark (M)": "M", "Space (S)": "S",
}
FLOW_MAP = {"None": (False, False), "RTS/CTS": (True, False), "XON/XOFF": (False, True)}

# 配色（浅色界面 + 深色数据区）
P = {
    "bg": "#F2F4F7", "surface": "#FFFFFF", "border": "#D9DEE8",
    "primary": "#3B6FE0", "primary_h": "#3059C4", "secondary": "#ECEFF4",
    "text": "#1B2733", "muted": "#6B7688",
    "success": "#22A06B", "danger": "#E5533D", "idle": "#9AA4B1",
    "te_bg": "#101A28", "te_fg": "#DDE4EC", "tx": "#7FC1FF", "rx": "#9BE3A4",
}


class EcomApp:
    def __init__(self, root, language="zh"):
        self.root = root
        self.core = SerialCore()
        self.P = P  # 供子面板取配色
        self.logger = Logger()
        self.config = Config()
        self._status_error = None
        self._log_path = self.config.get("log", "path", "") or None

        # 语言（config 优先，其次入参）
        cfg_lang = self.config.get("language") or "zh"
        self.lang = language if language in i18n.SUPPORTED_LANGUAGES else cfg_lang
        if cfg_lang in i18n.SUPPORTED_LANGUAGES:
            self.lang = cfg_lang

        # 键盘/字体
        self.ui_font = tkfont.nametofont("TkDefaultFont").copy()
        self.ui_font.configure(size=10)
        self.menu_font = self.ui_font.copy()
        self.menu_font.configure(size=12, weight="bold")
        self.mono_font = tkfont.nametofont("TkFixedFont").copy()
        self.mono_font.configure(size=12)

        root.geometry("1200x920")
        root.minsize(1000, 780)
        self._text_widgets = []  # [(key, widget)] 语言切换时批量刷新

        self._setup_style()
        self._build_vars()
        self._build_menu()
        self._build_widgets()
        self._bind_close()

        self._apply_language()
        self._update_counters()
        self._update_status()

        self._poll_interval_ms = 40
        # 接收分帧聚合：累积字节，静默 idle 后整体渲染，避免响应被发回显/断片打断
        self._rx_buf = bytearray()      # 累积的接收字节
        self._rx_last = 0.0             # 上次有数据的时刻(单调时钟)
        self._rx_idle_ms = 120          # 静默判定阈值
        self._apply_language_font()
        self._bind_events()
        self.root.after(self._poll_interval_ms, self._poll_rx)

    # ---------- 翻译 / 注册 ----------
    def _t(self, key, **fmt):
        return i18n.get(self.lang, key, **fmt)

    def _register(self, key, widget):
        self._text_widgets.append((key, widget))

    # ---------- 主题 ----------
    def _setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=P["bg"], foreground=P["text"], font=self.ui_font)
        style.configure("TFrame", background=P["bg"])
        style.configure("Card.TLabelframe", background=P["surface"],
                        foreground=P["muted"])
        style.configure("Card.TLabelframe.Label", background=P["surface"],
                        foreground=P["muted"])
        style.configure("TLabel", background=P["bg"], foreground=P["text"])
        style.configure("Surface.TLabel", background=P["surface"], foreground=P["text"])
        style.configure("Muted.TLabel", background=P["bg"], foreground=P["muted"])
        style.configure("TButton", background=P["secondary"], foreground=P["text"],
                        borderwidth=0, focuscolor=P["secondary"], padding=(8, 4))
        style.map("TButton", background=[("active", "#DFE3EA")])
        style.configure("Primary.TButton", background=P["primary"], foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", P["primary_h"])])
        style.configure("TCombobox", fieldbackground="#fff", background="#fff",
                        foreground=P["text"], arrowcolor=P["muted"])
        style.map("TCombobox", fieldbackground=[("readonly", "#fff"), ("disabled", "#EFF2F5")])
        style.configure("TCheckbutton", background=P["surface"], foreground=P["text"])
        style.map("TCheckbutton", background=[("active", P["surface"])])
        style.configure("TNotebook", background=P["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=P["secondary"], padding=(14, 6),
                        foreground=P["muted"])
        style.map("TNotebook.Tab",
                  background=[("selected", P["surface"])],
                  foreground=[("selected", P["primary"])])
        style.configure("TEntry", fieldbackground="#fff", foreground=P["text"])

    # ---------- 变量 ----------
    def _build_vars(self):
        cfg = self.config.data
        s = cfg["serial"]
        self.port_var = tk.StringVar(value=s["port"])
        self.baud_var = tk.StringVar(value=s["baudrate"])
        self.databits_var = tk.StringVar(value=s["databits"])
        self.stopbits_var = tk.StringVar(value=s["stopbits"])
        self.parity_var = tk.StringVar(value=s["parity"])
        self.flow_var = tk.StringVar(value=s["flow"])
        snd = cfg["send"]
        self.send_type_var = tk.StringVar(value=snd["type"])
        self.send_suffix_var = tk.StringVar(value=snd["suffix"])
        self.send_suffix_var.trace_add("write", lambda *_: self._on_suffix_changed())
        d = cfg["display"]
        self.show_ts = tk.BooleanVar(value=bool(d["timestamp"]))
        self.show_dir = tk.BooleanVar(value=bool(d["direction"]))
        self.show_crlf = tk.BooleanVar(value=bool(d["crlf"]))
        self.show_hex = tk.BooleanVar(value=bool(d["hex"]))
        self.dtr_var = tk.BooleanVar(value=False)   # 勾选=拉低(False)
        self.rts_var = tk.BooleanVar(value=False)   # 勾选=拉低(False)
        self.dtr_var.trace_add("write", lambda *_: self._apply_dtr_rts())
        self.rts_var.trace_add("write", lambda *_: self._apply_dtr_rts())
        self._port_map = {}  # display -> device 映射

    def _on_suffix_changed(self):
        panel = getattr(self, "file_panel", None)
        if panel is not None:
            panel._sync_suffix()

    def _apply_dtr_rts(self):
        self.core.set_dtr(self.dtr_var.get())
        self.core.set_rts(self.rts_var.get())

    # ---------- 事件 / 字体 ----------
    def _apply_language_font(self):
        """把当前 mono_font 应用到输入/输出框（供语言/缩放联动）。"""
        try:
            self.output.configure(font=self.mono_font)
            self.input.configure(font=self.mono_font)
        except tk.TclError:
            pass

    def _bind_events(self):
        """Ctrl+滚轮缩放输入/输出字体；输入框 Enter 发送。"""
        def on_wheel(event):
            if event.state & 0x0004:  # Ctrl
                delta = 1 if event.delta > 0 else -1
                size = max(8, min(28, self.mono_font.cget("size") + delta))
                if size != self.mono_font.cget("size"):
                    self.mono_font.configure(size=size)
                    self._apply_language_font()
                return "break"
            return None

        def on_enter(event):
            self._send()
            return "break"

        for w in (self.output, self.input):
            w.bind("<Control-MouseWheel>", on_wheel)
            w.bind("<Control-Button-4>", lambda e: self._zoom_font(1))
            w.bind("<Control-Button-5>", lambda e: self._zoom_font(-1))
        self.input.bind("<Return>", on_enter)
        self.input.bind("<KP_Enter>", on_enter)

    def _zoom_font(self, delta):
        size = max(8, min(28, self.mono_font.cget("size") + delta))
        if size != self.mono_font.cget("size"):
            self.mono_font.configure(size=size)
            self._apply_language_font()

    def _build_menu(self):
        # 下拉菜单本体（点击「设置」标题按钮时弹出）
        self.settings_menu = tk.Menu(self.root, tearoff=0, font=self.ui_font)
        self.lang_menu = tk.Menu(self.settings_menu, tearoff=0, font=self.ui_font)
        self._lang_var = tk.StringVar(value=self.lang)
        for code in i18n.SUPPORTED_LANGUAGES:
            self.lang_menu.add_radiobutton(
                label=i18n.lang_label(code), value=code, variable=self._lang_var,
                command=lambda c=code: self._set_language(c))
        self.settings_menu.add_cascade(label=self._t("menu_language"), menu=self.lang_menu)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self._t("menu_exit"), command=self._on_close)

        # 顶部标题栏：左侧「设置」大字标题按钮；左间距与「串口配置」标题对齐；下方留出间距
        if getattr(self, "_header_built", None) is None:
            self.header = ttk.Frame(self.root, style="TFrame")
            self.header.pack(side="top", fill="x", padx=0, pady=(0, 6))
            self.settings_btn = ttk.Label(self.header, text=self._t("menu_settings"),
                                          font=self.menu_font, cursor="hand2")
            self.settings_btn.pack(side="left", padx=(10, 6), pady=(8, 6))
            self.settings_btn.bind("<Button-1>", self._popup_settings)
            self._register("menu_settings", self.settings_btn)
            self._header_built = True
        else:
            self.settings_btn.config(text=self._t("menu_settings"))

    def _popup_settings(self, event=None):
        try:
            self.settings_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.settings_menu.grab_release()

    def _build_widgets(self):
        self._build_body()
        self._build_statusbar()

    def _label(self, parent, key, **kw):
        w = ttk.Label(parent, text=self._t(key), **kw)
        self._register(key, w)
        return w

    def _button(self, parent, key, command, style=None, **kw):
        w = ttk.Button(parent, text=self._t(key), command=command)
        if style:
            w.configure(style=style)
        self._register(key, w)
        if kw:
            w.pack(**kw)
        else:
            w.pack()
        return w

    # 串口配置卡
    def _build_serial_card(self, parent):
        box = ttk.LabelFrame(parent, text=self._t("serial_settings"), style="Card.TLabelframe")
        self._register("serial_settings", box)
        box.pack(fill="x", pady=(0, 4))
        self._populate_serial_card(box)

    def _populate_serial_card(self, box):
        # 第一行 Frame：端口 / 波特率 / 数据位（左） + 刷新 / 打开串口（右）
        top = ttk.Frame(box, style="Surface.TFrame")
        top.pack(fill="x", padx=4, pady=(6, 0))
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, width=18)
        self._field_pack(top, "port", self.port_combo)
        self.baud_combo = ttk.Combobox(top, textvariable=self.baud_var, values=BAUDRATES, width=7)
        self._field_pack(top, "baudrate", self.baud_combo)
        self.databits_combo = ttk.Combobox(top, textvariable=self.databits_var, values=DATABITS, width=6)
        self._field_pack(top, "databits", self.databits_combo)

        ops = ttk.Frame(top, style="Surface.TFrame")
        ops.pack(side="right", padx=(8, 0), pady=0)
        refresh = ttk.Button(ops, text=self._t("refresh"), command=self._refresh_ports)
        refresh.pack(fill="x", padx=(0, 2), pady=(0, 4))
        self._register("refresh", refresh)
        self.open_btn = ttk.Button(ops, text=self._t("open"), command=self._toggle_port,
                                   style="Primary.TButton")
        self.open_btn.pack(fill="x", padx=(0, 2))
        self._register("open", self.open_btn)

        # 第二行 Frame：停止位 / 校验位 / 流控
        row1 = ttk.Frame(box, style="Surface.TFrame")
        row1.pack(fill="x", padx=4, pady=(2, 0))
        self.stopbits_combo = ttk.Combobox(row1, textvariable=self.stopbits_var, values=STOPBITS, width=6)
        self._field_pack(row1, "stopbits", self.stopbits_combo)
        self.parity_combo = ttk.Combobox(row1, textvariable=self.parity_var, values=PARITY_OPTIONS, width=9)
        self._field_pack(row1, "parity", self.parity_combo)
        self.flow_combo = ttk.Combobox(row1, textvariable=self.flow_var, values=FLOW_OPTIONS, width=9)
        self._field_pack(row1, "flow", self.flow_combo)

        # 计数行：已发送 / 已接收 / 清零计数
        row2 = ttk.Frame(box, style="Surface.TFrame")
        row2.pack(fill="x", padx=4, pady=(6, 8))
        self.monitor_tx = ttk.Label(row2, text=self._t("tx", n=0), style="Muted.TLabel")
        self.monitor_tx.pack(side="left")
        self.monitor_rx = ttk.Label(row2, text=self._t("rx", n=0), style="Muted.TLabel")
        self.monitor_rx.pack(side="left", padx=(24, 0))
        clear = ttk.Button(row2, text=self._t("clear_counters"), command=self._clear_counters)
        clear.pack(side="right")
        self._register("clear_counters", clear)

    def _field_pack(self, parent, label_key, widget):
        """标签 + 控件横向排布在一个子 Frame 中（替代 grid 版 _field）。"""
        f = ttk.Frame(parent, style="Surface.TFrame")
        f.pack(side="left", padx=(0, 16), pady=(2, 2))
        self._label(f, label_key).pack(side="left", padx=(0, 6))
        widget.pack(side="left")

    def _field(self, box, row, label_col, label_key, widget):
        """标签右对齐 + 控件左对齐，紧凑间距（参考输入框下方「类型」）。"""
        self._label(box, label_key).grid(row=row, column=label_col,
                                         padx=(4, 4), pady=6, sticky="e")
        widget.grid(row=row, column=label_col + 1, padx=(8, 16), pady=6, sticky="w")

    def _build_body(self):
        body = ttk.Frame(self.root, style="TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(2, 5))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        # 左栏（0 列）：串口配置 + 输入输出（监控）
        left = ttk.Frame(body, style="TFrame")
        left.grid(row=0, column=0, sticky="nsew")
        self._build_serial_card(left)
        self._build_monitor(left)

        # 右栏（1 列）：常驻快捷 AT 命令组（占满高度，随窗口拉伸）
        self.sidebar = ttk.Frame(body, style="TFrame", width=320)
        self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(18, 0))
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(0, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.at_panel = AtPanel(self.sidebar, self)
        self.at_panel.grid(row=0, column=0, sticky="nsew")
        self._tab_at = self.at_panel

    def _build_monitor(self, parent):
        # 输出区（默认白底，数据统一黑色）
        out = ttk.LabelFrame(parent, text=self._t("output"), style="Card.TLabelframe")
        self._register("output", out)
        out.pack(fill="both", expand=True, padx=0, pady=4)
        self.output = scrolledtext.ScrolledText(
            out, font=self.mono_font, wrap="word",
            bg="#FFFFFF", fg="#1B2733", insertbackground="#1B2733",
            relief="flat", borderwidth=1, state="disabled")
        self.output.pack(fill="both", expand=True, padx=6, pady=6)
        self.output.tag_configure("tx", foreground="#1B2733")
        self.output.tag_configure("rx", foreground="#1B2733")

        # 输入区（高度=2 行，字体放大）
        inp = ttk.LabelFrame(parent, text=self._t("input"), style="Card.TLabelframe")
        self._register("input", inp)
        inp.pack(fill="x", padx=0, pady=4)
        self.input = scrolledtext.ScrolledText(
            inp, font=self.mono_font, wrap="none",
            bg="#FFFFFF", fg="#1B2733", insertbackground="#1B2733",
            relief="solid", borderwidth=1, height=2)
        self.input.pack(fill="both", expand=True, padx=6, pady=6)

        # 发送行（第 1 行）：类型 / 后缀 / 发送 / 清空
        bar = ttk.Frame(inp)
        bar.pack(fill="x", padx=6, pady=(0, 2))
        ttk.Label(bar, text=self._t("send_type"), style="Muted.TLabel").pack(side="left", padx=(4, 4))
        ttk.Combobox(bar, textvariable=self.send_type_var, values=codec.SEND_TYPES,
                     width=7, state="readonly").pack(side="left")
        ttk.Label(bar, text=self._t("send_suffix"), style="Muted.TLabel").pack(side="left", padx=(8, 4))
        ttk.Combobox(bar, textvariable=self.send_suffix_var, values=codec.SUFFIXES,
                     width=8, state="readonly").pack(side="left")
        send_btn = ttk.Button(bar, text=self._t("send"), command=self._send, style="Primary.TButton")
        send_btn.pack(side="right", padx=(12, 2))
        self._register("send", send_btn)
        clr_in = ttk.Button(bar, text=self._t("clear_input"), command=self._clear_input)
        clr_in.pack(side="right", padx=(8, 0))
        clr_out = ttk.Button(bar, text=self._t("clear_output"), command=self._clear_output)
        clr_out.pack(side="right", padx=(8, 0))

        # 显示选项 + DTR/RTS（第 2 行，单独一行，换行显示）
        opt = ttk.Frame(inp)
        opt.pack(fill="x", padx=6, pady=(2, 6))
        # 显示选项行：显示选项(左) + 分隔线 + DTR/RTS(右)，规整分组
        for key, var in [("display_timestamp", self.show_ts), ("display_direction", self.show_dir),
                         ("display_crlf", self.show_crlf), ("display_hex", self.show_hex)]:
            chk = tk.Checkbutton(opt, text=self._t(key), variable=var,
                                 font=self.ui_font, bg=P["surface"], fg=P["text"],
                                 activebackground=P["surface"], activeforeground=P["text"],
                                 selectcolor=P["surface"], highlightthickness=0, bd=0)
            self._register(key, chk)
            chk.pack(side="left", padx=(6, 0))
        ttk.Separator(opt, orient="vertical").pack(side="left", fill="y", padx=(12, 12), pady=2)
        for key, var in [("dtr", self.dtr_var), ("rts", self.rts_var)]:
            chk = tk.Checkbutton(opt, text=self._t(key), variable=var,
                                 font=self.ui_font, bg=P["surface"], fg=P["text"],
                                 activebackground=P["surface"], activeforeground=P["text"],
                                 selectcolor=P["surface"], highlightthickness=0, bd=0)
            self._register(key, chk)
            chk.pack(side="left", padx=(6, 0))

        # 文件发送行（输入框下方，整行）
        self.file_panel = FileSendPanel(parent, self)
        self.file_panel.pack(fill="x", padx=0, pady=(4, 4))

        # Log 保存行（文件发送下方，整行，去掉外层线框）
        self._build_log_row(parent)

    def _build_log_row(self, parent):
        row = ttk.Frame(parent, style="TFrame")
        row.pack(fill="x", padx=0, pady=(2, 4))
        ttk.Label(row, text=self._t("log_config"), style="Muted.TLabel").pack(side="left", padx=(2, 6))
        self.log_path_var = tk.StringVar(value=self._log_path or "")
        ent = ttk.Entry(row, textvariable=self.log_path_var, state="readonly")
        ent.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=4)
        btn_sel = ttk.Button(row, text=self._t("log_select"), command=self._choose_log)
        btn_sel.pack(side="left", padx=(0, 4))
        self._register("log_select", btn_sel)
        btn_start = ttk.Button(row, text=self._t("log_start"), command=self._log_start)
        btn_start.pack(side="left", padx=(0, 4))
        self._register("log_start", btn_start)
        btn_stop = ttk.Button(row, text=self._t("log_stop"), command=self._log_stop)
        btn_stop.pack(side="left", padx=(0, 4))
        self._register("log_stop", btn_stop)
        self.log_state_lbl = ttk.Label(row, text=self._t("log_off"), style="Muted.TLabel")
        self.log_state_lbl.pack(side="left", padx=(0, 6))

    def _build_statusbar(self):
        bar = ttk.Frame(self.root, style="TFrame")
        bar.pack(side="bottom", fill="x")

        left = ttk.Frame(bar)
        left.pack(side="left", padx=10, pady=4)
        self.dot = tk.Canvas(left, width=12, height=12, bg=P["bg"], highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 6))
        self.status_label = ttk.Label(left, text=self._t("status_idle"), style="Muted.TLabel")
        self.status_label.pack(side="left")
        self.connect_summary = ttk.Label(left, text="--", style="Muted.TLabel")
        self.connect_summary.pack(side="left", padx=(12, 0))

        right = ttk.Frame(bar)
        right.pack(side="right", padx=10)
        self.status_tx = ttk.Label(right, text="TX 0", style="Muted.TLabel")
        self.status_tx.pack(side="left", padx=(0, 12))
        self.status_rx = ttk.Label(right, text="RX 0", style="Muted.TLabel")
        self.status_rx.pack(side="left", padx=(0, 12))
        self.tz_label = ttk.Label(right, text="UTC+8", style="Muted.TLabel")
        self.tz_label.pack(side="left")

    def _set_language(self, code):
        self.lang = code
        self._lang_var.set(code)
        self._build_menu()
        self._apply_language()
        self._update_counters()
        self._update_status()
        self.config.data["language"] = code

    def _apply_language(self):
        self.root.title(self._t("app_title"))
        for key, widget in self._text_widgets:
            try:
                if isinstance(widget, ttk.LabelFrame):
                    widget.configure(text=self._t(key))
                elif isinstance(widget, (ttk.Label, ttk.Button, ttk.Checkbutton, tk.Checkbutton)):
                    widget.configure(text=self._t(key))
            except tk.TclError:
                pass
        self.open_btn.configure(text=self._t("close") if self.core.is_open else self._t("open"))
        self._sync_log_state()

    def _sync_log_state(self):
        self.log_state_lbl.config(text=self._t("log_on") if self.logger.active else self._t("log_off"))

    # ---------- 串口操作 ----------
    def _refresh_ports(self):
        self._port_map = {}
        displays = []
        for device, display in self.core.list_ports():
            self._port_map[display] = device
            displays.append(display)
        self.port_combo["values"] = displays
        cur = self.port_var.get()
        if cur not in displays:
            matched = next((d for d, dev in self._port_map.items()
                            if dev == cur or d == cur), None)
            self.port_var.set(matched if matched else "")
        # 刷新成功：端口框未选中时自动选中第一个，并在状态栏提示
        if displays and not self.port_var.get():
            self.port_var.set(displays[0])
        if displays:
            self._flash_status(self._t("refresh_ok", n=len(displays)))

    def _gather_params(self):
        baud = int(self.baud_var.get())
        data_bits = int(self.databits_var.get())
        parity = PARITY_MAP[self.parity_var.get()]
        stop_bits = float(self.stopbits_var.get())
        rtscts, xonxoff = FLOW_MAP[self.flow_var.get()]
        return baud, data_bits, parity, stop_bits, rtscts, xonxoff

    def _toggle_port(self):
        if self.core.is_open:
            self.core.close()
            self._status_error = None
            self._update_status()
            return
        display = self.port_var.get().strip()
        if not display:
            self._append_input_msg(self._t("no_port") + "\n")
            return
        port = self._port_map.get(display, display)
        try:
            baud, data_bits, parity, stop_bits, rtscts, xonxoff = self._gather_params()
            self.core.open(port, baudrate=baud, bytesize=data_bits, parity=parity,
                           stopbits=stop_bits, rtscts=rtscts, xonxoff=xonxoff)
            self._apply_dtr_rts()
            self._status_error = None
            self._update_status()
        except Exception as exc:
            self._append_input_msg(self._t("open_fail", e=exc) + "\n")
            self._set_status_error(str(exc))

    def _send(self):
        text = self.input.get("1.0", "end-1c")
        self.send_text(text)

    def send_text(self, text):
        raw = codec.encode(text, self.send_type_var.get(), self.send_suffix_var.get())
        return self.send_bytes(raw)

    def send_bytes(self, raw):
        if not raw:
            return 0
        if not self.core.is_open:
            self._append_input_msg(self._t("no_port") + "\n")
            return 0
        try:
            n = self.core.write(raw)
            self._append_line("TX", raw)
            self._rx_last = time.monotonic()
            return n
        except Exception as exc:
            self._append_input_msg(self._t("send_fail", e=exc) + "\n")
            return 0

    # ---------- 接收轮询 ----------
    def _poll_rx(self):
        import time as _t
        try:
            got = False
            for kind, payload in self.core.drain():
                if kind == SerialCore.RX_DATA:
                    self._rx_buf.extend(payload)
                    got = True
                elif kind == SerialCore.RX_ERROR:
                    self._flush_rx()
                    self._append_input_msg(self._t("serial_error", e=payload) + "\n")
                    self._set_status_error(str(payload))
                elif kind == SerialCore.RX_CLOSED:
                    self._flush_rx()
                    self._update_status()
            if got:
                self._rx_last = _t.monotonic()
            # 静默超时 → 整体渲染这一帧
            if self._rx_buf and (_t.monotonic() - self._rx_last) * 1000 >= self._rx_idle_ms:
                self._flush_rx()
        finally:
            self._update_counters()
            self.root.after(self._poll_interval_ms, self._poll_rx)

    def _append_interp(self, text):
        """在输出区追加纯文本（禁用 insert 状态，辅助函数内部处理）。"""
        try:
            self.output.configure(state="normal")
            self.output.insert("end", text)
        finally:
            self.output.configure(state="disabled")

    def _render_frame(self, direction, raw):
        """渲染一条完整消息（TX 或聚合后的 RX），统一黑色。"""
        now = time.time()
        dt = datetime.datetime.now()
        ts = "[%s:%03d]" % (dt.strftime("%Y-%m-%d_%H:%M:%S"), dt.microsecond // 1000)
        parts = []
        if self.show_ts.get():
            parts.append(ts)
        if self.show_dir.get():
            parts.append(direction)
        body = codec.decode_display(raw, self.show_hex.get())
        if self.show_crlf.get():
            body = codec.escape_control(body)
        if body:
            parts.append(body)
        line = "  ".join(parts) + "\n"
        try:
            self.output.configure(state="normal")
            self.output.insert("end", line)
            self.output.see("end")
        finally:
            self.output.configure(state="disabled")
        if self.logger.active and direction in ("TX", "RX"):
            self.logger.log(direction, now * 1000, body)

    def _flush_rx(self):
        """若接收缓冲非空，按换行拆分为多条 RX（每行独立时间戳）并清空。"""
        if self._rx_buf:
            data = bytes(self._rx_buf)
            self._rx_buf.clear()
            while True:
                idx = data.find(b"\n")
                if idx < 0:
                    if data:
                        self._render_frame("RX", data)
                    break
                self._render_frame("RX", data[:idx + 1])
                data = data[idx + 1:]

    def _append_line(self, direction, raw):
        """TX 入口：先冲刷未渲染的 RX 缓冲，避免 TX 插到 RX 中间。"""
        if direction == "TX":
            self._flush_rx()
        self._render_frame(direction, raw)

    def _append_input_msg(self, text):
        try:
            self.input.configure(state="normal")
            self.input.insert("end", text)
            self.input.see("end")
        finally:
            self.input.configure(state="normal")

    # ---------- 状态 ----------
    def _set_dot(self, color):
        self.dot.delete("all")
        self.dot.create_oval(2, 2, 11, 11, fill=color, outline=color)

    def _set_status_error(self, msg):
        self._status_error = msg
        self._set_dot(P["danger"])
        self.status_label.config(text=self._t("status_error", e=msg))
        self.open_btn.configure(text=self._t("open"))

    def _update_status(self):
        if self.core.is_open:
            self._set_dot(P["success"])
            self.status_label.config(text=self._t("status_connected"))
            device = self._port_map.get(self.port_var.get(), self.port_var.get())
            summary = (f"{device} · {self.baud_var.get()}-{self.databits_var.get()}-"
                       f"{PARITY_MAP[self.parity_var.get()]}-{self.stopbits_var.get()}")
            self.connect_summary.config(text=summary)
            self.open_btn.configure(text=self._t("close"))
        else:
            self._set_dot(P["danger"] if self._status_error else P["idle"])
            self.status_label.config(
                text=self._t("status_error", e=self._status_error) if self._status_error
                else self._t("status_disconnected"))
            self.connect_summary.config(text="--")
            self.open_btn.configure(text=self._t("open"))

    def _flash_status(self, msg, ms=2200):
        """状态栏临时显示一条消息，几秒后恢复为真实连接状态。"""
        try:
            if getattr(self, "_flash_job", None):
                self.root.after_cancel(self._flash_job)
        except tk.TclError:
            pass
        self.status_label.config(text=msg)
        self._flash_job = self.root.after(ms, self._update_status)

    def _update_counters(self):
        tx, rx = self.core.tx_count, self.core.rx_count
        self.monitor_tx.config(text=self._t("tx", n=tx) + " " + self._t("byte"))
        self.monitor_rx.config(text=self._t("rx", n=rx) + " " + self._t("byte"))
        self.status_tx.config(text=f"TX {tx}")
        self.status_rx.config(text=f"RX {rx}")

    # ---------- 计数 / 清空 ----------
    def _clear_counters(self):
        self.core.reset_counters()
        self._update_counters()

    def _clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _clear_input(self):
        self.input.delete("1.0", "end")

    # ---------- Log ----------
    def _choose_log(self):
        path = filedialog.asksaveasfilename(
            title=self._t("log_select"), defaultextension=".log",
            initialfile=f"ecom_{datetime.datetime.now():%Y%m%d_%H%M%S}.log")
        if path:
            self._log_path = path
            self._log_path_var.set(path)
            self.config.set("log", "path", path)

    def _log_start(self):
        if not self._log_path:
            self._choose_log()
        if not self._log_path:
            return
        if self.logger.start(self._log_path):
            self._sync_log_state()
        else:
            self._append_input_msg(self._t("log_off") + "\n")

    def _log_stop(self):
        if self.logger.active:
            self.logger.stop()
            self._sync_log_state()

    # ---------- 关闭 ----------
    def _bind_close(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _save_config(self):
        cfg = self.config.data
        cfg["serial"].update({
            "port": self.port_var.get(), "baudrate": self.baud_var.get(),
            "databits": self.databits_var.get(), "stopbits": self.stopbits_var.get(),
            "parity": self.parity_var.get(), "flow": self.flow_var.get()})
        cfg["display"].update({
            "timestamp": bool(self.show_ts.get()), "direction": bool(self.show_dir.get()),
            "crlf": bool(self.show_crlf.get()), "hex": bool(self.show_hex.get())})
        cfg["send"].update({
            "type": self.send_type_var.get(), "suffix": self.send_suffix_var.get()})
        cfg["language"] = self.lang
        try:
            self.config.save()
        except OSError:
            pass

    def _on_close(self):
        try:
            self.logger.stop()
        finally:
            self._save_config()
            self.core.close()
            self.root.destroy()


def run():
    root = tk.Tk()
    EcomApp(root, language="zh")
    root.mainloop()
