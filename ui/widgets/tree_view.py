from PyQt5.QtWidgets import QTreeView, QHeaderView, QMenu, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush
from config.settings import STATUS_COLORS
import os

class TargetTreeView(QTreeView):
    status_updated = pyqtSignal(str, str)  # target, status
    
    def __init__(self, parent=None):
        print("Initializing TargetTreeView...")
        try:
            super().__init__(parent)
            self.parent = parent
            self.search_results = []
            self.current_result = -1
            self.context_menu = None
            self.event_filter = None
            self.model = None
            self._is_running = True
            
            # 基本设置
            self.setSelectionMode(self.ExtendedSelection)
            self.setAlternatingRowColors(True)
            self.setEditTriggers(self.NoEditTriggers)
            self.setIndentation(20)
            print("Basic settings applied")
            
            # 创建模型
            self.setup_model()
            print("Model created")
            
            # 设置列头和列宽
            self.setup_header()
            print("Header setup completed")
            
            # 设置事件过滤器
            self.setup_event_filter()
            print("Event filter setup completed")
            
            # 设置右键菜单
            self.setup_context_menu()
            print("Context menu setup completed")
            
            print("TargetTreeView initialization completed.")
        except Exception as e:
            print(f"Error in TargetTreeView initialization: {e}")
            import traceback
            traceback.print_exc()
            
    def cleanup(self):
        """清理资源"""
        print("Cleaning up TargetTreeView...")
        self._is_running = False
        if self.event_filter:
            if self.viewport():
                self.viewport().removeEventFilter(self.event_filter)
            self.event_filter = None
        if self.context_menu:
            self.context_menu.deleteLater()
            self.context_menu = None
        if self.model:
            self.model.clear()
            self.model.deleteLater()
            self.model = None
        self.search_results = []
            
    def setup_model(self):
        """设置数据模型"""
        try:
            if not self._is_running:
                return
                
            self.model = QStandardItemModel(self)
            self.model.setHorizontalHeaderLabels(["level", "target", "status", "start time", "end time"])
            self.setModel(self.model)
        except Exception as e:
            print(f"Error in setup_model: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_header(self):
        """设置列头和列宽"""
        try:
            if not self._is_running:
                return
                
            header = self.header()
            if header:
                header.setSectionResizeMode(0, QHeaderView.Fixed)  # level列
                header.setSectionResizeMode(1, QHeaderView.Interactive)  # target列
                header.setSectionResizeMode(2, QHeaderView.Fixed)  # status列
                header.setSectionResizeMode(3, QHeaderView.Fixed)  # start time列
                header.setSectionResizeMode(4, QHeaderView.Fixed)  # end time列
                
                self.setColumnWidth(0, 50)   # level列
                self.setColumnWidth(1, 1000) # target列
                self.setColumnWidth(2, 80)   # status列
                self.setColumnWidth(3, 200)  # start time列
                self.setColumnWidth(4, 200)  # end time列
        except Exception as e:
            print(f"Error in setup_header: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_event_filter(self):
        """设置事件过滤器"""
        try:
            if not self._is_running:
                return
                
            self.event_filter = TreeViewEventFilter(self)
            if self.viewport():
                self.viewport().installEventFilter(self.event_filter)
                
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
        except Exception as e:
            print(f"Error in setup_event_filter: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_context_menu(self):
        """设置右键菜单"""
        try:
            if not self._is_running:
                return
                
            self.context_menu = QMenu(self)
            self.context_menu.addAction("Terminal")
            self.context_menu.addAction("csh")
            self.context_menu.addAction("Log")
            self.context_menu.addAction("cmd")
            self.context_menu.addSeparator()
            self.context_menu.addAction("Trace Up")
            self.context_menu.addAction("Trace Down")
        except Exception as e:
            print(f"Error in setup_context_menu: {e}")
            import traceback
            traceback.print_exc()
            
    def show_context_menu(self, position):
        """显示右键菜单"""
        try:
            if not self.context_menu:
                return
                
            index = self.indexAt(position)
            if not index.isValid():
                return
                
            action = self.context_menu.exec_(self.viewport().mapToGlobal(position))
            if action:
                self.handle_context_menu_action(action.text(), index)
        except Exception as e:
            print(f"Error in show_context_menu: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_context_menu_action(self, action_text, index):
        """处理右键菜单动作"""
        try:
            if not self.model:
                return
                
            target_index = self.model.index(index.row(), 1)  # target列
            target = self.model.data(target_index)
            
            if not target:
                return
                
            if not self.parent or not hasattr(self.parent, 'parent'):
                print("Parent object not properly initialized")
                return
                
            if action_text == "Terminal":
                self.parent.parent.execute_command("XMeta_term")
            elif action_text == "csh":
                self.open_file(target, "make_targets", ".csh")
            elif action_text == "Log":
                self.open_file(target, "logs", ".log")
            elif action_text == "cmd":
                self.open_file(target, "cmds", ".cmd")
            elif action_text == "Trace Up":
                self.parent.parent.trace_target(target, "up")
            elif action_text == "Trace Down":
                self.parent.parent.trace_target(target, "down")
        except Exception as e:
            print(f"Error in handle_context_menu_action: {e}")
            import traceback
            traceback.print_exc()
            
    def open_file(self, target, subdir, ext):
        """打开相关文件"""
        try:
            if not self.parent or not hasattr(self.parent, 'parent') or \
               not hasattr(self.parent.parent, 'target_model'):
                print("Parent object not properly initialized")
                return
                
            run_dir = self.parent.parent.target_model.current_dir
            if not run_dir:
                return
                
            file_path = os.path.join(run_dir, subdir, f"{target}{ext}")
            if os.path.exists(file_path):
                if ext == '.log' and os.path.exists(file_path + '.gz'):
                    file_path += '.gz'
                os.system(f"gvim {file_path}")
            else:
                QMessageBox.warning(self, "Warning", f"File not found: {file_path}")
        except Exception as e:
            print(f"Error in open_file: {e}")
            import traceback
            traceback.print_exc()
            
    def search(self, text):
        """搜索功能"""
        if not text:
            return
            
        self.search_results = []
        self.current_result = -1
        
        def search_in_model(parent=None):
            rows = self.model.rowCount(parent)
            for row in range(rows):
                for col in range(self.model.columnCount()):
                    index = self.model.index(row, col, parent)
                    if text.lower() in str(self.model.data(index)).lower():
                        self.search_results.append(index)
                if self.model.hasChildren(index):
                    search_in_model(index)
                    
        search_in_model()
        
        # 更新搜索对话框的计数
        if hasattr(self.parent.parent, 'search_dialog'):
            total = len(self.search_results)
            self.parent.parent.search_dialog.count_label.setText(f"0/{total}")
            
            if self.search_results:
                self.navigate_search(1)
                
    def navigate_search(self, direction):
        """在搜索结果中导航"""
        if not self.search_results:
            return
            
        total = len(self.search_results)
        self.current_result = (self.current_result + direction) % total
        
        # 更新计数显示
        if hasattr(self.parent.parent, 'search_dialog'):
            self.parent.parent.search_dialog.count_label.setText(
                f"{self.current_result + 1}/{total}")
        
        # 跳转到当前结果
        current_index = self.search_results[self.current_result]
        self.setCurrentIndex(current_index)
        self.scrollTo(current_index) 
        
    def update_item_status(self, item, status, start_time, end_time):
        """更新单个项目的状态"""
        if not item:
            return
            
        # 更新状态列
        status_item = self.model.item(item.row(), 2)
        if status_item and status_item.text() != status:
            status_item.setText(status)
            
            # 更新颜色
            if status in STATUS_COLORS:
                color = QColor(STATUS_COLORS[status])
                for col in range(self.model.columnCount()):
                    col_item = self.model.item(item.row(), col)
                    if col_item:
                        col_item.setBackground(QBrush(color))
            
            # 更新时间戳
            if start_time is not None:
                start_item = self.model.item(item.row(), 3)
                if start_item:
                    start_item.setText(start_time)
            if end_time is not None:
                end_item = self.model.item(item.row(), 4)
                if end_item:
                    end_item.setText(end_time)
                    
    def update_parent_status(self, parent_item):
        """更新父项目状态"""
        if not parent_item or not parent_item.hasChildren():
            return
            
        child_statuses = []
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 2)  # 状态列
            if child:
                child_statuses.append(child.text().lower())
                
        if not child_statuses:
            return
            
        # 根据子项目状态确定父项目状态
        new_status = ''
        if all(status == 'finish' for status in child_statuses):
            new_status = 'finish'
        elif any(status == 'failed' for status in child_statuses):
            new_status = 'failed'
        elif any(status == 'running' for status in child_statuses):
            new_status = 'running'
        elif any(status == 'pending' for status in child_statuses):
            new_status = 'pending'
        elif all(status == 'skip' for status in child_statuses):
            new_status = 'skip'
        else:
            new_status = 'invalid'
            
        # 更新父项目状态
        status_item = self.model.itemFromIndex(parent_item.index().sibling(
            parent_item.row(), 2))
        if status_item and status_item.text() != new_status:
            self.update_item_status(parent_item, new_status, None, None)
            
    def update_status(self):
        """更新所有项目的状态"""
        run_dir = self.parent.parent.target_model.current_dir
        if not run_dir:
            return
            
        def update_items(parent=None):
            rows = self.model.rowCount(parent)
            for row in range(rows):
                target_index = self.model.index(row, 1, parent)
                target = self.model.data(target_index)
                
                if target:
                    target_file = os.path.join(run_dir, 'status', target)
                    tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)
                    
                    info = self.parent.parent.target_model.get_target_info(target)
                    if info:
                        status_index = self.model.index(row, 2, parent)
                        current_status = self.model.data(status_index)
                        new_status = info['status']
                        
                        if new_status != current_status:
                            self.update_item_status(
                                self.model.itemFromIndex(target_index),
                                new_status,
                                info['start_time'],
                                info['end_time']
                            )
                            
                # 递归更新子项
                child_index = self.model.index(row, 0, parent)
                if self.model.hasChildren(child_index):
                    update_items(child_index)
                    # 更新父项状态
                    self.update_parent_status(self.model.itemFromIndex(child_index))
                    
        update_items()

    def load_data(self, targets_data):
        """加载目标数据"""
        print(f"Loading {len(targets_data)} targets into tree view")
        try:
            if not self._is_running or not self.model:
                print("Tree view not ready")
                return
                
            self.model.clear()
            self.model.setHorizontalHeaderLabels(["Level", "Target", "Status", "Start Time", "End Time"])
            
            for target in targets_data:
                try:
                    items = [
                        QStandardItem(str(target.get('level', ''))),
                        QStandardItem(target.get('name', '')),
                        QStandardItem(target.get('status', '')),
                        QStandardItem(target.get('start_time', '')),
                        QStandardItem(target.get('end_time', ''))
                    ]
                    
                    # 设置状态颜色
                    status = target.get('status', '')
                    if status in STATUS_COLORS:
                        color = QColor(STATUS_COLORS[status])
                        for item in items:
                            item.setBackground(QBrush(color))
                    
                    self.model.appendRow(items)
                except Exception as e:
                    print(f"Error processing target: {target}")
                    continue
                    
            print("Data loaded successfully")
        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()

    def copy_selected_targets(self):
        """复制选中的targets到剪贴板"""
        targets = self.get_selected_targets()
        if targets:
            text = '\n'.join(targets)
            clipboard = QApplication.clipboard()
            clipboard.setText(text) 