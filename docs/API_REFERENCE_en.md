# eCOM — API Reference

> For developers / second-party development. Covers every module in the `ecom` package: responsibilities, public classes & methods, parameters, return values, and caller/callee relationships.
> All signatures are extracted from the actual source; line numbers refer to the current version.

---

## 0. Conventions

- **Name prefix**: `_`-prefixed = private (module-internal only); others = callable entry points.
- **Call direction**: GUI layer (app / at_panel / stress_panel / file_panel) → core layer (serial_core / stress_model / stress_io / codec / logger / config / i18n / tooltip).
- **Threading**: except for the `serial_core` background reader thread, everything runs on the Tkinter main thread; cross-thread data flows only through `queue.Queue`.
- **Line numbers** are for locating code, not a stable API contract.

---

## 1. Module Dependency & Call Graph

```
                    ┌─────────────────────────────┐
                    │        app.py (EcomApp)      │
                    │   main window / mode switch  │
                    │   / display / logging        │
                    └──────┬──────┬──────┬────────┘
                           │      │      │
          ┌────────────────┘      │      └────────────────┐
          ▼                       ▼                       ▼
 ┌──────────────┐        ┌───────────────┐        ┌──────────────┐
 │  at_panel.py │        │ stress_panel  │        │ file_panel   │
 │  AT panel    │        │  stress panel │        │  file send   │
 └──────┬───────┘        └──────┬────────┘        └──────┬───────┘
        │                       │                         │
        └──────────┬────────────┴──────────┬──────────────┘
                   ▼                       ▼
        ┌────────────────────┐    ┌───────────────────┐
        │   serial_core.py   │    │  stress_model.py  │
        │  reader thread/q   │    │  model/match/stats│
        └───────┬────────────┘    └─────────┬─────────┘
                │                            │
   ┌────────────┼─────────────┐       ┌──────▼──────┐
   ▼            ▼             ▼       │ stress_io   │
┌──────┐  ┌─────────┐  ┌──────────┐  │  CSV IO     │
│codec │  │ logger  │  │  config  │  └──────┬──────┘
└──────┘  └─────────┘  └──────────┘         │
           i18n.py（translations）─────┐    │
           tooltip.py（tooltip）────────┐   │
┌─────────────┐  cli.py（CLI entry）     └─┴─ app.run()
│  __init__.py │  __version__ = "0.1.0"
└─────────────┘
```

**Direct import relationships**:

| Module | imports |
|---|---|
| app | codec, i18n, at_panel, file_panel, stress_panel, config, logger, serial_core, tooltip, tkinter, datetime, time |
| at_panel | codec, pathlib, tkinter, json, math |
| stress_panel | codec, i18n, stress_io, stress_model, logger, serial_core, tooltip, tkinter, datetime, math, time |
| stress_model | dataclasses, datetime, re |
| stress_io | csv, io, os |
| file_panel | tkinter, tooltip, os, queue, threading |
| serial_core | serial, serial.tools.list_ports, queue, threading, time |
| codec | (none; pure functions) |
| logger | datetime, os |
| config | json, os, pathlib |
| i18n | (none) |
| tooltip | tkinter |
| cli | argparse, sys, platform, app.run, __version__ |

---

## 2. Module API Details

### 2.1 `serial_core.py` — Serial core

Handles open/close, a background reader thread, byte counters, and port enumeration. **externally exposes only the queue & counters, not Tk.**

| Signature | Params | Returns | Description |
|---|---|---|---|
| `class SerialCore` | — | — | Thread-safe serial core |
| `__init__(self)` | — | — | `_ser=None`, `_running=False`, read queue, `rx_count/tx_count=0` |
| `is_open` (property) | — | bool | port open? |
| `open(self, port, baudrate=115200, bytesize=8, parity="N", stopbits=1, rtscts=False, xonxoff=False)` | port: name/URL (incl. `loop://`); rest=serial params | None | Open & start reader thread; closes first if already open; uses `serial_for_url` for real/virtual ports |
| `_read_loop(self)` | — | None | Reader thread: poll `in_waiting`, put `(RX_DATA, bytes)`; on error `(RX_ERROR, str)`; on unexpected exit `(RX_CLOSED, None)` |
| `write(self, data: bytes) -> int` | data | bytes written | raises `RuntimeError("串口未打开")` if closed; increments `tx_count` |
| `set_dtr(self, low=True)` | low=True means pull low | None | DTR; silent on error |
| `set_rts(self, low=True)` | low=True means pull low | None | RTS; silent on error |
| `close(self)` | — | None | stop reader thread (join ≤1s) & close port |
| `drain(self)` | — | `list[tuple]` | drain all queue events for the GUI `after` loop |
| `reset_counters(self)` | — | None | zero rx/tx counters |
| `list_ports()` (staticmethod) | — | `list[(device, display)]` | enumerate ports; `display` includes full device name |

