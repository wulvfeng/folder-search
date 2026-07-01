"""
GUI界面模块
"""
import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QListWidget, QComboBox, 
    QCheckBox, QGroupBox, QSplitter, QProgressBar, QMessageBox, 
    QFileDialog, QStatusBar, QTabWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QRadioButton, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from scanner import FastFolderScanner
from history import SearchHistory
from utils import APP_CONFIG, logger


class ScanThread(QThread):
    """扫描线程"""
    scan_finished = pyqtSignal(bool, list, str)
    scan_progress = pyqtSignal(int, str)
    
    def __init__(self, path, scanner, scan_mode):
        super().__init__()
        self.path = path
        self.scanner = scanner
        self.scan_mode = scan_mode
        self.is_running = True
    
    def run(self):
        """执行扫描"""
        def progress_callback(count, current_folder):
            if self.is_running:
                self.scan_progress.emit(count, current_folder)
        
        try:
            success, folders, error = self.scanner.scan_folders(
                self.path, self.scan_mode, progress_callback
            )
            if self.is_running:
                self.scan_finished.emit(success, folders, error)
        except Exception as e:
            if self.is_running:
                self.scan_finished.emit(False, [], f"扫描异常: {str(e)}")
    
    def stop(self):
        """停止扫描"""
        self.is_running = False
        self.scanner.stop_scan()
        self.quit()
        self.wait(2000)


