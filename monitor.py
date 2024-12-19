import os, sys, re, threading, time
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QStyleFactory, QMenu, QAction, QFileDialog, QMessageBox, QScrollBar, QTreeWidgetItemIterator,
                             QHeaderView)
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

        # 设置一个合理的最小和最大宽度
        min_width = 150  # 最小宽度
        max_width = 300  # 最大宽度
        combo_width = min(max(min_width, max_len + 40), max_width)  # 添加一些padding，并限制在最小最大值之间

        self.combobox = QComboBox()
        self.combobox.addItems(self.new_list)
        self.combobox.setEditable(False)
        self.combobox.setFixedWidth(combo_width)  # 使用setFixedWidth替代setMinimumWidth
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

        # 颜色字典
        self.colors = {
            'finish':'lightgreen',
            'skip':'peachpuff',
            'failed':'red',
            'scheduled':'deepskyblue',
            'running':'yellow',
            'pending':'orange',
            'invalid':'skyblue',
            'no_status':'#87CEEB'
        }

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
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.setSpacing(5)

        # 第一行按钮
        button_row1 = QWidget()
        hb1 = QHBoxLayout(button_row1)
        hb1.setContentsMargins(0,0,0,0)
        hb1.setSpacing(5)
        bt_runall = QPushButton("run all")
        bt_run = QPushButton("run")
        bt_stop = QPushButton("stop")
        bt_skip = QPushButton("skip")
        bt_unskip = QPushButton("unskip")
        bt_invalid = QPushButton("invalid")
        hb1.addWidget(bt_runall)
        hb1.addWidget(bt_run)
        hb1.addWidget(bt_stop)
        hb1.addWidget(bt_skip)
        hb1.addWidget(bt_unskip)
        hb1.addWidget(bt_invalid)

        # 第二行按钮
        button_row2 = QWidget()
        hb2 = QHBoxLayout(button_row2)
        hb2.setContentsMargins(0,0,0,0)
        hb2.setSpacing(5)
        bt_term = QPushButton("term")
        bt_csh = QPushButton("csh")
        bt_log = QPushButton("log")
        bt_cmd = QPushButton("cmd")
        bt_trace_up = QPushButton("trace up")
        bt_trace_dn = QPushButton("trace dn")
        hb2.addWidget(bt_term)
        hb2.addWidget(bt_csh)
        hb2.addWidget(bt_log)
        hb2.addWidget(bt_cmd)
        hb2.addWidget(bt_trace_up)
        hb2.addWidget(bt_trace_dn)

        # 将两行按钮��加到按钮布局
        button_layout.addWidget(button_row1)
        button_layout.addWidget(button_row2)

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

        bt_trace_up.clicked.connect(lambda: self.retrace_tab('in'))
        bt_trace_dn.clicked.connect(lambda: self.retrace_tab('out'))
        bt_cmd.clicked.connect(self.bt_cmd)
        bt_log.clicked.connect(self.bt_log)
        bt_csh.clicked.connect(self.bt_csh)
        bt_term.clicked.connect(self.Xterm)
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

        # 添加缓存
        self.target_level_cache = {}
        self.target_status_cache = {}
        self.target_time_cache = {}
        
        self.init_run_view(self.combo_sel_dir)

        # 窗口大小与位置初始化
        self.resize(1200,800)
        self.center()

        # 添加延迟搜索
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.do_search)
        self.En_search.textChanged.connect(self.schedule_search)

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
        self.combo_sel = os.path.join(self.gen_combo.cur_dir, self.gen_combo.combobox.currentText())
        try:
            # 清理缓存并更新所有树视图
            self.clear_status_cache()
            self.get_tree(self.combo_sel)
            self.update_all_trees()
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
        if status == 'XMeta_run all':
            self.bt_notar(status)
        else:
            self.bt_event(status)

    def Xterm(self):
        os.chdir(self.combo_sel)
        os.system('XMeta_term')

    def bt_event(self, status):
        current_tree = self.get_current_tree()
        if not current_tree:
            return
            
        selected = current_tree.selectedItems()
        os.chdir(self.combo_sel)
        select_run_targets = " ".join([itm.text(1) for itm in selected if itm.text(1) != ""])
        if select_run_targets.strip():
            os.system('%s %s' %(status, select_run_targets))
            # 清理缓存并更新所有树视图
            self.clear_status_cache()
            self.update_all_trees()
        current_tree.clearSelection()

    def bt_notar(self, status):
        os.chdir(self.combo_sel)
        os.system('%s' %status)
        # 清理缓存并更新所有树视图
        self.clear_status_cache()
        self.update_all_trees()

    def bt_csh(self):
        current_tree = self.get_current_tree()
        if not current_tree:
            return
            
        selected = current_tree.selectedItems()
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
        current_tree.clearSelection()

    def bt_log(self):
        current_tree = self.get_current_tree()
        if not current_tree:
            return
            
        selected = current_tree.selectedItems()
        for tar in selected:
            tar_sel = tar.text(1)
            if os.path.exists(self.combo_sel + '/logs/%s.log.gz' %tar_sel):
                os.system('gvim %s/logs/%s.log.gz' %(self.combo_sel, tar_sel))
            elif os.path.exists(self.combo_sel + '/logs/%s.log' %tar_sel):
                os.system('gvim %s/logs/%s.log' %(self.combo_sel, tar_sel))
            else:
                print("Error: cannot find log files")
        current_tree.clearSelection()

    def bt_cmd(self):
        current_tree = self.get_current_tree()
        if not current_tree:
            return
            
        selected = current_tree.selectedItems()
        for tar in selected:
            tar_sel = tar.text(1)
            if os.path.exists(self.combo_sel + '/cmds/%s.cmd' %tar_sel):
                os.system('gvim %s/cmds/%s.cmd' %(self.combo_sel, tar_sel))
            else:
                os.system('gvim %s/cmds/%s.tcl' %(self.combo_sel, tar_sel))
        current_tree.clearSelection()

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
        current_tree = self.get_current_tree()
        if not current_tree:
            return
            
        selected = current_tree.selectedItems()
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
            current_tree.clearSelection()

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
        current_tree = self.get_current_tree()
        if not current_tree:
            return []
            
        selected = current_tree.selectedItems()
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
        # end time列不需要设置宽度，因为已经设置为自动填充

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
        """设置项目颜色，如果状态为空则设置淡蓝色背景"""
        if status in self.colors:
            color = QColor(self.colors[status])
        else:
            # 无状态时使用淡蓝色
            color = QColor(self.colors['no_status'])
            
        for col in range(item.columnCount()):
            item.setBackground(col, QBrush(color))

    def get_target_status(self, target_file):
        """获取target状态"""
        # 使用缓存
        if target_file in self.target_status_cache:
            return self.target_status_cache[target_file]
            
        status = ''
        if os.path.exists(target_file + '.skip'):
            status = 'skip'
        elif os.path.exists(target_file + '.finish'):
            status = 'finish'
        elif os.path.exists(target_file + '.failed'):
            status = 'failed'
        elif os.path.exists(target_file + '.running'):
            status = 'running'
        elif os.path.exists(target_file + '.pending'):
            status = 'pending'
        elif os.path.exists(target_file + '.scheduled'):
            status = 'scheduled'
        
        # 更新缓存
        self.target_status_cache[target_file] = status
        return status

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

    def schedule_search(self):
        # 延迟300ms执行搜索，避免频繁更新
        self.search_timer.start(300)

    def do_search(self):
        """执行搜索操作"""
        self.filter_tab()
        
    # 添加获取当前活动树形视图的方法
    def get_current_tree(self):
        """获取当前活动tab中的树形视图"""
        current_tab = self.tabwidget.currentWidget()
        if current_tab == self.tab_run:
            return self.tree
        else:
            # 在其他tab中查找QTreeWidget
            for child in current_tab.children():
                if isinstance(child, QTreeWidget):
                    return child
        return None

    def clear_status_cache(self):
        """清理状态缓存"""
        self.target_status_cache.clear()

    def update_all_trees(self):
        """更新所有tab页面中的树视图状态"""
        # 更新所有打开的树视图
        for i in range(self.tabwidget.count()):
            tab = self.tabwidget.widget(i)
            tree_widget = None
            
            if tab == self.tab_run:
                tree_widget = self.tree
            else:
                # 在其他tab中查找QTreeWidget
                for child in tab.children():
                    if isinstance(child, QTreeWidget):
                        tree_widget = child
                        break
            
            if tree_widget:
                iterator = QTreeWidgetItemIterator(tree_widget)
                while iterator.value():
                    item = iterator.value()
                    if item.text(1):  # 只更新有target名称的项
                        target_file = os.path.join(self.combo_sel, 'status', item.text(1))
                        status = self.get_target_status(target_file)
                        item.setText(2, status)
                        self.set_item_color(item, status)
                    iterator += 1

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 可根据需要设置样式
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    w = MonitorRuns()
    w.show()
    sys.exit(app.exec_())
