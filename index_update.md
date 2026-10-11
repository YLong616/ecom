# index.html 修改记录

## 2026-09-15 修复工具模板输出以匹配 template.doc

### 问题描述
index.html 的工具模板（tool template）DOCX 输出与 template.doc 模板格式不符，主要差异：
1. 封面有行号（模板无行号）
2. 封面字体大小不匹配（版本号 20pt→26pt，"源程序清单" 20pt→26pt，编制单位/日期 14pt→26pt）
3. 代码正文有行号（模板无行号）
4. 左右边距 1250 twips→1797 twips（89.85pt）
5. 代码行距 270 twips→274 twips（13.7pt）
6. 封面行距 360 twips→240 twips

### 修改内容

#### 1. coverToolXml 函数（封面生成）
- **删除行号**：移除 `numRun`、`tabRun` 内部函数及制表位逻辑
- **统一字体大小**：所有封面内容段落统一使用 隶书 26pt（sz=52），包括：
  - 行2 系统名称（原已 26pt，不变）
  - 行3 版本号（20pt→26pt）
  - 行10-14 "源程序清单"竖排（20pt→26pt）
  - 行21 编制单位（14pt→26pt）
  - 行22 日期（14pt→26pt）
- **行距调整**：封面段落行距从 360 twips 改为 240 twips（w:lineRule="auto"）
- **居中对齐**：所有段落使用 `<w:jc w:val="center"/>` 居中

#### 2. bodyXml 函数（代码正文生成）
- **删除行号**：移除每行开头的行号文本（`run(String(li + 1), ...)`）和制表符（`<w:tab/>`）
- **删除制表位**：移除 `<w:tabs><w:tab w:val="left" w:pos="480"/></w:tabs>`
- **行距调整**：代码行距从 270 twips 改为 274 twips（13.7pt），含正文行和空白填充行

#### 3. sectPr 函数（页面设置）
- **左右边距**：从 1250 twips 改为 1797 twips（89.85pt），匹配模板

#### 4. codeLinePara 函数（代码行段落，当前未被调用，同步更新保持一致）
- 删除行号和制表位
- 行距从 270 twips 改为 274 twips

### 模板参数对照表

| 参数 | 模板值 (template.doc) | 修改前 | 修改后 |
|------|----------------------|--------|--------|
| 纸张 | A4 (11906×16838 twips) | A4 | A4（不变） |
| 上边距 | 72pt (1440 twips) | 1440 | 1440（不变） |
| 下边距 | 72pt (1440 twips) | 1440 | 1440（不变） |
| 左边距 | 89.85pt (1797 twips) | 1250 | 1797 |
| 右边距 | 89.85pt (1797 twips) | 1250 | 1797 |
| 封面字体 | 隶书 26pt | 隶书 14~26pt 不等 | 隶书 26pt |
| 封面行距 | 240 twips | 360 twips | 240 twips |
| 封面行号 | 无 | 有（1~22） | 无 |
| 代码字体 | 宋体 9pt | 宋体 9pt | 宋体 9pt（不变） |
| 代码行距 | 274 twips (13.7pt) | 270 twips | 274 twips |
| 代码行号 | 无 | 有 | 无 |
| 每页行数 | 50 | 50 | 50（不变） |
| 页眉 | 系统名称+版本号+页码 | 已有 | 已有（不变） |

---

## 2026-09-15 修复 4 个 BUG（弹框优化、信息校验、输出目录、标签）

### Bug 1: 排除的文件类型添加标签
- 在「排除的文件类型」标题后添加标签 `<span class="tag">选择保留的文件类型后可忽略</span>`
- 与「保留的文件类型」的「不选 = 全部」标签风格一致

### Bug 2: 未填写信息时弹框提示
- 新增 `DEFAULT_META` 常量，定义默认值：
  - 默认系统名称：软装申请的伟大系统
  - 默认系统版本：V1.0
  - 默认封面署名：EDISON
- 新增 `checkMetaOrPrompt()` 函数：
  - 检查系统名称、版本号、封面署名是否为空
  - 任一为空时弹出美观模态框，显示默认值列表
  - 两个按钮：「继续填写」（关闭弹框，用户自行填写）和「使用默认」（填入默认值）
  - 「使用默认」仅填入当前为空的字段，不覆盖已填写的值
- 在「生成并下载 DOCX」和「打印 / 导出 PDF」按钮点击时均先调用此校验
- `getMeta()` 函数同步更新，空值时回退到默认值

### Bug 3: 输出目录直接保存
- 删除 `showSaveFilePicker` 系统保存对话框逻辑（原代码在未指定输出目录时弹出保存对话框）
- 新逻辑：
  - 指定了输出目录（`outDirHandle`）→ 直接保存到该目录，Toast 通知成功
  - 未指定输出目录 → 浏览器默认下载，Toast 通知成功
  - 不再出现手动选择保存地址的对话框

