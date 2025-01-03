import os, sys, re, threading, time
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QStyleFactory, QMenu, QAction, QFileDialog, QMessageBox, QScrollBar, QTreeWidgetItemIterator,
                             QHeaderView, QStyle, QDialog, QTextEdit, QTabBar)
from PyQt5.QtCore import (Qt, QTimer, QRegExp, QObject)
from PyQt5.QtGui import (QFont, QBrush, QColor, QClipboard, QIcon, QRegExpValidator, QFontMetrics)

class ComboFrame(QWidget):
    '''A simple Combobox widget, contains all runs name.'''
    def __init__(self, parent, Menu):
        super().__init__(parent)
        self.Menu = Menu
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        font = QFont("Segoe UI", 10)
        self.get_combo_value()

        # 计算合适宽度
        fm = QFontMetrics(font)
        max_len = 0
        for i in self.new_list:
            w = fm.horizontalAdvance(i)  # 使用 horizontalAdvance 获取更准确的宽度
            if w > max_len:
                max_len = w

        # 设置合适的宽度，添加一些额外空间用于下拉箭头和边距
        combo_width = max_len + 50  # 增加50像素作为缓冲

        self.combobox = QComboBox()
        self.combobox.addItems(self.new_list)
        self.combobox.setEditable(False)
        self.combobox.setMinimumWidth(combo_width)
        layout.addWidget(self.combobox)

    def get_combo_value(self):
        self.pwd = os.getcwd()
        self.cur_dir = os.path.dirname(self.pwd)
        self.all_file = os.listdir(self.cur_dir)
        self.sorted_entries = sorted(self.all_file)
        self.all_runs = [os.path.basename(self.pwd)]
        self.peer_dir = []
        self.run_len = []
        for file in self.sorted_entries:
            peer_dir = os.path.join(self.cur_dir, file)
            if os.path.isdir(peer_dir) and (not os.path.islink(peer_dir)) and os.path.exists(os.path.join(peer_dir, '.target_dependency.csh')):
                self.peer_dir.append(peer_dir)
                self.all_runs.append(file)

        self.new_list = list(set(self.all_runs))
        self.new_list.sort(key=self.all_runs.index)
        return self.new_list


