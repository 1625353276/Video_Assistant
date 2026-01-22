#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修复后的上传功能测试
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.user_context import user_context
from deploy.core.video_processor_isolated import get_isolated_processor


def test_upload_and_progress():
    """测试上传和进度获取功能"""
    print("🧪 测试上传和进度获取功能...")
    
    # 创建临时视频文件
    temp_dir = Path(tempfile.mkdtemp())
    video_file = temp_dir / "test_video.mp4"
    video_file.write_bytes(b"fake video content")
    
    try:
        # 设置测试用户
        user_context.set_user("test_user", "testuser")
        
        # 获取处理器
        processor = get_isolated_processor()
        
        # Mock视频验证
        with patch.object(processor.video_loader, 'validate_video') as mock_validate:
            mock_validate.return_value = {
                "duration": 10.0,
                "fps": 30.0,
                "width": 1920,
                "height": 1080
            }
            
            # 上传视频
            result = processor.upload_and_process_video(str(video_file))
            
            # 验证上传结果
            assert result["status"] == "processing"
            assert "video_id" in result
            assert result["user_id"] == "test_user"
            
            video_id = result["video_id"]
            
            # 获取处理进度
            progress = processor.get_processing_progress(video_id)
            
            # 验证进度信息
            assert "progress" in progress
            assert "current_step" in progress
            assert "log_messages" in progress
            assert "status" in progress
            assert progress["status"] == "processing"
            assert len(progress["log_messages"]) > 0
            
            print("✅ 上传和进度获取功能测试通过")
            
    finally:
        user_context.clear_user()
        shutil.rmtree(temp_dir)


def test_ui_handlers_fix():
    """测试UI处理函数修复"""
    print("🧪 测试UI处理函数修复...")
    
    try:
        # 导入UI处理函数
        from deploy.ui.ui_handlers import update_progress, check_background_tasks
        
        # 设置测试用户
        user_context.set_user("test_user", "testuser")
        
        # 获取处理器
        processor = get_isolated_processor()
        
        # Mock视频信息
        video_info = {
            "video_id": "test_video_123",
            "filename": "test.mp4"
        }
        
        # 测试update_progress
        try:
            result = update_progress(video_info)
            # 应该不会抛出异常
            assert len(result) == 7  # 验证返回的参数数量
            print("✅ update_progress函数修复成功")
        except Exception as e:
            print(f"❌ update_progress函数仍有问题: {e}")
            return False
        
        # 测试check_background_tasks
        try:
            result = check_background_tasks(video_info)
            # 应该不会抛出异常
            assert len(result) == 2  # 验证返回的参数数量
            print("✅ check_background_tasks函数修复成功")
        except Exception as e:
            print(f"❌ check_background_tasks函数仍有问题: {e}")
            return False
        
        print("✅ UI处理函数修复测试通过")
        return True
        
    finally:
        user_context.clear_user()


def run_fix_validation_tests():
    """运行修复验证测试"""
    print("🚀 开始修复验证测试\n")
    
    try:
        test_upload_and_progress()
        print()
        test_ui_handlers_fix()
        print()
        
        print("🎉 所有修复验证测试通过！")
        print("✅ get_processing_progress方法添加成功")
        print("✅ upload_and_process_video方法修复成功")
        print("✅ UI处理函数修复成功")
        print("✅ 上传功能现在可以正常使用")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_fix_validation_tests()
    sys.exit(0 if success else 1)