### Bug 4: 全部弹框优化
- 新增模态弹框系统（`showModal`）：支持自定义图标、标题、正文、按钮列表
  - 模态框带半透明遮罩、圆角卡片、弹簧动画
  - 支持点击遮罩关闭、ESC 键关闭
  - 返回 Promise，支持异步等待用户选择
- 新增 Toast 通知系统（`showToast`）：右下角浮出式通知，自动消失
  - 四种类型：info（蓝）、success（绿）、warn（橙）、error（红）
- 新增快捷函数：`showInfo`（信息提示）、`showWarn`（警告提示）
- 替换全部 10 处 `alert()` 调用：
  | 原位置 | 替换为 |
  |--------|--------|
  | 输出目录-浏览器不支持 | showToast(warn) |
  | 输出目录-选择失败 | showToast(error) |
  | 输出目录-选择成功 | 新增 showToast(success) |
  | ensureReady-无入选文件 | showWarn |
  | ensureReady-无代码行 | showWarn |
  | DOCX-保存到输出目录成功 | showToast(success) |
  | DOCX-写入输出目录失败 | showToast(warn) |
  | DOCX-保存到所选位置成功 | 已删除（逻辑移除） |
  | DOCX-保存到所选位置失败 | 已删除（逻辑移除） |
  | DOCX-生成下载 | showToast(success) |
  | PDF-打印提示 | showInfo（模态框，用户点确定后打开打印） |

### CSS 新增
- `.modal-overlay` / `.modal-card` / `.modal-head` / `.modal-body` / `.modal-foot`：模态框样式
- `.toast-container` / `.toast`：Toast 通知样式
- `.modal-body .default-list`：默认值列表样式（用于 Bug 2 的信息填写提示）

---

## 2026-09-15 替换浏览器原生目录选择弹框

### 问题
点击「选择目录」时弹出浏览器原生的「是否将 N 个文件上传到此站点？」确认框，样式丑陋且无法通过 CSS 修改。

### 原因
原代码使用 `<input type="file" webkitdirectory>` 原生元素选择目录，浏览器会自动弹出上传确认弹框。

### 修改方案
改用 **File System Access API**（`showDirectoryPicker()`）：
- Chrome / Edge 桌面版直接使用 `showDirectoryPicker()`，弹出系统原生文件夹选择器（非上传确认框）
- 递归遍历目录树（`readDirRecursive`），逐个获取 `FileSystemFileHandle`
- 对每个文件句柄调用 `getFile()` 获取 `File` 对象（用于读取内容和文件大小）
- 不支持 `showDirectoryPicker()` 的浏览器回退到原有 `<input type="file">` 逻辑

### 代码变更
- 新增 `dirHandle` 变量（保存目录句柄）
- 新增 `readDirRecursive(handle, prefix)` 递归遍历函数
- 新增 `getExt(name)` 辅助函数
- 新增 `handleDirEntries(entries, rootName)` 统一处理函数（提取公共逻辑）
- `btn-dir` 点击事件：优先 `showDirectoryPicker()`，回退 `dir-input.click()`
- `dir-input` change 事件：仅作为回退保留，调用 `handleDirEntries`
- 目录加载成功后通过 `showToast` 提示文件数量

---

## 2026-09-15 两项微调

### 1. 默认系统名称修正
- `软装申请的伟大系统` → `软著申请的伟大系统`（修正错别字）

### 2. 移除输出目录功能
- 移除顶栏「输出目录（可选）」输入框和「选择…」按钮
- 移除 JS 变量 `outDirHandle`、`outDirName`
- 移除 `btn-outdir` 点击事件及相关逻辑
- 移除 `handleDirEntries` 中输出目录回显逻辑
- 移除 DOCX 生成中 `outDirHandle` 直接写入目录的逻辑，统一走浏览器下载
- 清理 CSS：`.field.w6`、`.outdir-box`、`.btn.mini`（已无使用）

### 3. 默认信息增加日期
- 新增 `getDefaultDate()` 函数，动态获取当前年月，格式 `YYYY.MM`（如 `2026.09`）
- `DEFAULT_META` 新增 `date` 字段，值为 `getDefaultDate()`
- `getMeta()` 中空日期回退到默认日期
- `checkMetaOrPrompt()` 校验中加入日期检查，未填写时默认值列表显示「默认日期」

---

## 2026-09-15 修复 DOCX 输出格式（页眉、行号、页码位置）

### 问题
1. 页眉没有黑色横线（模板有）
2. 代码页不显示行号（模板有）
3. 页码超出右页边距（位置不对）
4. 封面也需要行号（模板有）

