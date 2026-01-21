#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助函数
"""

import requests
import sys


def check_flask_service():
    """检查Flask服务是否运行"""
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def exit_if_no_flask_service():
    """如果没有Flask服务则退出程序"""
    if not check_flask_service():
        print("❌ Flask认证服务未启动，请先运行：")
        print("   python deploy/flask_app.py")
        print("或者使用集成启动脚本：")
        print("   python start_with_auth.py")
        print("\nFlask认证服务需要在端口5001上运行")
        sys.exit(1)
    
    print("✅ Flask认证服务正常运行")


def format_time(timestamp):
    """格式化时间戳"""
    import time
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))


def format_duration(seconds):
    """格式化时长"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_file_size(bytes_size):
    """格式化文件大小"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"


def create_progress_html(progress_percent, message, color="#007bff"):
    """创建进度条HTML"""
    return f"""
    <div style='width:100%; background-color:#f8f9fa; border-radius:5px; padding:10px; margin:10px 0;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
            <span>{message}</span>
            <span>{progress_percent}%</span>
        </div>
        <div style='width:100%; background-color:#e9ecef; border-radius:3px; overflow: hidden;'>
            <div style='width:{progress_percent}%; background-color:{color}; height:20px; transition: width 0.3s;'></div>
        </div>
    </div>
    """


def create_status_html(message, status_type="info"):
    """创建状态消息HTML"""
    colors = {
        "info": "#17a2b8",
        "success": "#28a745", 
        "warning": "#ffc107",
        "error": "#dc3545"
    }
    
    color = colors.get(status_type, "#17a2b8")
    
    return f"""
    <div style='width:100%; background-color:{color}20; border-left: 4px solid {color}; 
                border-radius:5px; padding:10px; margin:10px 0; color: {color};'>
        {message}
    </div>
    """


def validate_video_file(file_path):
    """验证视频文件"""
    import os
    from pathlib import Path
    
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    file_path = Path(file_path)
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    
    if file_path.suffix.lower() not in allowed_extensions:
        return False, f"不支持的文件格式: {file_path.suffix}"
    
    file_size = file_path.stat().st_size
    if file_size == 0:
        return False, "文件为空"
    
    # 检查文件大小限制 (例如: 2GB)
    max_size = 2 * 1024 * 1024 * 1024  # 2GB
    if file_size > max_size:
        return False, f"文件过大: {format_file_size(file_size)} (最大支持: {format_file_size(max_size)})"
    
    return True, "文件验证通过"


def generate_unique_id(prefix=""):
    """生成唯一ID"""
    import time
    import random
    
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_suffix}"
    else:
        return f"id_{timestamp}_{random_suffix}"


def safe_filename(filename):
    """生成安全的文件名"""
    import re
    from pathlib import Path
    
    # 移除或替换不安全的字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    safe_name = re.sub(r'[\x00-\x1f\x7f]', '', safe_name)
    # 限制长度
    if len(safe_name) > 200:
        name_part = Path(safe_name).stem[:150] + Path(safe_name).suffix
        safe_name = name_part
    
    return safe_name


def ensure_dir(directory):
    """确保目录存在"""
    import os
    os.makedirs(directory, exist_ok=True)


def cleanup_old_files(directory, max_age_days=7, pattern="*"):
    """清理旧文件"""
    import os
    import time
    from pathlib import Path
    import glob
    
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 3600
    
    pattern_path = os.path.join(directory, pattern)
    for file_path in glob.glob(pattern_path):
        try:
            file_stat = os.stat(file_path)
            if current_time - file_stat.st_mtime > max_age_seconds:
                os.remove(file_path)
                print(f"已删除旧文件: {file_path}")
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")


def get_system_info():
    """获取系统信息"""
    import platform
    import torch
    
    info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cuda_available": torch.cuda.is_available() if torch else False,
    }
    
    if torch and torch.cuda.is_available():
        info["cuda_version"] = torch.version.cuda
        info["gpu_count"] = torch.cuda.device_count()
        info["gpu_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    
    return info


def log_system_info():
    """记录系统信息"""
    info = get_system_info()
    print("=" * 50)
    print("系统信息:")
    print(f"操作系统: {info['platform']} {info['platform_release']}")
    print(f"架构: {info['architecture']}")
    print(f"Python版本: {info['python_version']}")
    print(f"CUDA可用: {'是' if info['cuda_available'] else '否'}")
    
    if info['cuda_available']:
        print(f"CUDA版本: {info.get('cuda_version', '未知')}")
        print(f"GPU数量: {info.get('gpu_count', 0)}")
        if 'gpu_names' in info:
            for i, name in enumerate(info['gpu_names']):
                print(f"GPU {i}: {name}")
    
    print("=" * 50)