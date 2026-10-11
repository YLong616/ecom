# Linux 串口排障手册

适用场景：eCOM 在 Linux（Ubuntu 等）上打开串口后，发送 AT 命令只有 TX、无 RX 返回；或打开串口提示被占用 / 失败。

## 1. 最常见根因：ModemManager 抢占 AT 口

**现象：**
- 串口已成功打开，发送 AT 只显示 `TX`，没有 `RX` 返回。
- 用 shell / microcom 手动发 AT 正常，但 eCOM 不行。
- `lsof <port>` / `fuser <port>` 能看到 `ModemManager` 占着该端口。

**原理：** ModemManager 会自动把蜂窝模组当成"上网卡"接管，自己打开 AT 口并持续发送初始化命令，导致 eCOM 发出的 AT 收不到干净的响应。

```bash
lsof /dev/ttyUSB3        # 看谁占着
fuser /dev/ttyUSB3       # 给占用进程 PID
```

## 2. 方案一（推荐，一劳永逸）：用 udev 让 ModemManager 忽略该模组

- 优点：永久生效、不动任何代码、不全局禁用 ModemManager、可随时删规则恢复。
- 适合：长期使用该模组做 AT 调试，且不需要把它当系统上网卡。

**步骤：**

1）查出模组真实的 USB 厂商/产品号：
```bash
udevadm info -a -n /dev/ttyUSB3 | grep -E "idVendor|idProduct"
```
取位于 `SUBSYSTEM=="usb"` 段下的值，例如 `<idVendor>:<idProduct>`（用你实际查到的值替换）。

2）创建规则文件（把 `<VID>` / `<PID>` 换成你的真实值）：
```bash
echo 'ACTION=="add|change", SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="<VID>", ATTRS{idProduct}=="<PID>", ENV{ID_MM_DEVICE_IGNORE}="1"' | sudo tee /etc/udev/rules.d/99-mm-ignore.rules
```

3）重载并触发：
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo systemctl restart ModemManager
```
若仍不生效，拔插一次模组，或重启机器。

**陷阱（社区常踩）：**
- 必须写在 `SUBSYSTEM=="usb"` + `DEVTYPE=="usb_device"` 上，**不要写到 tty 上**，否则 `ID_MM_DEVICE_IGNORE` 设不到 USB 设备、不生效。
- 规则只在设备"枚举"时读取，在线重载需 `udevadm trigger` 或拔插。

**验证：**
```bash
sudo systemctl start ModemManager
lsof /dev/ttyUSB3        # 应不再有 ModemManager
mmcli -m                 # ModemManager 不再列出该模组
```
再开 eCOM 发 `AT+QGMR`，应秒回 `OK`。

## 3. 方案二（临时，重启后需重来）：停止 ModemManager

```bash
sudo systemctl stop ModemManager
```
- 说明：仅本次开机生效，重启后 ModemManager 又会接管。适合临时快速用。
- 彻底禁用（可选，需取舍）：
```bash
sudo systemctl disable --now ModemManager
```
- 注意：全局禁用会影响系统里其它蜂窝网卡/蜂窝上网能力。

## 4. 其它 Linux 串口常见坑

- **端口权限**：打开失败常因用户不在 `dialout` 组。
  ```bash
  sudo usermod -aG dialout $USER   # 之后注销重新登录
  ```
- **UUCP 锁文件 / 被占用**：打开时提示"被其它程序占用"。先 `fuser <port>` / `lsof <port>` 看是谁占着，关闭占用进程再开。
- **E-SafeNet 加密源码**：Linux 端若复制到的是被加密的 `.py`（源码为密文），`python3` 无法解读、会报 null bytes。必须使用明文版源码。
- **波特率疑问**：这类蜂窝模组多为 USB CDC-ACM 设备，host 端 termios 波特率是"摆设"（设不进、停在 9600），**与 AT 正常通信无关**，无需纠结波特率。

## 5. 快速判断是否 ModemManager 问题

```bash
# 如果 stop ModemManager 后 eCOM 立刻能收到 OK，90% 是它抢占
sudo systemctl stop ModemManager
# 重新打开 eCOM 串口并发 AT 测试
# 测完可再 start 回来
sudo systemctl start ModemManager
```
