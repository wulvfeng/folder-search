"""
工具函数和配置模块
"""
import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger(__name__)

# 应用配置
APP_CONFIG = {
    "app_name": "高级文件夹扫描器",
    "version": "3.2",
    "max_history": 100,
    "history_file": "search_history.json",
    "default_encoding": ['utf-8', 'gbk', 'gb2312', 'latin-1', sys.getdefaultencoding()],
    "max_workers": min(8, (os.cpu_count() or 1) + 2),
    "progress_update_interval": 50,  # 进度更新间隔
}

# 匹配类型配置
MATCH_TYPES = [
    {"value": "contains", "name": "包含匹配", "description": "文件夹名称包含搜索文本"},
    {"value": "startswith", "name": "开头匹配", "description": "文件夹名称以搜索文本开头"},
    {"value": "endswith", "name": "结尾匹配", "description": "文件夹名称以搜索文本结尾"},
    {"value": "wildcard", "name": "通配符匹配", "description": "使用 * 匹配多个字符，? 匹配单个字符"},
    {"value": "regex", "name": "正则表达式", "description": "使用正则表达式进行高级匹配"},
]

def get_timestamp() -> str:
    """获取时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_decode_path(path_name: str, supported_encodings: List[str]) -> str:
    """安全解码路径名称"""
    for encoding in supported_encodings:
        try:
            return path_name.encode('latin-1').decode(encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return path_name.replace('\ufffd', '_')  # 替换无法解码的字符

def is_valid_path(path: str) -> bool:
    """验证路径是否有效"""
    try:
        path_obj = Path(path)
        return path_obj.exists() and path_obj.is_dir()
    except Exception:
        return False

def get_platform_open_command() -> str:
    """获取平台相关的打开命令"""
    if sys.platform == "win32":
        return "start"
    elif sys.platform == "darwin":
        return "open"
    else:
        return "xdg-open"
