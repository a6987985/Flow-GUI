import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                            QHeaderView, QMenu)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt

class TraceHandlers:
    """处理依赖追踪相关的操作"""
    
    def __init__(self, parent):
        self.parent = parent
        self.retrace_tar_name = []
        self.tar_sel = None
        
    def get_retrace_target(self, inout):
        """获取需要追踪的目标"""
        self.retrace_tar_name = []
        with open(os.path.join(self.parent.combo_sel, '.target_dependency.csh'), 'r') as f:
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

    def retrace_tab(self, inout):
        """创建追踪结果的标签页"""
        # 获取当前选中的项
        indexes = self.parent.tree_view.selectedIndexes()
        if not indexes:
            return
            
        # 获取target列的数据
        target_index = self.parent.model.index(indexes[0].row(), 1)  # 1是target列
        self.tar_sel = self.parent.model.data(target_index)
        
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
            retrace_tree.itemDoubleClicked.connect(lambda item: self.parent.copy_tar(item))

            # 设置列宽和调整模式
            self.parent.tree_manager.setup_column_settings(retrace_tree)

            # 生成retrace_tree数据
            l = []
            o = []
            run_dir = self.parent.combo_sel
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
                    target_status = self.parent.status_manager.get_target_status(target_file)
                    tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                    start_time, end_time = self.parent.status_manager.get_start_end_time(tgt_track_file)

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
                if st in self.parent.colors:
                    color = QColor(self.parent.colors[st])
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
            terminal_action.triggered.connect(lambda: self.parent.bt_terminal(retrace_tree.currentItem()))
            csh_action.triggered.connect(lambda: self.parent.bt_csh(retrace_tree.currentItem()))
            log_action.triggered.connect(lambda: self.parent.bt_log(retrace_tree.currentItem()))
            cmd_action.triggered.connect(lambda: self.parent.bt_cmd(retrace_tree.currentItem()))
            trace_up_action.triggered.connect(lambda: self.parent.bt_trace_up(retrace_tree.currentItem()))
            trace_down_action.triggered.connect(lambda: self.parent.bt_trace_down(retrace_tree.currentItem()))

            # 设置右键菜单策略
            retrace_tree.setContextMenuPolicy(Qt.CustomContextMenu)
            retrace_tree.customContextMenuRequested.connect(
                lambda pos, tree=retrace_tree, menu=context_menu: self.parent.show_context_menu_for_tree(pos, tree, menu)
            )

            trace_layout.addWidget(retrace_tree)

            # 创建事件过滤器
            event_filter = self.parent.tree_view_event_filter.__class__(retrace_tree, self.parent)
            event_filter.level_items = level_items
            retrace_tree.viewport().installEventFilter(event_filter)

            # 保存事件过滤器的引用，防止被垃圾回收
            retrace_tree.event_filter = event_filter

            # 添加到标签页
            idx = self.parent.tabwidget.addTab(tab_trace, self.tar_sel)
            self.parent.tabwidget.setCurrentIndex(idx)
            self.parent.tree_view.clearSelection()

            # 将retrace_tree添加到tab_trace的属性中，以便在change_run中能够找到它
            tab_trace.retrace_tree = retrace_tree

            # 立即更新状态
            self.parent.update_tree_widget_status(retrace_tree, run_dir) 