### 修改内容

#### 1. 页眉添加黑色下边框
- `headerXml` 中段落边框底部从 `w:val="none"` 改为 `w:val="single"`，线宽 `sz="6"`（0.75pt），颜色黑色

#### 2. 代码页恢复行号
- `bodyXml` 中每行开头恢复行号文本（宋体 9pt）+ 制表位 + 代码
- 空白填充行也恢复行号
- 段落属性恢复 `<w:tabs><w:tab w:val="left" w:pos="480"/></w:tabs>`
- `codeLinePara` 函数同步恢复行号逻辑

#### 3. 修正页码右对齐位置
- 页眉右对齐制表位从 `w:pos="9406"` 改为 `w:pos="8312"`
- 计算：内容宽度 = 11906 - 1797 - 1797 = 8312 twips，页码正好对齐右页边距内侧

#### 4. 封面恢复行号
- `coverToolXml` 恢复行号列（宋体 9pt，1~22）
- 使用居中制表位 `w:val="center" w:pos="4156"`（内容宽度 8312 的中点，行号列占 480，居中位置约 4156）
- 行距保持 240 twips，字体保持隶书 26pt

---

## 2026-09-15 修复每页 50 行 & 页码位置调整

### 问题
1. 每页代码行数不精确，需要保证恰好 50 行
2. 60 页及以上的文档，最后一页也必须满 50 行
3. 页眉页码位置偏右，需要再往左移

### 修改内容

#### 1. 行距调整（274 → 279 twips）
- 计算：页面高度 16838 - 上边距 1440 - 下边距 1440 = 13958 twips
- 50 行 / 页 → 13958 / 50 = 279.16 twips，取整 279 twips（约 13.95pt）
- 50 × 279 = 13950 twips，几乎填满正文区域，确保每页恰好 50 行
- 同步更新 `bodyXml` 和 `codeLinePara` 中的行距

#### 2. 最后一页填充逻辑
- 新增 `fillLast` 判断：总页数 >= 60 时，最后一页也用空行填满到 50 行
- 不足 60 页时，最后一页可以不满 50 行（保持原有行为）
- 填满最后一页时，第 50 行末尾也加分页符

#### 3. 页码位置左移
- 页眉右对齐制表位从 `w:pos="7800"`（原 8312）
- 距右页边距内侧约 512 twips，视觉上更平衡

---

## 2026-09-15 彻底修复「每页只有 32 行」的根因

### 问题现象
导出的 DOCX 在 Word 中每页只能显示 32 行左右代码，50 行的块被拆成「32 行 + 18 行」两页。

### 排查过程（用 Word COM 实测，非猜测）
对用户实际导出的文件逐段测量，得到关键数据：

| 实测项 | 数值 | 说明 |
|--------|------|------|
| 代码段落 LineSpacing | 13.7pt / exact | 行距设置本身是对的 |
| **代码段落 SpaceAfter** | **8pt** | ← **真正的元凶** |
| 实际每行占用 | 13.7 + 8 = 21.7pt | 13958÷434 ≈ **32 行**，与现象完全吻合 |
| 分页结果 | 32+18 / 31+19 | 每块被拆两页 |

**根因**：生成的 DOCX **缺少 `word/styles.xml`**。Word 打开无样式定义的文档时，会套用内置「正文」样式（段后 8 磅 + 1.08 倍行距）。而 LibreOffice 默认段后为 0，所以本地用 LibreOffice 验证时看不出问题。

### 修复内容

#### 1. 补全 styles.xml（根本修复）
- 新增 `stylesXml`，显式定义 `w:docDefaults`：
  - `w:rPrDefault`：宋体 / 9pt
  - `w:pPrDefault`：`before="0" after="0" line="240" auto` + `widowControl=0`
  - `Normal` 默认段落样式同样声明段后 0
- 在 `[Content_Types].xml` 注册 `styles.xml`，在 `document.xml.rels` 加 `rId2` 关联
- `makeZip` 打包列表加入 `word/styles.xml`

#### 2. 所有段落显式声明段前段后为 0
- `codePPr()`：`<w:spacing w:before="0" w:after="0" .../>`
- `coverToolXml` 封面段落：同样显式声明
- 封面与正文之间的分节符段落：同样显式声明

#### 3. 段落属性顺序修正（符合 OOXML 规范）
- 顺序改为 `widowControl → tabs → snapToGrid → spacing → ind → rPr`
- 原顺序把 `snapToGrid` 放在 `spacing` 之后，不符合 CT_PPr 序列要求

