"""文件面板：选择本地文件并一次性发送内容给模组（M6）。

交互接口同 at_panel：``app._t`` / ``app._register`` / ``app.send_bytes``。
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk


def _fmt_size(n):
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


class FileSendPanel(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.path_var = tk.StringVar()
        self.size_var = tk.StringVar()
        self.append_var = tk.BooleanVar(value=False)
        self.sent_var = tk.StringVar(value="")
        self._build()

    def _build(self):
        # 第 1 行：文件路径(拉伸) + 选择…
        row1 = ttk.Frame(self)
        row1.pack(fill="x", padx=8, pady=(6, 2))
        self._label(row1, "file_row_label", style="Muted.TLabel").pack(side="left", padx=(0, 6))
        self.path_entry = ttk.Entry(row1, textvariable=self.path_var, state="readonly")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._btn(row1, "file_select", self._choose_file).pack(side="left")

        # 第 2 行：大小 + 追加后缀 + 发送文件 + 清空 + 已发送（按钮保持自然宽度，不拉伸）
        row2 = ttk.Frame(self)
        row2.pack(fill="x", padx=8, pady=(2, 6))
        self._label(row2, "file_size", style="Muted.TLabel").pack(side="left", padx=(0, 4))
        size_lbl = ttk.Label(row2, textvariable=self.size_var, style="Muted.TLabel")
        size_lbl.pack(side="left", padx=(0, 14))

        # 追加后缀：用原生 tk.Checkbutton（选中显示 ✓ 而非无主题的 ✖）
        self.append_chk = tk.Checkbutton(
            row2, text=self.app._t("file_append_suffix"), variable=self.append_var,
            command=self._sync_suffix, font=self.app.ui_font,
            bg=self._bg(), fg=self._fg(), activebackground=self._bg(), activeforeground=self._fg(),
            selectcolor=self._bg(), highlightthickness=0, bd=0)
        self.app._register("file_append_suffix", self.append_chk)
        self.append_chk.pack(side="left", padx=(0, 6))
        self._suffix_lbl = ttk.Label(row2, text="", style="Muted.TLabel")
        self._suffix_lbl.pack(side="left", padx=(0, 4))

        self._btn(row2, "file_send", self._send_file).pack(side="left", padx=(8, 6))
        self._btn(row2, "file_clear", self._clear).pack(side="left", padx=(0, 6))
        self.sent_lbl = ttk.Label(row2, textvariable=self.sent_var, style="Muted.TLabel")
        self.sent_lbl.pack(side="left", padx=(10, 0))

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

    def _label(self, parent, key, **kw):
        w = ttk.Label(parent, text=self.app._t(key), **kw)
        self.app._register(key, w)
        return w

    def _btn(self, parent, key, command):
        w = ttk.Button(parent, text=self.app._t(key), command=command)
        self.app._register(key, w)
        return w

    def _sync_suffix(self):
        from . import codec
        suffix = self.app.send_suffix_var.get()
        if self.append_var.get():
            self._suffix_lbl.config(text="+" + codec._SUFFIX_BYTES.get(suffix, b"").decode("latin1"))
        elif suffix == "STX-ETX":
            self._suffix_lbl.config(text="+STX..ETX")
        else:
            self._suffix_lbl.config(text="")

    def _choose_file(self):
        path = filedialog.askopenfilename(title=self.app._t("file_select"))
        if path:
            self.path_var.set(path)
            try:
                self.size_var.set(_fmt_size(os.path.getsize(path)))
            except OSError:
                self.size_var.set("")
            self.sent_var.set("")

    def _clear(self):
        self.path_var.set("")
        self.size_var.set("")
        self.sent_var.set("")

    def _send_file(self):
        path = self.path_var.get()
        if not path:
            self.sent_var.set(self.app._t("file_no_file"))
            return
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError:
            self.sent_var.set(self.app._t("file_open_fail"))
            return
        if self.append_var.get():
            from . import codec
            extra = codec._SUFFIX_BYTES.get(self.app.send_suffix_var.get(), b"")
            raw = raw + extra
        n = self.app.send_bytes(raw)
        self.sent_var.set(self.app._t("file_sent", n=n))
