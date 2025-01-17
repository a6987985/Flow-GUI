import os

# 环境变量配置
XMETA_PROJECT = os.getenv('XMETA_PROJECT_NAME', 'XMetaProject')
FAMILY = os.getenv('FAMILY', 'Family')
XMETA_BACKGROUND = os.getenv('XMETA_BACKGROUND', '#ffffff')
VERSION = os.getenv('XMETA_VERSION', 'Version')

# 状态颜色配置
STATUS_COLORS = {
    'finish': '#67c23a',    # 绿色
    'skip': '#e6a23c',      # 橙色
    'failed': '#f56c6c',    # 红色
    'scheduled': '#409eff', # 蓝色
    'running': '#ffd700',   # 黄色
    'pending': '#ff9900',   # 橙色
    'invalid': '#909399'    # 灰色
}

# 应用样式
APP_STYLE = """
    QMainWindow {
        background-color: #FFFFFF;
    }
    QTreeView {
        background-color: #FFFFFF;
        alternate-background-color: #F5F5F5;
        border: 1px solid #E0E0E0;
    }
    QTreeView::item {
        padding: 5px;
    }
    QTreeView::item:selected {
        background-color: #E1BEE7;
        color: black;
    }
    QHeaderView::section {
        background-color: #F5F5F5;
        padding: 5px;
        border: none;
        border-right: 1px solid #E0E0E0;
        border-bottom: 1px solid #E0E0E0;
    }
    QTabWidget::pane {
        border: 1px solid #E0E0E0;
    }
    QTabBar::tab {
        background-color: #F5F5F5;
        padding: 8px 15px;
        border: 1px solid #E0E0E0;
        border-bottom: none;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #FFFFFF;
    }
    QTabBar::tab:hover {
        background-color: #E1BEE7;
    }
"""

# 其他配置
CONFIG = {
    'update_interval': 1000,  # 状态更新间隔（毫秒）
    'max_recent_runs': 10,    # 最近运行记录数量
    'editor_command': 'gvim', # 默认编辑器
    'log_level': 'INFO'       # 日志级别
} 