import os, sys, re, threading, time
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QStyleFactory, QMenu, QAction, QFileDialog, QMessageBox, QScrollBar, QTreeWidgetItemIterator,
                             QHeaderView)
from PyQt5.QtCore import Qt, QTimer, QRegExp
from PyQt5.QtGui import QFont, QBrush, QColor, QClipboard, QIcon, QRegExpValidator, QFontMetrics

class ComboFrame(QWidget):
    def __init__(self, parent, Menu):
        super().__init__(parent)
        self.Menu = Menu
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        font = QFont()
        font.setPointSize(10)
        self.get_combo_value()

        # 计算合适宽度
        fm = QFontMetrics(font)
        max_len = max((fm.width(i) for i in self.new_list), default=10)
        combo_width = max_len // 4 if max_len > 0 else 10

        self.combobox = QComboBox()
        self.combobox.addItems(self.new_list)
        self.combobox.setEditable(False)
        self.combobox.setMinimumWidth(combo_width*7)
        layout.addWidget(self.combobox)

    def get_combo_value(self):
        self.pwd = os.getcwd()
        self.cur_dir = os.path.dirname(self.pwd)
        self.sorted_entries = sorted(os.listdir(self.cur_dir))
        self.all_runs = [os.path.basename(self.pwd)]
        self.peer_dir = []
        
        for file in self.sorted_entries:
            peer_dir = os.path.join(self.cur_dir, file)
            if os.path.isdir(peer_dir) and (not os.path.islink(peer_dir)) and os.path.exists(os.path.join(peer_dir, '.target_dependency.csh')):
                self.peer_dir.append(peer_dir)
                self.all_runs.append(file)

        self.new_list = list(set(self.all_runs))
        self.new_list.sort(key=self.all_runs.index)
        return self.new_list