#### 4. 动态行距 layoutCode()：解决折行导致的溢出
- **新问题**：即使段后归零，长代码行会**折行**占掉额外行高，模板的 13.7pt 行距余量为 0，
  只要有 1 行折行就会溢出。实测该用户 707 行代码：13.7pt → 26 页（严重溢出），13.0pt → 17 页，12.6pt → 16 页（正确）
- **方案**：
  - `measureRows(text)`：用 canvas 以 9pt 宋体度量单行宽度，得到折行后的行数
    （实测宋体半角字符宽度恰为字号一半：12px 字体下 ASCII=6px、CJK=12px，因此模型精确；
     canvas 不可用时回退到「半角 4.5pt / 全角 9pt」等效估算）
  - `layoutCode(pages)`：取所有页中「折行后总行数」的最大值 R，
    行距 = `正文高度(13958 twips) × 0.98 / R`，上限 274twips(模板值)、下限 200twips
  - 无折行时 R=50 → 13.65pt（贴近模板、页面填满）；折行多时自动收紧
  - 2% 安全系数用于抵消 Word 行高取整误差
- `buildDocx()` 与 `renderPrint()` 在生成前调用 `layoutCode()`
- 打印视图行高改用 CSS 变量 `--pv-lh`，与 DOCX 保持一致

### 验证结果（Word COM 实测，用户真实代码 707 行 / 15 个块）
| 行距 | 总页数 | 结论 |
|------|--------|------|
| 13.7pt（模板值） | 26 页 | 块严重溢出 |
| 13.0pt | 17 页 | 仍溢出 |
| 12.65pt（算法预测值） | 16 页 | 每块正好一页 ✓ |
| **12.4pt（含安全系数）** | **16 页** | **每页恰好 50 行 ✓** |

12.4pt 下逐页实测：第 1 页封面 23 段，第 2~15 页**每页 50 段**，第 16 页 7 段（末页不足 50 行，符合预期）。

### 新增常量
- `BODY_HEIGHT_TWIPS = 13958`：A4 正文可用高度
- `TEMPLATE_LINE_TWIPS = 274`：模板基准行距（上限）
- `MIN_LINE_TWIPS = 200`：行距下限
- `SAFETY = 0.98`：安全余量
- `CODE_LINE_TWIPS`：当前实际行距（由 `layoutCode()` 计算）
- `CODE_TEXT_WIDTH_PT = 391.6`：代码文本可用宽度（415.6pt 正文宽 − 24pt 行号制表位）

---

## 2026-09-15 封面版式还原 + 加密文件诊断

### 问题
1. 封面（第 1 页）的系统名称、版本号等版式被改动，用户要求还原
2. 导出后几乎没有代码：保留类型选 py、目录 F:\llm\ecom，结果正文只有 1 行

### 问题 2 排查过程（关键发现）
用 Node 在本地复现 index.html 的完整流水线（目录读取 → 过滤 → 去注释 → 分页）：

- 目录下 180 个 .py 文件全部入选
- 但其中 **163 个被判为「二进制」跳过**，只有 17 个被成功读取

进一步对比同一文件的读取结果：

| 读取方式 | `ecom/ecom/app.py` 前 48 字节 |
|---------|------------------------------|
| Python | `"""GUI 主窗口（Tkinter）。\r\n\r\nM1：端口...`（明文） |
| Node | `b\x14#e,\x00 \xef\xbf\xbd \x01\x00\x00\x00\x01E-SafeNet\x00\x00\x00LOCK...`（密文） |

**结论**：这台电脑安装了**亿赛通 E-SafeNet 透明加密软件**（企业 DLP）。
它只允许白名单进程（python.exe、PyCharm 等）读取明文；浏览器和 Node 都不在白名单里，
读到的就是加密后的密文（含大量 NUL 字节），因此触发「二进制检测」被跳过 → 正文几乎为空。
**这是环境限制，不是 index.html 的代码缺陷。**

### 修改内容

#### 1. 封面版式还原（`coverToolXml`）
- 封面段落显式声明 `w:after="160"`（8 磅）+ 单倍行距，还原用户确认过的封面版式
- 移除上一轮加入的 `w:before="0" w:after="0"` 和 `w:widowControl`
- 原因：新增的 `styles.xml` 把默认段后设成 0，若封面不显式声明段后，整页会被压缩
  （实测末行位置从 661pt 跌到 517pt）

**实测（Word COM）**：封面段后 = 8pt，末行（日期）位置 = **685.4pt**，
与 template.doc 基准 686.75pt 几乎一致；代码页仍为第 2~15 页每页 50 行、总 16 页。

#### 2. 加密文件诊断（`buildLines` + `ensureReady` + 新增 `warnEncrypted`）
- `buildLines` 新增 `binaryCount` 统计；跳过原因文案改为「二进制/密文已跳过」，
  并在注释中说明可能是透明加密软件所致
