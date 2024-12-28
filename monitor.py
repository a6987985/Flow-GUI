import os, sys, re, threading, time
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QStyleFactory, QMenu, QAction, QFileDialog, QMessageBox, QScrollBar, QTreeWidgetItemIterator,
                             QHeaderView, QDialog, QVBoxLayout, QHBoxLayout, QColorDialog)
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

        # 定义主题方案
        self.themes = {
            'dark': {
                'background': '#282c34',    
                'text': '#e6e6e6',          
                'button': '#3d424a',        
                'button_hover': '#4a515c',  
                'header': '#363b44',        
                'border': '#1c1f24',        
                'input': '#1e2227',         
                'highlight': '#3d424a'      
            },
            'light': {
                'background': '#ffffff',
                'text': '#2c3e50',
                'button': '#ecf0f1',
                'button_hover': '#bdc3c7',
                'header': '#f5f6fa',
                'border': '#dcdde1',
                'input': '#f5f6fa',
                'highlight': '#dcdde1'
            }
        }
        
        # 当前主题
        self.current_theme = 'dark'
        self.theme = self.themes[self.current_theme]

        # 状态颜色
        self.colors = {
            'finish': '#67c23a',     
            'skip': '#e6a23c',       
            'failed': '#f56c6c',     
            'scheduled': '#409eff',  
            'running': '#ffd700',    
            'pending': '#ff9900',    
            'invalid': '#909399'     
        }

        # 创建菜单栏
        self.create_menu_bar()

        # 设置窗口标题
        title_name = "Console of XMeta/%s-%s @ %s" %(
            os.getenv('XMETA_VERSION', 'Version'),
            os.getenv('FAMILY', 'Family'),
            os.getenv('XMETA_PROJECT_NAME', 'XMetaProject')
        )
        self.setWindowTitle(title_name)

        # 应用当前主题
        self.apply_theme()
        
        # 设置应用样式
        app = QApplication.instance()
        app.setStyle(QStyleFactory.create('Fusion'))
        
        # 设置全局样式表
        app.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QWidget {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QPushButton {{
                background-color: {self.theme['button']};
                color: {self.theme['text']};
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QLineEdit {{
                background-color: {self.theme['input']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 3px;
                border-radius: 3px;
            }}
            QComboBox {{
                background-color: {self.theme['button']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 3px;
                border-radius: 3px;
            }}
            QComboBox:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QTreeWidget {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                alternate-background-color: {self.theme['header']};
            }}
            QTreeWidget::item:selected {{
                background-color: {self.theme['highlight']};
            }}
            QTreeWidget::item:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QHeaderView::section {{
                background-color: {self.theme['header']};
                color: {self.theme['text']};
                padding: 5px;
                border: none;
            }}
            QScrollBar {{
                background-color: {self.theme['background']};
                width: 12px;
                height: 12px;
            }}
            QScrollBar::handle {{
                background-color: {self.theme['button']};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QLabel {{
                color: {self.theme['text']};
            }}
            QMenuBar {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QMenuBar::item:selected {{
                background-color: {self.theme['button_hover']};
            }}
            QMenu {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QMenu::item:selected {{
                background-color: {self.theme['button_hover']};
            }}
        """)

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

        # 只保留操作按钮
        buttons = [
            ("run all", lambda: self.start('XMeta_run all')),
            ("run", lambda: self.start('XMeta_run')),
            ("stop", lambda: self.start('XMeta_stop')),
            ("skip", lambda: self.start('XMeta_skip')),
            ("unskip", lambda: self.start('XMeta_unskip')),
            ("invalid", lambda: self.start('XMeta_invalid'))
        ]

        button_row = QWidget()
        row_layout = QHBoxLayout(button_row)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.setSpacing(5)
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            row_layout.addWidget(btn)
        
        button_layout.addWidget(button_row)
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

        # 创建树形视图的右键菜单
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

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

    def Xterm(self, item):
        if item and item.text(1):  # 确保是target项
            target = item.text(1)
            # 原有的Xterm处理逻辑
            subprocess.Popen(['xterm'])

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
        """Shell - 使用gvim打开target对应的shell文件"""
        if item and item.text(1):
            target = item.text(1)
            # 修正shell文件路径到make_targets目录下
            shell_file = os.path.join(self.combo_sel, 'make_targets', f"{target}.csh")
            if not os.path.exists(shell_file):
                print(f"Shell file not found: {shell_file}")
                return
            
            try:
                subprocess.Popen(['gvim', shell_file])
            except Exception as e:
                print(f"Error opening shell file with gvim: {e}")

    def bt_log(self, item):
        """Log - 使用gvim打开target对应的log文件，支持直接打开.gz格式"""
        if item and item.text(1):
            target = item.text(1)
            log_file = os.path.join(self.combo_sel, 'logs', f"{target}.log")
            log_file_gz = f"{log_file}.gz"
            
            # 检查.log或.log.gz文件是否存在
            if os.path.exists(log_file):
                try:
                    subprocess.Popen(['gvim', log_file])
                except Exception as e:
                    print(f"Error opening log file with gvim: {e}")
            elif os.path.exists(log_file_gz):
                try:
                    subprocess.Popen(['gvim', log_file_gz])
                except Exception as e:
                    print(f"Error opening log.gz file with gvim: {e}")
            else:
                print(f"Log file not found: {log_file} or {log_file_gz}")

    def bt_cmd(self, item):
        """Command - 使用gvim打开target对应的cmd文件"""
        if item and item.text(1):
            target = item.text(1)
            cmd_file = os.path.join(self.combo_sel, 'cmds', f"{target}.cmd")
            if not os.path.exists(cmd_file):
                print(f"Command file not found: {cmd_file}")
                return
            
            try:
                subprocess.Popen(['gvim', cmd_file])
            except Exception as e:
                print(f"Error opening command file with gvim: {e}")

    def get_filter_target(self):
        pattern = self.En_search.text()
        # 原逻辑中使用正则从tar_name中选
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

    def retrace_tab(self, direction, item):
        if item and item.text(1):
            target = item.text(1)
            try:
                if direction == 'in':
                    self.create_trace_tab(target, 'in')
                else:
                    self.create_trace_tab(target, 'out')
            except Exception as e:
                print(f"Error in trace operation: {e}")

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

        # 清空
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

        # 构建��结构
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
            # 确保初始状态设置正确的背景色
            self.set_item_color(child_item, st)

        # 恢复用户的展开/折叠状态
        self.restore_tree_state(tree_state)

    def set_item_color(self, item, status):
        if status in self.colors:
            color = QColor(self.colors[status])
            # 调整透明度使颜色更柔和
            color.setAlpha(180)
            # 清除所有列的背景色
            for col in range(item.columnCount()):
                item.setBackground(col, QBrush())
            # 设置新��背景色
            for col in range(item.columnCount()):
                item.setBackground(col, QBrush(color))
                # 根据背景色亮度自动调整文字颜色
                if color.lightness() > 128:
                    item.setForeground(col, QBrush(QColor('#000000')))
                else:
                    item.setForeground(col, QBrush(QColor('#ffffff')))
        else:
            # 如果没有对应的状态颜色，清除背景色
            for col in range(item.columnCount()):
                item.setBackground(col, QBrush())
                item.setForeground(col, QBrush(QColor(self.theme['text'])))

    def get_target_status(self, target_file):
        # 缓存文件状态
        if not hasattr(self, '_status_cache'):
            self._status_cache = {}
        
        # 检查缓存是否有效
        current_time = time.time()
        if target_file in self._status_cache:
            cache_time, status = self._status_cache[target_file]
            if current_time - cache_time < 2:  # 2秒内的缓存有效
                return status
        
        # 获取新状态
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
        self._status_cache[target_file] = (current_time, status)
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
                if new_status != item.text(2):  # 状态发生变化
                    item.setText(2, new_status)
                    # 清除所有列的背景色
                    for col in range(item.columnCount()):
                        item.setBackground(col, QBrush())
                    # 设置新的状态颜色
                    self.set_item_color(item, new_status)
            iterator += 1

    def create_menu_bar(self):
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

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.theme = self.themes[theme_name]
        self.apply_theme()

    def apply_theme(self):
        # 获取应用实例
        app = QApplication.instance()
        
        # 应用样式表
        app.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QWidget {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QPushButton {{
                background-color: {self.theme['button']};
                color: {self.theme['text']};
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QLineEdit {{
                background-color: {self.theme['input']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 3px;
                border-radius: 3px;
            }}
            QComboBox {{
                background-color: {self.theme['button']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 3px;
                border-radius: 3px;
            }}
            QComboBox:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QTreeWidget {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                alternate-background-color: {self.theme['header']};
            }}
            QTreeWidget::item:selected {{
                background-color: {self.theme['highlight']};
            }}
            QTreeWidget::item:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QHeaderView::section {{
                background-color: {self.theme['header']};
                color: {self.theme['text']};
                padding: 5px;
                border: none;
            }}
            QScrollBar {{
                background-color: {self.theme['background']};
                width: 12px;
                height: 12px;
            }}
            QScrollBar::handle {{
                background-color: {self.theme['button']};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:hover {{
                background-color: {self.theme['button_hover']};
            }}
            QLabel {{
                color: {self.theme['text']};
            }}
            QMenuBar {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QMenuBar::item:selected {{
                background-color: {self.theme['button_hover']};
            }}
            QMenu {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
            }}
            QMenu::item:selected {{
                background-color: {self.theme['button_hover']};
            }}
        """)
        
        # 刷新界面
        self.update()

    def show_context_menu(self, position):
        # 获取当前选中的项
        item = self.tree.itemAt(position)
        if not item or not item.text(1):  # 确保选中了有效的target项
            return

        # 创建右键菜单
        context_menu = QMenu(self)
        context_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
            }}
            QMenu::item:selected {{
                background-color: {self.theme['button_hover']};
            }}
        """)

        # 添加菜单项
        actions = [
            ("Terminal", lambda: self.Xterm(item)),
            ("Shell", lambda: self.bt_csh(item)),
            ("Log", lambda: self.bt_log(item)),
            ("Command", lambda: self.bt_cmd(item)),
            (None, None),  # 分隔符
            ("Trace Up", lambda: self.retrace_tab('in', item)),
            ("Trace Down", lambda: self.retrace_tab('out', item))
        ]

        for text, handler in actions:
            if text is None:
                context_menu.addSeparator()
            else:
                action = QAction(text, self)
                action.triggered.connect(handler)
                context_menu.addAction(action)

        # 显示菜单
        context_menu.exec_(self.tree.viewport().mapToGlobal(position))

    def create_trace_tab(self, target, direction):
        """创建新的trace标签页"""
        try:
            # 创建新标签
            new_tab = QWidget()
            tab_layout = QVBoxLayout(new_tab)
            
            # 创建树形视图
            tree = QTreeWidget()
            tree.setColumnCount(5)
            tree.setHeaderLabels(["level", "target", "status", "start time", "end time"])
            
            # 添加到布局
            tab_layout.addWidget(tree)
            
            # 添加新标签页
            tab_name = f"Trace {'Up' if direction == 'in' else 'Down'}: {target}"
            self.tabwidget.addTab(new_tab, tab_name)
            
            # 切换到新标签页
            self.tabwidget.setCurrentWidget(new_tab)
            
            # TODO: 在这里添加trace数据的加载逻辑
            
        except Exception as e:
            print(f"Error creating trace tab: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 可根据需要设置样式
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    w = MonitorRuns()
    w.show()
    sys.exit(app.exec_())
