"""i18n 语言资源：中文(zh) / 英文(en)。

用法：
    from . import i18n
    i18n.get(lang, "open")                 # 取文本
    i18n.get(lang, "tx", n=12)             # 带格式化
    i18n.lang_label(lang)                  # 语言本名（用于菜单）
"""

SUPPORTED_LANGUAGES = ["zh", "en"]

I18N = {
    "zh": {
        "app_title": "eCOM 串口调试工具",
        # 菜单
        "menu_file": "文件",
        "menu_exit": "退出",
        "menu_settings": "设置",
        "menu_language": "语言",
        # LoG/Log
        "log_select": "选择Log文件…",
        "log_start": "开始记录Log",
        "log_stop": "停止记录Log",
        "log_on": "记录Log",
        "log_off": "未记录Log",
        "log_config": "Log 保存",
        # 串口卡
        "serial_settings": "串口配置",
        "port": "端口",
        "refresh": "刷新",
        "baudrate": "波特率",
        "databits": "数据位",
        "stopbits": "停止位",
        "parity": "校验位",
        "flow": "流控",
        "open": "打开串口",
        "close": "关闭串口",
        "clear_counters": "清零计数",
        "tx": "发送 {n}",
        "rx": "接收 {n}",
        "byte": "字节",
        # 状态
        "status_connected": "已连接",
        "status_disconnected": "未连接",
        "status_idle": "空闲",
        "status_error": "串口异常: {e}",
        # 监控 Tab
        "tab_monitor": "监控",
        "display_options": "显示选项",
        "display_timestamp": "时间戳",
        "display_direction": "方向",
        "display_crlf": "显示\\r\\n",
        "display_hex": "接收HEX",
        "dtr": "DTR",
        "rts": "RTS",
        "dtr_rts": "Flow Pins",
        "dtr_rts": "流控引脚",
        "output": "输出（接收）",
        "clear_output": "清空输出",
        "input": "输入（发送）",
        "cast": "监视",
        "send": "发送",
        "clear_input": "清空输入",
        "send_type": "类型",
        "send_suffix": "后缀",
        # AT 面板
        "tab_at": "AT 命令",
        "at_group": "命令组",
        "at_new": "新建",
        "at_delete": "删除",
        "at_save": "保存",
        "at_add_cmd": "添加",
        "at_del_cmd": "删除选中",
        "at_send": "发送",
        "at_send_all": "发送全部",
        "at_dbl_hint": "双击命令快速发送",
        "at_click_hint": "单击命令即发送；右键管理",
        "at_clear_group": "清空组",
        "at_clear_confirm": "确定清空当前命令组？",
        "at_group_name": "输入新命令组名称:",
        "at_empty_group": "（该组为空，请在下方输入命令）",
        "at_no_cmd": "请先选中一条命令",
        # 文件面板
        "tab_file": "文件发送",
        "file_select": "选择文件…",
        "file_path": "文件",
        "file_size": "大小",
        "file_bytes": "字节",
        "file_send": "发送文件",
        "file_clear": "清空",
        "file_no_file": "请先选择文件",
        "file_sent": "已发送 {n} 字节",
        "file_append_suffix": "发送后追加后缀",
        "file_open_fail": "文件不存在或不可读",
        "file_row_label": "文件发送",
        "file_no_path": "（未选择文件）",
        # 通用
        "no_port": "[提示] 未选择串口。",
        "open_fail": "[错误] 打开串口失败: {e}",
        "send_fail": "[错误] 发送失败: {e}",
        "serial_error": "[串口错误] {e}",
    },
    "en": {
        "app_title": "eCOM Serial Tool",
        # Menus
        "menu_file": "File",
        "menu_exit": "Exit",
        "menu_settings": "Settings",
        "menu_language": "Language",
        # Log
        "log_select": "Choose Log File…",
        "log_start": "Start Logging",
        "log_stop": "Stop Logging",
        "log_on": "Logging",
        "log_off": "Not Logging",
        "log_config": "Log Save",
        # Serial card
        "serial_settings": "Serial Settings",
        "port": "Port",
        "refresh": "Refresh",
        "baudrate": "Baudrate",
        "databits": "Data Bits",
        "stopbits": "Stop Bits",
        "parity": "Parity",
        "flow": "Flow Control",
        "open": "Open Port",
        "close": "Close Port",
        "clear_counters": "Clear Counters",
        "tx": "TX {n}",
        "rx": "RX {n}",
        "byte": "bytes",
        # Status
        "status_connected": "Connected",
        "status_disconnected": "Disconnected",
        "status_idle": "Idle",
        "status_error": "Serial error: {e}",
        # Monitor tab
        "tab_monitor": "Monitor",
        "display_options": "Display",
        "display_timestamp": "Timestamp",
        "display_direction": "Direction",
        "display_crlf": "Show CR-LF",
        "display_hex": "RX HEX",
        "dtr": "DTR",
        "rts": "RTS",
        "output": "Output (Receive)",
        "clear_output": "Clear Output",
        "input": "Input (Send)",
        "cast": "Watch",
        "send": "Send",
        "clear_input": "Clear Input",
        "send_type": "Type",
        "send_suffix": "Suffix",
        # AT panel
        "tab_at": "AT Commands",
        "at_group": "Group",
        "at_new": "New",
        "at_delete": "Delete",
        "at_save": "Save",
        "at_add_cmd": "Add",
        "at_del_cmd": "Remove",
        "at_send": "Send",
        "at_send_all": "Send All",
        "at_dbl_hint": "Double-click to send",
        "at_click_hint": "Click a command to send; right-click to manage",
        "at_clear_group": "Clear Group",
        "at_clear_confirm": "Clear the current command group?",
        "at_group_name": "Enter new group name:",
        "at_empty_group": "(empty — type below to add)",
        "at_no_cmd": "Select a command first",
        # File panel
        "tab_file": "File Send",
        "file_select": "Choose File…",
        "file_path": "File",
        "file_size": "Size",
        "file_bytes": "bytes",
        "file_send": "Send File",
        "file_clear": "Clear",
        "file_no_file": "Choose a file first",
        "file_sent": "Sent {n} bytes",
        "file_append_suffix": "Append suffix",
        "file_open_fail": "File missing or unreadable",
        "file_row_label": "File Send",
        "file_no_path": "(no file selected)",
        # Common
        "no_port": "[Info] No port selected.",
        "open_fail": "[Error] Failed to open port: {e}",
        "send_fail": "[Error] Failed to send: {e}",
        "serial_error": "[Serial Error] {e}",
    },
}


def get(lang, key, **fmt):
    try:
        text = I18N[lang][key]
    except KeyError:
        text = key
    if fmt:
        try:
            return text.format(**fmt)
        except (IndexError, KeyError):
            return text
    return text


def lang_label(lang):
    """语言的本名（不随当前语言翻译）。"""
    return "中文" if lang == "zh" else "English"