- 新增 `warnEncrypted()`：弹框说明透明加密原理（亿赛通 / 天锐绿盾 / 深信服等）
  并给出 4 种解决办法（客户端解密或外发、白名单程序另存、请 IT 加白名单、改用本地脚本）
- `ensureReady` 中新增两处判断：
  - 过滤后无代码行且存在密文文件 → 弹出加密说明
  - 密文文件占入选文件半数以上 → 导出前弹出加密说明，可选「取消」或「仍然继续」
- 效果：不再出现「导出一片空白却不知道为什么」的情况

---

## 2026-09-15 代码跑到封面页 + 行距被压到 11pt

### 问题（用户最新导出文件实测：3 页 / 123 段）
1. 第 1 页（封面页）里混进了 3 行代码，`1  __version__ = "0.1.0"` 出现在封面上
2. 代码行距变成 **11pt**，而不是模板的 13.7pt

### 排查
逐段读取 Word 实测数据：

| 现象 | 数据 |
|------|------|
| 第 1 页段落构成 | 26 段 = 22 封面 + 1 分节符 + **3 行代码** |
| 代码行行距 | `rule=4 line=11pt`（应为 13.7pt） |
| 分节起始方式 | 第 2 节 `SectionStart = 0`（**连续**分节，不是新页） |

**根因 1（代码跑到封面页）**：`sectPr()` 没有写 `<w:type>`。
缺失该元素时 Word 把分节当作「连续」，于是代码紧接着封面继续排在第 1 页。

**根因 2（行距被压到 11pt）**：截断宽度 `MAX_CODE_W = 88` 是错的。
9pt 宋体半角字符宽 4.5pt(90twips)，可用宽度 = 8312 − 480 = 7832twips，
最多只能放 `7832/90 = 87` 个半角字符。取 88 时行宽 396pt > 391.6pt，**每行都会折行**；
折行多占一行行高，导致 50 行放不下，`layoutCode()` 只能把行距一路压到 11pt。

### 修改内容

#### 1. `sectPr()` 显式声明分节类型为 nextPage
- 两处 sectPr 都加入 `<w:type w:val="nextPage"/>`
  （分节元素顺序：headerReference → type → pgSz → pgMar → pgNumType → cols → docGrid）
- 兼容两种语义解读，确保代码一定从新的一页开始

#### 2. `MAX_CODE_W` 88 → 86
- 理论极限 87 格（7830twips）距上限仅 2twips，Word 稍有差异就会折行，
  故取 86 留一格安全余量，保证**零折行**
- 零折行后 50 行正好放下，行距不再被压缩

#### 3. `layoutCode()` 行距取值规则
- 无折行（行数正好 50）时：直接用 `TEMPLATE_LINE_TWIPS = 274` = **13.7pt**，与模板完全一致
- 仅当确实折行、50 行放不下时，才按 `正文高度 × 0.98 ÷ 行数` 收紧行距

### 验证结果（Word COM 实测，用用户最新 100 行代码）
| 检查项 | 结果 |
|--------|------|
| 总页数 | 3 页（1 封面 + 2 代码页） |
| 第 1 页 | **23 段 = 纯封面 + 分节符，已无任何代码** |
| 第 2 页 / 第 3 页 | **各 50 行** |
| 首行代码位置 | 第 2 页 |
| 代码行距 | **13.7pt** |
| 封面 | 段后 8pt、日期行 top=685.4pt（版式未受影响） |
| 页眉 | 「软著申请的伟大系统 V1.0 1」正常显示 |

---

## 2026-09-15 新增「代码页数」输入框（默认 60 页，超出即丢弃）

### 需求
- 代码页总共只保留 N 页，超出部分丢弃；默认 60 页，用户可自行设置
- 输入框放在「日期」旁边
- 第 1 页的系统信息（封面）不计入页数

### 修改内容

#### 1. 界面（顶部信息栏）
- 「日期」右侧新增 `#inp-pages`：`<input type="number" min="1" max="9999" step="1" value="60">`
  - 标签「代码页数」，宽度 92px（新增 `.field.w1 input`）
  - 带 `title` 提示：「只导出前 N 页代码（封面不计入）。默认 60 页」
- 结果卡片标签由「总页数（50 行/页）」改为「代码页数（50 行/页）」，
  数值改为显示**本次实际导出的页数**，鼠标悬停显示「代码共 X 页，本次导出 Y 页，已丢弃 Z 页」

#### 2. 逻辑
- 删除已无用的 `CNIPA_PAGES` 常量，新增 `DEFAULT_PAGES = 60`
- 新增 `getPageLimit()`：读取输入框，非法/空值回退到 60，上限 9999
- `pagesForTemplate(pages)`：
  - 工具模板 → `pages.slice(0, limit)`（只保留前 N 页代码，超出丢弃）
  - 国知局模板 → `cnipaPages(pages, limit)`（超过 N 页时取前一半 + 后一半，
    默认 60 页时即原来的「前 30 + 后 30」，行为不变）
