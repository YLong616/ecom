"""AT 命令面板（常驻右侧边栏）—— 分页版 v3。

每页 PAGE_SIZE 行 AT list，每行组件（从左到右）：
    序号 | 选择复选 | 输入框(可编辑) | HEX复选 | Enter复选 | 发送按钮

交互特性：
  - 头部：config 下拉(可输入) + 保存 + 一键清空（清空所有行输入的 AT 命令文本）。
  - 表头行（首行上方）：全选(行) 全选(HEX) 全选(Enter)，各自联动本页。
  - 分页控件：上一页 | 页码输入框(跳转) | 下一页 | 添加下一页(+PAGE_SIZE 空行)
    | 第 x / n 页。
  - 底部：循环次数 + 间隔(ms) + Run + Stop + 当前轮次显示。

数据：``_all_data`` 保存所有页的命令行（persist 时只存非空 text 行）。
约定：``app._t`` / ``app._register`` / ``app.send_bytes``。
"""

from __future__ import annotations

import json
import math
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk

from . import codec

CONFIG_EXT = ".json"
LOOP_TIMES_MAX = 9999
PAGE_SIZE = 22          # 每页展示 22 行 AT list
MIN_DELAY_MS = 0
MAX_DELAY_MS = 3600000  # 上限 60min，防误输
EMPTY_ROW = {"txt": "", "hex": False, "ent": False}
DEFAULT_DELAY_MS = 300


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def configs_dir() -> Path:
    d = project_root() / "configs"
    try:
        d.mkdir(parents=True, exist_ok=True)
        return d
    except OSError:
        home = Path.home() / ".ecom" / "configs"
        home.mkdir(parents=True, exist_ok=True)
        return home


