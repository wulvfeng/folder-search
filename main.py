"""
文件夹扫描器 - 程序入口
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui import CompleteFolderScannerGUI


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Microsoft YaHei", 10))
    
    window = CompleteFolderScannerGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
