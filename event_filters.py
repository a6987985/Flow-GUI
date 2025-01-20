from PyQt5.QtCore import QObject, Qt, QModelIndex, QEvent
from PyQt5.QtWidgets import QTreeView, QTreeWidget

class TreeViewEventFilter(QObject):
    """事件过滤器，处理 TreeView 的展开/折叠"""
    def __init__(self, tree_view, parent=None):
        super().__init__(parent)
        self.tree_view = tree_view
        self.parent = parent
        self.level_expanded = {}
        self.level_items = {}

    def eventFilter(self, obj, event):
        if not self.tree_view or not obj:
            return False
            
        if obj == self.tree_view.viewport():
            if event.type() == event.MouseButtonPress:
                index = self.tree_view.indexAt(event.pos())
                if index.isValid():
                    column = self.tree_view.columnAt(event.x())
                    if column == 0:
                        model = self.tree_view.model()
                        if not model:
                            return False
                            
                        item = model.itemFromIndex(model.index(index.row(), 0))
                        if item and item.hasChildren():
                            is_expanded = self.tree_view.isExpanded(index)
                            if is_expanded:
                                self.tree_view.collapse(index)
                            else:
                                self.tree_view.expand(index)
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
            self.tree_view.setRowHidden(row, QModelIndex(), not self.level_expanded[level]) 