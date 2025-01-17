import os, sys, re, threading, time
import subprocess
from datetime import datetime

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QTabWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QStyleFactory, QMenu, QAction, QFileDialog, QMessageBox, QScrollBar,
                             QHeaderView, QStyle, QDialog, QTextEdit, QTabBar, QTreeWidget, QTreeWidgetItem,
                             QShortcut)
from PyQt5.QtCore import (Qt, QTimer, QRegExp, QObject, QSize)  # 添加 QSize 到 QtCore 导入
from PyQt5.QtGui import (QFont, QBrush, QColor, QClipboard, QIcon, QRegExpValidator, QFontMetrics, QKeySequence)

class TreeViewEventFilter(QObject):
    """事件过滤器，处理 TreeView 的展开/折叠"""
    def __init__(self, tree_view, parent):
        super().__init__(parent)  # 修改这里，将parent传递给QObject
        self.tree_view = tree_view
        self.parent = parent
        self.level_expanded = {}
        self.level_items = {}

    def eventFilter(self, obj, event):
        if obj == self.tree_view.viewport():
            if event.type() == event.MouseButtonPress:
                index = self.tree_view.indexAt(event.pos())
                if index.isValid():
                    # 获取点击的列
                    column = self.tree_view.columnAt(event.x())
                    # 只有在点击第一列时才触发折叠/展开
                    if column == 0:
                        # 获取点击的项
                        model = self.tree_view.model()
                        item = model.itemFromIndex(model.index(index.row(), 0))
                        
                        # 如果项目有子节点，切换其展开状态
                        if item and item.hasChildren():
                            is_expanded = self.tree_view.isExpanded(index)
                            if is_expanded:
                                self.tree_view.collapse(index)
                            else:
                                self.tree_view.expand(index)
                                
                            # 保存展开状态到父窗口的字典中
                            level = item.text()
                            run_dir = self.parent.combo_sel
                            if run_dir not in self.parent.level_expanded:
                                self.parent.level_expanded[run_dir] = {}
                            self.parent.level_expanded[run_dir][level] = not is_expanded
                            
                            return True
        return super().eventFilter(obj, event)

    def toggle_level_items(self, level):
        """切换level对应的items的显示/隐藏状态"""
        if level not in self.level_items:
            return
            
        # 切换展开状态
        self.level_expanded[level] = not self.level_expanded.get(level, True)
        
        # 遍历所有相同level的行
        rows = self.level_items[level]
        if not rows:
            return
            
        # 第一个项目始终显示，其他项目根据展开状态显示/隐藏
        for i, row in enumerate(rows):
            if i == 0:  # 第一个项目
                continue
            self.tree_view.setRowHidden(row, QtCore.QModelIndex(), not self.level_expanded[level])

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
        if level not in self.level_items:
            return
            
        # 切换展开状态
        self.level_expanded[level] = not self.level_expanded.get(level, True)
        
        # 遍历所有相同 level 的行
        rows = self.level_items[level]
        if not rows:
            return
            
        # 第一个项目始终显示，其他项目根据展开状态显示/隐藏
        for i, row in enumerate(rows):
            if i == 0:  # 第一个项目
                continue
            self.tree.setRowHidden(row, QtCore.QModelIndex(), not self.level_expanded[level])
   
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
        # self.create_menu()
        
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

        # 右边部分 - 按钮组
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.setSpacing(5)
        button_layout.addStretch()  # 添加弹性空间，使按钮靠右

        # 定义按钮样式
        button_style = """
            QPushButton {
                background-color: #6B5B95;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                min-width: 60px;  /* 减小最小宽度 */
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
        
        # 设置固定大小并应用样式到所有按钮
        button_size = QSize(100, 35)  # 设置固定大小
        for button in [bt_runall, bt_run, bt_stop, bt_skip, bt_unskip, bt_invalid]:
            button.setFixedSize(button_size)  # 应用固定大小
            button.setStyleSheet(button_style)
            button_layout.addWidget(button)

        # 将按钮组添加到主菜单布局
        menu_layout.addWidget(button_widget)

        # 设置伸缩因子，使两个部分合理分布
        menu_layout.setStretch(0, 1)  # ComboFrame
        menu_layout.setStretch(1, 2)  # Buttons

        # 将MenuFrame添加到主布局
        main_layout.addWidget(self.MenuFrame)

        # 添加TabWidget
        self.tabwidget = QTabWidget()
        self.tabwidget.setTabsClosable(True)  # 设置标签可关闭
        self.tabwidget.setMovable(True)
        self.tabwidget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tabwidget)

        # 初始化run_dir
        self.combo_sel = os.path.join(self.gen_combo.cur_dir, self.gen_combo.combobox.currentText())

        # 主Tab
        self.tab_run = QWidget()
        tab_run_layout = QVBoxLayout(self.tab_run)
        idx = self.tabwidget.addTab(self.tab_run, self.gen_combo.combobox.currentText())
        self.tabwidget.tabBar().setTabButton(idx, QTabBar.RightSide, None)

        # 创建 Model 和 TreeView
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["level", "target", "status", "start time", "end time"])
        
        # TreeView
        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setSelectionMode(QtWidgets.QTreeView.ExtendedSelection)
        self.tree_view.setRootIsDecorated(True)  # 显示展开/折叠图标
        self.tree_view.setItemsExpandable(True)  # 允许展开/折叠
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree_view.setIndentation(20)  # 设置缩进值
        
        # 设置列宽和调整模式
        header = self.tree_view.header()
        
        # 先设置每列为Fixed模式
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # level列
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # target列
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # status列
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # start time列
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # end time列
        header.setStretchLastSection(False)  # 最后一列不自动拉伸
        
        # 设置初始列宽
        self.tree_view.setColumnWidth(0, 50)   # level列
        self.tree_view.setColumnWidth(1, 1000)  # target列
        self.tree_view.setColumnWidth(2, 80)  # status列
        self.tree_view.setColumnWidth(3, 200)  # start time列
        self.tree_view.setColumnWidth(4, 200)  # end time列

        # 添加事件过滤器
        self.tree_view_event_filter = TreeViewEventFilter(self.tree_view, self)
        self.tree_view.viewport().installEventFilter(self.tree_view_event_filter)

        # 添加到布局
        tab_run_layout.addWidget(self.tree_view)

        # 信号槽连接
        self.gen_combo.combobox.currentIndexChanged.connect(self.click_event)
        self.tree_view.doubleClicked.connect(self.copy_tar_from_model)
        
        # 设置右键菜单
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu_for_view)

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

        self.init_run_view(self.combo_sel)

        # 窗口大小与位置初始化
        self.resize(1200,800)
        self.center()

        # 创建菜单栏和右键菜单
        self.create_menu()

        self.context_menu_active = False

        # 初始化搜索对话框
        self.search_dialog = SearchDialog(self)
        self.search_dialog.search_box.returnPressed.connect(self.search_in_code)
        # 移除这两行，不再使用 clicked 信号
        # self.search_dialog.prev_button.clicked.connect(lambda: self.navigate_search_results(-1))
        # self.search_dialog.next_button.clicked.connect(lambda: self.navigate_search_results(1))
        
        # 添加快捷键
        self.shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_search.activated.connect(self.toggle_search_dialog)

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
        if self.model:
            self.model.removeRows(0, self.model.rowCount())  # 使用 model 的方法清除数据
        
        self.get_tree(self.combo_sel)  # 重新加载新 run 的数据
        
        # 恢复展开状态
        if self.combo_sel in self.level_expanded:
            for level, is_expanded in self.level_expanded[self.combo_sel].items():
                # 查找对应的level项
                for row in range(self.model.rowCount()):
                    item = self.model.item(row, 0)
                    if item and item.text() == level:
                        index = self.model.indexFromItem(item)
                        if is_expanded:
                            self.tree_view.expand(index)
                        else:
                            self.tree_view.collapse(index)
                        break

    def change_run(self):
        """定时刷新所有树状态"""
        try:
            # 更新所有 tab 中的树控件
            for i in range(self.tabwidget.count()):
                tab = self.tabwidget.widget(i)
                tab_text = self.tabwidget.tabText(i)
                
                # 获取所有树控件
                tree_widgets = []
                tree_views = []
                
                # 检查是否是 retrace tab
                if hasattr(tab, 'retrace_tree'):
                    tree_widgets.append(tab.retrace_tree)
                else:
                    tree_widgets.extend(tab.findChildren(QTreeWidget))
                    tree_views.extend(tab.findChildren(QtWidgets.QTreeView))
                
                # 确定正确的 run_dir
                if tab_text == "All Runs Status":
                    # 对于All Runs Status标签页，使用专门的更新方法
                    if tree_widgets:
                        self.update_all_runs_status(tree_widgets[0])
                    continue
                
                run_dir = os.path.join(self.gen_combo.cur_dir, tab_text)
                    
                # 更新所有树控件的状态
                for tree_widget in tree_widgets:
                    self.update_tree_widget_status(tree_widget, run_dir)
                
                # 更新所有树视图的状态
                for tree_view in tree_views:
                    self.update_tree_view_status(tree_view, run_dir)
                
        except Exception as e:
            print(f"Error in change_run: {e}")

    def update_tree_widget_status(self, tree_widget, base_dir):
        """更新QTreeWidget的状态"""
        iterator = QtWidgets.QTreeWidgetItemIterator(tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.text(1):  # 确保有target
                target = item.text(1)
                current_status = item.text(2)  # 获取当前状态
                
                # 获取正确的run_dir
                if isinstance(tree_widget.parent(), QWidget) and hasattr(tree_widget.parent(), 'retrace_tree'):
                    # 如果是retrace tab中的tree widget
                    run_dir = self.combo_sel
                else:
                    run_dir = base_dir
                    
                target_file = os.path.join(run_dir, 'status', target)
                new_status = self.get_target_status(target_file)
                
                # 如果新状态为空且当前有状态，保持当前状态
                if new_status == '' and current_status != '':
                    if os.path.exists(target_file):
                        new_status = current_status
                
                # 只在状态确实改变时更新
                if new_status != current_status:
                    item.setText(2, new_status)
                    if new_status in self.colors:
                        color = QColor(self.colors[new_status])
                        for col in range(item.columnCount()):
                            item.setBackground(col, QBrush(color))
                    
                    if new_status != "":
                        tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                        start_time, end_time = self.get_start_end_time(tgt_track_file)
                        item.setText(3, start_time)
                        item.setText(4, end_time)
            iterator.__iadd__(1)

    def update_tree_view_status(self, tree_view, run_dir):
        """更新QTreeView的状态"""
        model = tree_view.model()
        if not model:
            return
            
        def update_row_status(row, parent=QtCore.QModelIndex()):
            target_index = model.index(row, 1, parent)
            target = model.data(target_index)
            if target:
                target_file = os.path.join(run_dir, 'status', target)
                new_status = self.get_target_status(target_file)
                
                status_index = model.index(row, 2, parent)
                current_status = model.data(status_index)
                
                if new_status != current_status:
                    model.setData(status_index, new_status)
                    if new_status in self.colors:
                        color = QColor(self.colors[new_status])
                        for col in range(model.columnCount()):
                            item = model.itemFromIndex(model.index(row, col, parent))
                            if item:
                                item.setBackground(QBrush(color))
                    
                    if new_status != "":
                        tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                        start_time, end_time = self.get_start_end_time(tgt_track_file)
                        model.setData(model.index(row, 3, parent), start_time)
                        model.setData(model.index(row, 4, parent), end_time)
        
        # 更新所有顶级项目
        for row in range(model.rowCount()):
            # 更新父项
            update_row_status(row)
            
            # 获取父项
            parent_item = model.item(row, 0)
            if parent_item and parent_item.hasChildren():
                # 更新所有子项
                for child_row in range(parent_item.rowCount()):
                    update_row_status(child_row, model.indexFromItem(parent_item))

    def get_entry(self):
        """保留方法但暂时不使用"""
        pass
        # self.filter_tab()  # 注释掉，保留方法

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

    def get_selected_targets(self):
        """获取当前选中的targets"""
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            return []
            
        # 获取选中行的target列(第2列)的值
        targets = []
        seen_indexes = set()  # 用于跟踪已处理的索引
        
        for index in selected_indexes:
            # 只处理target列
            if index.column() != 1:  # 1 是 target 列
                continue
                
            # 创建一个唯一标识符来跟踪已处理的索引
            index_key = (index.row(), index.parent().row() if index.parent().isValid() else -1)
            if index_key in seen_indexes:
                continue
                
            # 获取target列的值，考虑父子关系
            if index.parent().isValid():
                # 如果是子项，使用父索引来获取正确的target
                target_index = self.model.index(index.row(), 1, index.parent())
            else:
                # 如果是父项，直接使用当前行
                target_index = self.model.index(index.row(), 1)
                
            target = self.model.data(target_index)
            if target:
                targets.append(target)
            seen_indexes.add(index_key)
            
        return targets

    def start(self, action):
        """执行flow动作并刷新视图"""
        # 获取选中的targets
        selected_targets = self.get_selected_targets()
        if not selected_targets:
            return
        
        # 构建命令，只执行基本命令
        cmd = f"cd {self.combo_sel} && {action} "
        cmd += " ".join(selected_targets)
        
        # 执行命令
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        
        # 对于所有操作都立即更新状态
        for target in selected_targets:
            target_file = os.path.join(self.combo_sel, 'status', target)
            new_status = self.get_target_status(target_file)
            tgt_track_file = os.path.join(self.combo_sel, 'logs/targettracker', target)
            start_time, end_time = self.get_start_end_time(tgt_track_file)
            self.sync_item_status(target, new_status, start_time, end_time, self.tree_view, self.tree_view)
        
        # 如果是unskip动作或skip动作，需要重新构建树视图
        if action in ['XMeta_unskip', 'XMeta_skip']:
            self.get_tree(self.combo_sel)

    def Xterm(self):
        os.chdir(self.combo_sel)
        os.system('XMeta_term')

    def bt_event(self, status, tree_widget=None):
        """处理按钮事件，支持从指定的树获取选中项"""
        # 如果没有指定树，使用主树
        selected_tree = tree_widget if tree_widget else self.tree_view
        
        # 获取选中的 targets
        select_run_targets = []
        
        if isinstance(selected_tree, QtWidgets.QTreeView):
            # 处理 TreeView 的选中项
            selection_model = selected_tree.selectionModel()
            if selection_model:
                selected_indexes = selection_model.selectedIndexes()
                processed_indices = set()  # 用于跟踪已处理的索引
                
                for index in selected_indexes:
                    if index.column() != 1:  # 只处理 target 列
                        continue
                        
                    # 创建唯一标识符
                    identifier = f"{index.row()}-{index.parent().row() if index.parent().isValid() else 'root'}"
                    if identifier in processed_indices:
                        continue
                    processed_indices.add(identifier)
                    
                    # 获取target数据
                    model = selected_tree.model()
                    if index.parent().isValid():
                        # 如果是子项，从子项获取数据
                        target = model.data(index)
                    else:
                        # 如果是父项，从当前行获取数据
                        target = model.data(model.index(index.row(), 1))
                        
                    if target:
                        select_run_targets.append(target)
                        
        elif isinstance(selected_tree, QTreeWidget):
            # 处理 TreeWidget 的选中项
            selected = selected_tree.selectedItems()
            select_run_targets = [item.text(1) for item in selected if item.text(1) != ""]
        
        # 将targets列表转换为空格分隔的字符串
        select_run_targets = " ".join(select_run_targets)
        
        if select_run_targets.strip():
            # 执行命令
            os.chdir(self.combo_sel)
            os.system('%s %s' %(status, select_run_targets))
            
            # 获取当前 tab
            current_tab = self.tabwidget.currentWidget()
            
            # 查找当前 tab 中的 TreeView
            tree_view = None
            if current_tab == self.tab_run:
                tree_view = self.tree_view
            else:
                # 在当前 tab 中查找 QTreeView
                for child in current_tab.findChildren(QtWidgets.QTreeView):
                    tree_view = child
                    break
            
            # 立即更新状态
            if tree_view:
                for target in select_run_targets.split():
                    target_file = os.path.join(self.combo_sel, 'status', target)
                    new_status = self.get_target_status(target_file)
                    tgt_track_file = os.path.join(self.combo_sel, 'logs/targettracker', target)
                    start_time, end_time = self.get_start_end_time(tgt_track_file)
                    self.sync_item_status(target, new_status, start_time, end_time, selected_tree, tree_view)
            
            # 保存展开状态
            if isinstance(selected_tree, QtWidgets.QTreeView):
                model = selected_tree.model()
                expanded_indices = []
                if model:
                    def save_expanded_state(parent=QtCore.QModelIndex()):
                        for row in range(model.rowCount(parent)):
                            index = model.index(row, 0, parent)
                            if model.hasChildren(index) and selected_tree.isExpanded(index):
                                expanded_indices.append(index)
                            if model.hasChildren(index):
                                save_expanded_state(index)
                    save_expanded_state()
                
                # 清除选择
                selected_tree.clearSelection()
                
                # 恢复展开状态
                for index in expanded_indices:
                    selected_tree.expand(index)
                    
            elif isinstance(selected_tree, QTreeWidget):
                selected_tree.clearSelection()

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

    def bt_log(self, item=None):
        """Log - 打开 logs 目录下的 .log 文件"""
        # 获取当前选中的项
        if isinstance(item, QtWidgets.QTreeWidgetItem):
            target = item.text(1)
        else:
            indexes = self.tree_view.selectedIndexes()
            if not indexes:
                return
            target_index = self.model.index(indexes[0].row(), 1)  # 1是target列
            target = self.model.data(target_index)
        
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        log_file = os.path.join(current_run, 'logs', f"{current_target}.log")
        log_file_gz = f"{log_file}.gz"
        
        try:
            if os.path.exists(log_file):
                process = subprocess.Popen(['gvim', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()  # 等待进程完成
            elif os.path.exists(log_file_gz):
                process = subprocess.Popen(['gvim', log_file_gz], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()  # 等待进程完成
        except Exception as e:
            print(f"Error opening log file: {e}")

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
        """保留方法但暂时不使用"""
        pass
        # pattern = self.En_search.text()
        # ... 保留其余代码但暂时注释掉

    def filter_tab(self):
        """保留方法但暂时不使用"""
        pass
        # if not self.En_search.text().strip():
        #     return
        # ... 保留其余代码但暂时注释掉

    def sync_filter_selection_from_tree(self, tree, tree_view, model):
        """从过滤 TreeWidget 同步选择到过滤 TreeView"""
        if hasattr(self, '_syncing_filter_selection'):
            return
        self._syncing_filter_selection = True
        
        try:
            tree_view.selectionModel().clearSelection()
            selected_items = tree.selectedItems()
            selection = QtCore.QItemSelection()
            
            for tree_item in selected_items:
                target = tree_item.text(1)
                for row in range(model.rowCount()):
                    model_index = model.index(row, 1)
                    if model.data(model_index) == target:
                        left_index = model.index(row, 0)
                        right_index = model.index(row, model.columnCount() - 1)
                        selection.select(left_index, right_index)
            
            tree_view.selectionModel().select(selection, QtCore.QItemSelectionModel.Select)
        finally:
            delattr(self, '_syncing_filter_selection')

    def sync_filter_selection_from_view(self, selected, deselected, tree, model):
        """从过滤 TreeView 同步选择到过滤 TreeWidget"""
        if hasattr(self, '_syncing_filter_selection'):
            return
        self._syncing_filter_selection = True
        
        try:
            tree.clearSelection()
            selection = tree.selectionModel().selectedRows(1)
            
            for index in selection:
                target = model.data(index)
                # 修改这里的迭代器使用方式
                iterator = QtWidgets.QTreeWidgetItemIterator(tree)
                while iterator.value():
                    item = iterator.value()
                    if item.text(1) == target:
                        item.setSelected(True)
                        break
                    iterator.__iadd__(1)  # 使用 __iadd__ 方法替代 += 操作符
        finally:
            delattr(self, '_syncing_filter_selection')

    def retrace_tab(self, inout):
        # 获取当前选中的项
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
            
        # 获取target列的数据
        target_index = self.model.index(indexes[0].row(), 1)  # 1是target列
        self.tar_sel = self.model.data(target_index)
        
        if not self.tar_sel:
            return
            
        self.get_retrace_target(inout)
        if self.retrace_tar_name:
            tab_trace = QWidget()
            trace_layout = QVBoxLayout(tab_trace)

            retrace_tree = QTreeWidget()
            retrace_tree.setColumnCount(5)  # 修改为5列
            retrace_tree.setHeaderLabels(["level", "target", "status", "start time", "end time"])  # 添加所有列标签
            retrace_tree.setRootIsDecorated(True)
            retrace_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
            retrace_tree.itemDoubleClicked.connect(lambda item: self.copy_tar(item))

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

                    # 获取状态和时间信息
                    target_file = os.path.join(run_dir, 'status', target)
                    target_status = self.get_target_status(target_file)
                    tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                    start_time, end_time = self.get_start_end_time(tgt_track_file)

                    str_lv = ''.join(target_level)
                    o.append(str_lv)
                    d = [target_level, target, target_status, start_time, end_time]
                    l.append(d)

            all_lv = list(set(o))
            all_lv.sort(key=o.index)

            level_items = {}
            for data in l:
                lvl, tgt, st, ct, et = data
                str_data = ''.join(lvl)
                item = QTreeWidgetItem([str_data, tgt, st, ct, et])
                retrace_tree.addTopLevelItem(item)
                
                # 设置状态颜色
                if st in self.colors:
                    color = QColor(self.colors[st])
                    for col in range(item.columnCount()):
                        item.setBackground(col, QBrush(color))

                if str_data not in level_items:
                    level_items[str_data] = []
                level_items[str_data].append(item)

            # 创建右键菜单
            context_menu = QMenu()
            terminal_action = context_menu.addAction("Terminal")
            csh_action = context_menu.addAction("csh")
            log_action = context_menu.addAction("Log")
            cmd_action = context_menu.addAction("cmd")
            context_menu.addSeparator()
            trace_up_action = context_menu.addAction("Trace Up")
            trace_down_action = context_menu.addAction("Trace Down")

            # 连接右键菜单事件
            terminal_action.triggered.connect(lambda: self.bt_terminal(retrace_tree.currentItem()))
            csh_action.triggered.connect(lambda: self.bt_csh(retrace_tree.currentItem()))
            log_action.triggered.connect(lambda: self.bt_log(retrace_tree.currentItem()))
            cmd_action.triggered.connect(lambda: self.bt_cmd(retrace_tree.currentItem()))
            trace_up_action.triggered.connect(lambda: self.bt_trace_up(retrace_tree.currentItem()))
            trace_down_action.triggered.connect(lambda: self.bt_trace_down(retrace_tree.currentItem()))

            # 设置右键菜单策略
            retrace_tree.setContextMenuPolicy(Qt.CustomContextMenu)
            retrace_tree.customContextMenuRequested.connect(
                lambda pos, tree=retrace_tree, menu=context_menu: self.show_context_menu_for_tree(pos, tree, menu)
            )

            trace_layout.addWidget(retrace_tree)

            # 创建事件过滤器
            event_filter = TreeViewEventFilter(retrace_tree, self)
            event_filter.level_items = level_items
            retrace_tree.viewport().installEventFilter(event_filter)

            # 保存事件过滤器的引用，防止被垃圾回收
            retrace_tree.event_filter = event_filter

            # 添加到标签页
            idx = self.tabwidget.addTab(tab_trace, self.tar_sel)
            self.tabwidget.setCurrentIndex(idx)
            self.tree_view.clearSelection()

            # 将retrace_tree添加到tab_trace的属性中，以便在change_run中能够找到它
            tab_trace.retrace_tree = retrace_tree

            # 立即更新状态
            self.update_tree_widget_status(retrace_tree, run_dir)

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
        selected = self.tree_view.selectedItems()
        n = [itm.text(1) for itm in selected if itm.text(1) != ""]
        return n

    def get_tree(self, run_dir):
        """获取并构建树形视图"""
        # 使用已保存的展开状态
        if run_dir in self.level_expanded:
            expanded_states = self.level_expanded[run_dir]
        else:
            expanded_states = {}
        
        # 清空模型
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["level", "target", "status", "start time", "end time"])
        
        # 设置自定义代理来处理缩进
        delegate = IndentDelegate(self.tree_view)
        self.tree_view.setItemDelegate(delegate)
        
        # 获取数据
        self.get_target()
        
        l = []
        o = []
        
        # 读取数据
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

                target_file = os.path.join(run_dir, 'status', target)
                tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)

                start_time, end_time = self.get_start_end_time(tgt_track_file)
                target_status = self.get_target_status(target_file)

                str_lv = ''.join(target_level)
                o.append(str_lv)
                d = [target_level, target, target_status, start_time, end_time]
                l.append(d)
        
        # 获取所有唯一的level并排序
        all_lv = list(set(o))
        all_lv.sort(key=o.index)
        
        # 按level分组数据
        level_data = {}
        for data in l:
            lvl, tgt, st, ct, et = data
            str_data = ''.join(lvl)
            if str_data not in level_data:
                level_data[str_data] = []
            level_data[str_data].append((tgt, st, ct, et))
        
        # 创建父子节点结构
        level_items_model = {}
        
        # 遍历每个level
        for level in all_lv:
            if level not in level_data:
                continue
            
            items = level_data[level]
            if not items:
                continue
            
            # 创建父节点（第一个item）
            root_item = QtGui.QStandardItem()
            root_item.setText(level)
            root_item.setEditable(False)
            
            # 创建其他列的项目
            root_items = [root_item]
            first_item = items[0]
            for value in [first_item[0], first_item[1], first_item[2], first_item[3]]:
                item = QtGui.QStandardItem()
                item.setText(value)
                item.setEditable(False)
                root_items.append(item)
            
            # 设置父节点颜色
            if first_item[1] in self.colors:  # first_item[1] 是 status
                color = QColor(self.colors[first_item[1]])
                for item in root_items:
                    item.setBackground(QBrush(color))
            
            # 添加父节点到模型
            self.model.appendRow(root_items)
            parent_row = self.model.rowCount() - 1
            level_items_model[level] = [parent_row]
            
            # 如果有多个item，添加为子节点
            if len(items) > 1:
                for tgt, st, ct, et in items[1:]:
                    # 创建子节点的所有列
                    child_items = []
                    # level列
                    level_item = QtGui.QStandardItem()
                    level_item.setText(level)
                    level_item.setEditable(False)
                    child_items.append(level_item)
                    
                    # 其他列
                    for value in [tgt, st, ct, et]:
                        item = QtGui.QStandardItem()
                        item.setText(value)
                        item.setEditable(False)
                        child_items.append(item)
                    
                    # 设置子节点颜色
                    if st in self.colors:
                        color = QColor(self.colors[st])
                        for item in child_items:
                            item.setBackground(QBrush(color))
                    
                    # 添加子节点到父节点
                    root_item.appendRow(child_items)
                    level_items_model[level].append(self.model.rowCount())
        
        # 保存level项目映射到事件过滤器
        self.tree_view_event_filter.level_items = level_items_model
        
        # 设置列宽和调整模式
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # level列
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # target列
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # status列
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # start time列
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # end time列
        header.setStretchLastSection(False)  # 最后一列不自动拉伸
        
        # 设置列宽
        self.tree_view.setColumnWidth(0, 50)   # level列
        self.tree_view.setColumnWidth(1, 1000)  # target列
        self.tree_view.setColumnWidth(2, 80)  # status列
        self.tree_view.setColumnWidth(3, 200)  # start time列
        self.tree_view.setColumnWidth(4, 200)  # end time列

        # 恢复展开状态
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)
            if item and item.hasChildren():
                level = item.text()
                index = self.model.indexFromItem(item)
                # 如果有保存的状态，使用保存的状态
                if level in expanded_states:
                    self.tree_view.setExpanded(index, expanded_states[level])
                # 否则，根据子项数量决定是否展开
                else:
                    child_count = item.rowCount()
                    should_expand = child_count <= 3
                    self.tree_view.setExpanded(index, should_expand)
                    # 保存新的展开状态
                    if run_dir not in self.level_expanded:
                        self.level_expanded[run_dir] = {}
                    self.level_expanded[run_dir][level] = should_expand

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
            'scroll': self.tree_view.verticalScrollBar().value()
        }
        
        # 使用 model 来遍历 TreeView 的项目
        model = self.tree_view.model()
        if model:
            for row in range(model.rowCount()):
                level_index = model.index(row, 0)  # 第一列是 level
                target_index = model.index(row, 1)  # 第二列是 target
                
                level = model.data(level_index)
                target = model.data(target_index)
                
                # 保存展开状态
                if level:
                    state['expanded'][level] = self.tree_view.isExpanded(level_index)
                
                # 保存选中状态
                if self.tree_view.selectionModel().isSelected(level_index):
                    state['selected_parents'].append(level)
                if self.tree_view.selectionModel().isSelected(target_index):
                    state['selected'].append((level, target))
        
        return state

    def restore_tree_state(self, state):
        # 恢复展开状态和选中状态
        model = self.tree_view.model()
        if model:
            for row in range(model.rowCount()):
                level_index = model.index(row, 0)  # level 列
                target_index = model.index(row, 1)  # target 列
                
                level = model.data(level_index)
                target = model.data(target_index)
                
                # 恢复展开状态
                if level in state.get('expanded', {}):
                    self.tree_view.setExpanded(level_index, state['expanded'][level])
                
                # 恢复选中状态
                if level in state.get('selected_parents', []):
                    self.tree_view.selectionModel().select(level_index, 
                        QtCore.QItemSelectionModel.Select)
                
                # 恢复子项选中状态
                if state.get('selected'):
                    for parent_text, child_text in state['selected']:
                        if level == parent_text and target == child_text:
                            self.tree_view.selectionModel().select(target_index,
                                QtCore.QItemSelectionModel.Select)
        
        # 恢复滚动条位置
        if 'scroll' in state:
            self.tree_view.verticalScrollBar().setValue(state['scroll'])

    def create_menu(self):
        """Create menu bar and context menu"""
        # 创建菜单栏
        menubar = self.menuBar()
        
        # Add View menu
        view_menu = menubar.addMenu('View')
        
        # Add show all runs status action
        show_all_runs_action = QAction('Show All Runs Status', self)
        show_all_runs_action.triggered.connect(self.show_all_runs_status)
        view_menu.addAction(show_all_runs_action)
        
        # 创建右键菜单
        self.context_menu = QMenu()
        # 设置菜单样式
        self.context_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #C0C0C0;
                padding: 2px;
            }
            QMenu::item {
                padding: 3px 20px 3px 20px;
                border-radius: 2px;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #E1BEE7;
                color: black;
            }
            QMenu::item:hover {
                background-color: #F5F5F5;
                color: black;
            }
            QMenu::separator {
                height: 1px;
                background: #C0C0C0;
                margin: 2px 0px 2px 0px;
            }
        """)
        
        # 添加右键菜单项
        self.context_menu.addAction("Terminal")
        self.context_menu.addAction("csh")
        self.context_menu.addAction("Log")
        self.context_menu.addAction("cmd")
        self.context_menu.addSeparator()
        self.context_menu.addAction("Trace Up")
        self.context_menu.addAction("Trace Down")

    def update_all_runs_status(self, status_tree):
        """更新All Runs Status标签页的状态"""
        # 保存当前选中的项
        selected_items = []
        for item in status_tree.selectedItems():
            selected_items.append(item.text(0))  # 保存run directory名称
        
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

        # 清空现有项目
        status_tree.clear()

        # 重新添加数据
        for run_dir in sorted(run_dirs):
            run_path = os.path.join(base_path, run_dir)
            status_dir = os.path.join(run_path, 'status')
            
            if not os.path.isdir(status_dir):
                item = QTreeWidgetItem(status_tree)
                item.setText(0, run_dir)
                item.setText(1, 'N/A')
                item.setText(2, 'No status dir')
                item.setText(3, 'N/A')
                # 恢复选中状态
                if run_dir in selected_items:
                    item.setSelected(True)
                continue

            latest_target, latest_status, latest_mtime = self.get_latest_target_status(status_dir)
            if not latest_target or not latest_status:
                item = QTreeWidgetItem(status_tree)
                item.setText(0, run_dir)
                item.setText(1, 'N/A')
                item.setText(2, 'No valid mark files')
                item.setText(3, 'N/A')
                # 恢复选中状态
                if run_dir in selected_items:
                    item.setSelected(True)
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
                
            # 恢复选中状态
            if run_dir in selected_items:
                item.setSelected(True)

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
        status_tree.setSelectionMode(QTreeWidget.ExtendedSelection)  # 允许多选
        
        # Set column widths
        header = status_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Run Directory 可调整
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Latest Target 可调整
        header.setSectionResizeMode(2, QHeaderView.Fixed)       # Status 固定宽度
        header.setSectionResizeMode(3, QHeaderView.Stretch)     # Timestamp 自动填充
        
        # 设置右键菜单
        status_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        status_tree.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu_for_status(pos, status_tree)
        )
        
        tab_status_layout.addWidget(status_tree)
        
        # 添加数据并创建标签页
        self.update_all_runs_status(status_tree)
        
        idx = self.tabwidget.addTab(tab_status, "All Runs Status")
        self.tabwidget.setCurrentIndex(idx)

    def show_context_menu_for_status(self, position, tree_widget):
        """为 All Runs Status 显示右键菜单"""
        if self.context_menu_active:
            return
        self.context_menu_active = True
        
        selected_items = tree_widget.selectedItems()
        if not selected_items:
            return
        
        # 获取选中项的 run directory 和 target
        run_dir = selected_items[0].text(0)  # 第一列是 run directory
        target = selected_items[0].text(1)   # 第二列是 target
        
        # 如果没有有效的 target，不显示菜单
        if target == 'N/A':
            self.context_menu_active = False
            return
        
        # 设置当前工作目录为选中的 run directory
        self.combo_sel = os.path.join(self.gen_combo.cur_dir, run_dir)
        
        # 创建右键菜单
        context_menu = QMenu()
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #C0C0C0;
                padding: 2px;
            }
            QMenu::item {
                padding: 3px 20px 3px 20px;
                border-radius: 2px;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #E1BEE7;
                color: black;
            }
            QMenu::item:hover {
                background-color: #F5F5F5;
                color: black;
            }
            QMenu::separator {
                height: 1px;
                background: #C0C0C0;
                margin: 2px 0px 2px 0px;
            }
        """)
        
        # 只添加基本操作菜单项，移除 Trace Up 和 Trace Down
        terminal_action = context_menu.addAction("Terminal")
        csh_action = context_menu.addAction("csh")
        log_action = context_menu.addAction("Log")
        cmd_action = context_menu.addAction("cmd")
        
        def cleanup_menu():
            self.context_menu_active = False
        
        context_menu.aboutToHide.connect(cleanup_menu)
        
        # 显示菜单
        action = context_menu.exec_(tree_widget.viewport().mapToGlobal(position))
        
        # 创建一个模拟的 TreeWidgetItem 来传递给现有的处理函数
        mock_item = QTreeWidgetItem()
        mock_item.setText(1, target)  # 设置 target 到第二列
        
        # 处理菜单动作
        if action == terminal_action:
            self.Xterm()
        elif action == csh_action:
            self.bt_csh(mock_item)
        elif action == log_action:
            self.bt_log(mock_item)
        elif action == cmd_action:
            self.bt_cmd(mock_item)

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

    def create_context_menu(self):
        """Create context menu"""
        self.context_menu = QMenu()
        # 设置菜单样式
        self.context_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #C0C0C0;
                padding: 2px;
            }
            QMenu::item {
                padding: 3px 20px 3px 20px;
                border-radius: 2px;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #E1BEE7;
                color: black;
            }
            QMenu::item:hover {
                background-color: #F5F5F5;
                color: black;
            }
            QMenu::separator {
                height: 1px;
                background: #C0C0C0;
                margin: 2px 0px 2px 0px;
            }
        """)
        
        # 添加菜单项
        self.context_menu.addAction("Terminal")
        self.context_menu.addAction("csh")
        self.context_menu.addAction("Log")
        self.context_menu.addAction("cmd")
        self.context_menu.addSeparator()
        self.context_menu.addAction("Trace Up")
        self.context_menu.addAction("Trace Down")

    def show_context_menu_for_view(self, position, tree_view=None):
        """为 QTreeView 显示右键菜单"""
        if self.context_menu_active:
            return
        self.context_menu_active = True
        
        # 使用传入的 tree_view 或默认的 self.tree_view
        view = tree_view if tree_view is not None else self.tree_view
        index = view.indexAt(position)
        if not index.isValid():
            return
        
        # 获取选中项的 target
        model = view.model()
        target_index = model.index(index.row(), 1)  # 1 是 target 列
        target = model.data(target_index)
        
        if not target:
            return
            
        # 创建上下文菜单
        context_menu = QMenu()
        context_menu.setStyleSheet(self.context_menu.styleSheet())
        
        # 添加基本菜单项
        terminal_action = context_menu.addAction("Terminal")
        csh_action = context_menu.addAction("csh")
        log_action = context_menu.addAction("Log")
        cmd_action = context_menu.addAction("cmd")
        context_menu.addSeparator()
        
        # 检查是否存在 nlib 文件，如果存在则添加 Open nlib 菜单项
        open_nlib_action = None
        nlib_path = None
        if target.startswith('I2'):
            # 尝试两种可能的 nlib 文件名
            nlib_name1 = target[2:] + '.nlib'  # 去掉 I2 的情况
            nlib_name2 = target + '.nlib'      # 完整 target 名的情况
            nlib_path1 = os.path.join(self.combo_sel, 'data', nlib_name1)
            nlib_path2 = os.path.join(self.combo_sel, 'data', nlib_name2)
            
            if os.path.exists(nlib_path1):
                nlib_path = nlib_path1
            elif os.path.exists(nlib_path2):
                nlib_path = nlib_path2
                
            if nlib_path:
                open_nlib_action = context_menu.addAction("Open nlib")
                context_menu.addSeparator()
        
        trace_up_action = context_menu.addAction("Trace Up")
        trace_down_action = context_menu.addAction("Trace Down")
        
        def cleanup_menu():
            self.context_menu_active = False
        
        context_menu.aboutToHide.connect(cleanup_menu)
        
        # 显示菜单
        action = context_menu.exec_(view.viewport().mapToGlobal(position))
        
        # 处理菜单动作
        if action == terminal_action:
            self.Xterm()
        elif action == csh_action:
            self.bt_csh_for_model(index)
        elif action == log_action:
            self.bt_log_for_model(index)
        elif action == cmd_action:
            self.bt_cmd_for_model(index)
        elif open_nlib_action and action == open_nlib_action:
            try:
                cmd = f"XMeta_icc2 {nlib_path}"
                subprocess.Popen(cmd, shell=True)
            except subprocess.SubprocessError as e:
                print(f"Error opening nlib: {e}")
        elif action == trace_up_action:
            self.bt_trace_up_for_model(index)
        elif action == trace_down_action:
            self.bt_trace_down_for_model(index)

    def bt_csh_for_model(self, index):
        """为 Model 视图处理 csh 命令"""
        if not index.isValid():
            return
            
        target_index = self.model.index(index.row(), 1)
        target = self.model.data(target_index)
        if not target:
            return
            
        shell_file = os.path.join(self.combo_sel, 'make_targets', f"{target}.csh")
        if os.path.exists(shell_file):
            try:
                subprocess.run(['gvim', shell_file], check=True)
            except subprocess.CalledProcessError:
                pass
    
    def bt_log_for_model(self, index):
        """为 Model 视图处理 log 命令"""
        if not index.isValid():
            return
            
        # 获取当前选中项的model
        model = index.model()
        if not model:
            return
            
        # 获取target列的数据
        if index.parent().isValid():
            # 如果是子项，直接从子项的target列获取数据
            target_index = model.index(index.row(), 1, index.parent())
        else:
            # 如果是父项，从当前行获取数据
            target_index = model.index(index.row(), 1)
            
        target = model.data(target_index)
        if not target:
            return
            
        log_file = os.path.join(self.combo_sel, 'logs', f"{target}.log")
        log_file_gz = f"{log_file}.gz"
        
        # 检查文件是否存在
        if not os.path.exists(log_file) and not os.path.exists(log_file_gz):
            print(f"Log file not found: {log_file}")
            return
            
        # 打开存在的文件
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
    
    def bt_cmd_for_model(self, index):
        """为 Model 视图处理 cmd 命令"""
        if not index.isValid():
            return
            
        target_index = self.model.index(index.row(), 1)
        target = self.model.data(target_index)
        if not target:
            return
            
        cmd_file = os.path.join(self.combo_sel, 'cmds', f"{target}.cmd")
        if os.path.exists(cmd_file):
            try:
                subprocess.run(['gvim', cmd_file], check=True)
            except subprocess.CalledProcessError:
                pass
    
    def bt_trace_up_for_model(self, index):
        """为 Model 视图处理 Trace Up 命令"""
        if not index.isValid():
            return
            
        target_index = index.model().index(index.row(), 1)  # 1 是 target 列
        self.tar_sel = index.model().data(target_index)
        if self.tar_sel:
            self.retrace_tab('in')
    
    def bt_trace_down_for_model(self, index):
        """为 Model 视图处理 Trace Down 命令"""
        if not index.isValid():
            return
            
        target_index = index.model().index(index.row(), 1)  # 1 是 target 列
        self.tar_sel = index.model().data(target_index)
        if self.tar_sel:
            self.retrace_tab('out')

    def sync_item_status(self, target, new_status, start_time, end_time, tree_widget, tree_view):
        """更新 TreeView 中指定 target 的状态"""
        # 更新 TreeView
        if tree_view and tree_view.model():
            model = tree_view.model()
            
            def update_item(parent_index=QtCore.QModelIndex()):
                # 更新父项
                if not parent_index.isValid():
                    for row in range(model.rowCount()):
                        target_index = model.index(row, 1)
                        current_target = model.data(target_index)
                        if current_target == target:
                            self._update_item_data(model, row, new_status, start_time, end_time)
                            
                        # 检查子项
                        parent_item = model.item(row, 0)
                        if parent_item and parent_item.hasChildren():
                            child_parent = model.indexFromItem(parent_item)
                            for child_row in range(parent_item.rowCount()):
                                child_target_index = model.index(child_row, 1, child_parent)
                                child_target = model.data(child_target_index)
                                if child_target == target:
                                    self._update_item_data(model, child_row, new_status, start_time, end_time, child_parent)
            
            # 从根节点开始更新
            update_item()
            
    def _update_item_data(self, model, row, new_status, start_time, end_time, parent=QtCore.QModelIndex()):
        """更新单个项目的数据"""
        # 更新状态
        status_index = model.index(row, 2, parent)
        model.setData(status_index, new_status)
        
        # 更新时间
        start_time_index = model.index(row, 3, parent)
        end_time_index = model.index(row, 4, parent)
        model.setData(start_time_index, start_time)
        model.setData(end_time_index, end_time)
        
        # 更新颜色
        if new_status in self.colors:
            color = QColor(self.colors[new_status])
            for col in range(model.columnCount()):
                item = model.itemFromIndex(model.index(row, col, parent))
                if item:
                    item.setBackground(QBrush(color))

    def update_status_and_time(self, run_dir, tree_widget, tree_view):
        """更新指定目录下所有 target 的状态和时间"""
        if isinstance(tree_widget, QTreeWidget):
            # TreeWidget 的更新逻辑
            iterator = QTreeWidgetItemIterator(tree_widget)
            while iterator.value():
                item = iterator.value()
                if item.text(1):  # 如果有target名称
                    self.update_tree_widget_item(item, run_dir)
                iterator.__iadd__(1)  # 使用 __iadd__ 替代 += 操作符
        elif isinstance(tree_view, QtWidgets.QTreeView):
            # TreeView 的更新逻辑
            model = tree_view.model()
            if model:
                for row in range(model.rowCount()):
                    self.update_tree_view_item(model, row, run_dir)

    def update_tree_widget_item(self, item, run_dir):
        """更新 TreeWidget 项目的状态"""
        target = item.text(1)
        target_file = os.path.join(run_dir, 'status', target)
        new_status = self.get_target_status(target_file)
        current_status = item.text(2)
        
        if new_status != current_status:
            item.setText(2, new_status)
            if new_status in self.colors:
                color = QColor(self.colors[new_status])
                for col in range(item.columnCount()):
                    item.setBackground(col, QBrush(color))
            
            if new_status:
                tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                start_time, end_time = self.get_start_end_time(tgt_track_file)
                item.setText(3, start_time)
                item.setText(4, end_time)

    def update_tree_view_item(self, model, row, run_dir):
        """更新 TreeView 项目的状态"""
        target_index = model.index(row, 1)
        target = model.data(target_index)
        target_file = os.path.join(run_dir, 'status', target)
        new_status = self.get_target_status(target_file)
        status_index = model.index(row, 2)
        current_status = model.data(status_index)
        
        if new_status != current_status:
            model.setData(status_index, new_status)
            if new_status in self.colors:
                color = QColor(self.colors[new_status])
                for col in range(model.columnCount()):
                    model.item(row, col).setBackground(QBrush(color))
            
            if new_status:
                tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                start_time, end_time = self.get_start_end_time(tgt_track_file)
                model.setData(model.index(row, 3), start_time)
                model.setData(model.index(row, 4), end_time)

    def copy_tar_from_model(self, index):
        """处理双击事件，复制目标名称到剪贴板"""
        if not index.isValid():
            return
        
        # 获取目标名称（第2列）
        target_index = self.model.index(index.row(), 1)
        target = self.model.data(target_index)
        
        if target:
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(target)

    def search_in_code(self):
        """在当前显示的代码中搜索"""
        search_text = self.search_dialog.search_box.text()
        if not search_text:
            return

        # 获取当前活动的标签页
        current_tab = self.tabwidget.currentWidget()
        if not current_tab:
            return

        # 获取当前标签页中的树视图
        tree_view = None
        if current_tab == self.tab_run:
            tree_view = self.tree_view
        else:
            # 在当前标签页中查找树视图
            tree_views = current_tab.findChildren(QtWidgets.QTreeView)
            if tree_views:
                tree_view = tree_views[0]

        if not tree_view or not tree_view.model():
            return

        # 清除之前的搜索结果
        self.search_results = []
        self.current_result = -1

        # 在树视图中搜索
        model = tree_view.model()
        for row in range(model.rowCount()):
            for col in range(model.columnCount()):
                index = model.index(row, col)
                text = str(model.data(index))
                if search_text.lower() in text.lower():
                    self.search_results.append(index)

        # 更新搜索结果计数
        total = len(self.search_results)
        self.search_dialog.count_label.setText(f"0/{total}")

        # 如果有结果，跳转到第一个
        if self.search_results:
            self.navigate_search_results(1)

    def navigate_search_results(self, direction):
        """在搜索结果中导航
        direction: 1 表示下一个，-1 表示上一个
        """
        if not hasattr(self, 'search_results') or not self.search_results:
            return

        total = len(self.search_results)
        if direction > 0:
            self.current_result = (self.current_result + 1) % total
        else:
            self.current_result = (self.current_result - 1) % total

        # 获取当前活动的标签页中的树视图
        current_tab = self.tabwidget.currentWidget()
        tree_view = None
        if current_tab == self.tab_run:
            tree_view = self.tree_view
        else:
            # 在当前标签页中查找树视图
            tree_views = current_tab.findChildren(QtWidgets.QTreeView)
            if tree_views:
                tree_view = tree_views[0]

        if not tree_view:
            return

        # 更新计数显示
        self.search_dialog.count_label.setText(f"{self.current_result + 1}/{total}")

        # 跳转到当前结果
        current_index = self.search_results[self.current_result]
        tree_view.setCurrentIndex(current_index)
        tree_view.scrollTo(current_index)
        
        # 高亮显示当前结果
        tree_view.setFocus()
        tree_view.selectionModel().select(current_index, QtCore.QItemSelectionModel.ClearAndSelect)

    def eventFilter(self, obj, event):
        """事件过滤器，处理 ESC 键"""
        if obj == self.code_search and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.hide_search_widget()
                return True
        return super().eventFilter(obj, event)
    
    def toggle_search_widget(self):
        """切换搜索框的显示/隐藏状态"""
        if self.search_widget.isHidden():
            self.search_widget.show()
            self.code_search.setFocus()  # 显示时自动获取焦点
            self.code_search.selectAll()  # 选中所有文本
        else:
            self.hide_search_widget()
    
    def hide_search_widget(self):
        """隐藏搜索框"""
        self.search_widget.hide()
        # 将焦点返回给树视图
        current_tab = self.tabwidget.currentWidget()
        if current_tab == self.tab_run:
            self.tree_view.setFocus()
        else:
            tree_views = current_tab.findChildren(QtWidgets.QTreeView)
            if tree_views:
                tree_views[0].setFocus()

    def toggle_search_dialog(self):
        """切换搜索对话框的显示/隐藏状态"""
        if self.search_dialog.isHidden():
            self.search_dialog.show()
            self.search_dialog.search_box.setFocus()
            self.search_dialog.search_box.selectAll()
        else:
            self.search_dialog.hide()

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)  # 无边框窗口
        
        # 设置背景色和边框
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #C0C0C0;
                border-radius: 5px;
            }
        """)
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search in code...")
        self.search_box.setMinimumWidth(200)
        
        # 搜索结果计数标签
        self.count_label = QLabel("0/0")
        self.count_label.setFixedWidth(50)
        
        # 导航按钮
        self.prev_button = QPushButton("↑")
        self.next_button = QPushButton("↓")
        self.prev_button.setFixedWidth(30)
        self.next_button.setFixedWidth(30)
        
        # 添加到布局
        layout.addWidget(self.search_box)
        layout.addWidget(self.count_label)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        
        # 安装事件过滤器处理ESC键
        self.search_box.installEventFilter(self)
        
        # 创建定时器用于长按连续触发
        self.repeat_timer = QTimer()
        self.repeat_timer.setInterval(100)  # 设置重复间隔为100毫秒
        self.repeat_timer.timeout.connect(self.handle_button_repeat)
        
        # 记录当前按下的按钮和方向
        self.current_button = None
        self.current_direction = 0
        self.is_long_press = False  # 标记是否为长按
        self.press_time = 0  # 记录按下时间
        
        # 为按钮添加事件过滤器
        self.prev_button.installEventFilter(self)
        self.next_button.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        if obj == self.search_box and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.hide()
                return True
        elif obj in (self.prev_button, self.next_button):
            if event.type() == QtCore.QEvent.MouseButtonPress:
                direction = -1 if obj == self.prev_button else 1
                self.handle_button_press(obj, direction)
                return True
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                self.handle_button_release()
                return True
        return super().eventFilter(obj, event)
        
    def handle_button_press(self, button, direction):
        """处理按钮按下事件"""
        self.current_button = button
        self.current_direction = direction
        self.is_long_press = False
        self.press_time = time.time()
        
        # 立即触发一次
        if hasattr(self.parent(), 'navigate_search_results'):
            self.parent().navigate_search_results(direction)
            
        # 启动定时器，延迟800毫秒后开始连续触发
        QTimer.singleShot(800, self.start_repeat_timer)
        
    def handle_button_release(self):
        """处理按钮释放事件"""
        release_time = time.time()
        # 如果不是长按且按下时间小于200毫秒，不触发额外的点击
        if not self.is_long_press and (release_time - self.press_time) < 0.2:
            pass
        
        self.repeat_timer.stop()
        self.current_button = None
        self.current_direction = 0
        self.is_long_press = False
        
    def start_repeat_timer(self):
        """开始连续触发定时器"""
        if self.current_button and self.current_button.isDown():
            self.is_long_press = True
            self.repeat_timer.start()
            
    def handle_button_repeat(self):
        """处理定时器触发的重复事件"""
        if self.current_button and self.current_button.isDown() and self.is_long_press:
            if hasattr(self.parent(), 'navigate_search_results'):
                self.parent().navigate_search_results(self.current_direction)

    def showEvent(self, event):
        # 在父窗口中央显示
        parent = self.parent()
        if parent:
            geometry = parent.geometry()
            x = geometry.x() + (geometry.width() - self.width()) // 2
            y = geometry.y() + 80  # 距离顶部80像素
            self.move(x, y)
        super().showEvent(event)

class IndentDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        # 只对第一列（level列）特殊处理
        if index.column() == 0:
            # 保存原始的left位置
            original_left = option.rect.left()
            # 如果是子项，移除缩进
            if index.parent().isValid():
                # 直接使用parent()作为tree_view
                indent = self.parent().indentation()
                option.rect.setLeft(original_left - indent)
        super().paint(painter, option, index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 可根据需要设置样式
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    w = MonitorRuns()
    w.show()
    sys.exit(app.exec_())
