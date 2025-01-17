from PyQt5.QtCore import QObject, Qt, QEvent

class TreeViewEventFilter(QObject):
    def __init__(self, tree_view):
        super().__init__(tree_view)
        self.tree_view = tree_view
        self.last_pos = None
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                # 保存右键点击位置
                self.last_pos = event.pos()
            return False
            
        elif event.type() == QEvent.KeyPress:
            # 处理键盘事件
            if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
                # Ctrl+F 打开搜索对话框
                if hasattr(self.tree_view.parent.parent, 'toggle_search'):
                    self.tree_view.parent.parent.toggle_search()
                return True
                
            elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
                # Ctrl+C 复制选中的目标
                if hasattr(self.tree_view, 'get_selected_targets'):
                    targets = self.tree_view.get_selected_targets()
                    if targets:
                        clipboard = QApplication.clipboard()
                        clipboard.setText('\n'.join(targets))
                return True
                
        return super().eventFilter(obj, event)

    def toggle_level_items(self, level):
        if level not in self.level_items:
            return
            
        self.level_expanded[level] = not self.level_expanded.get(level, True)
        
        rows = self.level_items[level]
        if not rows:
            return
            
        for i, row in enumerate(rows):
            if i == 0:
                continue
            self.tree_view.setRowHidden(row, Qt.QModelIndex(), not self.level_expanded[level])


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
                    column = self.tree.columnAt(event.x())
                    if column == 0:
                        level = item.text(0)
                        if level in self.level_items:
                            self.toggle_level_items(level)
                            return True
        return super().eventFilter(obj, event)
 
    def toggle_level_items(self, level):
        if level not in self.level_items:
            return
            
        self.level_expanded[level] = not self.level_expanded.get(level, True)
        
        rows = self.level_items[level]
        if not rows:
            return
            
        for i, row in enumerate(rows):
            if i == 0:
                continue
            self.tree.setRowHidden(row, Qt.QModelIndex(), not self.level_expanded[level]) 