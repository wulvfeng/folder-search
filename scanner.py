"""
文件夹扫描器核心模块
"""
import sys
import os
import fnmatch
import re
import time
import threading
import queue
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any
from utils import APP_CONFIG, MATCH_TYPES

logger = logging.getLogger(__name__)


class FastFolderScanner:
    """高性能文件夹扫描器"""
    
    def __init__(self, max_workers=None):
        self.supported_encodings = APP_CONFIG["default_encoding"]
        self.max_workers = max_workers or APP_CONFIG["max_workers"]
        self._stop_event = threading.Event()
        self._lock = threading.Lock()  # 线程锁
        self.scanned_count = 0
        self.start_time = 0
        self._current_folders = []
        self._decode_cache = {}  # 路径解码缓存
        self._regex_cache = {}   # 正则表达式缓存
        self.progress_update_interval = APP_CONFIG["progress_update_interval"]
    
    def stop_scan(self):
        """停止扫描"""
        self._stop_event.set()
    
    def get_current_folders(self):
        """获取当前已扫描的文件夹"""
        with self._lock:
            return self._current_folders.copy()
    
    def scan_folders(self, path: str, scan_mode: str = "current", 
                    progress_callback=None) -> Tuple[bool, List[Dict], str]:
        """
        扫描文件夹
        """
        self._stop_event.clear()
        with self._lock:
            self.scanned_count = 0
            self.start_time = time.time()
            self._current_folders = []
        
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return False, [], "路径不存在"
            if not path_obj.is_dir():
                return False, [], "输入的不是一个目录"
            
            folders = []
            
            if scan_mode == "current":
                folders = self._scan_current_directory(path_obj, progress_callback)
            else:
                folders = self._scan_recursive_fixed(path_obj, progress_callback)
            
            if self._stop_event.is_set():
                with self._lock:
                    folders = self._current_folders
                folders.sort(key=lambda x: x['name'].lower())
                return True, folders, "扫描已停止，显示已扫描结果"
            
            folders.sort(key=lambda x: x['name'].lower())
            elapsed = time.time() - self.start_time
            logger.info(f"扫描完成: {len(folders)} 个文件夹, 耗时: {elapsed:.2f}秒")
            
            return True, folders, ""
            
        except PermissionError as e:
            return False, [], f"权限错误: {str(e)}"
        except Exception as e:
            return False, [], f"扫描错误: {str(e)}"
    
    def _scan_current_directory(self, path_obj: Path, progress_callback=None) -> List[Dict]:
        """扫描当前目录"""
        folders = []
        
        try:
            with os.scandir(path_obj) as entries:
                for entry in entries:
                    if self._stop_event.is_set():
                        break
                        
                    if entry.is_dir():
                        try:
                            folder_name = self._safe_decode_path(entry.name)
                            folder_data = {
                                'name': folder_name,
                                'full_path': entry.path,
                                'display_name': folder_name
                            }
                            with self._lock:
                                folders.append(folder_data)
                                self._current_folders.append(folder_data)
                                self.scanned_count += 1
                                
                            if progress_callback and self.scanned_count % self.progress_update_interval == 0:
                                progress_callback(self.scanned_count, folder_name)
                                
                        except (UnicodeDecodeError, OSError):
                            continue
                            
        except (PermissionError, OSError) as e:
            logger.warning(f"无法访问目录 {path_obj}: {e}")
        
        return folders
    
    def _scan_recursive_fixed(self, path_obj: Path, progress_callback=None) -> List[Dict]:
        """修复的递归扫描算法"""
        all_folders = []
        scanned_paths = set()
        
        def get_folder_info(dir_path, base_path):
            try:
                folder_name = self._safe_decode_path(dir_path.name)
                try:
                    relative_path = dir_path.relative_to(base_path)
                    display_name = f"{folder_name} ({relative_path})"
                except ValueError:
                    display_name = folder_name
                
                return {
                    'name': folder_name,
                    'full_path': str(dir_path),
                    'display_name': display_name
                }
            except (UnicodeDecodeError, OSError):
                return None
        
        def scan_directory_bfs(root_path):
            folders_queue = queue.Queue()
            folders_queue.put(root_path)
            scanned_paths.add(root_path.resolve())
            
            local_folders = []
            
            while not folders_queue.empty() and not self._stop_event.is_set():
                current_dir = folders_queue.get()
                
                try:
                    with os.scandir(current_dir) as entries:
                        for entry in entries:
                            if self._stop_event.is_set():
                                return local_folders
                                
                            if entry.is_dir():
                                try:
                                    entry_path = Path(entry.path)
                                    real_path = entry_path.resolve()
                                    
                                    if real_path not in scanned_paths:
                                        scanned_paths.add(real_path)
                                        
                                        folder_info = get_folder_info(entry_path, root_path)
                                        if folder_info:
                                            with self._lock:
                                                local_folders.append(folder_info)
                                                self._current_folders.append(folder_info)
                                                self.scanned_count += 1
                                            folders_queue.put(entry_path)
                                            
                                            if progress_callback and self.scanned_count % self.progress_update_interval == 0:
                                                progress_callback(self.scanned_count, folder_info['name'])
                                                
                                except (OSError, ValueError) as e:
                                    logger.debug(f"跳过目录 {entry.path}: {e}")
                                    continue
                                    
                except (PermissionError, OSError) as e:
                    logger.warning(f"无法访问目录 {current_dir}: {e}")
                    continue
            
            return local_folders
        
        try:
            if progress_callback:
                progress_callback(0, "开始递归扫描...")
            
            all_folders = scan_directory_bfs(path_obj)
            
        except Exception as e:
            logger.error(f"递归扫描错误: {e}")
        
        return all_folders
    
    def _safe_decode_path(self, path_name: str) -> str:
        """安全解码路径名称，带缓存机制"""
        # 检查缓存
        if path_name in self._decode_cache:
            return self._decode_cache[path_name]
        
        result = None
        for encoding in self.supported_encodings:
            try:
                result = path_name.encode('latin-1').decode(encoding)
                break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        
        if result is None:
            result = path_name.replace('\ufffd', '_')  # 替换无法解码的字符
        
        # 保存到缓存
        self._decode_cache[path_name] = result
        return result
    
    def fuzzy_match(self, folders: List[Dict], search_text: str, 
                   match_type: str = "contains", case_sensitive: bool = False) -> List[Dict]:
        """模糊匹配，优化正则表达式性能"""
        if not search_text:
            return folders
        
        matched_folders = []
        regex_pattern = None
        
        if match_type == "regex":
            # 使用缓存的正则表达式
            cache_key = f"{search_text}_{case_sensitive}"
            if cache_key not in self._regex_cache:
                try:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    self._regex_cache[cache_key] = re.compile(search_text, flags)
                except re.error:
                    return matched_folders
            regex_pattern = self._regex_cache[cache_key]
        
        # 预处理搜索文本
        search_pattern = search_text if case_sensitive else search_text.lower()
        
        for folder in folders:
            folder_name = folder['name']
            target_text = folder_name if case_sensitive else folder_name.lower()
            
            try:
                match_found = False
                
                if match_type == "contains":
                    if search_pattern in target_text:
                        match_found = True
                elif match_type == "startswith":
                    if target_text.startswith(search_pattern):
                        match_found = True
                elif match_type == "endswith":
                    if target_text.endswith(search_pattern):
                        match_found = True
                elif match_type == "wildcard":
                    pattern = search_pattern
                    if '*' not in pattern and '?' not in pattern:
                        pattern = f"*{pattern}*"
                    if fnmatch.fnmatch(target_text, pattern):
                        match_found = True
                elif match_type == "regex" and regex_pattern:
                    if regex_pattern.search(target_text):
                        match_found = True
                
                if match_found:
                    matched_folders.append(folder)
                    
            except Exception:
                continue
        
        return matched_folders
    
    def get_match_types(self) -> List[Dict[str, str]]:
        """获取匹配类型"""
        return MATCH_TYPES
