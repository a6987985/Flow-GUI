from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from ui.widgets.combo_frame import ComboFrame

class ToolBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 添加ComboFrame
        self.combo_frame = ComboFrame(self)
        layout.addWidget(self.combo_frame)

        # 添加按钮组
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 按钮样式
        button_style = """
            QPushButton {
                background-color: #6B5B95;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                min-width: 60px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8677AD;
            }
            QPushButton:pressed {
                background-color: #574B7C;
            }
        """
        
        # 创建按钮
        buttons = {
            'run all': 'XMeta_run all',
            'run': 'XMeta_run',
            'stop': 'XMeta_stop',
            'skip': 'XMeta_skip',
            'unskip': 'XMeta_unskip',
            'invalid': 'XMeta_invalid'
        }
        
        for text, command in buttons.items():
            btn = QPushButton(text)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda checked, cmd=command: self.parent.execute_command(cmd))
            button_layout.addWidget(btn)
            
        layout.addWidget(button_widget) 