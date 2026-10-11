"""嵌入式 Linux 串口排障手册查看器（只读、可选中复制）。

不依赖第三方 markdown 库，解析本文档用到的少量 md 子集：
  标题 # / ## / ###；列表 -；引用 >；代码块 ``` ... ```；加粗 ** ... **。

用法::

    from .help_viewer import show_help
    show_help(root, lang, ui_font=..., menu_font=..., out_font=...)
"""
import os
import tkinter as tk
from tkinter import scrolledtext
from tkinter import font as tkfont

# 浅色主题（与主界面一致）
_C = {
    "bg": "#FFFFFF",
    "fg": "#1B2733",
    "muted": "#59657A",
    "primary": "#0B57D0",
    "code_bg": "#EEF1F6",
    "border": "#D9DEE8",
}


def doc_path(lang):
    fname = "TROUBLESHOOT_en.md" if lang != "zh" else "TROUBLESHOOT_zh.md"
    return os.path.join(os.path.dirname(__file__), "docs", fname)


def _font(obj, fallback="TkDefaultFont"):
    if obj is None:
        return tkfont.nametofont(fallback)
    if isinstance(obj, str):
        try:
            return tkfont.nametofont(obj)
        except tk.TclError:
            return tkfont.nametofont(fallback)
    return obj


def _insert_runs(txt, seg, base_tag):
    """把一行文本插入 Text；支持内联 **加粗** 与 `代码`。"""
    i = 0
    n = len(seg)
    while i < n:
        # 内联代码
        if seg[i] == "`":
            j = seg.find("`", i + 1)
            if j < 0:
                txt.insert("end", seg[i:], base_tag)
                return
            txt.insert("end", seg[i + 1:j], base_tag + "_code")
            i = j + 1
            continue
        # 加粗
        if seg.startswith("**", i):
            j = seg.find("**", i + 2)
            if j < 0:
                txt.insert("end", seg[i:], base_tag)
                return
            txt.insert("end", seg[i + 2:j], base_tag + "_bold")
            i = j + 2
            continue
        # 普通片段（找下一个 ` 或 ** 起点）
        nxt = []
        p = seg.find("`", i)
        if p >= 0:
            nxt.append(p)
        p = seg.find("**", i)
        if p >= 0:
            nxt.append(p)
        nxt = [p for p in nxt if p >= 0]
        if not nxt:
            txt.insert("end", seg[i:], base_tag)
            return
        j = min(nxt)
        txt.insert("end", seg[i:j], base_tag)
        i = j


def render(txt, content, fonts):
    """把 md 内容渲染进 Text。"""
    lines = content.split("\n")
    in_code = False
    in_list = False
    h1f, h2f, h3f, mono = fonts

    txt.tag_configure("h1", font=h1f, foreground=_C["primary"], spacing3=9)
    txt.tag_configure("h2", font=h2f, foreground=_C["primary"], spacing3=8)
    txt.tag_configure("h3", font=h3f, foreground=_C["primary"], spacing3=7)
    txt.tag_configure("norm", foreground=_C["fg"])
    txt.tag_configure("bullet", foreground=_C["fg"], lmargin1=24, lmargin2=24)
    txt.tag_configure("quote", foreground=_C["muted"], lmargin1=20, lmargin2=20, font=h3f)
    txt.tag_configure("code", font=mono, background=_C["code_bg"], foreground=_C["fg"])
    txt.tag_configure("_bold", font=h3f)
    txt.tag_configure("_code", font=mono, background=_C["code_bg"])

    for raw in lines:
        line = raw.rstrip("\n")
        s = line.strip()
        if s.startswith("```"):
            if in_code:
                txt.insert("end", "\n", "norm")
            in_code = not in_code
            continue
        if in_code:
            txt.insert("end", line + "\n", "code")
            continue
        if not s:
            txt.insert("end", "\n", "norm")
            in_list = False
            continue
        if s.startswith("### "):
            txt.insert("end", s[4:] + "\n", "h3")
            continue
        if s.startswith("## "):
            txt.insert("end", s[3:] + "\n", "h2")
            in_list = False
            continue
        if s.startswith("# "):
            txt.insert("end", s[2:] + "\n", "h1")
            in_list = False
            continue
        if s.startswith("- "):
            txt.insert("end", "• ")
            _insert_runs(txt, s[2:], "bullet")
            txt.insert("end", "\n", "bullet")
            in_list = True
            continue
        if s.startswith(">"):
            txt.insert("end", s[2:] + "\n", "quote")
            continue
        # 普通段落
        txt.insert("end", "\n", "norm") if in_list else None
        in_list = False
        _insert_runs(txt, s, "norm")
        txt.insert("end", "\n", "norm")


