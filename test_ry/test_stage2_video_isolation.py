#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二阶段测试：视频处理流程隔离

测试用户隔离的视频处理和文件管理
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.user_context import user_context
from deploy.core.video_processor_isolated import IsolatedVideoProcessor, get_isolated_processor


def create_mock_video_file():
    """创建模拟视频文件"""
    temp_dir = Path(tempfile.mkdtemp())
    video_file = temp_dir / "test_video.mp4"
    
    # 创建一个小的测试文件（模拟视频）
    with open(video_file, 'wb') as f:
        f.write(b'fake video content' * 1000)  # 创建一个约25KB的文件
    
    return video_file, temp_dir


def test_video_processor_init():
    """测试视频处理器初始化"""
    print("🧪 测试视频处理器初始化...")
    
    processor = IsolatedVideoProcessor(cuda_enabled=False, whisper_model="base")
    
    assert processor.cuda_enabled == False
    assert processor.whisper_model == "base"
    assert processor.video_loader is not None
    assert processor.audio_extractor is not None
    assert processor.whisper_asr is not None
    
    print("✅ 视频处理器初始化测试通过")


def test_user_video_upload():
    """测试用户视频上传（模拟）"""
    print("🧪 测试用户视频上传...")
    
    # 设置测试用户
    test_user_id = "test_video_user"
    user_context.set_user(test_user_id, "testuser")
    
    # 创建模拟视频文件
    video_file, temp_dir = create_mock_video_file()
    
    try:
        # Mock视频验证
        with patch('modules.video.video_loader.VideoLoader.validate_video') as mock_validate:
            mock_validate.return_value = {
                "file_path": str(video_file),
                "file_name": video_file.name,
                "file_size": video_file.stat().st_size,
                "duration": 300.0,
                "validation_status": "passed"
            }
            
            processor = IsolatedVideoProcessor()
            result = processor.upload_and_process_video(str(video_file))
            
            # 验证结果
            assert result["status"] == "processing"
            assert result["filename"] == video_file.name
            assert result["user_id"] == test_user_id
            assert "video_id" in result
            assert test_user_id in result["video_id"]  # 验证用户前缀
            
            # 验证文件被复制到用户专属目录
            user_paths = user_context.get_paths()
            expected_path = user_paths.get_upload_path(result["video_id"], video_file.name)
            assert expected_path.exists()
            
            print("✅ 用户视频上传测试通过")
            
    finally:
        # 清理测试数据
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        shutil.rmtree(temp_dir)
        user_context.clear_user()


def test_user_video_isolation():
    """测试用户视频隔离"""
    print("🧪 测试用户视频隔离...")
    
    # 创建两个测试用户
    user1_id = "isolation_user_1"
    user2_id = "isolation_user_2"
    
    user_context.set_user(user1_id, "user1")
    user1_paths = user_context.get_paths()
    
    user_context.set_user(user2_id, "user2")
    user2_paths = user_context.get_paths()
    
    try:
        # 验证用户路径隔离
        assert user1_paths.base_path != user2_paths.base_path
        assert user1_id in str(user1_paths.base_path)
        assert user2_id in str(user2_paths.base_path)
        
        # 创建模拟视频文件
        video_file, temp_dir = create_mock_video_file()
        
        # Mock视频处理
        with patch('modules.video.video_loader.VideoLoader.validate_video') as mock_validate:
            mock_validate.return_value = {
                "file_path": str(video_file),
                "file_name": video_file.name,
                "validation_status": "passed"
            }
            
            # 用户1上传视频
            user_context.set_user(user1_id, "user1")
            processor1 = IsolatedVideoProcessor()
            result1 = processor1.upload_and_process_video(str(video_file))
            
            # 用户2上传同名视频
            user_context.set_user(user2_id, "user2")
            processor2 = IsolatedVideoProcessor()
            result2 = processor2.upload_and_process_video(str(video_file))
            
            # 验证隔离
            assert result1["user_id"] == user1_id
            assert result2["user_id"] == user2_id
            assert result1["video_id"] != result2["video_id"]
            
            # 验证文件路径隔离
            file1_path = user1_paths.get_upload_path(result1["video_id"], video_file.name)
            file2_path = user2_paths.get_upload_path(result2["video_id"], video_file.name)
            
            assert file1_path != file2_path
            assert file1_path.exists()
            assert file2_path.exists()
            
            print("✅ 用户视频隔离测试通过")
            
    finally:
        # 清理测试数据
        for paths in [user1_paths, user2_paths]:
            if paths and paths.base_path.exists():
                shutil.rmtree(paths.base_path)
        shutil.rmtree(temp_dir)
        user_context.clear_user()


