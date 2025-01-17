import os
import subprocess
from datetime import datetime

def get_run_directories():
    """获取运行目录"""
    print("Getting run directories...")
    try:
        # 获取当前工作目录
        pwd = os.getcwd()
        print(f"Current working directory: {pwd}")
        
        # 获取当前目录下的所有文件和目录
        try:
            all_files = os.listdir(pwd)
            print(f"Found {len(all_files)} entries in current directory")
        except Exception as e:
            print(f"Error listing directory {pwd}: {e}")
            return [], []
            
        # 按名称排序
        sorted_entries = sorted(all_files)
        
        # 收集运行目录
        run_dirs = []
        peer_dirs = []
        
        # 首先检查当前目录
        if os.path.exists(os.path.join(pwd, '.target_dependency.csh')):
            run_dirs.append(pwd)
            print(f"Current directory is a run directory")
        
        # 检查子目录
        for entry in sorted_entries:
            try:
                full_path = os.path.join(pwd, entry)
                dependency_file = os.path.join(full_path, '.target_dependency.csh')
                
                if (os.path.isdir(full_path) and 
                    not os.path.islink(full_path) and 
                    os.path.exists(dependency_file)):
                    print(f"Found run directory: {entry}")
                    run_dirs.append(full_path)
                    peer_dirs.append(full_path)
            except Exception as e:
                print(f"Error processing entry {entry}: {e}")
                continue
                
        print(f"Found {len(run_dirs)} run directories")
        return run_dirs, peer_dirs
        
    except Exception as e:
        print(f"Error in get_run_directories: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def execute_command(command, cwd=None):
    """执行shell命令"""
    print(f"Executing command: {command}")
    try:
        if not command:
            print("No command specified")
            return "", "No command specified", -1
            
        if cwd and not os.path.exists(cwd):
            print(f"Working directory does not exist: {cwd}")
            return "", f"Working directory does not exist: {cwd}", -1
            
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        try:
            output, error = process.communicate(timeout=300)  # 5分钟超时
            print(f"Command completed with return code: {process.returncode}")
            return output, error, process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            print("Command timed out after 5 minutes")
            return "", "Command timed out after 5 minutes", -1
    except Exception as e:
        print(f"Error executing command: {e}")
        import traceback
        traceback.print_exc()
        return "", str(e), -1

def get_timestamp(file_path):
    """获取文件时间戳"""
    try:
        if not file_path:
            print("No file path specified")
            return ""
            
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return ""
            
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error getting timestamp for {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return "" 