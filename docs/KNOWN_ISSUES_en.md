# eCOM — Known Issues & Leftover Items

> Records the known limitations, unresolved issues, and development notes for the current version. **This list is updated as fixes land**; once fixed and verified, remove the item.

---

## 1. Unresolved Leftover Items

### 1.1 Stress panel not following the language switch (unfixed)

- **Symptom**: after switching zh/en via the Language menu, the main UI (app layer) text refreshes, but **some newly-added/complex controls inside the stress mode (stress_panel) do not follow**, staying in the pre-switch language.
- **Root cause**: `stress_panel`'s widgets are not wired into `EcomApp._register` (the language refresh mechanism only re-renders registered widgets), so the stress panel text is not re-rendered in `_apply_language`.
- **Impact**: mixed-language UI, inconsistent experience. This is a **known leftover item**.
- **Why not fixed**: wiring `_register` requires individually registering many stress-panel widgets and refreshing them in `_apply_language`; the change surface is large and prone to regressions, so it was not forced this round.
- **Workaround / follow-up**: to fix fully, add a `refresh_text()` method to `StressPanel` (iterate its own widgets and re-render via `_t`), then call it explicitly in `app._apply_language`. Until then, use a single language.

### 1.2 Old-version backup directory not cleaned up

- `xbak/` holds older backups, **left untouched for now**. Not source; does not affect runtime. Delete if no longer needed to reduce repo size.

---

## 2. Environment Constraints (dev/deploy)

### 2.1 Source encrypted by security software (E-SafeNet / DLP)

- **Symptom**: in some enterprise environments, `ecom/*.py` is encrypted by security software (E-SafeNet/DLP). Using plain-text tooling or `read_file`/`edit_file` yields **ciphertext or truncated content** — observed: `app.py` read as truncated **237 ciphertext lines** (real disk file **746 lines**), `file_panel.py` read as **29 ciphertext lines** (real **127 lines**).
- **Root cause**: DLP does transparent encrypt/decrypt by process whitelist; only whitelisted processes (e.g. `python389.exe`) can read plaintext.
- **Impact**: you **cannot** rely on a text editor/read tool to create or modify source; otherwise you either read ciphertext or overwrite the encrypted file destructively.
- **Correct dev approach**:
  1. Read plaintext with Python (whitelisted) via `open(..., encoding='utf-8')`;
  2. Do **byte-level string replacement** and write back;
  3. `python -m compileall -q ecom` to validate syntax;
  4. `python -m unittest discover tests` to run regression.
- **Note**: `*.bak_*` files are historical backups, **not source — do not modify**.

### 2.2 Real GUI screenshot not reliably auto-capturable

- **Symptom**: automating a screenshot of the real eCOM window (running `python main.py`) often yields a **blank/near-solid** image (measured average brightness ≈251.6), because desktop-level capture is occluded and depends on the window being in the foreground.
- **Impact**: interface screenshots in the docs are hard to auto-generate; they need to be captured manually on a local run (see the "Screenshot Requirements" list in `USER_GUIDE_*.md`).
- **Workaround**: maintainers run in a real environment and capture per the list; the current docs use ASCII layout diagrams + a mockup render as placeholders.

---

## 3. Behavioral / Boundary Limits

### 3.1 Stress end condition supports only two modes

- "End-by" supports **count** or **time** (up to N minutes) only; no "run forever" option (you can still click "Stop" to finish manually).
- A `== Summary ==` is printed only after **at least one complete round**; if stopped before a round completes or before the end condition, only the executed fragment is output.

### 3.2 Custom check rules are substring matching

- Rule keywords use simple **substring contains** (`keyword in response_text`), **not regex**; rules are disabled by default and must be enabled to take effect.
- A hit counts into `errors` and records the response to the chosen target (AT / DOS / BOTH).

### 3.3 Expected-result matching degradation

- The `regex` mode degrades to `contains` on an **invalid regex** (no error).
- `contains`/`exact` are substring-contains and trimmed-exact respectively.
- A row with an empty expected is **compared as default `OK`** (`StressRow.expected` defaults to `OK`; `_collect_rows` backfills empty expected with `OK`), so there's no "skip verification when expected is empty".

### 3.4 Row-interval semantics

- Each AT-list row may set its own `interval_ms`: **>0 takes priority over the global row interval; =0 falls back to the global「row interval (ms)」**.
- The interval is the wait **after that row finishes** — i.e. "prev row → wait → next row".

### 3.5 Port dependency & virtual ports

- Port enumeration depends on `pyserial`'s `list_ports`; without hardware you can type `loop://` (supported by `serial_for_url`) into the port field to self-test.
- Some devices may need the correct DTR/RTS setting to wake up.

### 3.6 Layout depends on window size

- The UI uses fixed weight columns (left ~2/3, right ~1/3); at very narrow widths the right/table may need horizontal scroll or text truncation. Use the default window size (~1000×850) or enlarge moderately.

---

## 4. Data / Compatibility Notes

- Config stored at `~/.ecom/config.json` (JSON, `ensure_ascii=False, indent=2`), shared across projects.
- AT-list export/import uses **CSV**: write `utf-8-sig` (BOM, opening cleanly in Windows Excel & readable on Linux); read supports both with/without BOM.
- Old configs with `send.suffix == "CRLF"` are auto-migrated to `"CR-LF"` on load.
- Logs are **byte-identical to the output box**: `[2026-08-26_13:47:23:903]  TX  AT+QGMR`, convenient for direct comparison.

---

## 5. Maintainer Checklist (read before developing)

1. **Read `PROGRESS.md` first** (the single source of truth) to restore context, focusing on "next steps / todo / unresolved issues".
2. **Modify source only via a Python script** doing byte-level replacement (E-SafeNet); never save encrypted files with a plain-text editor.
3. After each change: `py_compile` syntax check + `unittest discover tests` regression + a virtual-port smoke test.
4. For bilingual UI changes, add new keys to `i18n.py` and wire them into `_register`/refresh, to avoid new non-following-language items.

---

*Version: 0.1.0 · Language: English (Chinese version: `KNOWN_ISSUES_zh.md`)*
