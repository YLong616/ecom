# -*- coding: utf-8 -*-
"""文件面板：选择本地文件并一次性发送内容给模组（M6）。

交互接口同 at_panel：``app._t`` / ``app._register`` / ``app.send_bytes``。

布局（v4）：
  第 1 行：路径回显框(拉伸) + 进度条/百分比 + 选择文件
  第 2 行：已发送(左) …… 大小 · [暂停] [发送文件]（居右，发送文件最右与选择文件对齐）
"""

from __future__ import annotations

import os
import threading
import queue
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from .tooltip import Tooltip


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
        self.sent_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.pct_var = tk.StringVar(value="0%")
        # 后台发送线程状态
        self._send_q = queue.Queue()
        self._send_th = None
        self._sending = False
        self._paused = False
        self._pause_evt = threading.Event()
        self._pause_evt.set()          # set=继续, clear=暂停
        self._stop_evt = threading.Event()
        self._poll_job = None
        self._build()

    def _build(self):
        # ===== 主操作行：路径回显框(拉伸) | 进度条+百分比 | 选择文件 =====
        op = ttk.Frame(self)
        op.pack(fill="x", padx=8, pady=(3, 1))
        self.path_entry = ttk.Entry(op, textvariable=self.path_var, state="readonly")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))          # 路径回显框
        Tooltip(self.path_entry, text=lambda: self.path_var.get() or "")
        # 进度组件：Canvas 自绘进度条（长度缩短 + 浅绿色填充）
        self.pb_len = 70
        self.progress_bar = tk.Canvas(op, width=self.pb_len, height=14,
                                      highlightthickness=0, bd=0, bg=self._bg())
        self._pb_trough = self.progress_bar.create_rectangle(
            0, 0, self.pb_len, 14, fill="#e8e8e8", outline="#cfcfcf")
        self._pb_fill = self.progress_bar.create_rectangle(
            0, 0, 0, 14, fill=self._pc("success", "#22A06B"), outline="")      # 统一成功绿
        self.progress_bar.pack(side="left", padx=(0, 6))
        self.pct_lbl = ttk.Label(op, textvariable=self.pct_var, style="Muted.TLabel",
                                 width=5, anchor="e")
        self.pct_lbl.pack(side="left", padx=(0, 8))
        sel_btn = self._btn(op, "file_select", self._choose_file)
        sel_btn.pack(side="left")                                                     # 选择文件最右
        # 悬浮在选择文件按钮上也显示当前路径
        Tooltip(sel_btn, text=lambda: self.path_var.get() or self.app._t("file_no_path"))

        # ===== 状态行：已发送(左) …… 大小 · [暂停] [发送文件]（居右，发送文件正对选择文件） =====
        row2 = ttk.Frame(self)
        row2.pack(fill="x", padx=8, pady=(1, 3))
        # 左侧：已发送状态
        self.sent_lbl = ttk.Label(row2, textvariable=self.sent_var, style="Muted.TLabel")
        self.sent_lbl.pack(side="left", padx=(0, 10))
        right = ttk.Frame(row2, style="TFrame")
        right.pack(side="right", padx=(8, 0))
        # 发送文件（最右，正对上方"选择文件"）
        self.send_btn = self._btn(right, "file_send", self._send_file)
        self.send_btn.pack(side="right", padx=(0, 0))
        # 暂停 / 继续（替换原"清空"）
        self.pause_btn = ttk.Button(right, text=self.app._t("file_pause"),
                                    command=self._toggle_pause)
        self.pause_btn.pack(side="right", padx=(0, 4))
        self.app._register("file_pause", self.pause_btn)
        self._label(right, "file_size", style="Muted.TLabel").pack(side="right", padx=(0, 8))
        size_lbl = ttk.Label(right, textvariable=self.size_var, style="Muted.TLabel")
        size_lbl.pack(side="right", padx=(0, 10))

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

    def _pc(self, key, default):
        try:
            return self.app.P[key]
        except Exception:
            return default

    def _label(self, parent, key, **kw):
        w = ttk.Label(parent, text=self.app._t(key), **kw)
        self.app._register(key, w)
        return w

    def _btn(self, parent, key, command):
        w = ttk.Button(parent, text=self.app._t(key), command=command)
        self.app._register(key, w)
        return w

    def _choose_file(self):
        self._stop_old_send()
        path = filedialog.askopenfilename(title=self.app._t("file_select"))
        if path:
            self.path_var.set(path)
            try:
                self.size_var.set(_fmt_size(os.path.getsize(path)))
            except OSError:
                self.size_var.set("")
            self.sent_var.set("")
            self._set_progress(0.0)

    def _send_file(self):
        self._stop_old_send()
        path = self.path_var.get()
        if not path:
            self.sent_var.set(self.app._t("file_no_file"))
            return
        if not self.app.core.is_open:
            self.sent_var.set(self.app._t("no_port"))
            return
        try:
            total = os.path.getsize(path)
        except OSError:
            self.sent_var.set(self.app._t("file_open_fail"))
            return
        self._set_progress(0.0)
        self._sending = True
        self._paused = False
        self._pause_evt.set()
        self._stop_evt.clear()
        self._update_pause_btn()
        self._send_th = threading.Thread(target=self._send_worker,
                                         args=(path,), daemon=True)
        self._send_th.start()
        self._start_poll()

    # ---------- 后台发送 worker：读文件/写串口不阻塞 UI ----------
    def _send_worker(self, path):
        chunk = 8192
        try:
            total = os.path.getsize(path)
        except OSError:
            self._send_q.put(("error", "file_open_fail"))
            return
        self._send_q.put(("total", total))
        sent = 0
        try:
            with open(path, "rb") as f:
                while not self._stop_evt.is_set():
                    self._pause_evt.wait()
                    if self._stop_evt.is_set():
                        break
                    data = f.read(chunk)
                    if not data:
                        break
                    n = self.app.core.write(data)
                    sent += n if n else len(data)
                    self._send_q.put(("progress", sent, total))
            if not self._stop_evt.is_set():
                self._send_q.put(("done", sent))
        except Exception as exc:
            self._send_q.put(("error", "EXC", str(exc)))

    # ---------- UI 轮询 / 暂停·继续 / 收尾 ----------
    def _start_poll(self):
        if self._poll_job is None:
            self._poll_job = self.after(40, self._poll_progress)

    def _poll_progress(self):
        self._poll_job = None
        try:
            while True:
                item = self._send_q.get_nowait()
                kind = item[0]
                if kind == "total":
                    pass
                elif kind == "progress":
                    _, sent, total = item
                    self._set_progress(sent / total if total else 1.0)
                elif kind == "done":
                    self._set_progress(1.0)
                    self.sent_var.set(self.app._t("file_sent", n=item[1]))
                    self._finish_send()
                    return
                elif kind == "error":
                    if item[1] == "EXC":
                        self.sent_var.set(item[2])
                    else:
                        self.sent_var.set(self.app._t(item[1]))
                    self._finish_send()
                    return
        except queue.Empty:
            pass
        if self._sending:
            self._poll_job = self.after(40, self._poll_progress)

    def _toggle_pause(self):
        if not self._sending:
            return
        if self._paused:
            self._pause_evt.set()
            self._paused = False
        else:
            self._pause_evt.clear()
            self._paused = True
        self._update_pause_btn()

    def _update_pause_btn(self):
        if self._paused:
            text = self.app._t("file_resume")
        else:
            text = self.app._t("file_pause")
        self.pause_btn.configure(text=text)

    def _finish_send(self):
        self._sending = False
        self._send_th = None
        self._update_pause_btn()

    def _stop_old_send(self):
        if self._send_th is not None and self._send_th.is_alive():
            self._stop_evt.set()
            self._pause_evt.set()
            self._send_th.join(timeout=0.6)
        self._send_th = None
        self._sending = False
        self._paused = False
        self._update_pause_btn()
        while True:
            try:
                self._send_q.get_nowait()
            except queue.Empty:
                break

    def _set_progress(self, frac):
        frac = max(0.0, min(1.0, frac))
        self.progress_var.set(frac * 100.0)
        self.pct_var.set(f"{frac * 100:.0f}%")
        # 更新自绘进度条填充宽度
        w = max(0, int(frac * self.pb_len))
        try:
            self.progress_bar.coords(self._pb_fill, 0, 0, w, 14)
        except tk.TclError:
            pass
