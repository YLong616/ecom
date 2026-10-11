# eCOM — Project Overview

> A lightweight, cross-platform (Windows + Linux) serial-port debugging tool that combines AT-command debugging, looped AT-command stress testing, file transfer, and serial logging.

---

## 1. Positioning

eCOM is a **Python + Tkinter** desktop serial-debugging tool aimed at embedded/module debugging scenarios. It prioritizes "lightweight, practical, testable." Core capabilities:

- **AT-command debugging**: send any AT command manually, with ASCII / HEX / DEC / BIN encodings and send-on-enter suffixes, real-time TX/RX display and log-to-file.
- **Looped AT-command stress test**: organize a group of AT commands into a list, loop them by *count / duration*, automatically verify each command's **expected result**, flag responses matching custom check rules as exceptions, and output structured run statistics.
- **File transfer**: send a local file to the serial port in chunks, with progress and pause.
- **Serial logging**: two-channel logging (AT log and DOS log) to disk.

The UI supports Chinese/English, switchable at runtime; state and styling are driven by a unified global config.

---

## 2. Technical Architecture

```
+--------------------------------------------------------------+
| Tkinter GUI main thread (root.after polling)                  |
|  +------------+ +--------------+ +-------------+ +---------+ |
|  |  app.py    | |  at_panel.py | |stress_panel | |file_panel| |
|  | (EcomApp)  | |  AT panel    | | stress panel| |  file   | |
|  +-----+------+ +------+-------+ +------+------+ +----+-----+ |
|        +-------+--------+----------+----------+        |      |
+----------------+-----------------+-------------------+------+
                 |                 |                 |
         +-------v--------+  +----v--------+   +-----v------+
         |  serial_core   |  | stress_*    |   |   codec    |
         |  reader thread |  | model/io    |   |  codec     |
         |  (queue)       |  +----+--------+   +-----+------+
         +-------+---------+       |                  |
                 |            +----v------+     +-----v------+
                 |            | stress_io |     |  logger    |
                 |            | CSV import|     |  log file  |
                 |            +----+------+     +-----+------+
                 +------------+----+----------------+------+
                          +-----v------+
                          |  config    |  ~/.ecom/config.json
                          +------------+
```

Design highlights:

- **Serial reader thread is separate from the GUI main thread**: `serial_core` reads in a background thread and hands data to the GUI through a `queue.Queue`; the GUI periodically calls `drain()` via `root.after`, avoiding direct Tk manipulation from another thread.
- **Main-loop driven**: TX/RX, the stress-test state machine (`send → wait → interval → next`), and statistics refresh are all scheduled on the main thread via `after` — single-threaded, lock-free.
- **Encrypted-source caveat**: in some environments the `ecom/*.py` source files are encrypted by corporate security software (E-SafeNet), so plain-text tooling reads them as ciphertext. **Any source change must be done via byte-level replacement in a Python script and validated with `py_compile`** (see the API reference doc).

---

## 3. Environment & Dependencies

### 3.1 Runtime

| Item | Requirement |
|---|---|
| Python | **≥ 3.8** |
| OS | Windows 10+ / major Linux distros |
| GUI | **tkinter** (system-level; not installable via pip) |
| Serial | **pyserial ≥ 3.5** |

### 3.2 Dependency list (`requirements.txt` / `pyproject.toml`)

```
pyserial>=3.5
```

> tkinter ships with the official Python distribution, but on some Linux distros it is not installed with Python and must be added via the system package manager (see §3.3).

### 3.3 System-level tkinter installation (Linux)

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

On Windows, use the tkinter bundled with the official python.org installer — no extra step.

---

## 4. Project Structure
```
eCOM/
├── main.py              used    GUI entry (python main.py)
├── run.bat              used    Windows one-click launcher (python main.py)
├── requirements.txt     used    Python deps (pyserial>=3.5)
├── pyproject.toml       used    Packaging/metadata; [project.scripts] ecom = ecom.cli:main
├── README.md            used    One-page overview
├── PROGRESS.md          used    Dev/fix progress log (maintenance doc)
├── UI_DESIGN.md         used    UI design notes
├── docs/                used    Documentation (this bilingual set)
│   ├── PROJECT_OVERVIEW_zh.md / _en.md   Overview
│   ├── API_REFERENCE_zh.md / _en.md      API reference
│   ├── USER_GUIDE_zh.md / _en.md         User guide
│   ├── KNOWN_ISSUES_zh.md / _en.md       Known issues
│   ├── ui_mockup.html                    UI mockup (design asset, not a runtime dep)
│   └── images/interface_mockup.png       UI mockup image (design asset, not a runtime dep)
├── configs/             used    AT command groups (at_panel reads *.json via configs_dir()=<root>/configs)
│   ├── config.json      used    Default AT command group (loaded at startup)
│   └── config1.json     used    Alternate / empty example group
├── scripts/             auxiliary
│   ├── install_deps.sh  used    Linux one-shot install of python3-tk (deploy helper)
│   ├── shot_pw.bmp      unused  Debug screenshot (3.4MB, cleanable)
│   └── stress_template_demo.xlsx  unused/example  Export-template demo (optional)
├── tests/               used    Unit/regression tests (6 files)
│   ├── test_fixes_verify.py      fixes/regression verification
│   ├── test_gui_regression.py    GUI layout regression (8 guards)
│   ├── test_serial_core.py       serial-core unit tests
│   ├── test_stress.py            stress state machine / model tests
│   ├── test_hotplug.py           serial hot-plug detection
│   └── test_stress_features.py   new stress features (export/import/all-batch/clear)
├── xbak/                unused  Old source backups (see 4.2)
└── ecom/                used    Core source package (see 4.3 / API_REFERENCE)
```