def show_help(master, lang="zh", ui_font=None, menu_font=None, out_font=None):
    path = doc_path(lang)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        content = "排障手册未找到：%s\n%s" % (path, e)

    body = _font(ui_font)
    mono = _font(out_font, "TkFixedFont")
    h1f = body.copy(); h1f.configure(size=int(body.cget("size")) + 4, weight="bold")
    h2f = body.copy(); h2f.configure(size=int(body.cget("size")) + 2, weight="bold")
    h3f = body.copy(); h3f.configure(size=int(body.cget("size")) + 1, weight="bold")

    win = tk.Toplevel(master)
    win.title("eCOM · Linux Serial Guide")
    win.geometry("780x700")
    win.minsize(560, 420)
    try:
        win.transient(master)
    except tk.TclError:
        pass

    top = tk.Frame(win, bg=_C["bg"])
    top.pack(side="top", fill="x")

    txt = scrolledtext.ScrolledText(
        win, wrap="word", font=body, bg=_C["bg"], fg=_C["fg"],
        insertbackground=_C["fg"], relief="flat", borderwidth=0,
        highlightthickness=1, highlightbackground=_C["border"],
        highlightcolor=_C["border"], padx=14, pady=10, spacing3=6)
    txt.pack(side="top", fill="both", expand=True, padx=8, pady=(6, 0))

    bottom = tk.Frame(win, bg=_C["bg"])
    bottom.pack(side="bottom", fill="x", pady=(4, 8))

    render(txt, content, (h1f, h2f, h3f, mono))
    txt.configure(state="normal")

    # 只读：拦截除 Ctrl 组合外的一切键入；保留选中/复制/全选
    def _guard(event):
        if event.state & 0x0004:  # Ctrl
            return None
        return "break"

    def _ctx(event):
        m = tk.Menu(txt, tearoff=0)
        m.add_command(label="复制", command=lambda: _copy())
        m.add_command(label="全选", command=lambda: _sel_all())
        m.add_command(label="复制全部", command=lambda: _copy_all())
        m.tk_popup(event.x_root, event.y_root)

    def _copy():
        try:
            s = txt.get("sel.first", "sel.last")
        except tk.TclError:
            s = ""
        if s:
            txt.clipboard_clear()
            txt.clipboard_append(s)

    def _sel_all():
        try:
            txt.tag_add("sel", "1.0", "end")
        except tk.TclError:
            pass

    def _copy_all():
        try:
            s = txt.get("1.0", "end-1c")
        except tk.TclError:
            s = ""
        if s:
            txt.clipboard_clear()
            txt.clipboard_append(s)

    def _close():
        win.destroy()

    txt.bind("<Key>", _guard)
    txt.bind("<Button-3>", _ctx)
    txt.bind("<Control-a>", lambda e: _sel_all())
    txt.bind("<Control-c>", lambda e: _copy())

    btn = tk.Button(bottom, text="关闭", command=_close,
                    bg=_C["primary"], fg="#FFFFFF", activebackground=_C["primary"],
                    relief="flat", padx=18, pady=4, font=body)
    btn.pack(side="right", padx=12, pady=(0, 4))

    return win
