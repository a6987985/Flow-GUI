from PyQt5.QtWidgets import (QTabWidget, QWidget, QVBoxLayout, QTreeWidget, 
                           QTreeWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QBrush
from ui.widgets.tree_view import TargetTreeView
from config.settings import STATUS_COLORS
import os

class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        print("Initializing TabWidget...")
        try:
            super().__init__(parent)
            self.parent = parent
            self.main_tab = None
            self.main_layout = None
            self.tree_view = None
            self._is_running = True
            
            # 基本设置
            self.setTabsClosable(True)
            self.setMovable(True)
            self.tabCloseRequested.connect(self.close_tab)
            
            # 创建主标签页
            self.main_tab = QWidget(self)
            print("Main tab created")
            
            # 创建布局
            self.main_layout = QVBoxLayout()
            self.main_tab.setLayout(self.main_layout)
            print("Main layout created")
            
            # 添加主标签页
            self.addTab(self.main_tab, "Main")
            print("Main tab added")
            
            # 直接创建树视图
            self.create_tree_view()
            
            print("Basic TabWidget initialization completed.")
        except Exception as e:
            print(f"Error in TabWidget initialization: {e}")
            import traceback
            traceback.print_exc()
            
    def cleanup(self):
        """清理资源"""
        print("Cleaning up TabWidget...")
        self._is_running = False
        if self.tree_view:
            self.tree_view.cleanup()
            self.tree_view.deleteLater()
        if self.main_tab:
            self.main_tab.deleteLater()
        self.clear()
            
    def create_tree_view(self):
        """创建树视图"""
        print("Creating tree view...")
        try:
            if not self._is_running:
                return
                
            if not self.main_layout:
                print("Main layout not initialized")
                return
                
            # 创建树视图
            self.tree_view = TargetTreeView(self)
            print("Tree view created")
            
            # 添加到布局
            self.main_layout.addWidget(self.tree_view)
            print("Tree view added to layout")
        except Exception as e:
            print(f"Error creating tree view: {e}")
            import traceback
            traceback.print_exc()
            
    def close_tab(self, index):
        """关闭标签页，但主标签页不能关闭"""
        try:
            if not self.main_tab:
                return
                
            if self.widget(index) != self.main_tab:
                self.removeTab(index)
        except Exception as e:
            print(f"Error in close_tab: {e}")
            import traceback
            traceback.print_exc()
            
    def add_trace_tab(self, target, deps, direction):
        """添加追踪标签页"""
        try:
            if not target or not deps:
                print("Invalid target or dependencies")
                return
                
            if not self.parent or not hasattr(self.parent, 'target_model'):
                print("Parent object not properly initialized")
                return
            
            # 创建新标签页
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # 创建树视图
            tree = QTreeWidget()
            tree.setColumnCount(5)
            tree.setHeaderLabels(["level", "target", "status", "start time", "end time"])
            
            # 设置列宽
            header = tree.header()
            if header:
                header.setSectionResizeMode(0, QHeaderView.Fixed)
                header.setSectionResizeMode(1, QHeaderView.Interactive)
                header.setSectionResizeMode(2, QHeaderView.Fixed)
                header.setSectionResizeMode(3, QHeaderView.Fixed)
                header.setSectionResizeMode(4, QHeaderView.Fixed)
            
                tree.setColumnWidth(0, 50)   # level列
                tree.setColumnWidth(1, 1000) # target列
                tree.setColumnWidth(2, 80)   # status列
                tree.setColumnWidth(3, 200)  # start time列
                tree.setColumnWidth(4, 200)  # end time列
            
            # 添加数据
            for dep in deps:
                info = self.parent.target_model.get_target_info(dep)
                if info:
                    item = QTreeWidgetItem([
                        "",  # level - 可以从target_model获取
                        dep,
                        info.get('status', ''),
                        info.get('start_time', ''),
                        info.get('end_time', '')
                    ])
                    
                    # 设置颜色
                    if info.get('status') in STATUS_COLORS:
                        color = QColor(STATUS_COLORS[info['status']])
                        for col in range(5):
                            item.setBackground(col, QBrush(color))
                    
                    tree.addTopLevelItem(item)
            
            layout.addWidget(tree)
            
            # 添加标签页
            title = f"{target} ({direction})"
            self.addTab(tab, title)
            self.setCurrentWidget(tab)
        except Exception as e:
            print(f"Error in add_trace_tab: {e}")
            import traceback
            traceback.print_exc()
        
    def add_all_runs_tab(self):
        """添加所有运行状态标签页"""
        try:
            if not self.parent or not hasattr(self.parent, 'target_model'):
                print("Parent object not properly initialized")
                return
            
            # 创建新标签页
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # 创建树视图
            tree = QTreeWidget()
            tree.setColumnCount(4)
            tree.setHeaderLabels(["Run Directory", "Latest Target", "Status", "Timestamp"])
            
            # 设置列宽
            header = tree.header()
            if header:
                header.setSectionResizeMode(0, QHeaderView.Interactive)
                header.setSectionResizeMode(1, QHeaderView.Interactive)
                header.setSectionResizeMode(2, QHeaderView.Fixed)
                header.setSectionResizeMode(3, QHeaderView.Stretch)
            
            # 获取所有运行目录
            run_dirs = self.parent.target_model.run_dirs
            if not run_dirs:
                print("No run directories found")
                return
                
            for run_dir in run_dirs:
                try:
                    # 获取最新状态
                    current_dir = os.path.join(os.path.dirname(run_dir), run_dir)
                    self.parent.target_model.current_dir = current_dir
                    targets = self.parent.target_model.load_targets(current_dir)
                    
                    if targets:
                        latest_target = targets[-1]
                        info = self.parent.target_model.get_target_info(latest_target)
                        if info:
                            item = QTreeWidgetItem([
                                run_dir,
                                latest_target,
                                info.get('status', ''),
                                info.get('start_time', '')
                            ])
                            
                            # 设置颜色
                            if info.get('status') in STATUS_COLORS:
                                color = QColor(STATUS_COLORS[info['status']])
                                for col in range(4):
                                    item.setBackground(col, QBrush(color))
                            
                            tree.addTopLevelItem(item)
                except Exception as e:
                    print(f"Error processing run directory {run_dir}: {e}")
                    continue
            
            layout.addWidget(tree)
            
            # 添加标签页
            self.addTab(tab, "All Runs Status")
            self.setCurrentWidget(tab)
        except Exception as e:
            print(f"Error in add_all_runs_tab: {e}")
            import traceback
            traceback.print_exc() 