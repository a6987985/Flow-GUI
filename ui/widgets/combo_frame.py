from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox
from PyQt5.QtGui import QFont, QFontMetrics
import os

class ComboFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        
        # 获取当前目录信息
        self.pwd = os.getcwd()
        self.cur_dir = os.path.dirname(self.pwd)
        
        # 设置字体
        font = QFont("Segoe UI", 10)
        
        # 获取运行目录列表
        self.run_dirs = self.get_combo_value()
        
        # 计算合适宽度
        fm = QFontMetrics(font)
        max_len = max(fm.horizontalAdvance(i) for i in self.run_dirs)
        combo_width = max_len + 50  # 增加50像素作为缓冲
        
        # 创建下拉框
        self.combobox = QComboBox()
        self.combobox.addItems(self.run_dirs)
        self.combobox.setEditable(False)
        self.combobox.setMinimumWidth(combo_width)
        self.combobox.currentIndexChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.combobox)
        
    def get_combo_value(self):
        """获取所有运行目录"""
        all_files = os.listdir(self.cur_dir)
        sorted_entries = sorted(all_files)
        
        all_runs = [os.path.basename(self.pwd)]
        peer_dirs = []
        
        for file in sorted_entries:
            peer_dir = os.path.join(self.cur_dir, file)
            if (os.path.isdir(peer_dir) and 
                not os.path.islink(peer_dir) and 
                os.path.exists(os.path.join(peer_dir, '.target_dependency.csh'))):
                peer_dirs.append(peer_dir)
                all_runs.append(file)
        
        # 去重并保持顺序
        unique_runs = list(dict.fromkeys(all_runs))
        return unique_runs
        
    def on_selection_changed(self, index):
        """处理选择改变事件"""
        if hasattr(self.parent, 'parent'):
            main_window = self.parent.parent
            if hasattr(main_window, 'target_model'):
                selected_dir = os.path.join(self.cur_dir, self.combobox.currentText())
                main_window.target_model.load_targets(selected_dir) 