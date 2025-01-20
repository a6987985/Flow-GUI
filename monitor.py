import os, sys, re, threading, time
import subprocess
from datetime import datetime

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QTabWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QStyleFactory, QMenu, QAction, QFileDialog, QMessageBox, QScrollBar,
                             QHeaderView, QStyle, QDialog, QTextEdit, QTabBar, QTreeWidget, QTreeWidgetItem,
                             QShortcut, QTreeWidgetItemIterator, QSplitter, QSizePolicy)
from PyQt5.QtCore import (Qt, QTimer, QRegExp, QObject, QSize)
from PyQt5.QtGui import (QFont, QBrush, QColor, QClipboard, QIcon, QRegExpValidator, QFontMetrics, QKeySequence)
from PyQt5.QtSvg import QSvgWidget
from event_filters import TreeViewEventFilter
from dialogs import SearchDialog
from widgets import ComboFrame
from managers import TreeManager, StatusManager, MenuManager, ActionManager
from tree_handlers import TreeHandlers
from trace_handlers import TraceHandlers

# 添加基类定义
class MonitorBase(QMainWindow):
    """基础监控类，提供基本功能"""
    def __init__(self):
        super().__init__()
        self.init_base_attributes()
        
    def init_base_attributes(self):
        """初始化基本属性"""
        # 环境变量
        self.xmeta_project = os.getenv('XMETA_PROJECT_NAME', 'XMetaProject')
        self.family = os.getenv('FAMILY', 'Family')
        self.xmeta_background = os.getenv('XMETA_BACKGROUND', '#ffffff')
        self.version = os.getenv('XMETA_VERSION', 'Version')
        
        # 状态颜色
        self.colors = {
            'finish': '#67c23a',
            'skip': '#e6a23c',
            'failed': '#f56c6c',
            'scheduled': '#409eff',
            'running': '#ffd700',
            'pending': '#ff9900',
            'invalid': '#909399'
        }
        
        # 基本状态
        self.level_expanded = {}
        self.context_menu_active = False