> `used` = referenced by runtime or maintenance flow; `unused` = not involved in running, only backups/debug/examples/design. Any `unused` file may be removed before release (see the 4.2 list).

### 4.1 Source-module roles (`ecom/`)

| Module | Role | Used by |
|---|---|---|
| `__init__.py` | package marker + `__version__` | import side-effect |
| `app.py` | main window `EcomApp` + `run()` | `cli.py`, `main.py` |
| `cli.py` | CLI entry `main()` (`ecom start` / `--version`) | `main.py`, entrypoint |
| `at_panel.py` | AT command panel (group load/paging/loop) | `app.py` |
| `stress_panel.py` | stress-mode panel + stress state machine | `app.py` |
| `stress_model.py` | data model/matching/stats/end condition | `stress_panel.py` |
| `stress_io.py` | AT-list CSV template/import/export | `stress_panel.py` |
| `file_panel.py` | file-send panel | `app.py` |
| `serial_core.py` | serial wrapper (read thread/queue/counters/hot-plug) | `app.py`, `stress_panel.py` |
| `codec.py` | codec (type/suffix/display conversion) | `app.py`, `at_panel.py`, `stress_panel.py` |
| `logger.py` | log-to-file `Logger` | `app.py`, `stress_panel.py` |
| `config.py` | config persistence `Config` (writes `~/.ecom/config.json`) | `app.py` |
| `i18n.py` | zh/en translation table + `get()` | `app.py`, `stress_panel.py` |
| `tooltip.py` | tooltip `Tooltip` | `app.py`, `file_panel.py`, `stress_panel.py` |

> API dependency (AST analysis): all 14 `ecom/` modules are referenced — **no dead code / no obsolete module**; only `__init__.py` is a package marker (not an import target), which is normal.

### 4.2 Unused / suggest-to-clean file list

| Path | Type | Suggestion |
|---|---|---|
| `ecom/stress_panel.py.bak_addwobble` | source backup | clean |
| `ecom/stress_panel.py.bak_addwobble2` | source backup | clean |
| `ecom/stress_panel.py.bak_repaint3` | source backup | clean |
| `ecom/stress_panel.py.bak_ui3` | source backup | clean |
| `ecom/stress_panel.py.bak_ui4` | source backup | clean |
| `xbak/app.py` | source backup | clean |
| `xbak/app_v5.py` | source backup | clean |
| `xbak/app_v6.py` | source backup | clean |
| `xbak/file_panel.py` | source backup | clean |
| `xbak/file_panel_v6.py` | source backup | clean |
| `xbak/i18n.py` | source backup | clean |
| `xbak/color_20260826_193203/` (app/at_panel/file_panel/stress_panel/tooltip.py + restore.bat/py) | color rollback backup | keep only if wanted, else clean |
| `scripts/shot_pw.bmp` | debug screenshot (3.4MB) | clean |
| `scripts/stress_template_demo.xlsx` | export-template demo | optional |
| `docs/ui_mockup.html`, `docs/images/interface_mockup.png` | design assets | keep as reference, not a runtime dep |

### 4.3 Runtime & config data

- `configs/*.json`: AT command groups (`at_panel` loads every `*.json` at startup from `<root>/configs`; `config.json` is the default group). This is **project-shared** command-group data.
- `~/.ecom/config.json`: persisted by `ecom/config.py` for serial/panel global settings — **lives in the user home dir, shared across projects**, not inside this repo.
- `scripts/stress_template_demo.xlsx`: sample produced by `stress_io.export_template`, demo only.

---


## 5. Run & Installation

### 5.1 Direct run (development)

```bash
python main.py
```

### 5.2 Install as a command

```bash
pip install .
```

After install:

```bash
ecom start        # start the GUI (equivalent to python main.py)
ecom --version    # show version
```

> The `ecom` command is registered by `[project.scripts] ecom = "ecom.cli:main"` in `pyproject.toml`; before starting, the CLI checks for tkinter and prints a distro-specific install hint and exits if missing.

### 5.3 Exit

- Close the window (click "x"), or
- Press `Ctrl+C` in the terminal.

---

## 6. License

Open source under the **MIT License** (see `license` in `pyproject.toml`).

---

## 7. Related Documents

| Document | Description |
|---|---|
| [API_REFERENCE_en.md](API_REFERENCE_en.md) | Files, methods, interfaces, parameters, callers/callees |
| [USER_GUIDE_en.md](USER_GUIDE_en.md) | User manual (with images) |
| [KNOWN_ISSUES_en.md](KNOWN_ISSUES_en.md) | Known limitations & leftover items |
| [README.md](../README.md) | One-page overview |

---

*Version: 0.1.0 · Language: English (Chinese version: `PROJECT_OVERVIEW_zh.md`)*