**Callers**: `app._toggle_port`, `stress_panel._toggle_port` use `open/close/drain/set_dtr/set_rts/reset_counters`; `app.send_bytes`, `stress_panel._send_current` use `write`.
**Callees**: `app._refresh_ports`, `stress_panel._refresh_ports` use `list_ports`.

---

### 2.2 `codec.py` — Codecs

Pure stateless functions: encode-before-send + display-after-receive.

| Signature | Params | Returns | Description |
|---|---|---|---|
| `_parse_hex(text)` | text | bytes | strips spaces/newlines/commas/`0x`; raises `ValueError` if odd length |
| `encode(text, data_type="ASCII", suffix="None")` | input; type: ASCII/HEX/DEC/BIN; suffix: None/CR/LF/CR-LF/SPACE/STX-ETX/NULL | bytes | build send data; STX-ETX wraps `\x02...\x03`; unknown type raises `ValueError` |
| `decode_display(data, display_hex=False)` | bytes; hex flag | str | display string; `errors="replace"` |
| `escape_control(text, show_crlf=True)` | text; flag | str | make `\r\n`→`\\r\\n` etc. visible |

**Callers**: `app.send_text/send_bytes`, `at_panel._encode_row`, `stress_panel._row_bytes` use `encode`; `app._render_frame`, `stress_panel._render_line` use `decode_display`/`escape_control`.

---

### 2.3 `logger.py` — Log to file

Writes TX/RX records to a text file. Format is **byte-identical to the output box**: `[timestamp]  TX/RX  body`.

| Signature | Params | Returns | Description |
|---|---|---|---|
| `class Logger` | — | — | single-file logger |
| `__init__(self)` | — | — | `_f=None, _path=None, entries=0` |
| `active` (property) | — | bool | recording? |
| `path` (property) | — | str | current log path |
| `start(self, path) -> bool` | path | success? | stop first; auto-mkdir; append; false on failure |
| `stop(self)` | — | None | flush + close |
| `log(self, line)` | full line (with timestamp prefix) | None | write `${line}\n` if active; increment `entries` |

**Callers**: `app._log_start/_log_stop/_append_line`, `stress_panel._start_logs/_stop_logs/_render_line/_log_round_marker` use `start/stop/log`.

---

### 2.4 `config.py` — Config persistence

JSON config at `~/.ecom/config.json`.

| Signature | Params | Returns | Description |
|---|---|---|---|
| `_deep_merge(base, overlay)` | two dicts | dict | recursive merge |
| `class Config` | — | — | config reader/writer |
| `__init__(self, path=None)` | path (default `~/.ecom/config.json`) | — | deep-copy defaults then `load()` |
| `load(self)` | — | None | read → `_deep_merge`; migrates `"CRLF"→"CR-LF"` |
| `save(self)` | — | None | write JSON (`ensure_ascii=False, indent=2`) |
| `get(self, section, key=None, default=None)` | section; key; default | any | read; whole section if key=None |
| `set(self, section, key, value)` | same | None | write (does not clear other keys) |
| `get_at_group(self, name, default=None)` | group name | command list | read AT command group |
| `set_at_group(self, name, commands)` | name; commands | None | write AT command group |
| `remove_at_group(self, name)` | name | None | delete AT command group |

**Callers**: `app._save_config/_on_close`, `at_panel._load_config/_save_config/_refresh_configs`, and `stress_panel` config reads use `get/set`.

---

### 2.5 `i18n.py` — zh/en translations

Two public functions.

| Signature | Params | Returns | Description |
|---|---|---|---|
| `get(lang, key, **fmt)` | lang:zh/en; key; fmt | str | get translation; missing key → key itself; `{e}` placeholder formatted via fmt |
| `lang_label(lang)` | lang | str | native name of the language ("中文"/"English"), not translated |

**Callers**: nearly every panel's `_t()` (`app._t`, `stress_panel._t`, etc.). `I18N = {"zh": {...}, "en": {...}}` is a two-level dict.

---

### 2.6 `tooltip.py` — Tooltip