class MonitorRuns(QMainWindow):
    def __init__(self):
        super().__init__()

        # 环境变量获取
        self.colors = {
            'finish':'lightgreen',
            'skip':'peachpuff', 
            'failed':'red',
            'scheduled':'deepskyblue',
            'running':'yellow',
            'pending':'orange',
            'invalid':'skyblue'
        }

        title_name = "Console of XMeta/%s-%s @ %s" %(
            os.getenv('XMETA_VERSION', 'Version'),
            os.getenv('FAMILY', 'Family'),
            os.getenv('XMETA_PROJECT_NAME', 'XMetaProject')
        )
        self.setWindowTitle(title_name)

        # 主部件设置
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # MenuFrame
        self.MenuFrame = QWidget()
        menu_layout = QHBoxLayout(self.MenuFrame)
        menu_layout.setContentsMargins(0,0,0,0)
        menu_layout.setSpacing(5)

        # ComboFrame
        self.gen_combo = ComboFrame(main_widget, self.MenuFrame)
        menu_layout.addWidget(self.gen_combo)

        # Filter
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0,0,0,0)
        self.En_search = QLineEdit()
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.En_search)
        menu_layout.addWidget(filter_widget)

        # Buttons
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.setSpacing(5)

        # Button rows
        buttons = [
            [("run all", lambda: self.start('XMeta_run all')),
             ("run", lambda: self.start('XMeta_run')),
             ("stop", lambda: self.start('XMeta_stop')),
             ("skip", lambda: self.start('XMeta_skip')),
             ("unskip", lambda: self.start('XMeta_unskip')),
             ("invalid", lambda: self.start('XMeta_invalid'))],
            [("term", self.Xterm),
             ("csh", self.bt_csh),
             ("log", self.bt_log),
             ("cmd", self.bt_cmd),
             ("trace up", lambda: self.retrace_tab('in')),
             ("trace dn", lambda: self.retrace_tab('out'))]
        ]

        for row in buttons:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0,0,0,0)
            row_layout.setSpacing(5)
            for text, handler in row:
                btn = QPushButton(text)
                btn.clicked.connect(handler)
                row_layout.addWidget(btn)
            button_layout.addWidget(row_widget)

        menu_layout.addWidget(button_widget)
        menu_layout.setStretch(0, 1)
        menu_layout.setStretch(1, 1)
        menu_layout.setStretch(2, 2)
        main_layout.addWidget(self.MenuFrame)

        # TabWidget
        self.tabwidget = QTabWidget()
        self.tabwidget.setTabsClosable(True)
        self.tabwidget.setMovable(True)
        self.tabwidget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tabwidget)

        # 主Tab
        self.tab_run = QWidget()
        self.tabwidget.addTab(self.tab_run, self.gen_combo.combobox.currentText())

        # Treeview
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["level", "target", "status", "start time", "end time"])
        self.tree.setRootIsDecorated(True)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.itemDoubleClicked.connect(self.copy_tar)
        
        # 设置列宽和调整模式
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        QVBoxLayout(self.tab_run).addWidget(self.tree)

        # 信号槽连接
        self.gen_combo.combobox.currentIndexChanged.connect(self.click_event)
        self.En_search.returnPressed.connect(self.get_entry)

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.change_run)
        self.timer.start(1000)

        self.tg = []
        self.tar_name = []
        self.countX = 0

        # 初始化
        self.combo_sel_dir = os.path.join(self.gen_combo.cur_dir, self.gen_combo.combobox.currentText())
        self.init_run_view(self.combo_sel_dir)
        
        # 窗口设置
        self.resize(1200,800)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_run_view(self, run_dir):
        self.get_tree(run_dir)

    def click_event(self):
        cur_text = self.gen_combo.combobox.currentText()
        idx = self.tabwidget.indexOf(self.tab_run)
        if idx >= 0:
            self.tabwidget.setTabText(idx, cur_text)
            self.tabwidget.setCurrentIndex(idx)
        self.tree.clear()
        self.change_run()

    def change_run(self):
        try:
            self.update_tree_items()
        except:
            pass

    def get_entry(self):
        self.filter_tab()

    def copy_tar(self):
        # 将选中target拷贝到剪贴板
        tar_selected = self.copy_item()
        cb = QApplication.clipboard()
        cb.clear()
        cb.setText(" ".join(tar_selected))

    def close_tab(self, index):
        if index == self.tabwidget.indexOf(self.tab_run):
            # 主tab不关闭，只关闭filter或retrace产生的
            if self.tabwidget.count() > 1:
                self.tabwidget.removeTab(index)
        else:
            self.tabwidget.removeTab(index)

    def start(self, status):
        # 与原逻辑一致
        if status == 'XMeta_run all':
            self.bt_notar(status)
        else:
            self.bt_event(status)

    def Xterm(self):
        os.chdir(self.combo_sel)
        os.system('XMeta_term')

    def bt_event(self, status):
        selected = self.tree.selectedItems()
        os.chdir(self.combo_sel)
        select_run_targets = " ".join([itm.text(1) for itm in selected if itm.text(1) != ""])
        if select_run_targets.strip():
            os.system('%s %s' %(status, select_run_targets))
        self.tree.clearSelection()

    def bt_notar(self, status):
        os.chdir(self.combo_sel)
        os.system('%s' %status)

    def bt_csh(self):
        selected = self.tree.selectedItems()
        if not selected:
            return
        tar_sel = selected[0].text(1)
        with open(os.path.join(self.combo_sel, 'user.params'), 'r') as f:
            a_file = f.read()
            family_name = re.search(r'FAMILY\s*\=(\s.*)', a_file).group(1).strip()
        tar_csh = os.path.join(os.path.dirname(os.path.dirname(self.combo_sel)),
                               'XMeta/%s/actions/%s.csh' %(family_name, tar_sel))
        if os.path.exists(tar_csh):
            os.system('gvim %s' %tar_csh)
        self.tree.clearSelection()

    def bt_log(self):
        selected = self.tree.selectedItems()
        for tar in selected:
            tar_sel = tar.text(1)
            if os.path.exists(self.combo_sel + '/logs/%s.log.gz' %tar_sel):
                os.system('gvim %s/logs/%s.log.gz' %(self.combo_sel, tar_sel))
            elif os.path.exists(self.combo_sel + '/logs/%s.log' %tar_sel):
                os.system('gvim %s/logs/%s.log' %(self.combo_sel, tar_sel))
            else:
                print("Error: cannot find log files")
        self.tree.clearSelection()

    def bt_cmd(self):
        selected = self.tree.selectedItems()
        for tar in selected:
            tar_sel = tar.text(1)
            if os.path.exists(self.combo_sel + '/cmds/%s.cmd' %tar_sel):
                os.system('gvim %s/cmds/%s.cmd' %(self.combo_sel, tar_sel))
            else:
                os.system('gvim %s/cmds/%s.tcl' %(self.combo_sel, tar_sel))
        self.tree.clearSelection()

    def get_filter_target(self):
        pattern = self.En_search.text()
        # 原逻辑中使用正则从tar_name中筛选
        add_wildcard = '*' + pattern + '*'
        wildcard_replace = add_wildcard.replace('*', '.*')
        input_pattern = re.compile(wildcard_replace + '$')
        self.matched_list = [e for e in self.tar_name if input_pattern.match(e)]

    def filter_tab(self):
        if not self.En_search.text().strip():
            return
        tab_filter = QWidget()
        tab_filter_layout = QVBoxLayout(tab_filter)
        filter_tree = QTreeWidget()
        filter_tree.setColumnCount(3)
        filter_tree.setHeaderLabels(["level", "target", "status"])
        filter_tree.setRootIsDecorated(True)
        filter_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        tab_filter_layout.addWidget(filter_tree)

        self.get_filter_target()
        # 生成filter_tree数据
        l = []
        o = []
        with open(os.path.join(self.combo_sel, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            for target in self.matched_list:
                level_name = 'TARGET_LEVEL_%s' %target
                match_lv = re.search(r'set\s*(%s)\s*\=(\s.*)' %level_name, a_file)
                if not match_lv:
                    continue
                target_name = match_lv.group(2).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    target_level = re.sub(r"^['\"]|['\"]$", '', target_name).split()

                target_file = os.path.join(self.combo_sel, 'status', target)
                target_status = self.get_target_status(target_file)
                
                str_lv = ''.join(target_level)
                o.append(str_lv)
                d = [target_level, target, target_status]
                l.append(d)

        all_lv = list(set(o))
        all_lv.sort(key=o.index)

        for i in all_lv:
            open_status = True
            parent_item = QTreeWidgetItem(filter_tree, [i])
            for data in l:
                str_data = ''.join(data[0])
                if str_data == i:
                    copy_data = data[1:]
                    child_item = QTreeWidgetItem(parent_item, ["", copy_data[0], copy_data[1]])
                    self.set_item_color(child_item, copy_data[1])

        idx = self.tabwidget.addTab(tab_filter, self.En_search.text())
        self.tabwidget.setCurrentIndex(idx)

    def retrace_tab(self, inout):
        selected = self.tree.selectedItems()
        if not selected:
            return
        self.tar_sel = selected[0].text(1)
        self.get_retrace_target(inout)
        if self.retrace_tar_name:
            tab_trace = QWidget()
            trace_layout = QVBoxLayout(tab_trace)
            retrace_tree = QTreeWidget()
            retrace_tree.setColumnCount(3)
            retrace_tree.setHeaderLabels(["level", "target", "status"])
            retrace_tree.setRootIsDecorated(True)
            retrace_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
            trace_layout.addWidget(retrace_tree)

            # 生成retrace_tree数据
            l = []
            o = []
            run_dir = self.combo_sel
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
                    target_file = os.path.join(run_dir, 'status', target)
                    target_status = self.get_target_status(target_file)
                    str_lv = ''.join(target_level)
                    o.append(str_lv)
                    d = [target_level, target, target_status]
                    l.append(d)

            all_lv = list(set(o))
            all_lv.sort(key=o.index)
            for i in all_lv:
                open_status = True
                parent_item = QTreeWidgetItem(retrace_tree, [i])
                for data in l:
                    str_data = ''.join(data[0])
                    if str_data == i:
                        copy_data = data[1:]
                        child_item = QTreeWidgetItem(parent_item, ["", copy_data[0], copy_data[1]])
                        self.set_item_color(child_item, copy_data[1])

            idx = self.tabwidget.addTab(tab_trace, self.tar_sel)
            self.tabwidget.setCurrentIndex(idx)
            self.tree.clearSelection()

    def get_retrace_target(self, inout):
        self.retrace_tar_name = []
        with open(os.path.join(self.combo_sel, '.target_dependency.csh'), 'r') as f:
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

    def get_target(self):
        with open(os.path.join(self.combo_sel, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            m = re.search(r'set\s*ACTIVE_TARGETS\s*\=(\s.*)', a_file)
            if m:
                target_name = m.group(1).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    self.tar_name = re.sub(r"^['\"]|['\"]$", "", target_name).split()
                    return self.tar_name
        self.tar_name = []
        return self.tar_name

    def copy_item(self):
        selected = self.tree.selectedItems()
        n = [itm.text(1) for itm in selected if itm.text(1) != ""]
        return n

    def get_tree(self, run_dir):
        # 如果数据没有变化，避免重复处理
        current_mtime = os.path.getmtime(os.path.join(run_dir, '.target_dependency.csh'))
        if hasattr(self, 'last_mtime') and current_mtime == self.last_mtime:
            return
        self.last_mtime = current_mtime
        
        # 保存当前状态
        tree_state = self.save_tree_state()
        
        self.combo_sel = run_dir
        self.tree.clear()
        self.get_target()

        # 清理
        self.countX = 0
        l = []
        o = []
        
        # 用于计算最大target名称宽度
        fm = QFontMetrics(self.tree.font())
        max_target_width = 0
        
        with open(os.path.join(run_dir, '.target_dependency.csh'), 'r') as f:
            a_file = f.read()
            for target in self.tar_name:
                level_name = 'TARGET_LEVEL_%s' %target
                match_lv = re.search(r'set\s*(%s)\s*\=(\s.*)' %level_name, a_file)
                if not match_lv:
                    continue
                target_name = match_lv.group(2).strip()
                if re.match(r"^(['\"]).*\"$", target_name):
                    target_level = re.sub(r"^['\"]|['\"]$", '', target_name).split()

                target_width = fm.width(target)
                max_target_width = max(max_target_width, target_width)

                target_file = os.path.join(run_dir, 'status', target)
                tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)

                start_time, end_time = self.get_start_end_time(tgt_track_file)
                target_status = self.get_target_status(target_file)

                str_lv = ''.join(target_level)
                o.append(str_lv)
                d = [target_level, target, target_status, start_time, end_time]
                l.append(d)

        # 设置列宽
        self.tree.setColumnWidth(0, 80)
        max_allowed_width = 600
        target_column_width = min(max_target_width + 20, max_allowed_width)
        self.tree.setColumnWidth(1, target_column_width)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 150)

        # 构建树结构
        all_lv = list(set(o))
        all_lv.sort(key=o.index)

        # 统计每个level的子节点数量
        level_counts = {}
        for level in o:
            level_counts[level] = level_counts.get(level, 0) + 1

        # 根据level分组
        level_dict = {}
        for i in all_lv:
            parent_item = QTreeWidgetItem(self.tree, [i])
            level_dict[i] = parent_item
            # 如果子节点数小于等于5，默认展开；大于5则折叠
            parent_item.setExpanded(level_counts[i] <= 5)

        for data in l:
            lvl, tgt, st, ct, et = data
            str_data = ''.join(lvl)
            parent_item = level_dict[str_data]
            child_item = QTreeWidgetItem(parent_item, ["", tgt, st, ct, et])
            self.set_item_color(child_item, st)

        # 恢复用户的展开/折叠状态
        self.restore_tree_state(tree_state)

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

    def save_tree_state(self):
        state = {
            'expanded': {},
            'selected': [],
            'selected_parents': [],
            'scroll': self.tree.verticalScrollBar().value()
        }
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.parent():
                parent_text = item.parent().text(0)
                state['expanded'][parent_text] = item.parent().isExpanded()
                if item.isSelected():
                    state['selected'].append((parent_text, item.text(1)))
            else:
                if item.isSelected():
                    state['selected_parents'].append(item.text(0))
            iterator += 1
        return state

    def restore_tree_state(self, state):
        # 恢复展开状态
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if not item.parent():
                level_text = item.text(0)
                if level_text in state['expanded']:
                    item.setExpanded(state['expanded'][level_text])
                # 复父节点的选中状态
                if level_text in state.get('selected_parents', []):
                    item.setSelected(True)
            iterator += 1
        
        # 恢复子节点选中状态
        if state.get('selected'):
            for parent_text, child_text in state['selected']:
                items = self.tree.findItems(child_text, Qt.MatchExactly | Qt.MatchRecursive, 1)
                for item in items:
                    if item.parent() and item.parent().text(0) == parent_text:
                        item.setSelected(True)
        
        # 恢复滚动条位置
        if 'scroll' in state:
            self.tree.verticalScrollBar().setValue(state['scroll'])

    def update_tree_items(self):
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.text(1):  # 只更新叶子节点
                target = item.text(1)
                target_file = os.path.join(self.combo_sel, 'status', target)
                new_status = self.get_target_status(target_file)
                if new_status != item.text(2):  # 只在状态变化时更新
                    item.setText(2, new_status)
                    self.set_item_color(item, new_status)
            iterator += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 可根据需要设置样式
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    w = MonitorRuns()
    w.show()
    sys.exit(app.exec_())