class CompleteFolderScannerGUI(QMainWindow):
    """完整的文件夹扫描器GUI"""
    
    def __init__(self):
        super().__init__()
        self.scanner = FastFolderScanner()
        self.search_history = SearchHistory()
        self.scan_thread = None
        self.current_folders = []
        self.current_path = ""
        self.scan_start_time = 0
        self.current_scan_mode = "current"
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("🚀 高级文件夹扫描器 v3.2")
        self.setGeometry(100, 100, 1400, 900)
        
        # 初始化状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🟢 就绪 - 请选择扫描路径")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        scan_tab = QWidget()
        tab_widget.addTab(scan_tab, "🔍 文件夹扫描")
        self.setup_scan_tab(scan_tab)
        
        history_tab = QWidget()
        tab_widget.addTab(history_tab, "📊 搜索历史")
        self.setup_history_tab(history_tab)
        
        help_tab = QWidget()
        tab_widget.addTab(help_tab, "❓ 使用帮助")
        self.setup_help_tab(help_tab)
    
    def setup_scan_tab(self, parent):
        """设置扫描标签页"""
        layout = QVBoxLayout(parent)
        
        self.setup_control_area(layout)
        self.setup_progress_area(layout)
        self.setup_results_area(layout)
    
    def setup_control_area(self, parent_layout):
        """设置控制区域"""
        path_layout = QHBoxLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("请输入或选择要扫描的路径...")
        self.path_input.textChanged.connect(self.on_path_changed)
        
        self.browse_btn = QPushButton("📁 浏览")
        self.browse_btn.clicked.connect(self.browse_path)
        self.browse_btn.setFixedWidth(80)
        
        mode_group = QGroupBox("扫描模式")
        mode_layout = QHBoxLayout(mode_group)
        self.mode_current = QRadioButton("当前文件夹")
        self.mode_recursive = QRadioButton("递归扫描所有子文件夹")
        self.mode_current.setChecked(True)
        mode_layout.addWidget(self.mode_current)
        mode_layout.addWidget(self.mode_recursive)
        
        button_layout = QHBoxLayout()
        self.scan_btn = QPushButton("🔍 开始扫描")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setFixedWidth(120)
        
        self.stop_btn = QPushButton("⏹️ 停止扫描")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedWidth(120)
        
        button_layout.addWidget(self.scan_btn)
        button_layout.addWidget(self.stop_btn)
        
        path_layout.addWidget(QLabel("路径:"))
        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(self.browse_btn)
        path_layout.addWidget(mode_group)
        path_layout.addLayout(button_layout)
        
        parent_layout.addLayout(path_layout)
        
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索文本...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        # 搜索建议列表
        self.search_suggestions = QListWidget()
        self.search_suggestions.setMaximumHeight(150)
        self.search_suggestions.setVisible(False)
        self.search_suggestions.itemClicked.connect(self.on_suggestion_clicked)
        
        self.match_type_combo = QComboBox()
        for match_type in self.scanner.get_match_types():
            self.match_type_combo.addItem(match_type["name"], match_type["value"])
        
        self.case_sensitive_check = QCheckBox("区分大小写")
        
        self.search_btn = QPushButton("🔎 搜索")
        self.search_btn.clicked.connect(self.start_search)
        self.search_btn.setEnabled(False)
        self.search_btn.setFixedWidth(80)
        
        # 创建搜索输入框和建议的垂直布局
        search_input_layout = QVBoxLayout()
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.search_suggestions)
        search_input_layout.setSpacing(0)
        search_input_layout.setContentsMargins(0, 0, 0, 0)
        
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addLayout(search_input_layout, 1)
        search_layout.addWidget(QLabel("模式:"))
        search_layout.addWidget(self.match_type_combo)
        search_layout.addWidget(self.case_sensitive_check)
        search_layout.addWidget(self.search_btn)
        
        parent_layout.addLayout(search_layout)
    
    def setup_progress_area(self, parent_layout):
        """设置进度显示区域"""
        progress_group = QGroupBox("📊 扫描进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        progress_info_layout = QHBoxLayout()
        
        self.progress_label = QLabel("就绪")
        self.progress_label.setStyleSheet("color: #666; font-size: 10pt;")
        
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("color: #009688; font-size: 10pt;")
        
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #2196F3; font-size: 10pt; font-weight: bold;")
        
        progress_info_layout.addWidget(self.progress_label, 2)
        progress_info_layout.addWidget(self.speed_label)
        progress_info_layout.addWidget(self.count_label)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(progress_info_layout)
        
        parent_layout.addWidget(progress_group)
    
    def setup_results_area(self, parent_layout):
        """设置结果区域"""
        results_splitter = QSplitter(Qt.Horizontal)
        
        all_group = QGroupBox("📂 所有文件夹")
        all_layout = QVBoxLayout(all_group)
        
        self.all_folders_list = QListWidget()
        self.all_folders_list.itemDoubleClicked.connect(self.on_folder_double_clicked)
        all_layout.addWidget(self.all_folders_list)
        
        self.all_count_label = QLabel("总计: 0 个文件夹")
        self.all_count_label.setStyleSheet("color: #666; padding: 5px;")
        all_layout.addWidget(self.all_count_label)
        
        match_group = QGroupBox("🎯 匹配结果")
        match_layout = QVBoxLayout(match_group)
        
        # 添加导出按钮
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("📥 导出结果")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        self.export_btn.setFixedWidth(100)
        export_layout.addStretch()
        export_layout.addWidget(self.export_btn)
        match_layout.addLayout(export_layout)
        
        self.matched_folders_list = QListWidget()
        self.matched_folders_list.itemDoubleClicked.connect(self.on_matched_folder_double_clicked)
        match_layout.addWidget(self.matched_folders_list)
        
        self.matched_count_label = QLabel("匹配: 0 个文件夹")
        self.matched_count_label.setStyleSheet("color: #666; padding: 5px;")
        match_layout.addWidget(self.matched_count_label)
        
        results_splitter.addWidget(all_group)
        results_splitter.addWidget(match_group)
        results_splitter.setSizes([500, 500])
        
        parent_layout.addWidget(results_splitter, 1)
    
    def setup_history_tab(self, parent):
        """设置历史记录标签页"""
        layout = QVBoxLayout(parent)
        layout.setSpacing(15)
        
        button_layout = QHBoxLayout()
        
        self.refresh_history_btn = QPushButton("🔄 刷新历史")
        self.refresh_history_btn.setFont(QFont("Microsoft YaHei", 10))
        self.refresh_history_btn.clicked.connect(self.refresh_history)
        self.refresh_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        self.clear_history_btn = QPushButton("🗑️ 清空历史")
        self.clear_history_btn.setFont(QFont("Microsoft YaHei", 10))
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        button_layout.addWidget(self.refresh_history_btn)
        button_layout.addWidget(self.clear_history_btn)
        button_layout.addStretch()
        
        self.history_table = QTableWidget()
        self.history_table.setFont(QFont("Microsoft YaHei", 9))
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "⏰ 时间", "📁 路径", "🔍 搜索文本", "🎯 匹配模式", "📊 结果数量", "模式"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addLayout(button_layout)
        layout.addWidget(self.history_table, 1)
        
        self.refresh_history()
    
    def setup_help_tab(self, parent):
        """设置帮助标签页"""
        layout = QVBoxLayout(parent)
        layout.setSpacing(15)
        
        help_text = QTextEdit()
        help_text.setFont(QFont("Microsoft YaHei", 10))
        help_text.setReadOnly(True)
        
        help_content = """
<h1>📖 文件夹扫描器使用帮助</h1>

<h2>🎯 主要功能</h2>
<ul>
<li><b>快速扫描</b> - 扫描指定路径下的文件夹</li>
<li><b>智能搜索</b> - 多种匹配模式快速定位目标文件夹</li>
<li><b>历史记录</b> - 自动保存搜索历史，方便重复使用</li>
<li><b>一键打开</b> - 双击匹配结果直接打开对应文件夹</li>
<li><b>结果导出</b> - 支持导出为TXT、CSV、JSON格式</li>
</ul>

<h2>🔍 扫描模式</h2>
<p><b>当前文件夹模式</b><br>
只扫描指定路径下的直接子文件夹，扫描速度快。</p>

<p><b>递归扫描模式</b><br>
扫描指定路径下的所有子文件夹（包括子文件夹的子文件夹），扫描全面但耗时较长。</p>

<h2>🎯 匹配模式详解</h2>

<p><b>1. 包含匹配</b><br>
查找文件夹名称中包含指定文本的文件夹。</p>

<p><b>2. 开头匹配</b><br>
查找文件夹名称以指定文本开头的文件夹。</p>

<p><b>3. 结尾匹配</b><br>
查找文件夹名称以指定文本结尾的文件夹。</p>

<p><b>4. 通配符匹配</b><br>
使用 <code>*</code> 匹配多个字符，<code>?</code> 匹配单个字符。</p>

<p><b>5. 正则表达式</b><br>
使用正则表达式进行高级模式匹配。</p>

<h2>💡 使用技巧</h2>
<ul>
<li><b>双击文件夹</b> - 快速填入搜索框</li>
<li><b>双击匹配结果</b> - 直接打开对应文件夹</li>
<li><b>实时搜索</b> - 输入时自动更新搜索结果</li>
<li><b>搜索建议</b> - 输入时显示历史搜索建议</li>
<li><b>停止扫描</b> - 可随时停止，显示已扫描结果</li>
<li><b>导出结果</b> - 点击导出按钮保存匹配结果</li>
</ul>
        """
        
        help_text.setHtml(help_content)
        layout.addWidget(help_text)
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #f8f9fa; 
            }
            QGroupBox { 
                background-color: white; 
                border: 2px solid #e9ecef; 
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #495057;
            }
            QPushButton {
                padding: 8px 16px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #4dabf7;
            }
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f1f3f4;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                background-color: white;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QComboBox {
                padding: 6px 12px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #4dabf7;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #dee2e6;
            }
        """)
    
    def browse_path(self):
        """浏览路径"""
        path = QFileDialog.getExistingDirectory(self, "选择扫描路径")
        if path:
            self.path_input.setText(path)
            self.current_path = path
    
    def on_path_changed(self):
        """路径改变"""
        path = self.path_input.text().strip()
        self.scan_btn.setEnabled(bool(path) and Path(path).exists())
    
    def on_search_text_changed(self):
        """搜索文本改变"""
        search_text = self.search_input.text().strip()
        has_folders = len(self.current_folders) > 0
        self.search_btn.setEnabled(bool(search_text) and has_folders)
        
        # 更新搜索建议
        self.update_search_suggestions(search_text)
        
        if has_folders and search_text:
            self.start_search()
    
    def on_folder_double_clicked(self, item):
        """文件夹双击"""
        folder_name = item.text().split(' (')[0]
        self.search_input.setText(folder_name)
    
    def on_matched_folder_double_clicked(self, item):
        """匹配文件夹双击"""
        folder_display_name = item.text()
        
        try:
            for folder in self.current_folders:
                if folder['display_name'] == folder_display_name:
                    full_path = folder['full_path']
                    
                    if not os.path.exists(full_path):
                        raise OSError("文件夹路径不存在")
                    
                    if sys.platform == "win32":
                        os.startfile(full_path)
                    elif sys.platform == "darwin":
                        os.system(f'open "{full_path}"')
                    else:
                        os.system(f'xdg-open "{full_path}"')
                    
                    self.status_bar.showMessage(f"📂 已打开文件夹: {full_path}")
                    break
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件夹失败: {str(e)}")
    
    def start_scan(self):
        """开始扫描"""
        if self.scan_thread and self.scan_thread.isRunning():
            QMessageBox.warning(self, "警告", "已有扫描任务在进行中")
            return
        
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "警告", "请输入扫描路径")
            return
        
        self.current_scan_mode = "recursive" if self.mode_recursive.isChecked() else "current"
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_label.setText("正在初始化扫描...")
        self.speed_label.setText("")
        self.count_label.setText("")
        self.current_folders = []
        self.all_folders_list.clear()
        self.matched_folders_list.clear()
        
        self.scan_start_time = time.time()
        
        self.scanner = FastFolderScanner()
        self.scan_thread = ScanThread(path, self.scanner, self.current_scan_mode)
        self.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.scan_thread.scan_progress.connect(self.on_scan_progress)
        self.scan_thread.start()
        
        mode_text = "递归扫描所有子文件夹" if self.current_scan_mode == "recursive" else "当前文件夹"
        self.status_bar.showMessage(f"🔄 开始扫描 - {mode_text}")
    
    def stop_scan(self):
        """停止扫描 - 显示已扫描结果"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread = None
            
            current_folders = self.scanner.get_current_folders()
            if current_folders:
                self.current_folders = current_folders
                self.update_folders_list(current_folders)
                
                elapsed = time.time() - self.scan_start_time
                self.status_bar.showMessage(f"⏹️ 扫描已停止 - 显示 {len(current_folders)} 个已扫描文件夹")
                self.progress_label.setText(f"扫描已停止 - 已找到 {len(current_folders)} 个文件夹")
                self.count_label.setText(f"已扫描: {len(current_folders)} 个")
                
                search_text = self.search_input.text().strip()
                if search_text:
                    self.start_search()
            else:
                self.status_bar.showMessage("⏹️ 扫描已停止 - 未扫描到任何文件夹")
                self.progress_label.setText("扫描已停止 - 未找到文件夹")
            
            self.progress_bar.setVisible(False)
            self.stop_btn.setEnabled(False)
            self.scan_btn.setEnabled(True)
    
    def on_scan_progress(self, count, current_folder):
        """扫描进度更新"""
        elapsed = time.time() - self.scan_start_time
        speed = count / elapsed if elapsed > 0 else 0
        
        self.progress_label.setText(f"扫描中: {current_folder}...")
        self.count_label.setText(f"已找到: {count} 个")
        self.speed_label.setText(f"速度: {speed:.1f} 个/秒")
    
    def on_scan_finished(self, success, folders, error):
        """扫描完成"""
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.scan_thread = None
        
        if success:
            self.current_folders = folders
            self.update_folders_list(folders)
            
            elapsed = time.time() - self.scan_start_time
            
            if "扫描已停止" in error:
                self.status_bar.showMessage(f"⏹️ {error} - {len(folders)} 个文件夹")
                self.progress_label.setText(f"{error} - {len(folders)} 个文件夹")
            else:
                self.status_bar.showMessage(f"✅ 扫描完成: {len(folders)} 个文件夹, 耗时 {elapsed:.1f} 秒")
                self.progress_label.setText(f"扫描完成 - 找到 {len(folders)} 个文件夹")
            
            self.speed_label.setText(f"总耗时: {elapsed:.1f}秒")
            
            search_text = self.search_input.text().strip()
            if search_text:
                self.start_search()
        else:
            QMessageBox.critical(self, "错误", error)
            self.status_bar.showMessage("❌ 扫描失败")
            self.progress_label.setText("扫描失败")
            self.progress_bar.setVisible(False)
    
    def update_folders_list(self, folders):
        """更新文件夹列表"""
        self.all_folders_list.clear()
        display_items = []
        
        for folder in folders:
            display_items.append(folder['display_name'])
        
        self.all_folders_list.addItems(display_items)
        self.all_count_label.setText(f"总计: {len(folders)} 个文件夹")
        
        self.matched_folders_list.clear()
        self.matched_count_label.setText("匹配: 0 个文件夹")
    
    def start_search(self):
        """开始搜索"""
        search_text = self.search_input.text().strip()
        if not search_text:
            return
        
        match_type = self.match_type_combo.currentData()
        case_sensitive = self.case_sensitive_check.isChecked()
        
        start_time = time.time()
        matched_folders = self.scanner.fuzzy_match(
            self.current_folders, search_text, match_type, case_sensitive
        )
        search_time = time.time() - start_time
        
        self.matched_folders_list.clear()
        display_items = []
        for folder in matched_folders:
            display_items.append(folder['display_name'])
        
        self.matched_folders_list.addItems(display_items)
        self.matched_count_label.setText(f"匹配: {len(matched_folders)} 个文件夹")
        
        # 更新导出按钮状态
        self.export_btn.setEnabled(len(matched_folders) > 0)
        
        self.search_history.add_search(
            self.path_input.text().strip(),
            search_text,
            self.match_type_combo.currentText(),
            len(matched_folders),
            "递归" if self.current_scan_mode == "recursive" else "当前"
        )
        
        self.status_bar.showMessage(f"🎯 搜索完成: {len(matched_folders)} 个匹配, 耗时 {search_time:.3f} 秒")
    
    def update_search_suggestions(self, search_text: str):
        """更新搜索建议列表"""
        if not search_text or not self.current_folders:
            self.search_suggestions.setVisible(False)
            return
        
        # 从历史记录中获取相关建议
        suggestions = set()
        history = self.search_history.get_history()
        
        # 添加历史记录中的搜索文本
        for record in history:
            if search_text.lower() in record["search_text"].lower():
                suggestions.add(record["search_text"])
        
        # 添加当前文件夹名称中包含搜索文本的项
        for folder in self.current_folders:
            if search_text.lower() in folder["name"].lower():
                suggestions.add(folder["name"])
        
        # 限制建议数量
        suggestions = list(suggestions)[:10]
        
        if suggestions:
            self.search_suggestions.clear()
            self.search_suggestions.addItems(suggestions)
            self.search_suggestions.setVisible(True)
        else:
            self.search_suggestions.setVisible(False)
    
    def on_suggestion_clicked(self, item):
        """点击搜索建议"""
        self.search_input.setText(item.text())
        self.search_suggestions.setVisible(False)
    
    def export_results(self):
        """导出搜索结果"""
        if not self.current_folders:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        # 创建文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出搜索结果", "", 
            "文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # 获取当前匹配结果
            matched_folders = []
            for i in range(self.matched_folders_list.count()):
                item = self.matched_folders_list.item(i)
                if item:
                    matched_folders.append(item.text())
            
            # 如果没有匹配结果，则导出所有文件夹
            folders_to_export = matched_folders if matched_folders else [
                self.all_folders_list.item(i).text() 
                for i in range(self.all_folders_list.count()) 
                if self.all_folders_list.item(i)
            ]
            
            if not folders_to_export:
                QMessageBox.warning(self, "警告", "没有可导出的结果")
                return
            
            # 根据文件扩展名选择导出格式
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(folders_to_export, f, ensure_ascii=False, indent=2)
            elif file_path.endswith('.csv'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("文件夹名称\n")
                    for folder in folders_to_export:
                        f.write(f'"{folder}"\n')
            else:  # .txt
                with open(file_path, 'w', encoding='utf-8') as f:
                    for folder in folders_to_export:
                        f.write(f"{folder}\n")
            
            # 显示导出成功消息
            count = len(folders_to_export)
            self.status_bar.showMessage(f"✅ 已导出 {count} 个文件夹到 {file_path}")
            QMessageBox.information(self, "导出成功", f"已成功导出 {count} 个文件夹")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误: {str(e)}")
            logger.error(f"导出失败: {e}")
    
    def refresh_history(self):
        """刷新历史记录"""
        history = self.search_history.get_history()
        self.history_table.setRowCount(len(history))
        
        for row, record in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(record["timestamp"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(record["path"]))
            self.history_table.setItem(row, 2, QTableWidgetItem(record["search_text"]))
            self.history_table.setItem(row, 3, QTableWidgetItem(record["match_type"]))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(record["results_count"])))
            self.history_table.setItem(row, 5, QTableWidgetItem(record["scan_mode"]))
        
        self.status_bar.showMessage(f"🔄 已刷新历史记录，共 {len(history)} 条")

    def clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有搜索历史吗？此操作不可撤销！",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.search_history.clear_history()
            self.refresh_history()
            self.status_bar.showMessage("🗑️ 历史记录已清空")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.stop_scan()
        
        # 强制保存搜索历史
        if hasattr(self, 'search_history'):
            self.search_history.force_save()
        
        event.accept()
