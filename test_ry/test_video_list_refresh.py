#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频列表刷新修复
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


def test_video_list_refresh():
    """测试视频列表刷新功能"""
    print("🔧 测试视频列表刷新修复...")
    
    # 设置测试用户
    user_context.set_user('video_list_test_user')
    
    try:
        # 1. 获取用户路径管理器
        from deploy.utils.user_context import get_current_user_paths
        user_paths = get_current_user_paths()
        
        if not user_paths:
            print("   ❌ 无法获取用户路径管理器")
            return False
        
        # 2. 获取上传目录
        upload_dir = user_paths.get_upload_path()
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 上传目录: {upload_dir}")
        
        # 3. 创建测试视频文件
        test_files = []
        for i in range(3):
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(b'fake video content')
                temp_path = temp_file.name
            
            # 构造上传文件名（模拟实际上传的文件名格式）
            video_id = f"video_list_test_user_{1234567890 + i}_test_video_{i+1}"
            upload_filename = f"{video_id}.mp4"
            upload_path = upload_dir / upload_filename
            
            # 复制到上传目录
            shutil.copy2(temp_path, upload_path)
            test_files.append(upload_path)
            
            # 清理临时文件
            os.unlink(temp_path)
        
        print(f"   ✅ 创建了 {len(test_files)} 个测试视频文件")
        
        # 4. 测试 get_user_video_list 方法
        from deploy.core.video_processor_isolated import get_isolated_processor
        processor = get_isolated_processor()
        
        video_list = processor.get_user_video_list()
        print(f"   ✅ 获取到 {len(video_list)} 个视频")
        
        # 5. 验证视频列表内容
        if len(video_list) != 3:
            print(f"   ❌ 视频数量不正确，期望3个，实际{len(video_list)}个")
            return False
        
        # 收集期望的文件名
        expected_filenames = set()
        for i in range(3):
            expected_filenames.add(f"video_list_test_user_{1234567890 + i}_test_video_{i+1}.mp4")
        
        # 验证每个视频
        actual_filenames = set()
        for video in enumerate(video_list):
            print(f"   ✅ 视频: {video[1]['video_id']} - {video[1]['filename']}")
            actual_filenames.add(video[1]['filename'])
        
        # 检查是否所有期望的文件都存在
        if expected_filenames != actual_filenames:
            print(f"   ❌ 文件名不匹配")
            print(f"      期望: {expected_filenames}")
            print(f"      实际: {actual_filenames}")
            return False
        
        # 6. 测试视频列表刷新功能
        from deploy.ui.ui_handlers import refresh_video_list
        
        # 调用刷新函数
        dropdown, textbox = refresh_video_list()
        
        # 获取Gradio组件的属性
        choices = dropdown.choices
        value = dropdown.value
        
        print(f"   ✅ 刷新函数返回: {len(choices)} 个选择")
        
        # 验证下拉列表内容
        if len(choices) != 3:
            print(f"   ❌ 下拉列表选项数量不正确，期望3个，实际{len(choices)}个")
            return False
        
        for choice in choices:
            print(f"   ✅ 下拉选项: {choice}")
        
        # 7. 验证格式是否正确 (video_id: filename)
        for choice in choices:
            # Gradio Dropdown 的 choices 是元组格式 (display_value, actual_value)
            if isinstance(choice, tuple):
                display_value = choice[0]
                if ': ' not in display_value:
                    print(f"   ❌ 下拉选项格式不正确: {display_value}")
                    return False
            else:
                # 兼容字符串格式
                if ': ' not in choice:
                    print(f"   ❌ 下拉选项格式不正确: {choice}")
                    return False
        
        print(f"   ✅ 视频列表刷新修复验证成功！")
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理测试文件
        try:
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
                print(f"   ✅ 测试文件清理完成")
        except:
            pass


if __name__ == "__main__":
    success = test_video_list_refresh()
    sys.exit(0 if success else 1)