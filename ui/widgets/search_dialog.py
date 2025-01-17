from PyQt5.QtWidgets import (QDialog, QLineEdit, QLabel, QPushButton, 
                           QHBoxLayout, QVBoxLayout)
from PyQt5.QtCore import Qt, QTimer

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 搜索框和按钮布局
        search_layout = QHBoxLayout()
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.returnPressed.connect(self.search)
        search_layout.addWidget(self.search_box)
        
        # 导航按钮
        self.prev_button = QPushButton("↑")
        self.next_button = QPushButton("↓")
        self.prev_button.setFixedWidth(30)
        self.next_button.setFixedWidth(30)
        
        search_layout.addWidget(self.prev_button)
        search_layout.addWidget(self.next_button)
        
        # 计数标签
        self.count_label = QLabel("0/0")
        search_layout.addWidget(self.count_label)
        
        layout.addLayout(search_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #C0C0C0;
                border-radius: 5px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #C0C0C0;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #6B5B95;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #8677AD;
            }
        """)
        
    def search(self):
        """执行搜索"""
        if self.parent and hasattr(self.parent, 'tab_widget'):
            self.parent.tab_widget.tree_view.search(self.search_box.text()) 