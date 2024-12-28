import os, sys, re, threading, time
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QStyleFactory, QMenu, QAction, QFileDialog, QMessageBox, QScrollBar, QTreeWidgetItemIterator,
                             QHeaderView, QStyle)
from PyQt5.QtCore import (Qt, QTimer, QRegExp)
from PyQt5.QtGui import (QFont, QBrush, QColor, QClipboard, QIcon, QRegExpValidator, QFontMetrics)

class ComboFrame(QWidget):
    '''A simple Combobox widget, contains all runs name.'''
    def __init__(self, parent, Menu):
        super().__init__(parent)
        self.Menu = Menu
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        font = QFont("Segoe UI", 10)
        self.get_combo_value()

        # 计算合适宽度
        fm = QFontMetrics(font)
        max_len = 0
        for i in self.new_list:
            w = fm.width(i)
            if w > max_len:
                max_len = w
        combo_width = max_len // 4 if max_len > 0 else 10

        self.combobox = QComboBox()
        self.combobox.addItems(self.new_list)
        self.combobox.setEditable(False)
        # 宽度可根据需要适当调整
        self.combobox.setMinimumWidth(combo_width*7)
        layout.addWidget(self.combobox)

    def get_combo_value(self):
        self.pwd = os.getcwd()
        self.cur_dir = os.path.dirname(self.pwd)
        self.all_file = os.listdir(self.cur_dir)
        self.sorted_entries = sorted(self.all_file)
        self.all_runs = [os.path.basename(self.pwd)]
        self.peer_dir = []
        self.run_len = []
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
        xmeta_project = os.getenv('XMETA_PROJECT_NAME', 'XMetaProject')
        family = os.getenv('FAMILY', 'Family')
        xmeta_background = os.getenv('XMETA_BACKGROUND', '#ffffff')
        version = os.getenv('XMETA_VERSION', 'Version')

        title_name = "Console of XMeta/%s-%s @ %s" %(version, family, xmeta_project)
        self.setWindowTitle(title_name)

        # 设置主题相关内容
        self.is_dark_mode = False
        self.setup_themes()
        
        # 创建菜单栏
        self.create_menu()
        
        # 主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # MenuFrame
        self.MenuFrame = QWidget()
        menu_layout = QHBoxLayout(self.MenuFrame)
        menu_layout.setContentsMargins(0,0,0,0)
        menu_layout.setSpacing(5)

        # 左边部分 - ComboFrame
        self.gen_combo = ComboFrame(main_widget, self.MenuFrame)
        menu_layout.addWidget(self.gen_combo)

        # 中间部分 - Filter
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0,0,0,0)
        self.En_search = QLineEdit()
        lb_filter = QLabel("Filter:")
        filter_layout.addWidget(lb_filter)
        filter_layout.addWidget(self.En_search)
        menu_layout.addWidget(filter_widget)

        # 右边部分 - 按钮组
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.setSpacing(5)

        # 添加所有按钮到同一行，移除图标
        bt_runall = QPushButton("run all")
        bt_run = QPushButton("run")
        bt_stop = QPushButton("stop")
        bt_skip = QPushButton("skip")
        bt_unskip = QPushButton("unskip")
        bt_invalid = QPushButton("invalid")
        
        button_layout.addWidget(bt_runall)
        button_layout.addWidget(bt_run)
        button_layout.addWidget(bt_stop)
        button_layout.addWidget(bt_skip)
        button_layout.addWidget(bt_unskip)
        button_layout.addWidget(bt_invalid)

        # 将按钮组添加到主菜单布局
        menu_layout.addWidget(button_widget)

        # 设置伸缩因子，使三个部分合理分布
        menu_layout.setStretch(0, 1)  # ComboFrame
        menu_layout.setStretch(1, 1)  # Filter
        menu_layout.setStretch(2, 2)  # Buttons

        # 将MenuFrame添加到主布局
        main_layout.addWidget(self.MenuFrame)

        # 添加TabWidget
        self.tabwidget = QTabWidget()
        self.tabwidget.setTabsClosable(True)
        self.tabwidget.setMovable(True)
        self.tabwidget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tabwidget)

        # 初始化run_dir
        self.combo_sel_dir = os.path.join(self.gen_combo.cur_dir, self.gen_combo.combobox.currentText())

        # 主Tab
        self.tab_run = QWidget()
        tab_run_layout = QVBoxLayout(self.tab_run)
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
        header.setStretchLastSection(True)  # 让最后一列填充剩余空间
        
        # 设置各列的调整模式
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # level列固定宽度
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # target列可手动调整
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # status列固定宽度
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # start time列固定宽度
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # end time列自动填充剩余空间
        
        tab_run_layout.addWidget(self.tree)

        # 信号槽
        self.gen_combo.combobox.currentIndexChanged.connect(self.click_event)
        self.En_search.returnPressed.connect(self.get_entry)

        bt_invalid.clicked.connect(lambda: self.start('XMeta_invalid'))
        bt_unskip.clicked.connect(lambda: self.start('XMeta_unskip'))
        bt_skip.clicked.connect(lambda: self.start('XMeta_skip'))
        bt_stop.clicked.connect(lambda: self.start('XMeta_stop'))
        bt_run.clicked.connect(lambda: self.start('XMeta_run'))
        bt_runall.clicked.connect(lambda: self.start('XMeta_run all'))

        # 定时器替代 after
        self.timer = QTimer()
        self.timer.timeout.connect(self.change_run)
        self.timer.start(1000)

        self.tg = []
        self.tar_name = []
        self.countX = 0

        self.init_run_view(self.combo_sel_dir)

        # 窗口大小与位置初始化
        self.resize(1200,800)
        self.center()

        self.create_context_menu()
        self.setup_theme_button()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_run_view(self, run_dir):
        self.get_tree(run_dir)

    def click_event(self):
        """当 combobox 选择改变时触发"""
        cur_text = self.gen_combo.combobox.currentText()
        
        # 更新当前选中的 run 目录
        self.combo_sel = os.path.join(self.gen_combo.cur_dir, cur_text)
        
        # 更新 tab 标签
        idx = self.tabwidget.indexOf(self.tab_run)
        if idx >= 0:
            self.tabwidget.setTabText(idx, cur_text)
            self.tabwidget.setCurrentIndex(idx)
        
        # 清空并重新加载树
        self.tree.clear()
        self.get_tree(self.combo_sel)  # 重新加载新 run 的数据

    def change_run(self):
        """定时刷新树状态"""
        try:
            # 保存当前选中的项
            current_item = self.tree.currentItem()
            current_target = current_item.text(1) if current_item else None
            
            # 如果之前有选中的项，尝试重新选中
            if current_target:
                items = self.tree.findItems(current_target, Qt.MatchExactly | Qt.MatchRecursive, 1)
                if items:
                    self.tree.setCurrentItem(items[0])
                
            # 刷新树显示
            self.tree.update()
            
        except Exception as e:
            pass  # 移除错误打印，使用静默处理

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

    def bt_csh(self, item):
        """Shell - 打开 make_targets 目录下的 .csh 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        shell_file = os.path.join(current_run, 'make_targets', f"{current_target}.csh")
        
        if os.path.exists(shell_file):
            try:
                subprocess.run(['gvim', shell_file], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_log(self, item):
        """Log - 打开 logs 目录下的 .log 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        log_file = os.path.join(current_run, 'logs', f"{current_target}.log")
        log_file_gz = f"{log_file}.gz"
        
        if os.path.exists(log_file):
            try:
                subprocess.run(['gvim', log_file], check=True)
            except subprocess.CalledProcessError:
                pass
        elif os.path.exists(log_file_gz):
            try:
                subprocess.run(['gvim', log_file_gz], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_cmd(self, item):
        """Command - 打开 cmds 目录下的 .cmd 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        cmd_file = os.path.join(current_run, 'cmds', f"{current_target}.cmd")
        
        if os.path.exists(cmd_file):
            try:
                subprocess.run(['gvim', cmd_file], check=True)
            except subprocess.CalledProcessError:
                pass

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

                # 计算target名称宽度
                target_width = fm.width(target)
                max_target_width = max(max_target_width, target_width)

                # 获取status等信息
                target_file = os.path.join(run_dir, 'status', target)
                tgt_track_file = os.path.join(run_dir, 'logs/targettracker', target)

                start_time, end_time = self.get_start_end_time(tgt_track_file)
                target_status = self.get_target_status(target_file)

                str_lv = ''.join(target_level)
                o.append(str_lv)
                d = [target_level, target, target_status, start_time, end_time]
                l.append(d)

        # 设置列宽
        self.tree.setColumnWidth(0, 80)  # level列
        
        # target列动态宽度但有最大限制
        max_allowed_width = 600
        target_column_width = min(max_target_width + 20, max_allowed_width)
        self.tree.setColumnWidth(1, target_column_width)
        
        # 其他列固定宽度
        self.tree.setColumnWidth(2, 100)  # status列
        self.tree.setColumnWidth(3, 150)  # start time列
        # end time列需要设置宽度，因为已经设置为自动填充

        # 构建树结构
        all_lv = list(set(o))
        all_lv.sort(key=o.index)

        # 初始化
        init_closed_tag = list(set([i for i in o if o.count(i) >= 5]))

        # 根据level分组
        level_dict = {}
        for i in all_lv:
            open_status = True
            parent_item = QTreeWidgetItem(self.tree, [i])
            level_dict[i] = parent_item

        for data in l:
            lvl, tgt, st, ct, et = data
            str_data = ''.join(lvl)
            parent_item = level_dict[str_data]
            child_item = QTreeWidgetItem(parent_item, ["", tgt, st, ct, et])
            self.set_item_color(child_item, st)

        self.tree.expandAll()

        # 恢复状态
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
                # 恢复父节点的选中状态
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

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = QMenu(self)
        
        # 添加菜单项
        action_terminal = self.context_menu.addAction("Terminal")
        action_csh = self.context_menu.addAction("Shell")
        action_log = self.context_menu.addAction("Log")
        action_cmd = self.context_menu.addAction("Command")
        action_trace_up = self.context_menu.addAction("Trace Up")
        action_trace_down = self.context_menu.addAction("Trace Down")
        
        # 连接信号到对应的槽函数
        action_terminal.triggered.connect(lambda: self.bt_terminal(self.tree.currentItem()))
        action_csh.triggered.connect(lambda: self.bt_csh(self.tree.currentItem()))
        action_log.triggered.connect(lambda: self.bt_log(self.tree.currentItem()))
        action_cmd.triggered.connect(lambda: self.bt_cmd(self.tree.currentItem()))
        action_trace_up.triggered.connect(lambda: self.bt_trace_up(self.tree.currentItem()))
        action_trace_down.triggered.connect(lambda: self.bt_trace_down(self.tree.currentItem()))
        
        # 设置树形视图上下文菜单策略
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.tree.itemAt(position)
        if item:
            # 确保只在叶子节点上显示完整菜单
            if item.childCount() == 0:  # 叶子节点
                self.context_menu.exec_(self.tree.viewport().mapToGlobal(position))

    def setup_theme_button(self):
        """设置主题切换按钮"""
        self.theme_button = QPushButton(self)
        self.theme_button.setFixedSize(24, 24)
        self.theme_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
        """)
        self.update_theme_icon()
        self.theme_button.clicked.connect(self.toggle_theme)

    def update_theme_icon(self):
        """更新主题图标"""
        icon_path = ":/dark_mode.png" if self.is_dark_mode else ":/light_mode.png"
        self.theme_button.setIcon(QIcon(icon_path))

    def toggle_theme(self):
        """切换主题"""
        self.is_dark_mode = not self.is_dark_mode
        self.change_theme("dark" if self.is_dark_mode else "light")
        self.update_theme_icon()

    def change_theme(self, theme_name):
        """切换主题样式"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.colors = self.themes[theme_name]['status_colors']
            self.apply_theme()

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        app = QApplication.instance()
        
        # 用样式表
        app.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            QPushButton {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QLineEdit {{
                background-color: {theme['input']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 3px;
                border-radius: 3px;
            }}
            QTreeWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
            }}
            QHeaderView::section {{
                background-color: {theme['header']};
                color: {theme['text']};
                padding: 5px;
                border: none;
            }}
            QMenu {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
            }}
            QMenu::item:selected {{
                background-color: {theme['button_hover']};
            }}
        """)
        
        # 刷新树形视图
        self.tree.update()

    def customize_theme(self):
        # 创建自定义主题对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("自定义主题")
        layout = QVBoxLayout(dialog)
        
        # 添加颜色选择器
        color_grid = QGridLayout()
        colors = self.themes[self.current_theme]['status_colors']
        row = 0
        for status, color in colors.items():
            label = QLabel(status)
            button = QPushButton()
            button.setStyleSheet(f"background-color: {color}")
            button.clicked.connect(lambda checked, s=status, b=button: self.pick_color(s, b))
            color_grid.addWidget(label, row, 0)
            color_grid.addWidget(button, row, 1)
            row += 1
        
        layout.addLayout(color_grid)
        
        # 添加确定和取消按钮
        buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        dialog.exec_()

    def pick_color(self, status, button):
        color = QColorDialog.getColor()
        if color.isValid():
            self.themes[self.current_theme]['status_colors'][status] = color.name()
            button.setStyleSheet(f"background-color: {color.name()}")
            self.colors = self.themes[self.current_theme]['status_colors']
            self.tree.update()

    def bt_trace_up(self, item):
        """Trace Up - 显示当前target的上游依赖"""
        if item and item.text(1):
            target = item.text(1)
            print(f"[Trace Up] Checking dependencies for target: {target}")
            try:
                cmd = f'cd {self.combo_sel} && make -n {target} | grep "^make"'
                print(f"[Trace Up] Executing command: {cmd}")
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'{cmd}; exec bash'])
            except Exception as e:
                print(f"[Trace Up] Error: {e}")

    def bt_trace_down(self, item):
        """Trace Down - 显示依赖于当前target的下游项目"""
        if item and item.text(1):
            target = item.text(1)
            print(f"[Trace Down] Checking reverse dependencies for target: {target}")
            try:
                cmd = f'cd {self.combo_sel}/make_targets && grep -l "{target}" *.csh'
                print(f"[Trace Down] Executing command: {cmd}")
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'{cmd}; exec bash'])
            except Exception as e:
                print(f"[Trace Down] Error: {e}")

    def bt_terminal(self, item):
        """Terminal - 执行 XMeta_term 命令"""
        try:
            os.chdir(self.combo_sel)
            os.system('XMeta_term')
        except Exception as e:
            pass

    def bt_csh(self, item):
        """Shell - 打开 make_targets 目录下的 .csh 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        shell_file = os.path.join(current_run, 'make_targets', f"{current_target}.csh")
        
        if os.path.exists(shell_file):
            try:
                subprocess.run(['gvim', shell_file], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_log(self, item):
        """Log - 打开 logs 目录下的 .log 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        log_file = os.path.join(current_run, 'logs', f"{current_target}.log")
        log_file_gz = f"{log_file}.gz"
        
        if os.path.exists(log_file):
            try:
                subprocess.run(['gvim', log_file], check=True)
            except subprocess.CalledProcessError:
                pass
        elif os.path.exists(log_file_gz):
            try:
                subprocess.run(['gvim', log_file_gz], check=True)
            except subprocess.CalledProcessError:
                pass

    def bt_cmd(self, item):
        """Command - 打开 cmds 目录下的 .cmd 文件"""
        if not item or item.childCount() > 0:
            return
        
        target = item.text(1)
        if not target:
            return
        
        current_target = target
        current_run = self.combo_sel
        
        cmd_file = os.path.join(current_run, 'cmds', f"{current_target}.cmd")
        
        if os.path.exists(cmd_file):
            try:
                subprocess.run(['gvim', cmd_file], check=True)
            except subprocess.CalledProcessError:
                pass

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        
        # 主题子菜单
        theme_menu = settings_menu.addMenu('主题')
        
        # 添加主题选项
        dark_theme = QAction('深色主题', self)
        dark_theme.triggered.connect(lambda: self.change_theme('dark'))
        theme_menu.addAction(dark_theme)
        
        light_theme = QAction('浅色主题', self)
        light_theme.triggered.connect(lambda: self.change_theme('light'))
        theme_menu.addAction(light_theme)
        
        # 添加自定义主题选项
        customize_theme = QAction('自定义主题', self)
        customize_theme.triggered.connect(self.customize_theme)
        theme_menu.addAction(customize_theme)

    def setup_themes(self):
        """初始化主题配置"""
        self.themes = {
            "light": {
                'background': '#F0F0F0',
                'text': '#333333',
                'button': '#ffffff',
                'button_hover': '#f8f8f8',
                'header': '#f5f5f5',
                'border': '#cccccc',
                'input': '#ffffff',
                'highlight': '#e8e8e8',
                'status_colors': {
                    'finish': '#67c23a',
                    'skip': '#e6a23c',
                    'failed': '#f56c6c',
                    'scheduled': '#409eff',
                    'running': '#ffd700',
                    'pending': '#ff9900',
                    'invalid': '#909399'
                }
            }
        }
        self.current_theme = "light"
        self.colors = self.themes[self.current_theme]['status_colors']
        
        # 应用基础样式
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F0F0F0;
                font-family: "Helvetica Neue", "Helvetica", sans-serif;
                font-size: 13px;
                color: #333;
            }
            
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #ffffff, stop: 1 #f0f0f0);
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 70px;
            }
            
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #f8f8f8, stop: 1 #e8e8e8);
                border-color: #b3b3b3;
            }
            
            QPushButton:pressed {
                background-color: #dddddd;
                border-color: #999999;
            }
            
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
                selection-background-color: #bddfff;
                selection-color: #000000;
            }
            
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
                min-width: 6em;
            }
            
            QComboBox:hover {
                border-color: #b3b3b3;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QTreeWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            
            QTreeWidget::item {
                height: 25px;
            }
            
            QTreeWidget::item:selected {
                font-weight: bold;
                color: black;
            }
            
            QTreeWidget::item:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            
            QHeaderView::section {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #ffffff, stop:1 #f0f0f0);
                border: none;
                border-right: 1px solid #cccccc;
                border-bottom: 1px solid #cccccc;
                padding: 4px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 可根据需要设置样式
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    w = MonitorRuns()
    w.show()
    sys.exit(app.exec_())