Shows full text on hover, for truncated path controls.

| Signature | Params | Returns | Description |
|---|---|---|---|
| `class Tooltip` | — | — | hover popup |
| `__init__(self, widget, text="")` | widget; text: str or callable | — | binds Enter/Leave/Motion; `text` may be a `lambda:` returning dynamic text |
| `_schedule(self, _event=None)` | event | None | show after `_DELAY_MS`(350ms) |
| `_show(self)` | — | None | borderless topmost Toplevel; `wraplength=560` auto-wrap; auto-flip near screen edges |
| `_hide(self, _event=None)` | event | None | cancel & destroy |

**Callers**: `app`, `stress_panel`, `file_panel` create `Tooltip` for path Entry/Button.

---

### 2.7 `stress_model.py` — Data model / matching / stats / end condition

Pure-logic module (no Tk); algorithmic core of stress testing.

**Constants**: `MATCH_CONTAINS`, `MATCH_EXACT`, `MATCH_REGEX`, `MATCH_MODES`; `TARGET_AT/TARGET_DOS/TARGET_BOTH`; `BUILTIN_RULES`.

| Signature | Params | Returns | Description |
|---|---|---|---|
| `class StressRow` (dataclass) | fields below | — | single AT-list row model |
| `__post_init__(self)` | — | None | normalizes `match_mode`/`send_type` |
| `effective_type` (property) | — | str | `"HEX"` if hex checked, else `send_type` |
| `effective_suffix` (property) | — | str | `"CR-LF"` if Enter checked, else `send_suffix` |
| `has_expected` (property) | — | bool | expected non-empty |
| `to_dict(self)` | — | dict | serialize → config/export |
| `from_dict(d)` (staticmethod) | d | StressRow | deserialize (fault-tolerant) |
| `class CheckRule` (dataclass) | name/keyword/record_to/as_exception/enabled | — | custom check rule |
| `parse_expected(expected)` | string | `list[str]` | split by newline/`|` |
| `match_expected(response_text, expected, mode)` | response/expected/mode | bool | any expected hit passes; **empty expected → True (no check)**; invalid regex degrades to contains |
| `run_check_rules(response_text, rules)` | response/rules | `list[(rule, text)]` | hits for enabled rules |
| `class RunStats` (dataclass) | sent_lines/errors/current_line/total_rounds/start_time/end_time | — | stats object |
| `format_duration(seconds)` | seconds | str | e.g. `"0.0H"` |
| `format_window(start, end)` | two datetime | str | `start~end` with microseconds |
| `compute_end_condition(current_rounds, mode, target_count, elapsed_seconds, target_seconds)` | current rounds / mode / target count / elapsed sec / target sec | bool | time mode by seconds; else by rounds |

**StressRow fields**: `txt`(str=""), `send_type`(str="ASCII"), `send_suffix`(str="CR-LF"), `hex`(bool=False), `enter`(bool=True), `interval_ms`(int=0, 0=use global), `expected`(str="OK", default), `match_mode`(str=contains), `enabled`(bool=True).

**Callers**: used heavily by `stress_panel` and `stress_io`; unit-tested by `test_stress.py`.

---

### 2.8 `stress_io.py` — AT-list CSV template / import / export

Cross-platform: writes `utf-8-sig` (BOM); reads with/without BOM.

| Signature | Params | Returns | Description |
|---|---|---|---|
| `HEADERS` | — | list | index/enabled/at/send_type/send_suffix/hex/enter/interval_ms/expected/match_mode |
| `export_template(path)` | path | bool | export template with sample rows |
| `export_data(path, rows)` | path; rows | bool | export full AT list |
| `import_data(path)` | path | `list[dict]` | import from CSV (may be empty) |
| `_write_csv`/`_read_csv`/`_row_to_list`/`_row_from_list` | private | — | low-level IO / row parsing |

**Callers**: `stress_panel._export_template/_export_data/_import_data`.

---

### 2.9 `app.py` — Main window (`EcomApp`)

Responsible for: main window, mode switching (AT / stress / file), serial open/close, TX/RX display, status bar, menu, config saving, logging, language switch, font zoom.

