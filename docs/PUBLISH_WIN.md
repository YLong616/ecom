# eCOM Windows 本机发布手册（PyPI）

> 适用：在**当前 Windows 机器**（源文件被 E-SafeNet 加密）上完成打包并上传 PyPI，无需 Linux。
> 按 §4 的命令顺序执行即可；§1 先读，§7 是验证，§8 是坑。

---

## 1. 关键结论（先读）

| 项 | 值 |
|---|---|
| 发行名（`pip install` 用） | `ecom-serial-tool` |
| 命令名 / 模块名 | `ecom`（不受发行名影响） |
| **当前版本** | **0.2.0** |
| 版本号必须**两处一致** | `pyproject.toml` 的 `version` + `ecom/__init__.py` 的 `__version__` |
| 上传产物（dist/ 下 2 个） | `ecom_serial_tool-0.2.0.tar.gz`、`ecom_serial_tool-0.2.0-py3-none-any.whl` |
| Python 依赖 | `pyserial>=3.5`、`openpyxl>=3.0`（安装时自动拉） |
| 系统级依赖 | `tkinter`（pip 装不了；Linux 需 `sudo apt install python3-tk`） |
| 构建工具 | `setuptools>=61`、`wheel`、`build`、`twine` |

> ⚠️ **`ecom` 这个名字在 PyPI 上已被他人占用**（电商框架）。发行名必须用 `ecom-serial-tool`，
> 否则 `pip install ecom` 装到别人的包。命令名/模块名 `ecom` 不受影响。

> ⚠️ **必须用 `E:\software\python389\python.exe` 构建，且加 `--no-isolation`**。
> 该解释器是唯一对 E-SafeNet 密文源**透明解密**的进程：加 `--no-isolation` 才能让 setuptools
> 在**同一个进程**里读到明文；普通 `python -m build`（默认隔离建 venv，venv 里的 python.exe
> 不在白名单）会把**密文**打进 wheel，用户装完 `import ecom` 直接炸。

> 💡 **副产品是好消息**：白名单进程（python389）**新写出的文件在磁盘上是明文**（实测 `findstr`
> 等普通进程也能读）。所以 `dist/` 里的 wheel/sdist 可以直接上传或拷贝到别的机器。

---

## 2. 发布前要改的文件（只有 1 处必需，2 个文件）

| 文件 | 改什么 | 说明 |
|---|---|---|
| `pyproject.toml` | `version = "0.2.0"` | 决定产物文件名与 PyPI 版本；**每次发布必须比上一版大** |
| `ecom/__init__.py` | `__version__ = "0.2.0"` | `ecom --version` / 关于弹窗读的是这里；**必须与上一处一致** |

可选（不影响上传）：
- `README.md`：PyPI 项目页正文（即 `readme = "README.md"`）。改完记得重新构建。
- 建议打个 tag：`git tag v0.2.0 && git push --tags`。

> 已经发布过 `0.1.0`（PyPI 上已有），所以**本次必须用 0.2.0 或更高**；同名同版本会被拒（见 §8）。

---

## 3. 前置条件

1. PyPI 账号；**API Token**（`https://pypi.org/manage/account/token/`，只显示一次）。
2. 本机 `E:\software\python389\python.exe` 可用（Python 3.8.9，自带 tkinter）。
3. 构建工具已装（命令见 §4 第 1 步，已装会提示 already satisfied）。
4. 能访问 `pypi.org`。
5. Token **只放在当前 cmd 会话的环境变量**里，不要写进文件/仓库/截图。

---

## 4. 完整命令（同一个 cmd 窗口，按顺序）

