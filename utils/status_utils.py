import os
from utils.file_utils import get_timestamp

def get_target_status(target_file):
    """获取target状态"""
    try:
        if not target_file:
            print("No target file specified")
            return 'invalid'
            
        status_files = {
            'skip': target_file + '.skip',
            'finish': target_file + '.finish',
            'failed': target_file + '.failed',
            'running': target_file + '.running',
            'pending': target_file + '.pending',
            'scheduled': target_file + '.scheduled'
        }
        
        for status, file_path in status_files.items():
            try:
                if os.path.exists(file_path):
                    return status
            except Exception as e:
                print(f"Error checking status file {file_path}: {e}")
                continue
                
        return 'invalid'
    except Exception as e:
        print(f"Error getting target status for {target_file}: {e}")
        import traceback
        traceback.print_exc()
        return 'invalid'

def sync_parent_status(target_path):
    """同步父目录的状态"""
    try:
        if not target_path:
            print("No target path specified")
            return
            
        parent_dir = os.path.dirname(target_path)
        if not parent_dir or parent_dir == target_path:
            return
            
        if not os.path.exists(parent_dir):
            print(f"Parent directory does not exist: {parent_dir}")
            return
            
        # 获取所有子目录的状态
        children_status = []
        try:
            for item in os.listdir(parent_dir):
                try:
                    item_path = os.path.join(parent_dir, item)
                    if os.path.isdir(item_path):
                        children_status.append(get_target_status(item_path))
                except Exception as e:
                    print(f"Error processing child directory {item}: {e}")
                    continue
        except Exception as e:
            print(f"Error listing parent directory {parent_dir}: {e}")
            return
            
        if not children_status:
            print("No valid children status found")
            return
            
        # 根据子目录状态决定父目录状态
        new_status = 'invalid'
        if 'failed' in children_status:
            new_status = 'failed'
        elif 'running' in children_status:
            new_status = 'running'
        elif 'pending' in children_status:
            new_status = 'pending'
        elif 'scheduled' in children_status:
            new_status = 'scheduled'
        elif all(status == 'finish' for status in children_status):
            new_status = 'finish'
        elif all(status == 'skip' for status in children_status):
            new_status = 'skip'
        
        # 更新父目录状态
        update_item_status(parent_dir, new_status)
    except Exception as e:
        print(f"Error syncing parent status for {target_path}: {e}")
        import traceback
        traceback.print_exc()

def update_item_status(item_path, new_status):
    """更新项目状态"""
    try:
        if not item_path:
            print("No item path specified")
            return
            
        if not os.path.exists(item_path):
            print(f"Item path does not exist: {item_path}")
            return
            
        if new_status not in ['skip', 'finish', 'failed', 'running', 'pending', 'scheduled', 'invalid']:
            print(f"Invalid status: {new_status}")
            return
            
        # 先删除所有可能的状态文件
        status_files = ['.skip', '.finish', '.failed', '.running', '.pending', '.scheduled']
        for status_file in status_files:
            try:
                status_path = item_path + status_file
                if os.path.exists(status_path):
                    os.remove(status_path)
            except Exception as e:
                print(f"Error removing status file {status_file}: {e}")
                continue
        
        # 创建新的状态文件
        if new_status != 'invalid':
            try:
                with open(item_path + '.' + new_status, 'w') as f:
                    pass
            except Exception as e:
                print(f"Error creating new status file for {new_status}: {e}")
    except Exception as e:
        print(f"Error updating item status for {item_path}: {e}")
        import traceback
        traceback.print_exc()

def get_timestamps(track_file):
    """获取开始和结束时间"""
    try:
        if not track_file:
            print("No track file specified")
            return "", ""
            
        start_time = ""
        end_time = ""
        
        start_file = track_file + '.start'
        finish_file = track_file + '.finished'
        
        try:
            if os.path.exists(start_file):
                start_time = get_timestamp(start_file)
        except Exception as e:
            print(f"Error getting start timestamp: {e}")
            
        try:
            if os.path.exists(finish_file):
                end_time = get_timestamp(finish_file)
        except Exception as e:
            print(f"Error getting end timestamp: {e}")
            
        return start_time, end_time
    except Exception as e:
        print(f"Error getting timestamps for {track_file}: {e}")
        import traceback
        traceback.print_exc()
        return "", ""

def update_status(target_file):
    """更新状态文件"""
    try:
        if not target_file:
            print("No target file specified")
            return 'invalid'
            
        status = get_target_status(target_file)
        if status == 'invalid':
            try:
                # 创建pending状态文件
                with open(target_file + '.pending', 'w') as f:
                    pass
                status = 'pending'
            except Exception as e:
                print(f"Error creating pending status file: {e}")
                return 'invalid'
        return status
    except Exception as e:
        print(f"Error updating status for {target_file}: {e}")
        import traceback
        traceback.print_exc()
        return 'invalid'

def get_status_color(status):
    """获取状态对应的颜色"""
    try:
        if not status:
            return '#000000'  # 默认黑色
            
        color_map = {
            'skip': '#808080',      # 灰色
            'finish': '#00FF00',    # 绿色
            'failed': '#FF0000',    # 红色
            'running': '#0000FF',   # 蓝色
            'pending': '#FFA500',   # 橙色
            'scheduled': '#FFFF00', # 黄色
            'invalid': '#000000'    # 黑色
        }
        return color_map.get(status, '#000000')
    except Exception as e:
        print(f"Error getting status color for {status}: {e}")
        return '#000000'  # 出错时返回黑色 