| Signature | Description |
|---|---|
| `__init__(self, root, language="zh")` | build all widgets & vars |
| `_t(self, key, **fmt)` | translate (i18n.get wrapper) |
| `_register(self, key, widget)` | register widget so language switch refreshes its text |
| `_setup_style(self)` | ttk theme (`theme_use("clam")`) + global styles |
| `_build_vars(self)` | create serial/display/send vars |
| `_switch_mode(self, mode)` | switch AT / stress / file panel |
| `_build_serial_card/_build_body/_build_monitor/_build_statusbar` | serial card / body / TX-RX area / statusbar |
| `send_text(self, text)` / `send_bytes(self, raw)` | send entry (encode/write) |
| `_poll_rx(self)` / `_flush_rx(self)` / `_append_line(self, direction, raw)` | receive poll / flush / render line |
| `_render_frame(self, direction, raw)` | render by frame (protocol-frame splitting) |
| `_open_log/_log_start/_log_stop` | logging on/off |
| `_save_config(self)` / `_on_close(self)` | save / exit |
| `_set_language(self, code)` / `_apply_language(self)` | zh/en switch |
| `_set_dot/_set_status_error/_update_status/_flash_status` | status indicators |
| `_update_counters/_clear_counters` | TX/RX counters |
| `_choose_log(self)` | choose log file |

**Public entry**: `run()` (module-level; creates Tk root and runs `mainloop`). `cli._start()` calls `app.run()`.

---

### 2.10 `at_panel.py` — AT command panel

Handles an editable AT list (pagination / select-all / encoding / suffix / HEX / Enter), save/load command groups, single-row send, and looped send (count + interval).

| Signature | Description |
|---|---|
| `__init__(self, master, app)` | build panel |
| `_send_row(self, idx)` | send a row |
| `_encode_row(self, v)` | encode row to bytes |
| `_selected_rows(self)` | enabled rows |
| `_run_loop(self)` | start looped send |
| `_loop_step(self)` | loop step (send next row after interval) |
| `_stop_loop(self)` | stop loop |
| `_load_config(self)` / `_save_config(self)` | load/save command group |
| `_read_config(self, name)` / `_write_config(self, name, commands)` | read/write named group |
| `_refresh_configs(self, select=None, keep=True)` | refresh group dropdown |
| `project_root()` / `configs_dir()` (module-level) | project root / config dir path |

**Callers**: `app` (panel as a child); serial writes go through `app.send_bytes` or `app.core`.

---

### 2.11 `stress_panel.py` — Stress-mode panel (state-machine core)

Handles stress config (count/duration, row interval, response timeout, AT/DOS Log), looped AT-list verification, custom check rules, run statistics and log annotations.

**State machine** (see §3): `_start_run` → `_send_current`(send) → `_wait_tick`(wait) → `_finish_response` → `_advance`(interval→next).

Selected methods:

| Signature | Description |
|---|---|
| `__init__(self, master, app)` | build all sub-areas |
| `_collect_rows(self)` | enabled non-empty rows → `_rows_run`; **auto-fills `"OK"` for empty expected** |
| `_start_run(self)` | init run state, disable run_btn, start first round |
| `_start_logs(self)` / `_stop_logs(self)` | open/close AT/DOS logs |
| `_header_line(self)` | build `=== name | count | interval | timeout ===` |
| `_row_bytes(self, row)` | encode row (codec.encode) |
| `_send_current(self)` | send current row; **prints `Runtimes N` marker on first row of each round** |
| `_schedule_wait(self, delay)` | schedule response collection |
| `_wait_tick(self)` | decide end-of-stream by silence/timeout, then `_finish_response` |
| `_finish_response(self)` | match expected/rules, count errors; `_row_idx+=1` then `_advance` |
| `_advance(self)` | rounds/end check; **row interval = interval_ms of "just-executed row" (>0 overrides global, 0 falls back)**; schedule next row |
| `_stop_run(self, finished=False)` | stop, write summary, restore buttons |
| `_append_summary(self)` | output `== Summary ==` (name/duration/run window/total rounds/sent/errors) |
| `_update_stats(self)` / `_tick_stats(self)` | stats refresh |
| `_log_round_marker(self, n)` | write `== Runtimes N ==` to output box + AT Log |
| `_edit_expected(self, gidx)` / `_sync_expected(self, gidx)` | expected editing |
| `_add_rule(self)` / `_del_rule(self, idx)` / `_collect_rules_ui(self)` | check-rule management |
| `_export_template/_export_data/_import_data` | CSV template/export/import |
| `_toggle_hex_all(self)` | HEX master checkbox: set all rows' `hex` on the current page to the same value (`hex_all_var`) |
| `_toggle_enter_all(self)` | Enter master checkbox: set all rows' `enter` on the current page to the same value (`enter_all_var`) |
| `_apply_type_all(self, _evt=None)` | Type batch dropdown: set all rows' `type` to the selected value (ignored if empty, `type_all_var`) |
| `_apply_suffix_all(self, _evt=None)` | Suffix batch dropdown: set all rows' `suffix` to the selected value (ignored if empty, `suffix_all_var`) |
| `_clear_at_list(self)` | one-click clear all AT commands in the current list (only clears memory rows, keeps row structure, does not touch templates/pending-import files; after confirm `_rows` rebuilt to blank default rows and back to page 1) |
| `_choose_log(self, tag)` | choose AT/DOS log file |