- `updateLines()` 的统计与提示文案同步显示「共 X 页 / 导出 Y 页 / 已丢弃 Z 页」
- 输入框绑定 `change` 事件（而非 `input`，避免每次敲键都重算），
  触发时把非法值回写为默认值并刷新统计
- DOCX 与 PDF 两条导出路径都经过 `pagesForTemplate()`，限制对两者同时生效
- 页数只约束**代码页**，封面独立于 pages 数组之外，天然不计入

### 验证结果（Word COM 实测，707 行代码）
| 设置 | 导出结果 |
|------|---------|
| 代码页数 = 3 | 共 4 页：p1=封面 23 段、**p2/p3/p4 各 50 行**；末行为第 3 页第 50 行 |
| 代码页数 = 60（默认） | 共 16 页：p1 封面、p2~p15 各 50 行、p16 = 7 行（全部 15 页代码，未超 60） |

两种设置下行距均为 **13.7pt**，首行代码均在第 2 页（封面无代码）。

---

## 2026-09-15 翻页方式改「段前分页」+ 页数卡片与设置位置调整

### 问题
2. 每个代码页**首行上方多出空白**，把第 50 行挤到下一页
3. 「代码页数」卡片跟着用户设定的导数值变化，应固定显示目录内可导出的**总页数**
4. 把「导出页数上限」输入框移到「代码页数」卡片旁边，UI 做成统计卡片样式

### 修改内容

#### 1. 翻页改用「段前分页」（根因修复）
- 旧实现：在第 50 行段落**内部**追加 `<w:br w:type="page"/>`（`pageBreakRun()`）
- 新实现：给每页**首行段落**加 `<w:pageBreakBefore/>`（`codePPr(breakBefore)`），
  并删除 `pageBreakRun()`
- 原因：段内分页符会把该段落的**段落标记留在下一页**，于是下一页首行上方多出一个空行；
  部分渲染器（WPS / LibreOffice）会如实呈现，导致每页只排下 49 行、第 50 行被挤走。
- 段落属性顺序：`pageBreakBefore → widowControl → tabs → snapToGrid → spacing → ind → rPr`

#### 2. 「代码页数」卡片固定显示总页数
- `$("st-pages")` 由导出页数改回 `pages.length`（目录内可导出的代码页总数）
- 悬停提示：「目录内共 X 页代码（50 行/页，封面不计入）；本次导出 Y 页，超出上限丢弃 Z 页」
- 下方提示条仍说明本次实际导出与丢弃情况

#### 3. 页数设置移到统计卡片区
- 移除顶部信息栏的「代码页数」输入框
- 在「代码页数」卡片右侧新增统计卡片，「导出页数上限」输入框放在卡片的数字位
- `.stat-grid` 由 4 列改 5 列；`.stat .num input` 与统计数字同字体/字号/颜色，
  用虚线下划线表示可编辑；隐藏数字输入框的上下箭头
- 「代码页数」标签简化为「代码页数」，「50 行/页」移入悬停提示

### 验证结果（Word COM 实测，707 行代码，导出上限 5 页）
| 检查项 | 结果 |
|--------|------|
| 总页数 | 6 页（1 封面 + 5 代码页） |
| 每页段落数 | 封面 23，p2~p6 **各 50 行** |
| 每个代码页首行 top | **恒为 72pt**（正好等于上边距，无空行占位） |
| 行间距 | 13.85pt（规格 13.7pt） |
| XML 结构 | `pageBreakBefore` 出现 4 次（5 页 4 个分页），`w:br type="page"` 为 **0** |

---

## 2026-09-15 新增「排除的文件名」过滤器

### 背景（关于列表首行 `__version__ = "0.1.0"`）
用户反馈列表首行出现 `1  __version__ = "0.1.0"`，怀疑是程序自行添加的内容。
核查结论：**该行来自用户自己的源文件**，程序不会生成任何代码行：

```
F:\llm\ecom\ecom\ecom\__init__.py
  1  """eCOM — 跨平台串口调试工具"""
  2
  3  __version__ = "0.1.0"
```

- 第 1 行 docstring 与第 2 行空行被「去注释 / 删空行」处理掉，只剩第 3 行
- 入选文件按路径自然排序，`ecom/__init__.py` 排在最前，因此这一行成为列表首行

