#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试视频列表刷新问题
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from deploy.utils.user_context import user_context


def debug_video_list():
    """调试视频列表刷新问题"""
    print("🔧 调试视频列表刷新问题...")
    
    # 设置测试用户
    user_context.set_user('debug_video_user')
    
    try:
        # 1. 获取用户路径管理器
        from deploy.utils.user_context import get_current_user_paths
        user_paths = get_current_user_paths()
        
        # 2. 创建测试视频文件
        upload_dir = user_paths.get_upload_path()
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建一个简单的测试文件
        test_file = upload_dir / "debug_video_user_1234567890_test.mp4"
        test_file.write_bytes(b'fake video content')
        
        print(f"   ✅ 创建测试文件: {test_file}")
        
        # 3. 调用 get_user_video_list
        from deploy.core.video_processor_isolated import get_isolated_processor
        processor = get_isolated_processor()
        
        video_list = processor.get_user_video_list()
        print(f"   ✅ 视频列表: {video_list}")
        
        # 4. 调用 refresh_video_list
        from deploy.ui.ui_handlers import refresh_video_list
        
        dropdown, textbox = refresh_video_list()
        
        print(f"   ✅ Dropdown类型: {type(dropdown)}")
        print(f"   ✅ Dropdown.choices: {dropdown.choices}")
        print(f"   ✅ Dropdown.value: {dropdown.value}")
        
        # 检查每个choice
        for i, choice in enumerate(dropdown.choices):
            print(f"   ✅ Choice {i}: type={type(choice)}, value={choice}")
            if isinstance(choice, str):
                print(f"      - 是字符串，包含': {' : ' in choice}")
                if ': ' in choice:
                    parts = choice.split(': ')
                    print(f"      - 分割结果: {parts}")
        
    except Exception as e:
        print(f"   ❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        try:
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
                print(f"   ✅ 测试文件清理完成")
        except:
            pass


if __name__ == "__main__":
    debug_video_list()