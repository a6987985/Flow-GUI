from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QLabel, QPushButton, QTreeView
from PyQt5.QtCore import Qt, QTimer, QEvent, QItemSelectionModel, QModelIndex
import time

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)  # 无边框窗口
        
        # 初始化拖动相关变量
        self.dragging = False
        self.drag_position = None
        
        # 初始化搜索相关变量
        self.search_results = []
        self.current_result = -1
        
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
        self.search_box.setPlaceholderText("Find")
        self.search_box.setMinimumWidth(200)
        
        # 搜索结果计数标签
        self.count_label = QLabel("0/0")
        self.count_label.setFixedWidth(50)
        
        # 导航按钮
        self.prev_button = QPushButton("↑")
        self.next_button = QPushButton("↓")
        self.prev_button.setFixedWidth(30)
        self.next_button.setFixedWidth(30)
        
        # 添加悬停提示
        self.prev_button.setToolTip("Previous Match")
        self.next_button.setToolTip("Next Match")
        
        # 添加关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setFixedWidth(20)
        self.close_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #666666;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #000000;
            }
            QPushButton:pressed {
                color: #999999;
            }
        """)
        self.close_button.clicked.connect(self.hide)
        
        # 添加到布局
        layout.addWidget(self.search_box)
        layout.addWidget(self.count_label)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.close_button)
        
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
        
        # 连接搜索信号
        self.search_box.returnPressed.connect(self.search_in_code)
        
    def eventFilter(self, obj, event):
        if obj == self.search_box and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.hide()
                return True
        elif obj in (self.prev_button, self.next_button):
            if event.type() == QEvent.MouseButtonPress:
                direction = -1 if obj == self.prev_button else 1
                self.handle_button_press(obj, direction)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
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
        self.navigate_search_results(direction)
            
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
            self.navigate_search_results(self.current_direction)

    def showEvent(self, event):
        # 在父窗口中央显示
        parent = self.parent()
        if parent:
            geometry = parent.geometry()
            x = geometry.x() + (geometry.width() - self.width()) // 2
            y = geometry.y() + 80  # 距离顶部80像素
            self.move(x, y)
        super().showEvent(event)

    def search_in_code(self):
        """在当前显示的代码中搜索"""
        search_text = self.search_box.text()
        if not search_text:
            return

        # 获取当前活动的标签页
        current_tab = self.parent().tabwidget.currentWidget()
        if not current_tab:
            return

        # 获取当前标签页中的树视图
        tree_view = None
        if current_tab == self.parent().tab_run:
            tree_view = self.parent().tree_view
        else:
            # 在当前标签页中查找树视图
            tree_views = current_tab.findChildren(QTreeView)
            if tree_views:
                tree_view = tree_views[0]

        if not tree_view or not tree_view.model():
            return

        # 清除之前的搜索结果
        self.search_results = []
        self.current_result = -1

        # 在树视图中搜索（包括折叠的项）
        model = tree_view.model()
        
        def search_in_model(parent=QModelIndex()):
            for row in range(model.rowCount(parent)):
                # 检查每一列
                for col in range(model.columnCount()):
                    index = model.index(row, col, parent)
                    text = str(model.data(index))
                    if search_text.lower() in text.lower():
                        self.search_results.append(index)
                
                # 递归搜索子项
                if model.hasChildren(model.index(row, 0, parent)):
                    search_in_model(model.index(row, 0, parent))
        
        # 开始搜索
        search_in_model()

        # 更新搜索结果计数
        total = len(self.search_results)
        self.count_label.setText(f"0/{total}")

        # 如果有结果，跳转到第一个
        if self.search_results:
            self.navigate_search_results(1)

    def navigate_search_results(self, direction):
        """在搜索结果中导航
        direction: 1 表示下一个，-1 表示上一个
        """
        if not self.search_results:
            return

        total = len(self.search_results)
        # 更新当前结果索引
        if direction > 0:
            if self.current_result < 0:  # 第一次搜索
                self.current_result = 0
            else:
                self.current_result = (self.current_result + 1) % total
        else:
            if self.current_result < 0:  # 第一次搜索
                self.current_result = total - 1
            else:
                self.current_result = (self.current_result - 1) % total

        # 获取当前活动的标签页中的树视图
        current_tab = self.parent().tabwidget.currentWidget()
        tree_view = None
        if current_tab == self.parent().tab_run:
            tree_view = self.parent().tree_view
        else:
            # 在当前标签页中查找树视图
            tree_views = current_tab.findChildren(QTreeView)
            if tree_views:
                tree_view = tree_views[0]

        if not tree_view:
            return

        # 更新计数显示
        self.count_label.setText(f"{self.current_result + 1}/{total}")

        # 跳转到当前结果
        current_index = self.search_results[self.current_result]
        
        # 展开所有父节点
        parent = current_index.parent()
        while parent.isValid():
            tree_view.expand(parent)
            parent = parent.parent()
            
        # 设置当前项并滚动到视图中
        tree_view.setCurrentIndex(current_index)
        tree_view.scrollTo(current_index)
        
        # 高亮显示当前结果
        tree_view.setFocus()
        selection_model = tree_view.selectionModel()
        if selection_model:
            selection_model.clear()  # 清除之前的选择
            selection_model.select(current_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def mousePressEvent(self, event):
        """处理鼠标按下事件，开始拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，更新窗口位置"""
        if event.buttons() & Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，结束拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()