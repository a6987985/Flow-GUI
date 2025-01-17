from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import os
import re
from utils.file_utils import get_run_directories, execute_command
from utils.status_utils import get_target_status, get_timestamps

class TargetModel(QObject):
    # 定义类级别的信号
    data_loaded = pyqtSignal(list)  # 数据加载完成信号
    status_changed = pyqtSignal(dict)  # 状态改变信号
    
    def __init__(self):
        print("Initializing TargetModel...")
        super().__init__()
        
        # 初始化成员变量
        self.targets = []
        self.current_dir = None
        self.level_expanded = {}
        self.run_dirs = []
        self.peer_dirs = []
        self._is_running = True
        
        try:
            # 立即加载数据
            self.load_data()
            print("TargetModel initialized.")
        except Exception as e:
            print(f"Error in TargetModel initialization: {e}")
            import traceback
            traceback.print_exc()
            
    def cleanup(self):
        """清理资源"""
        print("Cleaning up TargetModel...")
        self._is_running = False
        self.targets = []
        self.current_dir = None
        self.run_dirs = []
        self.peer_dirs = []
        
    def load_data(self):
        """加载数据"""
        print("Loading target data...")
        try:
            if not self._is_running:
                return
                
            # 获取运行目录
            print("Getting run directories...")
            self.run_dirs, self.peer_dirs = get_run_directories()
            print(f"Found {len(self.run_dirs)} run directories")
            
            if self.run_dirs:
                # 获取第一个有效的运行目录
                for run_dir in self.run_dirs:
                    try:
                        print(f"Trying to load targets from {run_dir}")
                        full_path = os.path.abspath(run_dir)
                        if os.path.exists(full_path):
                            self.current_dir = full_path
                            targets_data = self.load_targets(full_path)
                            if targets_data:
                                print(f"Successfully loaded {len(targets_data)} targets from {run_dir}")
                                # 更新目标列表
                                self.targets = [target['name'] for target in targets_data]
                                # 发送数据加载信号
                                try:
                                    print("Emitting data_loaded signal...")
                                    self.data_loaded.emit(targets_data)
                                    print("Signal emitted successfully")
                                except Exception as e:
                                    print(f"Error emitting signal: {e}")
                                    import traceback
                                    traceback.print_exc()
                                return
                    except Exception as e:
                        print(f"Error loading targets from {run_dir}: {e}")
                        continue
                
                print("No valid targets found in any run directory")
            else:
                print("No run directories found")
            
        except Exception as e:
            print(f"Error loading target data: {e}")
            import traceback
            traceback.print_exc()
            
    def load_targets(self, directory):
        """从指定目录加载目标"""
        print(f"Loading targets from directory: {directory}")
        try:
            if not os.path.exists(directory):
                print(f"Directory does not exist: {directory}")
                return []
                
            # 读取依赖文件
            dependency_file = os.path.join(directory, '.target_dependency.csh')
            print(f"Looking for dependency file: {dependency_file}")
            
            if not os.path.exists(dependency_file):
                # 尝试在父目录查找
                parent_dir = os.path.dirname(directory)
                dependency_file = os.path.join(parent_dir, '.target_dependency.csh')
                print(f"Trying parent directory: {dependency_file}")
                
                if not os.path.exists(dependency_file):
                    print(f"Dependency file not found in either directory")
                    return []
                
            print(f"Found dependency file: {dependency_file}")
            targets_data = []
            with open(dependency_file, 'r') as f:
                content = f.read()
                print("Reading dependency file content...")
                
                # 获取所有targets
                m = re.search(r'set\s*ACTIVE_TARGETS\s*\=(\s*["\'].*?["\'])', content, re.DOTALL)
                if m:
                    target_list = m.group(1).strip()
                    print(f"Found target list: {target_list}")
                    
                    # 移除引号并分割
                    targets = re.sub(r'^["\']|["\']$', '', target_list).split()
                    print(f"Parsed targets: {targets}")
                    
                    # 获取每个target的信息
                    for target in targets:
                        try:
                            print(f"Processing target: {target}")
                            # 获取level
                            level = self.get_target_level(target)
                            print(f"Target {target} level: {level}")
                            
                            # 获取状态和时间信息
                            info = self.get_target_info(target)
                            if info:
                                target_data = {
                                    'name': target,
                                    'level': level or '0',
                                    'status': info.get('status', 'unknown'),
                                    'start_time': info.get('start_time', ''),
                                    'end_time': info.get('end_time', '')
                                }
                                print(f"Target data: {target_data}")
                                targets_data.append(target_data)
                        except Exception as e:
                            print(f"Error processing target {target}: {e}")
                            continue
                else:
                    print("No ACTIVE_TARGETS found in dependency file")
                                
            print(f"Loaded {len(targets_data)} targets from {directory}")
            return targets_data
            
        except Exception as e:
            print(f"Error loading targets from directory: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    def get_target_info(self, target):
        """获取target的详细信息"""
        try:
            if not self.current_dir or not target:
                return None
                
            target_file = os.path.join(self.current_dir, 'status', target)
            track_file = os.path.join(self.current_dir, 'logs/targettracker', target)
            
            status = get_target_status(target_file)
            start_time, end_time = get_timestamps(track_file)
            
            return {
                'status': status or '',
                'start_time': start_time or '',
                'end_time': end_time or ''
            }
        except Exception as e:
            print(f"Error getting info for target {target}: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def execute_command(self, command, targets=None):
        """执行命令"""
        try:
            if not self.current_dir:
                print("No current directory set")
                return
                
            if not command:
                print("No command specified")
                return
                
            cmd = f"cd {self.current_dir} && {command}"
            if targets:
                cmd += f" {' '.join(targets)}"
                
            output, error, code = execute_command(cmd)
            
            # 更新状态
            if targets:
                for target in targets:
                    try:
                        info = self.get_target_info(target)
                        if info and info.get('status'):
                            self.status_changed.emit(target, info['status'])
                    except Exception as e:
                        print(f"Error updating status for target {target}: {e}")
                        continue
        except Exception as e:
            print(f"Error executing command: {e}")
            import traceback
            traceback.print_exc()
                    
    def get_target_dependencies(self, target, direction='up'):
        """获取target的依赖关系"""
        try:
            if not self.current_dir or not target:
                return []
                
            dependency_file = os.path.join(self.current_dir, '.target_dependency.csh')
            if not os.path.exists(dependency_file):
                print(f"Dependency file not found: {dependency_file}")
                return []
                
            with open(dependency_file, 'r') as f:
                content = f.read()
                
                # 根据方向选择依赖类型
                if direction == 'up':
                    pattern = f'ALL_RELATED_{target}'
                else:
                    pattern = f'DEPENDENCY_OUT_{target}'
                    
                match = re.search(r'set\s*(%s)\s*\=(\s.*)' % pattern, content)
                if match:
                    deps = match.group(2).strip()
                    if re.match(r"^(['\"]).*\"$", deps):
                        return re.sub(r"^['\"]|['\"]$", '', deps).split()
            return []
        except Exception as e:
            print(f"Error getting dependencies for target {target}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_target_level(self, target):
        """获取target的level信息"""
        try:
            if not self.current_dir or not target:
                print(f"Invalid current_dir or target: {self.current_dir}, {target}")
                return "0"
                
            dependency_file = os.path.join(self.current_dir, '.target_dependency.csh')
            print(f"Looking for dependency file for level: {dependency_file}")
            
            if not os.path.exists(dependency_file):
                # 尝试在父目录查找
                parent_dir = os.path.dirname(self.current_dir)
                dependency_file = os.path.join(parent_dir, '.target_dependency.csh')
                print(f"Trying parent directory for level: {dependency_file}")
                
                if not os.path.exists(dependency_file):
                    print(f"Dependency file not found for level")
                    return "0"
                    
            print(f"Reading dependency file for level...")
            with open(dependency_file, 'r') as f:
                content = f.read()
                level_name = f'TARGET_LEVEL_{target}'
                print(f"Searching for level pattern: {level_name}")
                
                match = re.search(r'set\s*%s\s*\=\s*["\']([^"\']+)["\']' % level_name, content)
                if match:
                    level = match.group(1)
                    print(f"Found level for {target}: {level}")
                    return level
                else:
                    print(f"No level found for {target}")
                    return "0"
                    
        except Exception as e:
            print(f"Error getting level for target {target}: {e}")
            import traceback
            traceback.print_exc()
            return "0"

    def update_target_status(self, target_name, new_status):
        """更新目标状态"""
        try:
            if not target_name or not new_status:
                return
                
            status_info = {
                'name': target_name,
                'status': new_status
            }
            
            try:
                print(f"Emitting status_changed signal for {target_name}...")
                self.status_changed.emit(status_info)
                print("Signal emitted successfully")
            except Exception as e:
                print(f"Error emitting status signal: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"Error updating target status: {e}")
            import traceback
            traceback.print_exc()