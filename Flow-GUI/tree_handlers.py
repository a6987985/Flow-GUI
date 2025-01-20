import os
import re
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt

class TreeHandlers:
    """处理树形结构相关的操作"""
    
    def __init__(self, parent):
        self.parent = parent
        # 保持对父对象重要属性的引用
        self.tree_view = parent.tree_view
        self.model = parent.model
        self.colors = parent.colors
        self.level_expanded = parent.level_expanded
        self.tree_view_event_filter = parent.tree_view_event_filter
        
    def get_tree(self, run_dir):
        """获取并构建树形视图"""
        print("\n=== get_tree start ===")
        print(f"Current level_expanded dict: {self.level_expanded}")
        print(f"Current run_dir: {run_dir}")
        
        # 使用已保存的展开状态
        if run_dir in self.level_expanded:
            expanded_states = self.level_expanded[run_dir]
        else:
            expanded_states = {}
        
        # 在构建完树后恢复展开状态
        if self.tree_view and self.tree_view.model():
            for row in range(self.tree_view.model().rowCount()):
                index = self.tree_view.model().index(row, 0)
                if self.tree_view.model().hasChildren(index):
                    level = self.tree_view.model().data(index)
                    if level in expanded_states:
                        print(f"Restoring state for level {level}: {expanded_states[level]}")
                        self.tree_view.setExpanded(index, expanded_states[level])
        
        print("=== get_tree end ===\n")
        
        # 清空模型
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["level", "target", "status", "start time", "end time"])
        
        # 设置自定义代理来处理缩进
        delegate = IndentDelegate(self.tree_view)
        self.tree_view.setItemDelegate(delegate)
        
        # 获取数据
        self.parent.get_target()
        
        l = []
        o = []
        
        # 读取数据
        with open(os.path.join(run_dir, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            for target in self.parent.tar_name:
                level_name = f'TARGET_LEVEL_{target}'
                match_lv = re.search(r'set\s*(%s)\s*\=(\s.*)' % level_name, a_file)
                if not match_lv:
                    continue
                target_name = match_lv.group(2).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    target_level = re.sub(r"^['\"]|['\"]$", '', target_name).split()

                target_file = os.path.join(run_dir, 'status', target)
                tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)

                start_time, end_time = self.parent.get_start_end_time(tgt_track_file)
                target_status = self.parent.get_target_status(target_file)

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
        self.parent.tree_manager.setup_column_settings(self.tree_view)
        
        # 根据子项数量自动展开/折叠level
        self._handle_auto_expand(run_dir, level_data)

    def _handle_auto_expand(self, run_dir, level_data):
        """处理树节点的自动展开/折叠"""
        if run_dir not in self.level_expanded:  # 只在没有保存的状态时应用自动展开规则
            self.level_expanded[run_dir] = {}
            for level, items in level_data.items():
                # 获取子项数量（减去父项）
                child_count = len(items) - 1
                # 如果子项数量小于等于3，则展开
                should_expand = child_count <= 3
                
                # 保存展开状态
                self.level_expanded[run_dir][level] = should_expand
                
                # 查找并展开/折叠对应的level项
                for row in range(self.model.rowCount()):
                    item = self.model.item(row, 0)
                    if item and item.text() == level:
                        index = self.model.indexFromItem(item)
                        if should_expand:
                            self.tree_view.expand(index)
                        else:
                            self.tree_view.collapse(index)
                        break

    def save_tree_state(self):
        """保存树的状态"""
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
        """恢复树的状态"""
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

    def get_target(self):
        """获取目标列表"""
        with open(os.path.join(self.parent.combo_sel, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            m = re.search(r'set\s*ACTIVE_TARGETS\s*\=(\s.*)', a_file)
            if m:
                target_name = m.group(1).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    self.parent.tar_name = re.sub(r"^['\"]|['\"]$", "", target_name).split()
                    return self.parent.tar_name
        self.parent.tar_name = []
        return self.parent.tar_name

class IndentDelegate(QtWidgets.QStyledItemDelegate):
    """处理树形视图的缩进"""
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