def test_user_video_list():
    """测试用户视频列表"""
    print("🧪 测试用户视频列表...")
    
    test_user_id = "list_test_user"
    user_context.set_user(test_user_id, "listuser")
    
    try:
        user_paths = user_context.get_paths()
        videos_dir = user_paths.get_user_videos_dir()
        
        # 创建一些模拟视频文件
        test_videos = [
            "video1.mp4",
            "video2.avi", 
            "video3.mov"
        ]
        
        for video_name in test_videos:
            video_path = videos_dir / video_name
            with open(video_path, 'wb') as f:
                f.write(b'fake video content')
        
        # 获取处理器和视频列表
        processor = IsolatedVideoProcessor()
        video_list = processor.get_user_video_list()
        
        # 验证结果
        assert len(video_list) == len(test_videos)
        
        filenames = [v["filename"] for v in video_list]
        for video_name in test_videos:
            assert video_name in filenames
        
        # 验证用户ID
        for video in video_list:
            assert video["user_id"] == test_user_id
        
        print("✅ 用户视频列表测试通过")
        
    finally:
        # 清理测试数据
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_transcript_saving():
    """测试转录文件保存（用户隔离）"""
    print("🧪 测试转录文件保存...")
    
    test_user_id = "transcript_test_user"
    user_context.set_user(test_user_id, "transcriptuser")
    
    try:
        processor = IsolatedVideoProcessor()
        user_paths = user_context.get_paths()
        
        # 创建模拟转录数据
        video_id = "test_video_123"
        transcript_data = {
            "text": "这是测试转录文本",
            "segments": [
                {"id": 0, "start": 0.0, "end": 5.0, "text": "第一段"},
                {"id": 1, "start": 5.0, "end": 10.0, "text": "第二段"}
            ],
            "language": "zh"
        }
        
        # 保存转录文件
        transcript_path = processor.save_transcript(video_id, transcript_data)
        
        # 验证文件保存到用户专属目录
        expected_path = user_paths.get_transcript_path(video_id)
        assert transcript_path == expected_path
        assert transcript_path.exists()
        
        # 验证文件内容
        with open(transcript_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["text"] == transcript_data["text"]
        assert len(saved_data["segments"]) == len(transcript_data["segments"])
        
        print("✅ 转录文件保存测试通过")
        
    finally:
        # 清理测试数据
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_processor_caching():
    """测试处理器缓存"""
    print("🧪 测试处理器缓存...")
    
    processor1 = get_isolated_processor(cuda_enabled=True, whisper_model="base")
    processor2 = get_isolated_processor(cuda_enabled=True, whisper_model="base")
    processor3 = get_isolated_processor(cuda_enabled=False, whisper_model="small")
    
    # 验证缓存机制
    assert processor1 is processor2  # 相同配置应该返回同一实例
    assert processor1 is not processor3  # 不同配置应该返回不同实例
    
    assert processor1.cuda_enabled == True
    assert processor1.whisper_model == "base"
    assert processor3.cuda_enabled == False
    assert processor3.whisper_model == "small"
    
    print("✅ 处理器缓存测试通过")


def run_stage2_tests():
    """运行第二阶段所有测试"""
    print("🚀 开始第二阶段测试：视频处理流程隔离\n")
    
    try:
        test_video_processor_init()
        print()
        test_user_video_upload()
        print()
        test_user_video_isolation()
        print()
        test_user_video_list()
        print()
        test_transcript_saving()
        print()
        test_processor_caching()
        print()
        
        print("🎉 第二阶段所有测试通过！")
        print("✅ 视频处理器隔离实现完成")
        print("✅ 用户专属文件路径实现完成")
        print("✅ 视频文件隔离机制实现完成")
        print("✅ 转录文件隔离实现完成")
        print("✅ 处理器缓存机制实现完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage2_tests()
    sys.exit(0 if success else 1)