### 修改内容：新增「排除的文件名」过滤器（左栏，位于「排除的文件夹」下方）
- `state.excludeNames`：按文件名小写精确匹配
- `getSelected()` 增加该条件的排除判断
- 新增 `collectNames(entries)`：选择目录后自动列出全部文件名（小写去重）作为可点击建议
- 新增标签输入框 `wrap-exnames` / `suggest-exnames`，提示语「输入文件名后回车，如 __init__.py」
- 用户在框内加入 `__init__.py` 后，该行即从列表中消失（若某文件仅贡献 1 行，排除该文件即等于去掉那一行）

### 验证（用真实目录 F:\llm\ecom 跑完整流水线）
| 检查项 | 结果 |
|--------|------|
| 排除 `__init__.py` 后是否仍入选 | **否** ✅ |
| 列表中是否还有 `__version__ = "0.1.0"` | **没有** ✅ |
| 列表首行变为 | `from __future__ import annotations` ✅ |

---

## 2026-09-15 【严重】行号改为 Word 自动行号（此前手写行号属篡改源码）

### 问题
此前把行号当作**正文文字**写进每个代码行前（`1<TAB>代码`），用户指出：
行号应该是 Word 的**行号版式配置**，手写行号等于篡改源码内容，会导致材料无法过审。

### 模板实测（template.doc）
用 Word COM 读取模板的两个分节：

| 项 | 模板值 |
|----|--------|
| LineNumbering.Active | **True**（两个分节都是） |
| CountBy / StartingNumber | 1 / 1 |
| Distance | 0 |
| 代码段落是否含手写行号 | **否**（段落文本首字符就是代码） |

把模板转成 docx 后读原始 OOXML，分节里只有一行：

```xml
<w:lnNumType w:countBy="1"/>
```

未写 `w:restart` → 按 OOXML 默认值即 **newPage（每页从 1 重新编号）**；
未写 `w:distance` → 默认 0，行号紧贴正文左侧画在页边距内。
模板 PDF 实测：每个代码页行号都是 **1…50**（第3、4页同样从 1 开始）。

### 修改内容

#### 1. `sectPr()` 增加自动行号设置
- 代码分节（`withHeader = true`）加入 `<w:lnNumType w:countBy="1"/>`，与模板完全一致
- 顺序：`headerReference → type → pgSz → pgMar → lnNumType → pgNumType → cols → docGrid`
- 封面分节不加（封面沿用模板那样的文字行号列 1~22），避免模板中那处多余的行号

#### 2. 删除全部手写行号
- `bodyXml()`：每个代码行只输出代码本身，删除行号 run 与制表位 run
- 填充行改为真正的空段落（Word 自动行号同样会给它编号）
- `codePPr()`：删除 `<w:tabs>`（行号已移到页边距，正文不再需要让位）
- `codeLinePara()` 同步改为只输出代码

#### 3. 可用宽度随之增大
- 正文不再被行号列占用：可用宽度 `391.6pt → 415.6pt`（行号画在左侧页边距内）
- `CODE_TEXT_WIDTH_PT` = 415.6；`MAX_CODE_W` 由 86 改为 **91**
  （415.6 / 4.5 = 92.3 个半角字符，取 91 留一格余量）

### 验证结果（Word COM + PDF 实测，707 行代码、上限 5 页）
| 检查项 | 模板 | 本次输出 |
|--------|------|---------|
| 行号来源 | Word 自动行号 | **Word 自动行号**（第 2 分节 Active=True） |
| 每页行号序列 | 1…50 | **1…50**（pdfplumber 提取确认，每页 50 个） |
| 行号 x 坐标 | 61.3 ~ 66.6 | **67.3** |
| 正文起始 x | 89.9 | **89.9** |
| 末行 y | 746.0 | **746.6** |
| 正文是否含手写数字 | 无 | **无**（段落首字符即代码） |
| 每页行数 | 50 | **50**（p2~p6） |
| 行距 | 13.7pt | **13.7pt** |

---

## 2026-09-16 移除 PDF 导出功能

### 变更
- 删除 `btn-pdf` 按钮（打印 / 导出 PDF），仅保留 `btn-docx`（生成并下载 DOCX）并设为 primary 样式
- 删除 `#print-root` 容器及其全部 CSS（打印视图容器、`@media print` 样式、`.pv-*` 类）
- 删除 `renderPrint()` 函数（打印视图渲染逻辑）
- 保留 `escHtml()` 函数（UI 其他模块仍在使用）
- 删除 `btn-pdf` 事件监听器及其 `window.print()` 调用

---

## 2026-09-16 文件级删除 + 重新扫描

### 新增功能
- **文件行删除按钮**：每个文件行末尾新增 `.del-btn`（垃圾桶图标，默认 45% 透明，hover 变红）。
  点击后弹出确认框「确认删除」，提供「取消」「确认删除」两个按钮；
  仅当确认时把该文件 `relPath` 加入 `state.deletedPaths`，该文件代码不再参与导出。
