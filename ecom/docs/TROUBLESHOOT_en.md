# Linux Serial Troubleshooting Guide

Applies to: eCOM on Linux (Ubuntu etc.). Symptom: after opening a serial port, sending an AT command shows only `TX` with no `RX` reply; or the port is reported as busy / fails to open.

## 1. Most common root cause: ModemManager grabs the AT port

**Symptoms:**
- The port opens successfully, but sending AT shows only `TX`, no `RX`.
- Sending AT via shell / microcom works, but not via eCOM.
- `lsof <port>` / `fuser <port>` shows `ModemManager` holding the port.

**Why:** ModemManager auto-takes over cellular modules as a "WWAN card". It opens the AT port itself and continuously sends its own init commands, so eCOM's AT gets no clean reply.

```bash
lsof /dev/ttyUSB3        # see who holds it
fuser /dev/ttyUSB3       # print holding PIDs
```

## 2. Option A (recommended, permanent): make ModemManager ignore the modem via udev

- Pros: permanent, no code change, does not globally disable ModemManager, reversible by deleting the rule.
- Best for: long-term AT debugging with this module, if you don't need it as a system WWAN card.

**Steps:**

1) Find the real USB vendor/product ID:
```bash
udevadm info -a -n /dev/ttyUSB3 | grep -E "idVendor|idProduct"
```
Take the values under `SUBSYSTEM=="usb"`, e.g. `<idVendor>:<idProduct>` (replace with the values you actually found).

2) Create the rule file (replace `<VID>` / `<PID>` with your real values):
```bash
echo 'ACTION=="add|change", SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="<VID>", ATTRS{idProduct}=="<PID>", ENV{ID_MM_DEVICE_IGNORE}="1"' | sudo tee /etc/udev/rules.d/99-mm-ignore.rules
```

3) Reload and trigger:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo systemctl restart ModemManager
```
If still not in effect, unplug/replug the module, or reboot.

**Pitfalls (common):**
- Must be on `SUBSYSTEM=="usb"` + `DEVTYPE=="usb_device"`; **do NOT put it on a tty**, otherwise the `ID_MM_DEVICE_IGNORE` env never reaches the USB device.
- The rule is only read at device enumeration; reload online needs `udevadm trigger` or replug.

**Verify:**
```bash
sudo systemctl start ModemManager
lsof /dev/ttyUSB3        # should no longer show ModemManager
mmcli -m                 # ModemManager should no longer list this modem
```
Then open eCOM and send `AT+QGMR`; it should return `OK` immediately.

## 3. Option B (temporary, re-apply after reboot): stop ModemManager

```bash
sudo systemctl stop ModemManager
```
- Note: effective only until reboot; ModemManager will take the port again after boot. Good for a quick temporary session.
- To disable permanently (trade-off):
```bash
sudo systemctl disable --now ModemManager
```
- Caution: disabling globally also affects other cellular modems / host WWAN capability.

## 4. Other common Linux serial pitfalls

- **Port permissions**: open failures often mean the user is not in the `dialout` group.
  ```bash
  sudo usermod -aG dialout $USER   # then log out/in
  ```
- **UUCP lock / port busy**: "port is locked" messages. Use `fuser <port>` / `lsof <port>` to find the holder, close it, then reopen.
- **E-SafeNet encrypted source**: if you copied encrypted `.py` files (source is ciphertext) to Linux, `python3` cannot read them (null bytes). Use the plaintext source.
- **Baud rate doubts**: such cellular modules are usually USB CDC-ACM devices; the host-side termios baud rate is cosmetic (cannot be set, stays 9600) and is **unrelated** to successful AT communication. No need to chase baud.

## 5. Quick check: is it ModemManager?

```bash
# If eCOM immediately returns OK after stopping ModemManager, ~90% it was the culprit
sudo systemctl stop ModemManager
# reopen the eCOM port and test AT
# bring it back after testing
sudo systemctl start ModemManager
```
