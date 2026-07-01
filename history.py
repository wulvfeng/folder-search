"""
搜索历史管理模块
"""
import os
import json
import threading
import logging
from typing import List, Dict, Any
from utils import get_timestamp, APP_CONFIG

logger = logging.getLogger(__name__)


class SearchHistory:
    """搜索历史管理类，支持持久化存储，带延迟保存机制"""
    
    def __init__(self, max_history: int = None, history_file: str = None):
        self.max_history = max_history or APP_CONFIG["max_history"]
        self.history_file = history_file or APP_CONFIG["history_file"]
        self.history: List[Dict[str, Any]] = []
        self.load_history()
        self._save_timer = None
        self._dirty = False  # 标记是否有未保存的更改

    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                    if not isinstance(self.history, list):
                        self.history = []
        except Exception as e:
            logger.warning(f"加载历史记录失败: {e}")
            self.history = []

    def save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            self._dirty = False
        except Exception as e:
            logger.warning(f"保存历史记录失败: {e}")

    def _schedule_save(self):
        """延迟保存，避免频繁IO操作"""
        if self._save_timer is not None:
            self._save_timer.cancel()
        self._save_timer = threading.Timer(1.0, self.save_history)
        self._save_timer.start()
        self._dirty = True

    def add_search(self, path: str, search_text: str, match_type: str, 
                   results_count: int, scan_mode: str):
        """添加搜索记录"""
        record = {
            "timestamp": get_timestamp(),
            "path": path,
            "search_text": search_text,
            "match_type": match_type,
            "results_count": results_count,
            "scan_mode": scan_mode
        }
        
        self.history.insert(0, record)
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        # 使用延迟保存
        self._schedule_save()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取搜索历史"""
        return self.history.copy()
    
    def clear_history(self):
        """清空搜索历史"""
        self.history.clear()
        self.save_history()
    
    def force_save(self):
        """强制保存（程序退出时调用）"""
        if self._save_timer is not None:
            self._save_timer.cancel()
        if self._dirty:
            self.save_history()