- **重新扫描按钮**：`<h2>扫描结果与入选文件` 右侧新增 `#btn-rescan`（刷新图标 + 「重新扫描」文案，
  `margin-left:auto` 右对齐）。点击后复用已保存的 `dirHandle` 静默重读目录，
  清空 `state.deletedPaths`，恢复完整文件列表；不支持 File System Access API 时回退为重新触发 `#dir-input`。

### 实现要点
- `state` 新增两个字段：
  - `deletedPaths: Set<relPath>` — 用户手动删除的文件集合
  - `rootName: string` — 已加载目录名（供重新扫描与 `dir-path` 展示）
- `getSelected()` 首位新增 `if (state.deletedPaths.has(en.relPath)) return false;`，
  删除的文件在入选、代码行统计、页数统计、DOCX 导出全链路中一并失效。
- `handleDirEntries()` 重置 `deletedPaths` 并记录 `rootName`。
- `onStateChange()`：
  - 「扫描文件总数」显示有效文件数（`entries.length - deletedPaths.size`），
    `title` 显示「原扫描 N 个，已手动删除 M 个，可点击重新扫描恢复」
  - `#dir-path` 目录信息随删除实时同步，附「已删除 N」提示
- 新增 `deletedTip()`：在底部提示栏追加「已手动删除 N 个文件（不计入导出），可点击「重新扫描」恢复」。
- 弹框内容经 `escHtml()` 转义，避免文件名注入 HTML。

### 样式
```css
.file-row .del-btn{...;opacity:.45}
.file-row .del-btn:hover{color:#dc2626;border-color:#fca5a5;background:#fef2f2;opacity:1}
.file-row:hover .del-btn{opacity:1}
.panel h2 .rescan-btn{...;margin-left:auto;border:1px solid var(--accent-line);
  background:var(--accent-soft);color:var(--accent-strong);...}
```

### 验证
- 页面为单文件自包含 HTML，无任何外部依赖（无外链 script/link/src），无 iframe、无沙箱，双击即可在浏览器直接运行
- 内联脚本语法检查通过
- 静态交叉校验：脚本内 18 处 `$("id")` 引用与 HTML 的 29 个 id 全部匹配；无 PDF 残留
- 逻辑核对项：删除后 `getSelected()` 过滤生效、卡片与目录信息计数同步、`deletedTip` 输出、
  重新扫描清空 `deletedPaths`、`handleDirEntries` 重置删除集合、行内 `.del-btn` 与 `data-rel` 渲染、`btn-rescan` 事件绑定

---

## 2026-09-16 移除「国知局标准」模板，仅保留工具模板

### UI 变更
- 底栏 `<div class="tpl-group">`（两个 `radio-card` 单选）替换为静态徽标 `<div class="tpl-badge">`：
  「输出模板」+ 带文档图标的「工具模板」胶囊 + 说明文字「全部代码 · 50 行/页」。
  不再需要选择，模板固定为工具模板。
- CSS 删除 `.tpl-group{...}`、`.tpl-group .lbl`、`.radio-card`、`.radio-card input`、`.radio-card.on`；
  新增 `.tpl-badge`、`.tpl-badge .lbl`、`.tpl-badge .chip-fixed`、`.tpl-badge .sub`。

### 逻辑变更
- 删除全局变量 `var curTemplate = "tool";`（含全部引用）。
- 删除 `cnipaPages(pages, limit)`（原「前一半 + 后一半」取页逻辑）。
- `pagesForTemplate(pages)` 简化为 `return pages.slice(0, getPageLimit());`。
- 删除 `coverCnipaXml(meta)`（国知局居中简洁封面）。
- `bodyXml(pages, meta, template)` → `bodyXml(pages, meta)`，封面固定调用 `coverToolXml(meta)`。
- `buildDocx(pages, meta, template)` → `buildDocx(pages, meta)`，行距固定执行 `layoutCode(pages)`。
- `updateLines()` 提示文案去掉 `curTemplate === "cnipa"` 分支，固定输出工具模板提示。
- `btn-docx` 生成逻辑：`label` 固定为「工具模板」，`buildDocx` 不再传模板参数。
- 删除「模板单选」事件监听（`input[name="tpl"]` 的 change 与 `.radio-card` 初始高亮）。

### 验证
- 内联脚本语法检查通过；脚本内 `$("id")` 引用与 HTML id 全部匹配
- 全文件检索 `cnipa` / `国知局` / `curTemplate` / `radio-card` / `tpl-group` / `coverCnipa`：残留 0 处
- `buildDocx` / `bodyXml` / `pagesForTemplate` / `coverToolXml` 的签名与调用点逐一核对一致