class MonitorRuns(MonitorBase):
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.tree_manager = TreeManager(self)
        self.status_manager = StatusManager(self)
        self.menu_manager = MenuManager(self)
        self.action_manager = ActionManager(self)
        
        # 获取 tree_view 的引用
        self.tree_view = self.tree_manager.tree_view
        self.model = self.tree_manager.model
        
        # 设置事件过滤器
        self.tree_view_event_filter = TreeViewEventFilter(self.tree_view, self)
        self.tree_view.viewport().installEventFilter(self.tree_view_event_filter)
        
        # 初始化 Handlers
        self.tree_handlers = TreeHandlers(self)
        self.trace_handlers = TraceHandlers(self)
        
        # 主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
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
        tab_run_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        tab_run_layout.setSpacing(0)  # 移除间距
        idx = self.tabwidget.addTab(self.tab_run, self.gen_combo.combobox.currentText())
        self.tabwidget.tabBar().setTabButton(idx, QTabBar.RightSide, None)
        
        # 创建一个容器widget来包含tree_view
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self.tree_view)
        
        # 将容器添加到tab布局
        tab_run_layout.addWidget(container)
        
        # 设置tab和tree_view的大小策略
        self.tab_run.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tree_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
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
        
        # 添加快捷键
        self.shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_search.activated.connect(lambda: self.search_dialog.show())
        
        # 添加 Ctrl+C 快捷键
        self.shortcut_copy = QShortcut(QKeySequence("Ctrl+C"), self)
        self.shortcut_copy.activated.connect(self.copy_selected_target)
        
        # 设置窗口标题
        title_name = "Console of XMeta/%s-%s @ %s" %(self.version, self.family, self.xmeta_project)
        self.setWindowTitle(title_name)

        # 创建分隔器
        self.splitter = QSplitter(Qt.Vertical)
        
        # 将TabWidget添加到分隔器
        self.splitter.addWidget(self.tabwidget)
        
        # 创建日志输出区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)  # 设置为只读
        self.log_area.setMinimumHeight(100)  # 设置最小高度
        
        # 设置字体
        font = QtGui.QFont("Consolas", 12)
        font.setStyleHint(QtGui.QFont.Monospace)
        self.log_area.setFont(font)
        
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #F8F0FC;
                border: none;
                border-top: 1px solid #E1BEE7;
                padding: 10px;
            }
        """)
        
        # 将日志区域添加到分隔器
        self.splitter.addWidget(self.log_area)
        
        # 设置分隔器的初始比例
        self.splitter.setStretchFactor(0, 7)  # TabWidget占70%
        self.splitter.setStretchFactor(1, 3)  # 日志区域占30%
        
        # 将分隔器添加到主布局
        main_layout.addWidget(self.splitter)

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
        """更新运行状态"""
        if not hasattr(self, 'model') or not self.model:
            return
            
        for i in range(self.model.rowCount()):
            level_item = self.model.item(i, 0)
            if not level_item:
                continue
                
            target_item = self.model.item(i, 1)
            status_item = self.model.item(i, 2)
            start_time_item = self.model.item(i, 3)
            end_time_item = self.model.item(i, 4)
            
            if not all([target_item, status_item, start_time_item, end_time_item]):
                continue
                
            target = target_item.text()
            target_file = os.path.join(self.combo_sel, 'status', target)
            tgt_track_file = os.path.join(self.combo_sel, 'logs/targettracker', target)
            
            # 使用 StatusManager 获取状态和时间
            status = self.status_manager.get_target_status(target_file)
            start_time, end_time = self.status_manager.get_start_end_time(tgt_track_file)
            
            # 更新状态和时间
            if status and status != status_item.text():
                status_item.setText(status)
                color = self.colors.get(status, '#000000')
                status_item.setForeground(QBrush(QColor(color)))
                
            if start_time != start_time_item.text():
                start_time_item.setText(start_time)
            if end_time != end_time_item.text():
                end_time_item.setText(end_time)

    def get_target_status(self, target_file):
        """获取目标状态，委托给 StatusManager"""
        return self.status_manager.get_target_status(target_file)
        
    def get_start_end_time(self, tgt_track_file):
        """获取开始和结束时间，委托给 StatusManager"""
        return self.status_manager.get_start_end_time(tgt_track_file)

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
        
        # 获取当前run的名字
        current_run = os.path.basename(self.combo_sel)
        
        # 构建命令，只执行基本命令
        if action == 'XMeta_run all':
            cmd = f"cd {self.combo_sel} && {action}"
            # 记录日志 - run all 不需要显示target
            log_msg = f"{current_run}, {action}."
        else:
            cmd = f"cd {self.combo_sel} && {action} "
            cmd += " ".join(selected_targets)
            # 记录日志 - 其他命令显示target
            log_msg = f"{current_run}, {action} {' '.join(selected_targets)}."
        
        self.log_message(log_msg, "info")
        
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
            # 保存当前展开状态
            expanded_states = {}
            for row in range(self.model.rowCount()):
                item = self.model.item(row, 0)
                if item and item.hasChildren():
                    level = item.text()
                    index = self.model.indexFromItem(item)
                    expanded_states[level] = self.tree_view.isExpanded(index)
            
            # 重新加载树
            self.get_tree(self.combo_sel)
            
            # 恢复展开状态
            for row in range(self.model.rowCount()):
                item = self.model.item(row, 0)
                if item and item.hasChildren():
                    level = item.text()
                    index = self.model.indexFromItem(item)
                    if level in expanded_states:
                        self.tree_view.setExpanded(index, expanded_states[level])

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
        """委托给 TraceHandlers"""
        self.trace_handlers.retrace_tab(inout)

    def get_retrace_target(self, inout):
        """委托给 TraceHandlers"""
        self.trace_handlers.get_retrace_target(inout)

    def get_target(self):
        """委托给 TreeHandlers"""
        return self.tree_handlers.get_target()

    def copy_item(self):
        selected = self.tree_view.selectedItems()
        n = [itm.text(1) for itm in selected if itm.text(1) != ""]
        return n

    def get_tree(self, run_dir):
        """委托给 TreeHandlers"""
        self.tree_handlers.get_tree(run_dir)
        
    def save_tree_state(self):
        """委托给 TreeHandlers"""
        return self.tree_handlers.save_tree_state()
        
    def restore_tree_state(self, state):
        """委托给 TreeHandlers"""
        self.tree_handlers.restore_tree_state(state)

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

    def create_menu(self):
        """创建菜单，委托给 MenuManager"""
        self.menu_manager.create_menu()
        
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

    def show_context_menu_for_view(self, pos):
        """显示右键菜单"""
        if self.context_menu_active:
            return
            
        self.context_menu_active = True
        
        # 获取当前选中的项
        index = self.tree_view.indexAt(pos)
        if not index.isValid():
            self.context_menu_active = False
            return
            
        # 获取选中项的 target
        target_index = self.model.index(index.row(), 1)  # 1 是 target 列
        target = self.model.data(target_index)
        
        if not target:
            self.context_menu_active = False
            return
            
        # 创建上下文菜单
        context_menu = QMenu()
        context_menu.setStyleSheet(self.menu_manager.context_menu.styleSheet())
        
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
        
        # 显示菜单
        action = context_menu.exec_(self.tree_view.viewport().mapToGlobal(pos))
        
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
            
        self.context_menu_active = False

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
                for row in range(model.rowCount(parent_index)):
                    target_index = model.index(row, 1, parent_index)
                    current_target = model.data(target_index)
                    
                    if current_target == target:
                        # 更新状态
                        status_index = model.index(row, 2, parent_index)
                        model.setData(status_index, new_status)
                        # 更新时间
                        start_time_index = model.index(row, 3, parent_index)
                        end_time_index = model.index(row, 4, parent_index)
                        model.setData(start_time_index, start_time)
                        model.setData(end_time_index, end_time)
                        
                        # 获取当前行的所有列的item
                        items = [model.itemFromIndex(model.index(row, col, parent_index)) 
                               for col in range(model.columnCount())]
                        
                        # 清除所有列的背景色
                        for item in items:
                            if item:  # 确保item存在
                                item.setBackground(QBrush())
                                
                        # 如果有新状态，设置新的背景色
                        if new_status in self.colors:
                            color = QColor(self.colors[new_status])
                            for item in items:
                                if item:  # 确保item存在
                                    item.setBackground(QBrush(color))
                    
                    # 如果当前项有子项，递归处理
                    if model.hasChildren(target_index):
                        update_item(target_index)
            
            # 从根节点开始更新
            update_item()

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
                new_status = self.status_manager.get_target_status(target_file)
                
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
                        start_time, end_time = self.status_manager.get_start_end_time(tgt_track_file)
                        item.setText(3, start_time)
                        item.setText(4, end_time)
            iterator.__iadd__(1)  # 使用 __iadd__ 方法替代 += 操作符

    def show_context_menu_for_tree(self, pos, tree_widget, context_menu):
        """为 QTreeWidget 显示右键菜单"""
        if self.context_menu_active:
            return
            
        self.context_menu_active = True
        
        item = tree_widget.itemAt(pos)
        if not item:
            self.context_menu_active = False
            return
            
        # 显示菜单
        action = context_menu.exec_(tree_widget.viewport().mapToGlobal(pos))
        self.context_menu_active = False

    def bt_terminal(self, item):
        """Terminal - 打开终端"""
        self.Xterm()
        
    def bt_trace_up(self, item):
        """Trace Up - 向上追踪依赖"""
        if not item:
            return
        self.tar_sel = item.text(1)
        if self.tar_sel:
            self.retrace_tab('in')
            
    def bt_trace_down(self, item):
        """Trace Down - 向下追踪依赖"""
        if not item:
            return
        self.tar_sel = item.text(1)
        if self.tar_sel:
            self.retrace_tab('out')

    def copy_selected_target(self):
        """复制当前选中的target到剪贴板"""
        selected_targets = self.get_selected_targets()
        if selected_targets:
            # 将选中的targets用空格连接
            text = " ".join(selected_targets)
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

    def log_message(self, message, level="info"):
        """
        向日志区域添加消息
        level: "info"（黑色）, "warning"（深橙色）, "error"（深红色）, "success"（深绿色）
        """
        color_map = {
            "info": "#000000",     # 纯黑色
            "warning": "#B45F04",  # 深橙色
            "error": "#CC0000",    # 深红色
            "success": "#2E7D32"   # 深绿色
        }
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        color = color_map.get(level, "#000000")
        formatted_message = f'<pre style="margin:0;"><span style="color: #555555;">[{timestamp}]</span> <span style="color: {color};">{message}</span></pre>'
        
        self.log_area.append(formatted_message)
        # 滚动到底部
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

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

