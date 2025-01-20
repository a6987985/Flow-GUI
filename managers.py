import os
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QHeaderView, QMenu, QAction, QTreeView, QMessageBox, 
                            QWidgetAction, QWidget)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtSvg import QSvgWidget
import subprocess
import time

class TreeManager:
    """树形视图管理类，处理树相关操作"""
    def __init__(self, parent):
        self.parent = parent
        self.tree_view = QTreeView()
        self.model = QtGui.QStandardItemModel()
        self.tree_view.setModel(self.model)
        
        # 设置列标题
        self.model.setHorizontalHeaderLabels(["level", "target", "status", "start time", "end time"])
        
        # 设置基本属性
        self.tree_view.setAlternatingRowColors(True)  # 交替行颜色
        self.tree_view.setUniformRowHeights(True)     # 统一行高
        self.tree_view.setAllColumnsShowFocus(True)   # 所有列都显示焦点
        self.tree_view.setAnimated(False)             # 禁用动画以提高性能
        
        # 设置列宽和调整模式
        self.setup_column_settings(self.tree_view)
        
        # 设置选择模式
        self.tree_view.setSelectionMode(QtWidgets.QTreeView.ExtendedSelection)
        self.tree_view.setSelectionBehavior(QtWidgets.QTreeView.SelectRows)
        
        # 设置大小策略
        self.tree_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, 
                                   QtWidgets.QSizePolicy.Expanding)
        
        # 设置滚动条策略
        self.tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 添加事件过滤器
        from event_filters import TreeViewEventFilter
        self.tree_view_event_filter = TreeViewEventFilter(self.tree_view, parent)
        self.tree_view.viewport().installEventFilter(self.tree_view_event_filter)

    @staticmethod
    def setup_column_settings(tree_view):
        """设置树形视图的列宽和调整模式
        
        Args:
            tree_view: 要设置的树形视图对象（QTreeView或QTreeWidget）
        """
        header = tree_view.header()
        header.setSectionsMovable(False)  # 禁止移动列的位置
        
        # 先将所有列设置为Fixed模式
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
        
        # 设置各列的调整模式
        header.setSectionResizeMode(0, QHeaderView.Fixed)       # level列固定宽度
        header.setSectionResizeMode(1, QHeaderView.Interactive) # target列可手动调整
        header.setSectionResizeMode(2, QHeaderView.Fixed)      # status列固定宽度
        header.setSectionResizeMode(3, QHeaderView.Fixed)      # start time列固定宽度
        header.setSectionResizeMode(4, QHeaderView.Stretch)    # end time列自动拉伸
        
        # 设置默认列宽
        tree_view.setColumnWidth(0, 50)   # level列
        tree_view.setColumnWidth(1, 400)  # target列默认宽度
        tree_view.setColumnWidth(2, 80)   # status列
        tree_view.setColumnWidth(3, 200)  # start time列
        
        # 禁用最后一列自动拉伸
        header.setStretchLastSection(False)

class StatusManager:
    """状态管理类，处理状态相关操作"""
    def __init__(self, parent):
        self.parent = parent
        
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

