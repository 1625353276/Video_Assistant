#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段4：文件管理系统重构测试
测试文件管理系统的用户隔离功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.utils.file_manager import FileManager
from deploy.utils.user_context import user_context
from deploy.utils.path_manager import get_path_manager


def create_test_file_manager(user_id: str = None):
    """创建测试用文件管理器"""
    return FileManager(user_id=user_id)


def test_file_manager_creation():
    """测试文件管理器创建"""
    print("🧪 测试文件管理器创建...")
    
    try:
        # 测试共享文件管理器
        fm1 = create_test_file_manager()
        assert fm1.user_id is None
        assert not fm1.is_isolated
        print("✅ 共享文件管理器创建成功")
        
        # 测试用户隔离文件管理器
        fm2 = create_test_file_manager("test_user")
        assert fm2.user_id == "test_user"
        assert fm2.is_isolated
        print("✅ 用户隔离文件管理器创建成功")
        
        print("✅ 文件管理器创建测试通过")
        
    except Exception as e:
        print(f"❌ 文件管理器创建失败: {e}")
        raise


def test_file_path_isolation():
    """测试文件路径隔离"""
    print("🧪 测试文件路径隔离...")
    
    try:
        # 创建两个不同用户的文件管理器
        fm1 = create_test_file_manager("user1")
        fm2 = create_test_file_manager("user2")
        
        # 测试转录目录隔离
        transcript_dir1 = fm1.get_transcripts_dir()
        transcript_dir2 = fm2.get_transcripts_dir()
        
        # 验证路径不同
        assert transcript_dir1 != transcript_dir2
        
        # 验证路径包含用户ID
        assert "user1" in str(transcript_dir1)
        assert "user2" in str(transcript_dir2)
        
        # 测试视频目录隔离
        video_dir1 = fm1.get_videos_dir()
        video_dir2 = fm2.get_videos_dir()
        
        assert video_dir1 != video_dir2
        assert "user1" in str(video_dir1)
        assert "user2" in str(video_dir2)
        
        print("✅ 文件路径隔离测试通过")
        
    except Exception as e:
        print(f"❌ 文件路径隔离失败: {e}")
        raise


def test_transcript_file_isolation():
    """测试转录文件隔离"""
    print("🧪 测试转录文件隔离...")
    
    try:
        # 创建两个不同用户的文件管理器
        fm1 = create_test_file_manager("user1")
        fm2 = create_test_file_manager("user2")
        
        # 准备测试数据
        transcript_data = {
            "video_filename": "test_video.mp4",
            "duration": 120.0,
            "segments": [
                {"text": "测试内容", "start": 0.0, "end": 5.0}
            ]
        }
        
        # 保存转录文件到用户1
        output_path1 = fm1.get_transcripts_dir() / "test_transcript.json"
        fm1.save_transcript_json(transcript_data, output_path1)
        
        # 验证文件存在
        assert output_path1.exists()
        
        # 验证用户2的目录中没有这个文件
        output_path2 = fm2.get_transcripts_dir() / "test_transcript.json"
        assert not output_path2.exists()
        
        # 验证文件内容
        loaded_data = fm1.load_transcript_json(output_path1)
        assert loaded_data["video_filename"] == "test_video.mp4"
        
        print("✅ 转录文件隔离测试通过")
        
    except Exception as e:
        print(f"❌ 转录文件隔离失败: {e}")
        raise


def test_video_file_isolation():
    """测试视频文件隔离"""
    print("🧪 测试视频文件隔离...")
    
    try:
        # 创建两个不同用户的文件管理器
        fm1 = create_test_file_manager("user1")
        fm2 = create_test_file_manager("user2")
        
        # 模拟视频文件上传
        video_content = b"fake video content"
        video_filename = "test_video.mp4"
        
        # 保存视频文件到用户1
        video_path1 = fm1.get_videos_dir() / video_filename
        video_path1.write_bytes(video_content)
        
        # 验证文件存在
        assert video_path1.exists()
        
        # 验证用户2的目录中没有这个文件
        video_path2 = fm2.get_videos_dir() / video_filename
        assert not video_path2.exists()
        
        # 验证文件列表隔离
        user1_videos = list(fm1.get_videos_dir().glob("*.mp4"))
        user2_videos = list(fm2.get_videos_dir().glob("*.mp4"))
        
        assert len(user1_videos) == 1
        assert len(user2_videos) == 0
        
        print("✅ 视频文件隔离测试通过")
        
    except Exception as e:
        print(f"❌ 视频文件隔离失败: {e}")
        raise


