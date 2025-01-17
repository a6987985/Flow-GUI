from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QMenuBar, 
                           QAction, QMessageBox, QShortcut, QApplication)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence

from ui.widgets.toolbar import ToolBar
from ui.widgets.tab_widget import TabWidget
from ui.widgets.search_dialog import SearchDialog
from models.target_model import TargetModel
from utils.status_utils import update_status

class MonitorRuns(QMainWindow):
    def __init__(self):
        print("Initializing MonitorRuns...")
        try:
            super().__init__()
            self.setWindowTitle("Monitor Runs")
            self.resize(1200, 800)
            
            # 初始化成员变量
            self.central_widget = None
            self.main_layout = None
            self.tab_widget = None
            self.target_model = None
            self.search_dialog = None
            self.timer = None
            self.toolbar = None
            self._is_running = True
            
            # 初始化UI
            self.init_ui()
            print("UI initialized")
            
            # 创建目标模型
            self.target_model = TargetModel()
            print("Target model created")
            
            # 等待一下确保组件都已创建
            QApplication.processEvents()
            
            # 设置信号连接
            self.setup_connections()
            
            # 设置快捷键
            self.setup_shortcuts()
            
            # 设置定时器
            self.setup_timer()
            
            # 设置信号处理
            self.setup_signal_handlers()
            
            # 注册退出处理
            import atexit
            atexit.register(self.cleanup)
            
            print("MonitorRuns initialization completed.")
        except Exception as e:
            print(f"Error in MonitorRuns initialization: {e}")
            import traceback
            traceback.print_exc()
            
    def init_ui(self):
        """初始化UI组件"""
        try:
            # 创建菜单栏
            self.create_menu()
            print("Menu bar created")
            
            # 创建中心部件
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            self.main_layout = QVBoxLayout()
            self.central_widget.setLayout(self.main_layout)
            print("Central widget created")
            
            # 创建工具栏
            self.toolbar = ToolBar(self)
            self.main_layout.addWidget(self.toolbar)
            print("Toolbar created")
            
            # 创建标签页
            self.tab_widget = TabWidget(self)
            self.main_layout.addWidget(self.tab_widget)
            print("Tab widget created")
            
            # 创建搜索对话框
            self.search_dialog = SearchDialog(self)
            print("Search dialog created")
            
            print("UI initialization completed")
        except Exception as e:
            print(f"Error in init_ui: {e}")
            import traceback
            traceback.print_exc()
            
    def create_menu(self):
        """创建菜单栏"""
        try:
            menubar = self.menuBar()
            view_menu = menubar.addMenu('View')
            
            # 添加显示所有运行状态的动作
            show_all_action = QAction('Show All Runs Status', self)
            show_all_action.triggered.connect(self.show_all_runs)
            view_menu.addAction(show_all_action)
            
            # 添加搜索动作
            search_action = QAction('Search', self)
            search_action.setShortcut('Ctrl+F')
            search_action.triggered.connect(self.toggle_search)
            view_menu.addAction(search_action)
        except Exception as e:
            print(f"Error creating menu: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_connections(self):
        """设置信号连接"""
        print("Setting up connections...")
        try:
            if not self.target_model:
                print("Target model not initialized")
                return
                
            if not self.tab_widget:
                print("Tab widget not initialized")
                return
                
            if not hasattr(self.tab_widget, 'tree_view'):
                print("Tree view not initialized")
                return
                
            print("Connecting signals...")
            # 连接数据加载信号
            self.target_model.data_loaded.connect(self.tab_widget.tree_view.load_data)
            print("Data loaded signal connected")
            
            # 连接状态更新信号
            self.target_model.status_changed.connect(self.tab_widget.tree_view.status_updated)
            print("Status changed signal connected")
            
            print("All connections established successfully")
        except Exception as e:
            print(f"Error setting up connections: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_shortcuts(self):
        """设置快捷键"""
        try:
            # 搜索快捷键
            search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
            search_shortcut.activated.connect(self.toggle_search)
            
            # 复制快捷键
            copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
            copy_shortcut.activated.connect(
                lambda: self.tab_widget.tree_view.copy_selected_targets())
            print("Shortcuts setup completed.")
        except Exception as e:
            print(f"Error setting up shortcuts: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_timer(self):
        """设置定时器"""
        try:
            if not self._is_running:
                return
                
            self.timer = QTimer(self)
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.update_status)
            self.timer.start()
            print("Timer started.")
        except Exception as e:
            print(f"Error setting up timer: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_signal_handlers(self):
        """设置信号处理"""
        try:
            # 设置应用程序退出信号处理
            app = QApplication.instance()
            if app:
                app.aboutToQuit.connect(self.cleanup)
                print("Application quit signal connected.")
                
            # 设置 SIGINT 处理（Ctrl+C）
            import signal
            signal.signal(signal.SIGINT, self.signal_handler)
            print("SIGINT handler registered.")
        except Exception as e:
            print(f"Error setting up signal handlers: {e}")
            import traceback
            traceback.print_exc()
            
    def signal_handler(self, signum, frame):
        """处理信号"""
        print(f"\nReceived signal {signum}")
        self.cleanup()
        QApplication.quit()
            
    def cleanup(self):
        """清理资源"""
        if not self._is_running:
            return
            
        print("Cleaning up MonitorRuns...")
        self._is_running = False
        
        # 停止定时器
        if self.timer:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
            
        # 清理组件
        if self.target_model:
            self.target_model.cleanup()
            self.target_model.deleteLater()
            self.target_model = None
            
        if self.tab_widget:
            self.tab_widget.cleanup()
            self.tab_widget.deleteLater()
            self.tab_widget = None
            
        if self.search_dialog:
            self.search_dialog.close()
            self.search_dialog.deleteLater()
            self.search_dialog = None
            
        if self.toolbar:
            self.toolbar.deleteLater()
            self.toolbar = None
            
        print("MonitorRuns cleanup completed.")
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            print("Handling close event...")
            self.cleanup()
            event.accept()
            QApplication.quit()
        except Exception as e:
            print(f"Error in close event: {e}")
            import traceback
            traceback.print_exc()
            event.accept()
            QApplication.quit()
            
    def update_status(self):
        """更新状态"""
        try:
            if not self._is_running:
                return
                
            if self.tab_widget and self.tab_widget.tree_view:
                self.tab_widget.tree_view.update_status()
        except Exception as e:
            print(f"Error updating status: {e}")
            
    def execute_command(self, command):
        """执行命令"""
        try:
            if not self._is_running:
                return
                
            selected_targets = self.tab_widget.tree_view.get_selected_targets()
            if selected_targets:
                self.target_model.execute_command(command, selected_targets)
            else:
                QMessageBox.warning(self, "Warning", "No targets selected!")
        except Exception as e:
            print(f"Error executing command: {e}")
            import traceback
            traceback.print_exc()
            
    def trace_target(self, target, direction):
        """追踪目标依赖"""
        try:
            if not self._is_running:
                return
                
            deps = self.target_model.get_target_dependencies(target, direction)
            if deps:
                # 创建新的标签页显示依赖关系
                self.tab_widget.add_trace_tab(target, deps, direction)
            else:
                QMessageBox.information(self, "Info", f"No {direction} dependencies found for {target}")
        except Exception as e:
            print(f"Error tracing target: {e}")
            import traceback
            traceback.print_exc()
            
    def toggle_search(self):
        """切换搜索对话框显示状态"""
        try:
            if not self._is_running or not self.search_dialog:
                return
                
            if self.search_dialog.isVisible():
                self.search_dialog.hide()
            else:
                # 显示在主窗口中央
                pos = self.geometry()
                x = pos.x() + (pos.width() - self.search_dialog.width()) // 2
                y = pos.y() + 100
                self.search_dialog.move(x, y)
                self.search_dialog.show()
                self.search_dialog.search_box.setFocus()
        except Exception as e:
            print(f"Error toggling search: {e}")
            import traceback
            traceback.print_exc()
            
    def show_all_runs(self):
        """显示所有运行状态"""
        try:
            if not self._is_running:
                return
                
            self.tab_widget.add_all_runs_tab()
        except Exception as e:
            print(f"Error showing all runs: {e}")
            import traceback
            traceback.print_exc()
            
    def __del__(self):
        """析构函数"""
        print("MonitorRuns destructor called.")
        self.cleanup() 