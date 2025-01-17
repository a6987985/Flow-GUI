import sys
import os
import signal
import platform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def init_environment():
    """初始化环境变量"""
    print("Initializing environment...")
    try:
        # 检测操作系统
        os_type = platform.system()
        os_release = platform.release()
        print(f"Operating System: {os_type}, Release: {os_release}")
        
        # CentOS 特定设置
        if os_type == 'Linux':
            # 使用 xcb 平台插件
            os.environ['QT_QPA_PLATFORM'] = 'xcb'
            
            # 设置XDG运行时目录
            runtime_dir = f'/tmp/runtime-{os.getenv("USER")}'
            os.environ['XDG_RUNTIME_DIR'] = runtime_dir
            if not os.path.exists(runtime_dir):
                os.makedirs(runtime_dir, mode=0o700)
                
            # 禁用 GTK 主题
            os.environ['QT_QPA_PLATFORMTHEME'] = ''
            
        elif os_type == 'Darwin':  # macOS
            if 'QT_QPA_PLATFORM' in os.environ:
                del os.environ['QT_QPA_PLATFORM']
                
        # 通用设置
        os.environ['QT_ACCESSIBILITY'] = '0'  # 禁用辅助功能
        os.environ['QT_NO_GLIB'] = '1'       # 禁用GLIB
        os.environ['QT_NO_DBUS'] = '1'       # 禁用DBUS
        
        # 显示当前环境变量
        print("\nCurrent Environment Variables:")
        for key in ['QT_QPA_PLATFORM', 'QT_QPA_PLATFORMTHEME', 'XDG_RUNTIME_DIR',
                   'QT_ACCESSIBILITY', 'QT_NO_GLIB', 'QT_NO_DBUS']:
            print(f"{key}: {os.environ.get(key, 'Not Set')}")
            
        print("\nEnvironment initialized.")
    except Exception as e:
        print(f"Error initializing environment: {e}")
        import traceback
        traceback.print_exc()

def signal_handler(signum, frame):
    """处理信号"""
    print(f"\nReceived signal {signum}")
    QApplication.quit()

def main():
    """主函数"""
    try:
        # 初始化环境
        init_environment()
        
        # 设置应用程序属性
        QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        QApplication.setAttribute(Qt.AA_X11InitThreads)  # 启用X11线程支持
        
        print("Creating QApplication...")
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 设置信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("Importing MonitorRuns...")
        # 导入主窗口类
        from ui.monitor_runs import MonitorRuns
        
        print("Creating main window...")
        # 创建主窗口
        window = MonitorRuns()
        window.show()
        
        print("Entering event loop...")
        # 进入事件循环
        return app.exec_()
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("Application exiting...")

if __name__ == '__main__':
    # 设置 Python 的默认编码
    if sys.getdefaultencoding() != 'utf-8':
        reload(sys)
        sys.setdefaultencoding('utf-8')
    
    # 运行应用程序
    sys.exit(main()) 