```bat
:: ---------- 0) 进项目根目录 ----------
cd /d E:\software\quecagent\workspaces\EdisonCode\projects\eCOM

:: ---------- 1) 确认版本号两处一致（都应是 0.2.0）----------
findstr /N "version" pyproject.toml
findstr /N "__version__" ecom\__init__.py
:: 不一致就先改齐再往下（改完记得重跑本步骤确认）

:: ---------- 2) 构建工具（首次或换机器才需要）----------
"E:\software\python389\python.exe" -m pip install --upgrade setuptools wheel build twine

:: ---------- 3) 清掉旧产物（关键！dist 里现在还有 0.1.0，不清会被一起传上去）----------
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
for /d %d in (*.egg-info) do @rmdir /s /q "%d"

:: ---------- 4) 构建（必须 --no-isolation）----------
"E:\software\python389\python.exe" -m build --no-isolation

:: ---------- 5) 元数据校验（两行都应是 PASSED）----------
"E:\software\python389\python.exe" -m twine check dist\*

:: ---------- 6) 产物“明文”校验（关键，防密文进包）----------
:: 能在 wheel 里搜到明文文件名 -> 说明打进包的是明文，可放心上传
findstr /M /C:"ecom/cli.py" dist\*.whl
findstr /M /C:"ecom/macro.py" dist\*.whl
:: 上面两条都要打印出 whl 文件名；若什么都没打印，立刻停下按 §8-2 排查

:: ---------- 7) 包完整性冒烟：解 sdist -> 编译 -> 跑测试 ----------
rmdir /s /q "%TEMP%\ecom_verify" 2>nul
mkdir "%TEMP%\ecom_verify"
tar -xf dist\ecom_serial_tool-0.2.0.tar.gz -C "%TEMP%\ecom_verify"
cd /d "%TEMP%\ecom_verify\ecom_serial_tool-0.2.0"
"E:\software\python389\python.exe" -m compileall -q ecom
"E:\software\python389\python.exe" -m unittest discover tests
:: 期望：全部用例通过（当前 142 个）。这一步同时证明“包里的源码是完整的、可编译的”

:: ---------- 8) 本地试装（装到临时目录，别覆盖你日常在用的 ecom）----------
set SMOKE=%TEMP%\ecom_smoke
rmdir /s /q "%SMOKE%" 2>nul
"E:\software\python389\python.exe" -m pip install --no-deps --target "%SMOKE%" ^
    "E:\software\quecagent\workspaces\EdisonCode\projects\eCOM\dist\ecom_serial_tool-0.2.0-py3-none-any.whl"
set PYTHONPATH=%SMOKE%
"E:\software\python389\python.exe" -c "import ecom, ecom.macro, ecom.clipboard; print('版本', ecom.__version__)"
set PYTHONPATH=

:: ---------- 9) 回到项目目录，上传 ----------
cd /d E:\software\quecagent\workspaces\EdisonCode\projects\eCOM

:: 先演练（可选，强烈建议）：TestPyPI 需要单独的 token
set TWINE_USERNAME=__token__
set TWINE_PASSWORD=pypi-测试token
"E:\software\python389\python.exe" -m twine upload --repository-url https://test.pypi.org/legacy/ dist\*

:: 正式上传（把密码换成正式 token）
set TWINE_USERNAME=__token__
set TWINE_PASSWORD=pypi-正式token
"E:\software\python389\python.exe" -m twine upload dist\*
```

> 环境变量只在当前 cmd 会话有效 —— `set`、`twine upload` 必须连着执行，别关窗口。
> 想免去每次 set：在 `%USERPROFILE%\.pypirc` 写 `[pypi]` 段（`username = __token__` / `password = pypi-...`），
> 然后只需 `-m twine upload dist\*`；记得该文件不要进仓库。

---

## 5. dist/ 里该有什么（上传对象）

| 文件 | 说明 |
|---|---|
| `ecom_serial_tool-0.2.0.tar.gz` | sdist 源码包 |
| `ecom_serial_tool-0.2.0-py3-none-any.whl` | 平台无关 wheel（py3 = Python 3，none-any = 跨平台） |

**不要上传**：`dist/` 之外的一切（源码、`docs/`、`configs/`、`tests/`、`*.zip`、`.bak`、`__pycache__`）。
wheel + sdist 已包含运行所需全部内容（含随包的 `ecom/docs/*.md` 手册）。

---

## 6. 打包范围（为什么只有 ecom/ 进包）