class AtPanel(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.config_name = tk.StringVar()
        self.loop_times_var = tk.IntVar(value=0)
        self.delay_var = tk.IntVar(value=DEFAULT_DELAY_MS)
        self.select_all_var = tk.BooleanVar(value=False)       # 行全选
        self.select_all_hex_var = tk.BooleanVar(value=False)   # HEX 全选
        self.select_all_enter_var = tk.BooleanVar(value=False)  # Enter 全选
        self.page_var = tk.StringVar(value="1")
        # 分页
        self._page = 1              # 当前页（1-based）
        self._all_data: list[dict] = []   # 全部分页数据（空行也占位，保证行位）
        self._pages: list[dict] = []      # 当前页数据（PAGE_SIZE 个 row）
        self._row_vars: list[dict] = []   # 当前页每行的 tk 变量
        # 循环状态
        self._loop_job = None
        self._loop_running = False
        self._loop_round = 0
        self._ensure_styles()
        self._build()
        self._refresh_configs()

    def _ensure_styles(self):
        try:
            style = ttk.Style(self)
            style.configure("Run.TButton", background="#1E9E4A", foreground="#ffffff",
                            borderwidth=0, focuscolor="#1E9E4A", padding=(12, 3))
            style.map("Run.TButton", background=[("active", "#17833d")])
            style.configure("Stop.TButton", background="#C6352F", foreground="#ffffff",
                            borderwidth=0, focuscolor="#C6352F", padding=(12, 3))
            style.map("Stop.TButton", background=[("active", "#a92f2a")])
        except Exception:
            pass

    # ---------- 构建 ----------
    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(8, 4))
        self.config_combo = ttk.Combobox(
            top, textvariable=self.config_name, state="normal", width=10)
        self.config_combo.pack(side="left")
        self.config_combo.bind("<<ComboboxSelected>>", lambda e: self._load_config())
        self._btn(top, "at_save", self._save_config).pack(side="left", padx=(6, 0))
        self._btn(top, "at_clear_all", self._clear_all).pack(side="left", padx=(4, 0))

        # --- 列表区（表头 + 数据行共用同一 body grid，列几何一致）---
        self._list_frame = ttk.Frame(self)
        self._list_frame.pack(side="top", fill="x", padx=8, pady=(4, 0))

        self._body = ttk.Frame(self._list_frame)
        self._body.grid(row=0, column=0, sticky="nsew")
        self._list_frame.rowconfigure(0, weight=1)
        self._list_frame.columnconfigure(0, weight=1)
        for c, w in [(0, 0), (1, 0), (2, 1), (3, 0), (4, 0), (5, 0)]:
            self._body.columnconfigure(c, weight=w)

        # 表头为 body 的 row0，与数据行同一列几何，保证 HEX/Enter 列对齐
        self._grid_header()

        # 分页条（底部，先于底部控制放置 so 它出现在列表之下、控制之上）
        self.build_pager()
        # 底部控制（最底部）
        self.build_ctrl()


    def _grid_header(self):
        """表头（body 的 row0）：序号 | 行全选 | 输入框表头 | HEX全选 | Enter全选 | 发送表头。
        与数据行共用 body 的 grid，保证各列（尤其 HEX/Enter）严格对齐。"""
        b = self._body
        ttk.Label(b, text="#", style="Muted.TLabel", width=3,
                  anchor="center").grid(row=0, column=0, padx=(0, 2), pady=1)

        master = tk.Checkbutton(
            b, text=self.app._t("at_select_all"),
            variable=self.select_all_var, command=self._toggle_select_all,
            bg=self._bg(), fg=self._fg(), activebackground=self._bg(),
            activeforeground=self._fg(), selectcolor=self._bg(),
            highlightthickness=0, bd=0, anchor="w")
        master.grid(row=0, column=1, sticky="w", padx=(0, 2), pady=1)

        ttk.Label(b, text=" ", width=8).grid(row=0, column=2, pady=1)

        hexm = tk.Checkbutton(
            b, text="",
            variable=self.select_all_hex_var, command=self._toggle_select_all_hex,
            bg=self._bg(), fg=self._fg(), activebackground=self._bg(),
            activeforeground=self._fg(), selectcolor=self._bg(),
            highlightthickness=0, bd=0, anchor="w")
        hexm.grid(row=0, column=3, sticky="w", padx=(0, 2), pady=1)

        entm = tk.Checkbutton(
            b, text="",
            variable=self.select_all_enter_var, command=self._toggle_select_all_enter,
            bg=self._bg(), fg=self._fg(), activebackground=self._bg(),
            activeforeground=self._fg(), selectcolor=self._bg(),
            highlightthickness=0, bd=0, anchor="w")
        entm.grid(row=0, column=4, sticky="w", padx=(0, 2), pady=1)

        ttk.Label(b, text=" ", width=6).grid(row=0, column=5, pady=1)

    def _render_page(self):
        """渲染当前页的 PAGE_SIZE 行（保留 row0 表头，只重建数据行）。"""
        for w in list(self._body.grid_slaves()):
            try:
                if int(w.grid_info()["row"]) >= 1:
                    w.destroy()
            except (KeyError, ValueError, tk.TclError):
                w.destroy()
        self._row_vars = []
        for i in range(PAGE_SIZE):
            row = self._pages[i] if i < len(self._pages) else dict(EMPTY_ROW)
            self._build_row(i, row)

    def _build_row(self, idx, row):
        # 序号
        num = ttk.Label(self._body, text=str(idx + 1), style="Muted.TLabel",
                        anchor="center", width=3)
        num.grid(row=idx + 1, column=0, sticky="w", padx=(0, 2), pady=1)
        # 选择复选
        selvar = tk.BooleanVar(value=bool(row.get("sel", False)))
        chk = tk.Checkbutton(
            self._body, variable=selvar,
            bg=self._bg(), fg=self._fg(), activebackground=self._bg(),
            activeforeground=self._fg(), selectcolor=self._bg(),
            highlightthickness=0, bd=0)
        chk.grid(row=idx + 1, column=1, sticky="w", padx=(0, 2), pady=1)
        # 输入框
        txtvar = tk.StringVar(value=row.get("txt", ""))
        entry = ttk.Entry(self._body, textvariable=txtvar)
        entry.grid(row=idx + 1, column=2, sticky="ew", padx=(0, 4), pady=1)
        # HEX 复选
        hexvar = tk.BooleanVar(value=bool(row.get("hex", False)))
        hexc = tk.Checkbutton(
            self._body, text=self.app._t("at_hex"), variable=hexvar,
            bg=self._bg(), fg=self._fg(), activebackground=self._bg(),
            activeforeground=self._fg(), selectcolor=self._bg(),
            highlightthickness=0, bd=0)
        hexc.grid(row=idx + 1, column=3, sticky="w", padx=(0, 2), pady=1)
        # Enter 复选
        entvar = tk.BooleanVar(value=bool(row.get("ent", False)))
        entc = tk.Checkbutton(
            self._body, text=self.app._t("at_enter"), variable=entvar,
            bg=self._bg(), fg=self._fg(), activebackground=self._bg(),
            activeforeground=self._fg(), selectcolor=self._bg(),
            highlightthickness=0, bd=0)
        entc.grid(row=idx + 1, column=4, sticky="w", padx=(0, 2), pady=1)
        # 发送按钮（独立，与选择复选无关）
        btn = ttk.Button(self._body, text=self.app._t("at_send"),
                         width=6, command=lambda i=idx: self._send_row(i))
        btn.grid(row=idx + 1, column=5, sticky="e", pady=1)
        self._register("at_send", btn)  # 用真实 i18n key，避免语言切换时被覆盖为伪 key

        self._row_vars.append({"sel": selvar, "txt": txtvar,
                               "hex": hexvar, "ent": entvar})

    def _toggle_select_all(self):
        val = self.select_all_var.get()
        for v in self._row_vars:
            v["sel"].set(val)

    def _toggle_select_all_hex(self):
        val = self.select_all_hex_var.get()
        for v in self._row_vars:
            v["hex"].set(val)

    def _toggle_select_all_enter(self):
        val = self.select_all_enter_var.get()
        for v in self._row_vars:
            v["ent"].set(val)

    def _sync_page_vars(self):
        """把当前页 tk 变量写回 self._pages（供保存/分页切页用）。"""
        for i, v in enumerate(self._row_vars):
            if i < len(self._pages):
                pass
        # 直接由 _pages 驱动渲染，这里无需回填

    # ---------- 分页 ----------
    def _total_nonempty(self):
        return sum(1 for r in self._all_data if r.get("txt", "").strip())

    def _total_pages(self):
        # 分页按"总行数(含空行)"计算：每页 PAGE_SIZE 行，空行也占位。
        return max(1, math.ceil(len(self._all_data) / PAGE_SIZE))

    def _sync_all_from_pages(self):
        """把当前已渲染行(_row_vars)的实时值写回 _all_data 的对应切片。"""
        start = (self._page - 1) * PAGE_SIZE
        for i, v in enumerate(self._row_vars):
            idx = start + i
            while len(self._all_data) <= idx:
                self._all_data.append(dict(EMPTY_ROW))
            self._all_data[idx] = {"txt": v["txt"].get(),
                                   "hex": bool(v["hex"].get()),
                                   "ent": bool(v["ent"].get())}
        self._normalize_all_data()

    def _normalize_all_data(self):
        """确保 _all_data 至少 1 页、总长度为 PAGE_SIZE 的倍数。"""
        while len(self._all_data) < PAGE_SIZE:
            self._all_data.append(dict(EMPTY_ROW))
        if len(self._all_data) % PAGE_SIZE:
            for _ in range(PAGE_SIZE - len(self._all_data) % PAGE_SIZE):
                self._all_data.append(dict(EMPTY_ROW))

    def _current_page_slice(self):
        start = (self._page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        # 从 _all_data 切片，不足补空行
        page = [dict(r) for r in self._all_data[start:end]]
        while len(page) < PAGE_SIZE:
            page.append(dict(EMPTY_ROW))
        return page

    def _refresh_page(self):
        """渲染当前页数据切片（不写回数据源，避免覆盖待渲染页）。"""
        self._pages = self._current_page_slice()
        self._render_page()
        self._update_pager()

    def _update_pager(self):
        n = self._total_pages()
        if self._page > n:
            self._page = n
        self.page_var.set(str(self._page))
        self.page_lbl.configure(
            text=self.app._t("at_page_of", p=self._page, n=n))
        self.prev_btn.configure(state="normal" if self._page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self._page < n else "disabled")

    def _go_prev(self):
        if self._page > 1:
            self._sync_all_from_pages()   # 先存回旧页
            self._page -= 1
            self._refresh_page()

    def _go_next(self):
        n = self._total_pages()
        if self._page < n:
            self._sync_all_from_pages()   # 先存回旧页
            self._page += 1
            self._refresh_page()

    def _goto_page(self):
        try:
            p = int(self.page_var.get())
        except (ValueError, tk.TclError):
            messagebox.showinfo(self.app._t("at_page_goto"), self.app._t("at_page_bad"))
            return
        n = self._total_pages()
        if p < 1 or p > n:
            messagebox.showinfo(self.app._t("at_page_goto"), self.app._t("at_page_bad"))
            self.page_var.set(str(self._page))
            return
        if p != self._page:
            self._sync_all_from_pages()   # 先存回旧页
            self._page = p
        self._refresh_page()

    def _add_page(self):
        """追加 PAGE_SIZE 空行，并跳到新页（这样可操作下一页）。"""
        self._sync_all_from_pages()
        self._all_data.extend([dict(EMPTY_ROW) for _ in range(PAGE_SIZE)])
        self._normalize_all_data()
        # 跳到新增的这一页，便于用户直接操作
        new_total = self._total_pages()
        self._page = new_total
        self._pages = self._current_page_slice()
        self._render_page()
        self._update_pager()

    # ---------- configs/ 文件操作 ----------
    def _list_config_names(self):
        return sorted(f.stem for f in configs_dir().glob(f"*{CONFIG_EXT}"))

    def _read_config(self, name):
        f = configs_dir() / f"{name}{CONFIG_EXT}"
        if not f.exists():
            return []
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_config(self, name, commands):
        if not name or "/" in name or "\\" in name or name != name.strip():
            return False
        f = configs_dir() / f"{name}{CONFIG_EXT}"
        try:
            f.write_text(json.dumps(commands, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            return True
        except OSError:
            return False

    def _refresh_configs(self, select=None, keep=True):
        names = self._list_config_names()
        self.config_combo["values"] = names
        if select is None:
            select = self.config_name.get()
        if select and select in names:
            self.config_name.set(select)
            self._load_config()
        elif names and not select and keep:
            self.config_name.set(names[0])
            self._load_config()
        elif not select:
            self._all_data = [dict(EMPTY_ROW) for _ in range(PAGE_SIZE)]
            self._page = 1
            self._pages = self._current_page_slice()
            self._render_page()
            self._update_pager()

    def _load_config(self):
        name = self.config_name.get().strip()
        data = self._read_config(name) if name else []
        rows = []
        for item in data:
            if isinstance(item, str):
                rows.append({"txt": item, "hex": False, "ent": False})
            elif isinstance(item, dict):
                rows.append({"txt": str(item.get("text", item.get("txt", ""))),
                             "hex": bool(item.get("hex", False)),
                             "ent": bool(item.get("ent", False))})
        # 铺成 _all_data（含空行占位）
        self._all_data = []
        for r in rows:
            self._all_data.append({"txt": r["txt"], "hex": r["hex"], "ent": r["ent"]})
        self._normalize_all_data()
        self._page = 1
        self._pages = self._current_page_slice()
        self._render_page()
        self._update_pager()

    def _clear_all(self):
        """一键清空：清空所有页输入框里的 AT 命令文本（保留勾选状态+HEX/Enter状态）。"""
        if messagebox.askyesno(self.app._t("at_clear_all"),
                               self.app._t("at_clear_confirm")):
            # 只改 txt 绑定变量，不重建 body，保留 sel/hex/ent
            for v in self._row_vars:
                v["txt"].set("")
            self._sync_all_from_pages()  # 已清空的 txt 回写 _all_data
            for r in self._all_data:
                r["txt"] = ""
            self._pages = self._current_page_slice()
            self._update_pager()

    # ---------- 发送 ----------
    def _encode_row(self, v):
        t = v["txt"].get()
        if v["hex"].get():
            return codec.encode(t, "HEX", "None")
        return codec.encode(t, "ASCII",
                            "CR-LF" if v["ent"].get() else "None")

    def _send_row(self, idx):
        v = self._row_vars[idx]
        t = v["txt"].get().strip()
        if not t:
            return 0
        raw = self._encode_row(v)
        return self.app.send_bytes(raw)

    # ---------- 循环发送 ----------
    def _norm_loop_times(self):
        try:
            val = int(self.loop_times_var.get())
        except (ValueError, tk.TclError):
            val = 0
        self.loop_times_var.set(max(0, min(val, LOOP_TIMES_MAX)))

    def _norm_delay(self):
        try:
            val = int(self.delay_var.get())
        except (ValueError, tk.TclError):
            val = 0
        self.delay_var.set(max(MIN_DELAY_MS, min(val, MAX_DELAY_MS)))

    def _get_delay(self):
        self._norm_delay()
        return max(MIN_DELAY_MS, int(self.delay_var.get()))

    def _selected_rows(self):
        return [self._row_vars[i] for i, v in enumerate(self._row_vars)
                if v["sel"].get()]

    def _run_loop(self):
        if self._loop_running:
            return
        rows = self._selected_rows()
        if not rows:
            messagebox.showinfo(self.app._t("at_run"), self.app._t("at_no_cmd"))
            return
        self._norm_loop_times()
        times = self.loop_times_var.get()
        self._loop_running = True
        self._loop_rows = rows
        self._loop_idx = 0
        self._loop_round = 1
        # 循环次数为空/0 时默认按 1 次执行，避免无限循环不可控
        self._loop_target = times if times > 0 else 1
        self._loop_delay = self._get_delay()
        self._update_run_btn()
        self._loop_step()

    def _update_run_btn(self):
        """运行时把轮次显示在 Run 按钮上；结束后恢复为 Run。"""
        if self._loop_running:
            self.run_btn.configure(text=str(self._loop_round))
        else:
            self.run_btn.configure(text=self.app._t("at_run"))

    def _loop_step(self):
        if not self._loop_running:
            return
        v = self._loop_rows[self._loop_idx % len(self._loop_rows)]
        t = v["txt"].get().strip()
        if t:
            self.app.send_bytes(self._encode_row(v))
        self._loop_idx += 1
        if self._loop_idx % len(self._loop_rows) == 0:
            # 完成一轮
            if self._loop_round >= self._loop_target:
                self._stop_loop()
                return
            self._loop_round += 1
            self._update_run_btn()
        self._loop_job = self.after(self._loop_delay, self._loop_step)

    def _stop_loop(self):
        self._loop_running = False
        if self._loop_job:
            try:
                self.after_cancel(self._loop_job)
            except Exception:
                pass
            self._loop_job = None
        self._update_run_btn()

    # ---------- 底部控制 ----------
    def build_ctrl(self):
        """底部：循环次数 + 间隔ms + Run + Stop + 当前轮次。"""
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=8, pady=(4, 2))
        ttk.Label(ctrl, text=self.app._t("at_loop_times"),
                  style="Muted.TLabel").pack(side="left")
        self.loop_spin = ttk.Spinbox(
            ctrl, from_=0, to=LOOP_TIMES_MAX, textvariable=self.loop_times_var,
            width=5, command=self._norm_loop_times)
        self.loop_spin.pack(side="left", padx=(4, 8))
        self.loop_spin.bind("<KeyRelease>", lambda e: self._norm_loop_times())

        ttk.Label(ctrl, text=self.app._t("at_delay"),
                  style="Muted.TLabel").pack(side="left")
        self.delay_spin = ttk.Spinbox(
            ctrl, from_=MIN_DELAY_MS, to=MAX_DELAY_MS, textvariable=self.delay_var,
            width=7, command=self._norm_delay)
        self.delay_spin.pack(side="left", padx=(4, 8))
        self.delay_spin.bind("<KeyRelease>", lambda e: self._norm_delay())

        self.run_btn = ttk.Button(ctrl, text=self.app._t("at_run"),
                                  command=self._run_loop, style="Run.TButton",
                                  width=4)
        self.run_btn.pack(side="left", padx=(0, 4))
        self._register("at_run", self.run_btn)
        self.stop_btn = ttk.Button(ctrl, text=self.app._t("at_stop"),
                                   command=self._stop_loop, style="Stop.TButton",
                                   width=4)
        self.stop_btn.pack(side="left", padx=(0, 8))
        self._register("at_stop", self.stop_btn)

    # ---------- 分页控件 ----------
    def build_pager(self):
        """分页条：上一页 | 页码输入框 | 下一页 | 添加下一页 | 第 x/n 页。"""
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=(8, 2))
        self.prev_btn = self._btn(bar, "at_prev", self._go_prev)
        self.prev_btn.pack(side="left")
        self.next_btn = self._btn(bar, "at_next", self._go_next)
        self.next_btn.pack(side="left", padx=(4, 0))
        ttk.Label(bar, text=" ", style="Muted.TLabel").pack(side="left",
                                                            padx=(8, 0))
        self.page_entry = ttk.Entry(bar, textvariable=self.page_var, width=5)
        self.page_entry.pack(side="left")
        self.page_entry.bind("<Return>", lambda e: self._goto_page())
        go = self._btn(bar, "at_page_goto", self._goto_page)
        go.pack(side="left", padx=(4, 0))
        self.page_lbl = ttk.Label(bar, text="", style="Muted.TLabel")
        self.page_lbl.pack(side="left", padx=(10, 0))
        self._btn(bar, "at_add_page", self._add_page).pack(side="right")

    def _btn(self, parent, key, command):
        w = ttk.Button(parent, text=self.app._t(key), command=command)
        self.app._register(key, w)
        return w

    # ---------- 保存 ----------
    def _collect_rows(self):
        """收集所有页的非空命令行，每条 = {text, hex, enter}。"""
        self._sync_all_from_pages()
        out = []
        for r in self._all_data:
            t = r.get("txt", "").strip()
            if t:
                out.append({"text": t, "hex": bool(r.get("hex", False)),
                            "enter": bool(r.get("ent", False))})
        return out

    def _save_config(self):
        name = self.config_name.get().strip()
        if not name:
            messagebox.showinfo(self.app._t("at_save"), self.app._t("at_group_name"))
            return
        commands = self._collect_rows()
        ok = self._write_config(name, commands)
        if ok:
            self._refresh_configs(select=name)
            messagebox.showinfo(self.app._t("at_save"),
                                f"{name} → {len(commands)} 条已保存")
        else:
            messagebox.showerror(self.app._t("at_save"), self.app._t("at_group_name"))

    def _bg(self):
        try:
            return self.app.P["surface"]
        except AttributeError:
            return "#FFFFFF"

    def _fg(self):
        try:
            return self.app.P["text"]
        except AttributeError:
            return "#1B2733"
