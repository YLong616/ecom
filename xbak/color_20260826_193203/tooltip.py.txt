# -*- coding: utf-8 -*-
"""悬浮提示（tooltip）：鼠标悬停在控件上时弹出完整文本的小窗。

用于路径类控件（Entry / Button），当文本过长被截断或不可见时，
悬停即可看到完整内容。组件本身尺寸不变。
"""

from __future__ import annotations

import tkinter as tk


class Tooltip:
    """把 ``text``（或一个回调返回的文本）显示在控件旁的悬浮小窗里。

    用法::

        Tooltip(widget, "完整路径...")
        Tooltip(entry, text=lambda: entry.get())
    """

    _WIDTH = 560          # 小窗最大像素宽，超出自动换行
    _DELAY_MS = 350       # 悬停多久后出现

    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text if callable(text) else (lambda: text)
        self._tip = None  # toplevel 引用
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Motion>", self._schedule, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self._DELAY_MS, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip is not None:
            return
        content = str(self.text()).strip()
        if not content:
            return
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)          # 无边框
        tip.wm_attributes("-topmost", True)    # 置顶
        try:
            tip.wm_attributes("-alpha", 0.92)
        except tk.TclError:
            pass

        lbl = tk.Label(
            tip, text=content, justify="left", anchor="w",
            bg="#FFFDF5", fg="#333333", relief="solid", borderwidth=1,
            font=("Segoe UI", 9), wraplength=self._WIDTH)   # 用系统字体读取任意语言文件名; 超宽自动换行防止超出屏幕
        lbl.pack(fill="both", padx=6, pady=4)

        # 定位：优先在控件正下方，接近屏幕边缘时自动上翻/左移
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        sw = tip.winfo_screenwidth()
        sh = tip.winfo_screenheight()
        tip.update_idletasks()
        tw = tip.winfo_reqwidth()
        th = tip.winfo_reqheight()
        if x + tw > sw - 8:
            x = max(8, sw - tw - 8)
        if y + th > sh - 8:
            y = self.widget.winfo_rooty() - th - 6
        tip.geometry(f"+{x}+{y}")

        self._tip = tip
        tip.bind("<Leave>", self._hide)

    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None