- `[tool.setuptools.packages.find] include = ["ecom*"]` → 只打 `ecom/` 包；
- `[tool.setuptools.package-data] ecom = ["docs/*.md"]` → 额外把 `ecom/docs/TROUBLESHOOT_zh.md`、
  `ecom/docs/TROUBLESHOOT_en.md` 打进包（`ecom help` 与 GUI「帮助 → Linux 串口排障手册」读的就是它）。

---

## 7. 发布后验证

**(A) 线上（任意机器）**

```bat
"E:\software\python389\python.exe" -m pip install --no-cache-dir --upgrade ecom-serial-tool==0.2.0
ecom --version                 :: 期望：ecom 0.2.0
ecom help                      :: 期望：打印 Linux 串口排障手册（证明 ecom/docs 已进包）
ecom start                     :: 期望：弹出 GUI
```
> 刚上传完可能命中 CDN 缓存，等 1–2 分钟或加 `--no-cache-dir`。
> 也可用项目里的 `tools\check_pypi.py` 直接查 PyPI 上的版本与产物清单。

**(B) 本机注意**：`pip install ecom-serial-tool` 会**覆盖 `E:\software\python389\lib\site-packages\ecom`**
—— 那正是你日常 `ecom start` 用的那份（开发时你们是手动同步过去的）。所以本机冒烟请用 §4-8 的
`--target` 方式（装到临时目录），别直接装到 site-packages。

**回滚/下线**：PyPI 不支持删除已发布版本；出错就 **Yank** 该版本（不再被默认安装），或发新版本覆盖。

---

## 8. 常见的坑

1. **`400 File already exists`** → 版本号没升（或 `dist/` 里残留旧版本文件被一起传）。
   处理：改两处版本号 → `rmdir /s /q dist` → 重跑 §4-4 起。
2. **wheel 里是密文**（用户 `import ecom` 报 SyntaxError / 乱码）→ 漏了 `--no-isolation`，或没用 python389。
   用 §4-6 的 `findstr` 自检即可当场发现。
3. **`403 Invalid or non-existent authentication`** → token 不对/权限不足；要用**项目 scope + upload 权限**的 token。
4. **`twine check` FAIL** → README 渲染问题（相对链接/图片在 PyPI 页面会失效，通常只是警告）。
5. **版本号两处不一致** → `ecom --version` 与 PyPI 版本对不上，排查困难；发布前务必跑 §4-1。
6. **不要 `python setup.py upload`** → 已废弃且被 PyPI 拒绝；只用 `python -m build` + `twine`。
7. **tkinter 缺失**（用户侧）→ 系统包，Windows 官方 Python 自带；Linux 需 `python3-tk`。
8. **别把加密树里的文件直接 zip 上传**：顶层 `docs/` 的参考文档在本机是占位/密文；需要明文素材时走 §9。

---

## 9. 附：重建明文源码包（传别的机器 / 重建包内手册时才需要）

用 python389（白名单）打包，**只收运行所需**，产出的 zip 在磁盘上就是明文（可被普通进程读取）：

```python
# 用 "E:\software\python389\python.exe" 运行
import os, zipfile
base = r'E:\software\quecagent\workspaces\EdisonCode\projects\eCOM'
out = os.path.join(base, 'ecom_plain_src.zip')
targets = ['pyproject.toml', 'README.md', 'requirements.txt', 'main.py', 'run.bat',
           'ecom', 'tests', 'scripts', 'configs']
skip_dirs = {'__pycache__', '.git'}
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for t in targets:
        p = os.path.join(base, t)
        if os.path.isfile(p):
            z.write(p, t)
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                for f in files:
                    rp = os.path.join(root, f)
                    z.write(rp, os.path.relpath(rp, base))
print('done', out)
```

> 重建包内手册（`ecom/docs/*.md`）：从明文 zip 里取 `ecom/docs/TROUBLESHOOT_{zh,en}.md` 写回即可；
> 或直接在本机用 python389 读顶层 `docs/TROUBLESHOOT_{zh,en}.md`（白名单进程能读明文）再写入 `ecom/docs/`。