**Callers**: `app` creates `StressPanel` as the right column; internally uses `serial_core`, `stress_model`, `stress_io`, `codec`, `Logger`, `Tooltip`.

---

### 2.12 `file_panel.py` — File-send panel

Handles file selection, chunked send, progress/pause/cancel, background thread + queue feedback.

| Signature | Description |
|---|---|
| `__init__(self, master, app)` | build panel |
| `_choose_file(self)` | pick file |
| `_send_file(self)` | start send (spawns thread) |
| `_send_worker(self, path)` | background chunked-send thread |
| `_start_poll(self)` / `_poll_progress(self)` | progress polling |
| `_toggle_pause(self)` / `_update_pause_btn(self)` | pause/resume |
| `_finish_send(self)` / `_stop_old_send(self)` | finish / cancel old send |
| `_set_progress(self, frac)` | update progress bar |

**Callers**: `app`; the background thread talks to the main thread via `queue`, and the main thread reads progress with `root.after`.

---

### 2.13 `cli.py` — CLI entry

| Signature | Description |
|---|---|
| `main(argv=None)` | argparse parses `command(start)` & `--version`; return value = exit code |
| `_start()` | check tkinter; if missing print hint and return 1; else `app.run()` |
| `_check_tkinter()` | returns None or an install hint |
| `_tk_install_hint()` | platform-specific install hint |

---

## 3. Stress-Test State Machine

```
_start_run
   │  init stats/rounds, run_btn=disabled, _start_logs, header
   ▼
_send_current ───────────────┐  (row_idx==0 → _log_round_marker(N))
   │  write(row) → show RX   │
   ▼                          │
_wait_tick ──────────────────┤  (silence/timeout decides end-of-stream)
   ▼                          │
_finish_response ─────────────┤  (match expected/rules, count errors)
   │  _row_idx+=1              │
   ▼                          │
_advance ─────────────────────┘
   │  rows done? ──yes──> _rounds_done+=1, _row_idx=0
   │  end condition? ──yes──> _stop_run(finished=True)
   │  else: interval = prev row.interval_ms(>0)? * : global interval
   ▼
_schedule_follow(interval, _send_current)  →  back to _send_current
```

**Row-interval priority**: if the "just-executed row" (the row whose interval is the basis for the next wait) has `interval_ms>0`, use it; otherwise fall back to the global **row interval (ms)** in the stress config.

**Expected-result rule**: when a row's expected is empty, `_collect_rows` auto-fills `"OK"`, so `has_expected=True` and comparison happens; `match_expected` pass on hit, mismatch counts as an error.

---

## 4. Key Call Chains (examples)

- **Send AT**: `app.send_text(text)` → `codec.encode(...)` → `app.core.write(raw)` → `serial_core.write`.
- **Receive & display**: `serial_core` reader thread puts to queue → `app._poll_rx` (`after`) → `drain()` → `_flush_rx` → `_render_frame` → `_append_line` (output box + `Logger.log`).
- **One stress round**: `stress_panel._start_run` → `_send_current` → `core.write` + `_render_line`; RX handled via `_wait_tick/_finish_response`; `_advance` schedules next row.
- **Language switch**: `app._set_language` → `_apply_language` → refreshes registered widgets via `_t`.

---

## 5. ⚠️ Developer Note: E-SafeNet Encryption

- `ecom/*.py` may be encrypted by corporate security software (E-SafeNet) in the user's environment; **plain-text tooling / `read_file` may read ciphertext** (a past case: "reads 237 ciphertext lines while the disk file has 746 real lines").
- **Any source change**: use a Python script (`open(..., encoding='utf-8')` to read plaintext → string replacement → write back) for **byte-level replacement**, then validate syntax with `python -m compileall -q ecom`, and run `unittest discover tests` for regression.
- Do not save encrypted files with a plain text editor; `*.bak_*` backups are reference-only, do not modify.