class MonitorRuns(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 环境变量获取
        xmeta_project = os.getenv('XMETA_PROJECT_NAME', 'XMetaProject')
        family = os.getenv('FAMILY', 'Family')
        xmeta_background = os.getenv('XMETA_BACKGROUND', '#ffffff')
        version = os.getenv('XMETA_VERSION', 'Version')

        # 添加level展开状态跟踪
        self.level_expanded = {}

        title_name = "Console of XMeta/%s-%s @ %s" %(version, family, xmeta_project)
        self.setWindowTitle(title_name)
        
        # 定义基本的状态颜色
        self.colors = {
            'finish': '#67c23a',
            'skip': '#e6a23c',
            'failed': '#f56c6c',
            'scheduled': '#409eff',
            'running': '#ffd700',
            'pending': '#ff9900',
            'invalid': '#909399'
        }
        
        # 创建菜单栏
        self.create_menu()
        
        # 主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 设置全局背景色和滚动条样式
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F3E5F5;
                color: black;
            }
            QTreeWidget {
                background-color: white;
                color: black;
            }
            QTabWidget::pane {
                background-color: white;
            }
            QTabBar::tab {
                background-color: #E1BEE7;
                color: black;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: black;
            }
            QLabel, QComboBox, QLineEdit {
                color: black;
            }
            /* 滚动条整体样式 */
            QScrollBar:vertical {
                width: 12px;
                background: transparent;
                margin: 2px;
                border-radius: 6px;
            }
            /* 滚动条滑块 */
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #AAAAAA;
            }
            /* 滚动条上下按钮 */
            QScrollBar::add-line:vertical {
                height: 0px;
                background: transparent;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                background: transparent;
            }
            /* 滚动条背景槽 */
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #F0F0F0;
                border-radius: 6px;
            }
            /* 水平滚动条样式 */
            QScrollBar:horizontal {
                height: 12px;
                background: transparent;
                margin: 2px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #CCCCCC;
                min-width: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #AAAAAA;
            }
            QScrollBar::add-line:horizontal {
                width: 0px;
                background: transparent;
            }
            QScrollBar::sub-line:horizontal {
                width: 0px;
                background: transparent;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: #F0F0F0;
                border-radius: 6px;
            }
        """)

        # MenuFrame
        self.MenuFrame = QWidget()
        menu_layout = QHBoxLayout(self.MenuFrame)
        menu_layout.setContentsMargins(0,0,0,0)
        menu_layout.setSpacing(5)

        # 左边部分 - ComboFrame
        self.gen_combo = ComboFrame(main_widget, self.MenuFrame)
        menu_layout.addWidget(self.gen_combo)

        # 中间部分 - Filter
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0,0,0,0)
        self.En_search = QLineEdit()
        lb_filter = QLabel("Filter:")
        filter_layout.addWidget(lb_filter)
        filter_layout.addWidget(self.En_search)
        menu_layout.addWidget(filter_widget)

        # 右边部分 - 按钮组
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.setSpacing(5)

        # 定义按钮样式
        button_style = """
            QPushButton {
                background-color: #6B5B95;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                min-width: 80px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8677AD;
            }
            QPushButton:pressed {
                background-color: #574B7C;
            }
        """

        # 添加所有按钮到同一行，应用新样式
        bt_runall = QPushButton("run all")
        bt_run = QPushButton("run")
        bt_stop = QPushButton("stop")
        bt_skip = QPushButton("skip")
        bt_unskip = QPushButton("unskip")
        bt_invalid = QPushButton("invalid")
        
        # 应用样式到所有按钮
        for button in [bt_runall, bt_run, bt_stop, bt_skip, bt_unskip, bt_invalid]:
            button.setStyleSheet(button_style)
            button_layout.addWidget(button)

        # 将按钮组添加到主菜单布局
        menu_layout.addWidget(button_widget)

        # 设置伸缩因子，使三个部分合理分布
        menu_layout.setStretch(0, 1)  # ComboFrame
        menu_layout.setStretch(1, 1)  # Filter
        menu_layout.setStretch(2, 2)  # Buttons

        # 将MenuFrame添加到主布局
        main_layout.addWidget(self.MenuFrame)

        # 添加TabWidget
        self.tabwidget = QTabWidget()
        self.tabwidget.setTabsClosable(True)  # 设置标签可关闭
        self.tabwidget.setMovable(True)
        self.tabwidget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tabwidget)

        # 初始化run_dir
        self.combo_sel_dir = os.path.join(self.gen_combo.cur_dir, self.gen_combo.combobox.currentText())

        # 主Tab
        self.tab_run = QWidget()
        tab_run_layout = QVBoxLayout(self.tab_run)
        idx = self.tabwidget.addTab(self.tab_run, self.gen_combo.combobox.currentText())
        self.tabwidget.tabBar().setTabButton(idx, QTabBar.RightSide, None)  # 移除主tab的关闭按钮

        # Treeview
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["level", "target", "status", "start time", "end time"])
        self.tree.setRootIsDecorated(True)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.itemDoubleClicked.connect(self.copy_tar)
        
        # 设置滚动条样式
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: none;
            }
            QScrollBar:vertical {
                width: 15px;
                background-color: transparent;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                min-height: 30px;
                background: #CCCCCC;
                margin: 3px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #AAAAAA;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                border: none;
            }
            QScrollBar:horizontal {
                height: 15px;
                background-color: transparent;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                min-width: 30px;
                background: #CCCCCC;
                margin: 3px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #AAAAAA;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                border: none;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
                border: none;
            }
        """)
        
        # 设置列宽和调整模式
        header = self.tree.header()
        header.setStretchLastSection(True)  # 让最后一列填充剩余空间
        
        # 设置各列的调整模式
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # level列固定宽度
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # target列可手动调整
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # status列固定宽度
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # start time列固定宽度
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # end time列自动填充剩余空间
        
        tab_run_layout.addWidget(self.tree)

        # 信号槽
        self.gen_combo.combobox.currentIndexChanged.connect(self.click_event)
        self.En_search.returnPressed.connect(self.get_entry)

        bt_invalid.clicked.connect(lambda: self.start('XMeta_invalid'))
        bt_unskip.clicked.connect(lambda: self.start('XMeta_unskip'))
        bt_skip.clicked.connect(lambda: self.start('XMeta_skip'))
        bt_stop.clicked.connect(lambda: self.start('XMeta_stop'))
        bt_run.clicked.connect(lambda: self.start('XMeta_run'))
        bt_runall.clicked.connect(lambda: self.start('XMeta_run all'))

        # 定时器替代 after
        self.timer = QTimer()
        self.timer.timeout.connect(self.change_run)
        self.timer.start(1000)

        self.tg = []
        self.tar_name = []
        self.countX = 0

        self.init_run_view(self.combo_sel_dir)

        # 窗口大小与位置初始化
        self.resize(1200,800)
        self.center()

        self.create_context_menu()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_run_view(self, run_dir):
        self.get_tree(run_dir)

    def click_event(self):
        """当 combobox 选择改变时触发"""
        cur_text = self.gen_combo.combobox.currentText()
        
        # 更新当前选中的 run 目录
        self.combo_sel = os.path.join(self.gen_combo.cur_dir, cur_text)
        
        # 更新 tab 标签
        idx = self.tabwidget.indexOf(self.tab_run)
        if idx >= 0:
            self.tabwidget.setTabText(idx, cur_text)
            self.tabwidget.setCurrentIndex(idx)
        
        # 清空并重新加载树
        self.tree.clear()
        self.get_tree(self.combo_sel)  # 重新加载新 run 的数据

    def change_run(self):
        """定时刷新树状态"""
        try:
            # 保存所有选中的项
            selected_items = self.tree.selectedItems()
            selected_info = []
            for item in selected_items:
                if item.parent():
                    selected_info.append((item.parent().text(0), item.text(1)))
            
            # 刷新树显示
            self.tree.update()
            
            # 恢复所有选中状态
            for parent_text, target_text in selected_info:
                items = self.tree.findItems(target_text, Qt.MatchExactly | Qt.MatchRecursive, 1)
                for item in items:
                    if item.parent() and item.parent().text(0) == parent_text:
                        item.setSelected(True)
                
        except Exception as e:
            pass  # 静默处理异常

    def get_entry(self):
        self.filter_tab()

    def copy_tar(self):
        # 将选中target拷贝到剪贴板
        tar_selected = self.copy_item()
        cb = QApplication.clipboard()
        cb.clear()
        cb.setText(" ".join(tar_selected))

    def close_tab(self, index):
        """关闭标签页，但主tab不能关闭"""
        if self.tabwidget.widget(index) != self.tab_run:  # 如果不是主tab
            self.tabwidget.removeTab(index)

    def start(self, status):
        # 与原逻辑一致
        if status == 'XMeta_run all':
            self.bt_notar(status)
        else:
            self.bt_event(status)

    def Xterm(self):
        os.chdir(self.combo_sel)
        os.system('XMeta_term')

    def bt_event(self, status):
        selected = self.tree.selectedItems()
        os.chdir(self.combo_sel)
        select_run_targets = " ".join([itm.text(1) for itm in selected if itm.text(1) != ""])
        if select_run_targets.strip():
            os.system('%s %s' %(status, select_run_targets))
        self.tree.clearSelection()

    def bt_notar(self, status):
        os.chdir(self.combo_sel)
        os.system('%s' %status)

    def bt_csh(self, item):
        """Shell - 打开 make_targets 目录下的 .csh 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        shell_file = os.path.join(current_run, 'make_targets', f"{current_target}.csh")
        
        if os.path.exists(shell_file):
            try:
                subprocess.run(['gvim', shell_file], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_log(self, item):
        """Log - 打开 logs 目录下的 .log 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        log_file = os.path.join(current_run, 'logs', f"{current_target}.log")
        log_file_gz = f"{log_file}.gz"
        
        if os.path.exists(log_file):
            try:
                subprocess.run(['gvim', log_file], check=True)
            except subprocess.CalledProcessError:
                pass
        elif os.path.exists(log_file_gz):
            try:
                subprocess.run(['gvim', log_file_gz], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_cmd(self, item):
        """Command - 打开 cmds 目录下的 .cmd 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        cmd_file = os.path.join(current_run, 'cmds', f"{current_target}.cmd")
        
        if os.path.exists(cmd_file):
            try:
                subprocess.run(['gvim', cmd_file], check=True)
            except subprocess.CalledProcessError:
                pass

    def get_filter_target(self):
        pattern = self.En_search.text()
        # 原逻辑中使用正则从tar_name中筛选
        add_wildcard = '*' + pattern + '*'
        wildcard_replace = add_wildcard.replace('*', '.*')
        input_pattern = re.compile(wildcard_replace + '$')
        self.matched_list = [e for e in self.tar_name if input_pattern.match(e)]

    def filter_tab(self):
        if not self.En_search.text().strip():
            return
        tab_filter = QWidget()
        tab_filter_layout = QVBoxLayout(tab_filter)
        filter_tree = QTreeWidget()
        filter_tree.setColumnCount(3)
        filter_tree.setHeaderLabels(["level", "target", "status"])
        filter_tree.setRootIsDecorated(True)
        filter_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        tab_filter_layout.addWidget(filter_tree)

        self.get_filter_target()
        # 生成filter_tree数据
        l = []
        o = []
        with open(os.path.join(self.combo_sel, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            for target in self.matched_list:
                level_name = 'TARGET_LEVEL_%s' %target
                match_lv = re.search(r'set\s*(%s)\s*\=(\s.*)' %level_name, a_file)
                if not match_lv:
                    continue
                target_name = match_lv.group(2).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    target_level = re.sub(r"^['\"]|['\"]$", '', target_name).split()

                target_file = os.path.join(self.combo_sel, 'status', target)
                target_status = self.get_target_status(target_file)
                
                str_lv = ''.join(target_level)
                o.append(str_lv)
                d = [target_level, target, target_status]
                l.append(d)

        all_lv = list(set(o))
        all_lv.sort(key=o.index)

        # 创建一个字典来存储每个level的items
        level_items = {level: [] for level in all_lv}

        # 为每个数据创建item
        for data in l:
            str_data = ''.join(data[0])
            item = QTreeWidgetItem(filter_tree)
            item.setText(0, str_data)  # level
            item.setText(1, data[1])   # target
            item.setText(2, data[2])   # status
            self.set_item_color(item, data[2])
            level_items[str_data].append(item)

        # 为每个level的第一个item设置展开/折叠指示器
        for level, items in level_items.items():
            if items:
                first_item = items[0]
                first_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                first_item.setExpanded(True)
                # 设置为有子节点，这样就会一直显示三角标
                first_item.setFlags(first_item.flags() | Qt.ItemIsTristate)

        # 创建事件过滤器并保存状态
        event_filter = FilterTreeEventFilter(filter_tree)
        event_filter.level_items = level_items
        event_filter.level_expanded = {level: True for level in all_lv}
        
        # 添加事件过滤器
        filter_tree.viewport().installEventFilter(event_filter)
        
        # 保存事件过滤器的引用，防止被垃圾回收
        filter_tree.event_filter = event_filter

        idx = self.tabwidget.addTab(tab_filter, self.En_search.text())
        self.tabwidget.setCurrentIndex(idx)

    def retrace_tab(self, inout):
        selected = self.tree.selectedItems()
        if not selected:
            return
        self.tar_sel = selected[0].text(1)
        self.get_retrace_target(inout)
        if self.retrace_tar_name:
            tab_trace = QWidget()
            trace_layout = QVBoxLayout(tab_trace)
            retrace_tree = QTreeWidget()
            retrace_tree.setColumnCount(5)  # 修改为5列
            retrace_tree.setHeaderLabels(["level", "target", "status", "start time", "end time"])  # 添加所有列标签
            retrace_tree.setRootIsDecorated(True)
            retrace_tree.setSelectionMode(QTreeWidget.ExtendedSelection)

            # 设置列宽和调整模式
            header = retrace_tree.header()
            header.setSectionResizeMode(QHeaderView.Interactive)  # 所有列都可以手动调整
            header.setStretchLastSection(False)  # 最后一列不自动拉伸

            # 设置默认列宽，与主界面保持一致
            retrace_tree.setColumnWidth(0, 80)   # level列
            retrace_tree.setColumnWidth(1, 600)  # target列
            retrace_tree.setColumnWidth(2, 100)  # status列
            retrace_tree.setColumnWidth(3, 150)  # start time列
            retrace_tree.setColumnWidth(4, 150)  # end time列

            trace_layout.addWidget(retrace_tree)

            # 生成retrace_tree数据
            l = []
            o = []
            run_dir = self.combo_sel
            if inout == 'in':
                self.retrace_tar_name.append(self.tar_sel)
            elif inout == 'out':
                self.retrace_tar_name.insert(0, self.tar_sel)

            with open(os.path.join(run_dir, '.target_dependency.csh'), 'r') as f:
                a_file = f.read()
                for target in self.retrace_tar_name:
                    level_name = 'TARGET_LEVEL_%s' %target
                    match_lv = re.search(r'set\s*(%s)\s*\=(\s.*)' %level_name, a_file)
                    if not match_lv:
                        continue
                    target_name = match_lv.group(2).strip()
                    if re.match(r"^(['\"]).*\"$", target_name):
                        target_level = re.sub(r"^['\"]|['\"]$", '', target_name).split()
                    target_file = os.path.join(run_dir, 'status', target)
                    target_status = self.get_target_status(target_file)
                    
                    # 获取开始和结束时间
                    tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                    start_time, end_time = self.get_start_end_time(tgt_track_file)
                    
                    str_lv = ''.join(target_level)
                    o.append(str_lv)
                    d = [target_level, target, target_status, start_time, end_time]  # 添加时间信息
                    l.append(d)

            all_lv = list(set(o))
            all_lv.sort(key=o.index)

            # 创建一个字典来存储每个level的items
            level_items = {level: [] for level in all_lv}

            # 为每个数据创建item
            for data in l:
                str_data = ''.join(data[0])
                item = QTreeWidgetItem(retrace_tree)
                item.setText(0, str_data)  # level
                item.setText(1, data[1])   # target
                item.setText(2, data[2])   # status
                item.setText(3, data[3])   # start time
                item.setText(4, data[4])   # end time
                self.set_item_color(item, data[2])
                level_items[str_data].append(item)

            # 为每个level的第一个item设置展开/折叠指示器
            for level, items in level_items.items():
                if items:
                    first_item = items[0]
                    first_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    first_item.setExpanded(True)
                    # 设置为有子节点，这样就会一直显示三角标
                    first_item.setFlags(first_item.flags() | Qt.ItemIsTristate)

            # 创建事件过滤器并保存状态
            event_filter = FilterTreeEventFilter(retrace_tree)
            event_filter.level_items = level_items
            event_filter.level_expanded = {level: True for level in all_lv}
            
            # 添加事件过滤器
            retrace_tree.viewport().installEventFilter(event_filter)
            
            # 保存事件过滤器的引用，防止被垃圾回收
            retrace_tree.event_filter = event_filter

            idx = self.tabwidget.addTab(tab_trace, self.tar_sel)
            self.tabwidget.setCurrentIndex(idx)
            self.tree.clearSelection()

    def get_retrace_target(self, inout):
        self.retrace_tar_name = []
        with open(os.path.join(self.combo_sel, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            matct_up = 'ALL_RELATED_%s' %self.tar_sel
            match_down = 'DEPENDENCY_OUT_%s' %self.tar_sel

            if inout == 'in':
                m = re.search(r'set\s*(%s)\s*\=(\s.*)' %matct_up, a_file)
                if m:
                    target_name = m.group(2).strip()
                    if re.match(r"^(['\"]).*\"$", target_name):
                        self.retrace_tar_name = re.sub(r"^['\"]|['\"]$", '', target_name).split()
            elif inout == 'out':
                m = re.search(r'set\s*(%s)\s*\=(\s.*)' %match_down, a_file)
                if m:
                    target_name = m.group(2).strip()
                    if re.match(r"^(['\"]).*\"$", target_name):
                        self.retrace_tar_name = re.sub(r"^['\"]|['\"]$", '', target_name).split()

    def get_target(self):
        with open(os.path.join(self.combo_sel, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            m = re.search(r'set\s*ACTIVE_TARGETS\s*\=(\s.*)', a_file)
            if m:
                target_name = m.group(1).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    self.tar_name = re.sub(r"^['\"]|['\"]$", "", target_name).split()
                    return self.tar_name
        self.tar_name = []
        return self.tar_name

    def copy_item(self):
        selected = self.tree.selectedItems()
        n = [itm.text(1) for itm in selected if itm.text(1) != ""]
        return n

    def get_tree(self, run_dir):
        # 保存当前状态
        tree_state = self.save_tree_state()
        
        self.combo_sel = run_dir
        self.tree.clear()
        self.get_target()

        # 清理
        self.countX = 0
        l = []
        o = []
        
        # 用于计算最大target名称宽度
        fm = QFontMetrics(self.tree.font())
        max_target_width = 0
        
        with open(os.path.join(run_dir, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            for target in self.tar_name:
                level_name = 'TARGET_LEVEL_%s' %target
                match_lv = re.search(r'set\s*(%s)\s*\=(\s.*)' %level_name, a_file)
                if not match_lv:
                    continue
                target_name = match_lv.group(2).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    target_level = re.sub(r"^['\"]|['\"]$", '', target_name).split()

                # 计算target名称宽度
                target_width = fm.width(target)
                max_target_width = max(max_target_width, target_width)

                # 获取status等信息
                target_file = os.path.join(run_dir, 'status', target)
                tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)

                start_time, end_time = self.get_start_end_time(tgt_track_file)
                target_status = self.get_target_status(target_file)

                str_lv = ''.join(target_level)
                o.append(str_lv)
                d = [target_level, target, target_status, start_time, end_time]
                l.append(d)

        # 设置列宽
        self.tree.setColumnWidth(0, 80)  # level列
        
        # target列动态宽度但有最大限制
        max_allowed_width = 600
        target_column_width = min(max_target_width + 20, max_allowed_width)
        self.tree.setColumnWidth(1, target_column_width)
        
        # 其他列固定宽度
        self.tree.setColumnWidth(2, 100)  # status列
        self.tree.setColumnWidth(3, 150)  # start time列

        # 构建扁平化的树结构
        all_lv = list(set(o))
        all_lv.sort(key=o.index)

        # 为每个level创建一个字典来存储其items
        self.level_items = {level: [] for level in all_lv}
        
        # 初始化level展开状态
        self.level_expanded = {level: True for level in all_lv}

        # 创建所有项目
        for data in l:
            lvl, tgt, st, ct, et = data
            str_data = ''.join(lvl)
            
            # 创建item
            item = QTreeWidgetItem(self.tree)
            item.setText(0, str_data)  # level
            item.setText(1, tgt)       # target
            item.setText(2, st)        # status
            item.setText(3, ct)        # start time
            item.setText(4, et)        # end time
            
            # 设置颜色
            self.set_item_color(item, st)
            
            # 将item添加到对应level的列表中
            self.level_items[str_data].append(item)

        # 为每个level的第一个item设置展开/折叠指示器
        for level, items in self.level_items.items():
            if items:
                first_item = items[0]
                first_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                first_item.setExpanded(self.level_expanded[level])
                # 设置为有子节点，这样就会一直显示三角标
                first_item.setFlags(first_item.flags() | Qt.ItemIsTristate)

        # 使用事件过滤器处理点击事件
        self.tree.viewport().installEventFilter(self)
        
        # 恢复状态
        self.restore_tree_state(tree_state)

    def set_item_color(self, item, status):
        if status in self.colors:
            color = QColor(self.colors[status])
            for col in range(item.columnCount()):
                item.setBackground(col, QBrush(color))

    def get_target_status(self, target_file):
        if os.path.exists(target_file + '.skip'):
            return 'skip'
        elif os.path.exists(target_file + '.finish'):
            return 'finish'
        elif os.path.exists(target_file + '.failed'):
            return 'failed'
        elif os.path.exists(target_file + '.running'):
            return 'running'
        elif os.path.exists(target_file + '.pending'):
            return 'pending'
        elif os.path.exists(target_file + '.scheduled'):
            return 'scheduled'
        else:
            return ''

    def get_start_end_time(self, tgt_track_file):
        start_time = ""
        end_time = ""
        if os.path.exists(tgt_track_file + '.start'):
            st_mtime = os.path.getmtime(tgt_track_file + '.start')+28800
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(st_mtime))
        if os.path.exists(tgt_track_file + '.finished'):
            ft_mtime = os.path.getmtime(tgt_track_file + '.finished')+28800
            end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ft_mtime))
        return start_time, end_time

    def save_tree_state(self):
        state = {
            'expanded': {},
            'selected': [],
            'selected_parents': [],
            'scroll': self.tree.verticalScrollBar().value()
        }
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.parent():
                parent_text = item.parent().text(0)
                state['expanded'][parent_text] = item.parent().isExpanded()
                if item.isSelected():
                    state['selected'].append((parent_text, item.text(1)))
            else:
                if item.isSelected():
                    state['selected_parents'].append(item.text(0))
            iterator += 1
        return state

    def restore_tree_state(self, state):
        # 恢复展开状态
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if not item.parent():
                level_text = item.text(0)
                if level_text in state['expanded']:
                    item.setExpanded(state['expanded'][level_text])
                # 恢复父节点的选中状态
                if level_text in state.get('selected_parents', []):
                    item.setSelected(True)
            iterator += 1
        
        # 恢复子节点选中状态
        if state.get('selected'):
            for parent_text, child_text in state['selected']:
                items = self.tree.findItems(child_text, Qt.MatchExactly | Qt.MatchRecursive, 1)
                for item in items:
                    if item.parent() and item.parent().text(0) == parent_text:
                        item.setSelected(True)
        
        # 恢复滚动条位置
        if 'scroll' in state:
            self.tree.verticalScrollBar().setValue(state['scroll'])

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = QMenu(self)
        
        # 添加菜单项
        terminal_action = self.context_menu.addAction("Terminal")
        csh_action = self.context_menu.addAction("csh")
        log_action = self.context_menu.addAction("Log")
        cmd_action = self.context_menu.addAction("cmd")
        self.context_menu.addSeparator()
        trace_up_action = self.context_menu.addAction("Trace Up")
        trace_down_action = self.context_menu.addAction("Trace Down")
        
        # 连接信号到对应的槽函数
        terminal_action.triggered.connect(lambda: self.bt_terminal(self.tree.currentItem()))
        csh_action.triggered.connect(lambda: self.bt_csh(self.tree.currentItem()))
        log_action.triggered.connect(lambda: self.bt_log(self.tree.currentItem()))
        cmd_action.triggered.connect(lambda: self.bt_cmd(self.tree.currentItem()))
        trace_up_action.triggered.connect(lambda: self.bt_trace_up(self.tree.currentItem()))
        trace_down_action.triggered.connect(lambda: self.bt_trace_down(self.tree.currentItem()))
        
        # 设置树形视图上下文菜单策略
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.tree.itemAt(position)
        if item:
            # 确保只在叶子节点上显示完整菜单
            if item.childCount() == 0:  # 叶子节点
                self.context_menu.exec_(self.tree.viewport().mapToGlobal(position))

    def bt_trace_up(self, item):
        """Trace Up - 显示当前target的上游依赖"""
        if item and item.childCount() == 0:  # 确保是叶子节点
            self.retrace_tab('in')

    def bt_trace_down(self, item):
        """Trace Down - 显示依赖于当前target的下游项目"""
        if item and item.childCount() == 0:  # 确保是叶子节点
            self.retrace_tab('out')

    def bt_terminal(self, item):
        """Terminal - 执行 XMeta_term 命令"""
        try:
            os.chdir(self.combo_sel)
            os.system('XMeta_term')
        except Exception as e:
            pass

    def bt_csh(self, item):
        """Shell - 打开 make_targets 目录下的 .csh 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        shell_file = os.path.join(current_run, 'make_targets', f"{current_target}.csh")
        
        if os.path.exists(shell_file):
            try:
                subprocess.run(['gvim', shell_file], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_log(self, item):
        """Log - 打开 logs 目录下的 .log 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        log_file = os.path.join(current_run, 'logs', f"{current_target}.log")
        log_file_gz = f"{log_file}.gz"
        
        if os.path.exists(log_file):
            try:
                subprocess.run(['gvim', log_file], check=True)
            except subprocess.CalledProcessError:
                pass
        elif os.path.exists(log_file_gz):
            try:
                subprocess.run(['gvim', log_file_gz], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_cmd(self, item):
        """Command - 打开 cmds 目录下的 .cmd 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        cmd_file = os.path.join(current_run, 'cmds', f"{current_target}.cmd")
        
        if os.path.exists(cmd_file):
            try:
                subprocess.run(['gvim', cmd_file], check=True)
            except subprocess.CalledProcessError:
                pass

    def create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # Add View menu
        view_menu = menubar.addMenu('View')
        
        # Add show all runs status action
        show_all_runs_action = QAction('Show All Runs Status', self)
        show_all_runs_action.triggered.connect(self.show_all_runs_status)
        view_menu.addAction(show_all_runs_action)

    def show_all_runs_status(self):
        """Show status of all runs in a new tab"""
        # Create new tab
        tab_status = QWidget()
        tab_status_layout = QVBoxLayout(tab_status)
        
        # Create tree widget for status display
        status_tree = QTreeWidget()
        status_tree.setColumnCount(4)
        status_tree.setHeaderLabels(["Run Directory", "Latest Target", "Status", "Timestamp"])
        status_tree.setRootIsDecorated(False)  # 不显示展开箭头
        
        # Set column widths
        header = status_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Run Directory 可调整
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Latest Target 可调整
        header.setSectionResizeMode(2, QHeaderView.Fixed)       # Status 固定宽度
        header.setSectionResizeMode(3, QHeaderView.Stretch)     # Timestamp 自动填充
        
        tab_status_layout.addWidget(status_tree)
        
        # Get data
        base_path = self.gen_combo.cur_dir
        
        try:
            entries = os.listdir(base_path)
        except OSError:
            return

        run_dirs = [entry for entry in entries 
                   if os.path.isdir(os.path.join(base_path, entry)) 
                   and self.is_run_directory(os.path.join(base_path, entry))]

        if not run_dirs:
            return

        # Add data to tree
        for run_dir in sorted(run_dirs):
            run_path = os.path.join(base_path, run_dir)
            status_dir = os.path.join(run_path, 'status')
            
            if not os.path.isdir(status_dir):
                item = QTreeWidgetItem(status_tree)
                item.setText(0, run_dir)
                item.setText(1, 'N/A')
                item.setText(2, 'No status dir')
                item.setText(3, 'N/A')
                continue

            latest_target, latest_status, latest_mtime = self.get_latest_target_status(status_dir)
            if not latest_target or not latest_status:
                item = QTreeWidgetItem(status_tree)
                item.setText(0, run_dir)
                item.setText(1, 'N/A')
                item.setText(2, 'No valid mark files')
                item.setText(3, 'N/A')
                continue

            timestamp = datetime.fromtimestamp(latest_mtime).strftime("%Y-%m-%d %H:%M:%S")
            item = QTreeWidgetItem(status_tree)
            item.setText(0, run_dir)
            item.setText(1, latest_target)
            item.setText(2, latest_status)
            item.setText(3, timestamp)
            
            # Set status color
            if latest_status in self.colors:
                color = QColor(self.colors[latest_status])
                for col in range(item.columnCount()):
                    item.setBackground(col, QBrush(color))

        # Resize columns to content
        status_tree.resizeColumnToContents(0)  # Run Directory
        status_tree.resizeColumnToContents(1)  # Latest Target
        status_tree.resizeColumnToContents(2)  # Status
        
        # Add new tab
        idx = self.tabwidget.addTab(tab_status, "All Runs Status")
        self.tabwidget.setCurrentIndex(idx)

    def is_run_directory(self, dir_path):
        """检查是否为有效的 run 目录"""
        target_dependency_file = os.path.join(dir_path, '.target_dependency.csh')
        return os.path.isfile(target_dependency_file)

    def parse_mark_file(self, filename):
        """解析标记文件名"""
        if '.' not in filename:
            return None, None
        target, status = filename.rsplit('.', 1)
        return target, status

    def get_latest_target_status(self, status_dir):
        """获取最新 target 的状态"""
        latest_target = None
        latest_status = None
        latest_mtime = -1

        try:
            files = os.listdir(status_dir)
        except OSError as e:
            print(f"Can not read {status_dir}: {e}", file=sys.stderr)
            return latest_target, latest_status, latest_mtime

        for file in files:
            file_path = os.path.join(status_dir, file)
            if not os.path.isfile(file_path):
                continue
            target, status = self.parse_mark_file(file)
            if not target or not status:
                continue
            try:
                mtime = os.path.getmtime(file_path)
            except OSError as e:
                print(f"Can not get timestamp {file_path}: {e}", file=sys.stderr)
                continue

            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_target = target
                latest_status = status

        return latest_target, latest_status, latest_mtime

    def get_status_color(self, status):
        """获取状态对应的颜色"""
        if status == 'failed':
            return QColor('#f56c6c')  # 红色
        elif status == 'running':
            return QColor('#ffd700')  # 黄色
        elif status == 'pending':
            return QColor('#ff9900')  # 橙色
        elif status == 'finish':
            return QColor('#67c23a')  # 绿色
        else:
            return QColor('#333333')  # 默认颜色

    def colorize_status(self, status, fixed_width):
        """为状态添加颜色"""
        padded_status = status.ljust(fixed_width)
        if status == 'failed':
            return f"{self.ANSI_BOLD}{self.ANSI_RED}{padded_status}{self.ANSI_RESET}"
        elif status == 'running':
            return f"{self.ANSI_BOLD}{self.ANSI_YELLOW}{padded_status}{self.ANSI_RESET}"
        elif status == 'pending':
            return f"{self.ANSI_BOLD}{self.ANSI_ORANGE}{padded_status}{self.ANSI_RESET}"
        elif status == 'finish':
            return f"{self.ANSI_BOLD}{self.ANSI_GREEN}{padded_status}{self.ANSI_RESET}"
        else:
            return padded_status

    def eventFilter(self, obj, event):
        """事件过滤器，处理鼠标点击事件"""
        if obj == self.tree.viewport():
            if event.type() == event.MouseButtonPress:
                item = self.tree.itemAt(event.pos())
                if item:
                    # 获取点击的列
                    column = self.tree.columnAt(event.x())
                    # 只有在点击第一列时才触发折叠/展开
                    if column == 0:
                        level = item.text(0)
                        if level in self.level_items:
                            self.toggle_level_items(item, self.level_items)
                            return True  # 事件已处理
        return super().eventFilter(obj, event)

    def toggle_level_items(self, clicked_item, level_items):
        """切换level对应的items的展开/折叠状态"""
        level = clicked_item.text(0)
        if level in level_items:
            items = level_items[level]
            if not items:
                return

            # 切换展开状态
            self.level_expanded[level] = not self.level_expanded[level]
            
            # 更新第一个item的展开状态
            items[0].setExpanded(self.level_expanded[level])
            
            # 如果是展开状态，显示所有items
            if self.level_expanded[level]:
                for item in items:
                    item.setHidden(False)
            # 如果是折叠状态，只显示第一个item
            else:
                for i, item in enumerate(items):
                    item.setHidden(i != 0)  # 只有第一个item不隐藏

class FilterTreeEventFilter(QObject):
    def __init__(self, tree):
        super().__init__()
        self.tree = tree
        self.level_items = {}
        self.level_expanded = {}

    def eventFilter(self, obj, event):
        if obj == self.tree.viewport():
            if event.type() == event.MouseButtonPress:
                item = self.tree.itemAt(event.pos())
                if item:
                    # 获取点击的列
                    column = self.tree.columnAt(event.x())
                    # 只有在点击第一列时才触发折叠/展开
                    if column == 0:
                        level = item.text(0)
                        if level in self.level_items:
                            self.toggle_level_items(level)
                            return True  # 事件已处理
        return super().eventFilter(obj, event)

    def toggle_level_items(self, level):
        """切换level对应的items的展开/折叠状态"""
        if level in self.level_items:
            items = self.level_items[level]
            if not items:
                return

            # 切换展开状态
            self.level_expanded[level] = not self.level_expanded[level]
            
            # 更新第一个item的展开状态
            items[0].setExpanded(self.level_expanded[level])
            
            # 如果是展开状态，显示所有items
            if self.level_expanded[level]:
                for item in items:
                    item.setHidden(False)
            # 如果是折叠状态，只显示第一个item
            else:
                for i, item in enumerate(items):
                    item.setHidden(i != 0)  # 只有第一个item不隐藏

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 可根据需要设置样式
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    w = MonitorRuns()
    w.show()
    sys.exit(app.exec_())