class MenuManager:
    """菜单管理类，处理菜单相关操作"""
    def __init__(self, parent):
        self.parent = parent
        self.context_menu = None
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.parent.menuBar()
        
        # 添加 SVG logo
        try:
            svg_path = os.path.abspath('image-2.svg')
            print(f"Loading SVG from: {svg_path}")  # 调试信息
            if os.path.exists(svg_path):
                # 创建一个容器 widget
                logo_container = QWidget()
                logo_container.setFixedWidth(28)
                
                # 创建 SVG widget
                logo_label = QSvgWidget(svg_path)
                logo_label.setFixedSize(20, 20)
                
                # 创建布局并添加 SVG widget
                layout = QtWidgets.QHBoxLayout(logo_container)
                layout.setContentsMargins(2, 1, 2, 2)  # 减小上边距为 1
                layout.setSpacing(0)
                layout.setAlignment(Qt.AlignVCenter)
                layout.addWidget(logo_label)
                
                # 直接将容器添加到菜单栏
                menubar.setCornerWidget(logo_container, Qt.TopLeftCorner)
                print("SVG logo loaded successfully")
            else:
                print(f"SVG file not found at: {svg_path}")
        except Exception as e:
            print(f"Error loading SVG: {e}")
        
        # 创建菜单项
        view_menu = menubar.addMenu('View')
        view_menu.addAction('All Runs Status', self.parent.show_all_runs_status)
        
        # 创建右键菜单
        self.create_context_menu()
        
    def create_context_menu(self):
        self.context_menu = QMenu()
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
        
        # 添加菜单项并连接动作
        terminal_action = self.context_menu.addAction("Terminal")
        csh_action = self.context_menu.addAction("csh")
        log_action = self.context_menu.addAction("Log")
        cmd_action = self.context_menu.addAction("cmd")
        self.context_menu.addSeparator()
        trace_up_action = self.context_menu.addAction("Trace Up")
        trace_down_action = self.context_menu.addAction("Trace Down")
        
        # 连接动作到处理函数
        terminal_action.triggered.connect(self.parent.Xterm)
        csh_action.triggered.connect(lambda: self.handle_csh())
        log_action.triggered.connect(lambda: self.handle_log())
        cmd_action.triggered.connect(lambda: self.handle_cmd())
        trace_up_action.triggered.connect(lambda: self.handle_trace_up())
        trace_down_action.triggered.connect(lambda: self.handle_trace_down())
        
    def handle_csh(self):
        index = self.parent.tree_view.currentIndex()
        if index.isValid():
            self.parent.bt_csh_for_model(index)
            
    def handle_log(self):
        index = self.parent.tree_view.currentIndex()
        if index.isValid():
            self.parent.bt_log_for_model(index)
            
    def handle_cmd(self):
        index = self.parent.tree_view.currentIndex()
        if index.isValid():
            self.parent.bt_cmd_for_model(index)
            
    def handle_trace_up(self):
        index = self.parent.tree_view.currentIndex()
        if index.isValid():
            self.parent.bt_trace_up_for_model(index)
            
    def handle_trace_down(self):
        index = self.parent.tree_view.currentIndex()
        if index.isValid():
            self.parent.bt_trace_down_for_model(index)

class ActionManager:
    """动作管理类，处理各种按钮动作"""
    def __init__(self, parent):
        self.parent = parent
        
    def start(self, action):
        selected_targets = self.parent.get_selected_targets()
        if not selected_targets:
            return
            
        cmd = f"cd {self.parent.combo_sel} && {action} "
        cmd += " ".join(selected_targets)
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        
        # 对于所有操作都立即更新状态
        for target in selected_targets:
            target_file = os.path.join(self.parent.combo_sel, 'status', target)
            new_status = self.parent.get_target_status(target_file)
            tgt_track_file = os.path.join(self.parent.combo_sel, 'logs/targettracker', target)
            start_time, end_time = self.parent.get_start_end_time(tgt_track_file)
            self.parent.sync_item_status(target, new_status, start_time, end_time, self.parent.tree_view, self.parent.tree_view)
        
        if action in ['XMeta_unskip', 'XMeta_skip']:
            # 保存当前展开状态
            expanded_states = {}
            for row in range(self.parent.model.rowCount()):
                item = self.parent.model.item(row, 0)
                if item and item.hasChildren():
                    level = item.text()
                    index = self.parent.model.indexFromItem(item)
                    expanded_states[level] = self.parent.tree_view.isExpanded(index)
            
            # 重新加载树
            self.parent.get_tree(self.parent.combo_sel)
            
            # 恢复展开状态
            for row in range(self.parent.model.rowCount()):
                item = self.parent.model.item(row, 0)
                if item and item.hasChildren():
                    level = item.text()
                    index = self.parent.model.indexFromItem(item)
                    if level in expanded_states:
                        self.parent.tree_view.setExpanded(index, expanded_states[level]) 