def test_file_manager_context_integration():
    """测试文件管理器与用户上下文集成"""
    print("🧪 测试文件管理器与用户上下文集成...")
    
    try:
        # 设置用户上下文
        user_context.set_user("test_user", "测试用户")
        
        # 创建文件管理器（应该自动使用当前用户）
        fm = FileManager()  # 不传user_id，让它自动获取
        
        # 验证用户隔离
        assert fm.user_id == "test_user"
        assert fm.is_isolated
        
        # 验证路径管理器集成
        paths = get_path_manager("test_user")
        expected_transcripts_dir = paths.get_transcripts_dir()
        assert fm.get_transcripts_dir() == expected_transcripts_dir
        
        print("✅ 文件管理器与用户上下文集成测试通过")
        
    finally:
        user_context.clear_user()


def test_file_cleanup_isolation():
    """测试文件清理隔离"""
    print("🧪 测试文件清理隔离...")
    
    try:
        # 创建两个不同用户的文件管理器
        fm1 = create_test_file_manager("user1")
        fm2 = create_test_file_manager("user2")
        
        # 清理之前的测试文件
        fm1.cleanup_transcripts()
        fm2.cleanup_transcripts()
        
        # 为每个用户创建一些文件
        for i in range(3):
            # 用户1的文件
            file1 = fm1.get_transcripts_dir() / f"transcript_{i}.json"
            file1.write_text(f"user1 transcript {i}")
            
            # 用户2的文件
            file2 = fm2.get_transcripts_dir() / f"transcript_{i}.json"
            file2.write_text(f"user2 transcript {i}")
        
        # 验证文件存在
        user1_files = list(fm1.get_transcripts_dir().glob("*.json"))
        user2_files = list(fm2.get_transcripts_dir().glob("*.json"))
        print(f"调试: 清理前 user1文件数={len(user1_files)}, user2文件数={len(user2_files)}")
        assert len(user1_files) == 3
        assert len(user2_files) == 3
        
        # 清理用户1的文件
        fm1.cleanup_transcripts()
        
        # 验证只有用户1的文件被清理
        user1_files_after = list(fm1.get_transcripts_dir().glob("*.json"))
        user2_files_after = list(fm2.get_transcripts_dir().glob("*.json"))
        print(f"调试: 清理后 user1文件数={len(user1_files_after)}, user2文件数={len(user2_files_after)}")
        assert len(user1_files_after) == 0
        assert len(user2_files_after) == 3
        
        print("✅ 文件清理隔离测试通过")
        
    except Exception as e:
        print(f"❌ 文件清理隔离失败: {e}")
        raise


def run_stage4_tests():
    """运行阶段4所有测试"""
    print("🚀 开始第四阶段测试：文件管理系统重构\n")
    
    test_functions = [
        test_file_manager_creation,
        test_file_path_isolation,
        test_transcript_file_isolation,
        test_video_file_isolation,
        test_file_manager_context_integration,
        test_file_cleanup_isolation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 失败: {e}")
            failed += 1
        print()
    
    print(f"🎉 第四阶段测试完成！")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed == 0:
        print("\n🎊 所有文件管理系统重构测试通过！")
        print("✅ 文件管理器创建和使用正常")
        print("✅ 用户隔离文件系统工作正常")
        print("✅ 转录文件隔离成功")
        print("✅ 视频文件隔离成功")
        print("✅ 用户上下文集成成功")
        print("✅ 文件清理隔离成功")
    
    return failed == 0


if __name__ == "__main__":
    run_stage4_tests()