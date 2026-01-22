#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第六阶段测试：路径系统重构

测试新的路径管理系统和用户上下文
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.path_manager import PathManager, get_path_manager, get_current_user_path_manager
from deploy.utils.user_context import user_context, get_current_user_paths, get_current_user_id


def test_path_manager_creation():
    """测试路径管理器创建"""
    print("🧪 测试路径管理器创建...")
    
    # 测试共享路径管理器
    shared_manager = PathManager()
    assert shared_manager.user_id is None
    assert not shared_manager.is_isolated
    assert shared_manager.base_path.name == "data"
    print("✅ 共享路径管理器创建成功")
    
    # 测试用户路径管理器
    user_manager = PathManager("test_user_123")
    assert user_manager.user_id == "test_user_123"
    assert user_manager.is_isolated
    assert user_manager.base_path.name == "test_user_123"
    assert "users" in str(user_manager.base_path)
    print("✅ 用户路径管理器创建成功")


def test_path_manager_directories():
    """测试路径管理器目录功能"""
    print("🧪 测试路径管理器目录功能...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建路径管理器并手动设置项目根目录
        manager = PathManager("test_user")
        original_root = manager.project_root
        manager.project_root = temp_dir
        
        try:
            # 测试各种目录路径
            expected_memory = temp_dir / "data/users/test_user/memory"
            expected_conversations = temp_dir / "data/users/test_user/conversations"
            expected_transcripts = temp_dir / "data/users/test_user/transcripts"
            expected_vectors = temp_dir / "data/users/test_user/vectors"
            expected_videos = temp_dir / "data/users/test_user/videos"
            expected_cache = temp_dir / "data/users/test_user/cache"
            expected_temp = temp_dir / "data/users/test_user/temp"
            expected_config = temp_dir / "data/users/test_user/config"
            
            assert manager.get_memory_dir() == expected_memory
            assert manager.get_conversations_dir() == expected_conversations
            assert manager.get_transcripts_dir() == expected_transcripts
            assert manager.get_vectors_dir() == expected_vectors
            assert manager.get_videos_dir() == expected_videos
            assert manager.get_cache_dir() == expected_cache
            assert manager.get_temp_dir() == expected_temp
            assert manager.get_config_dir() == expected_config
            
            print("✅ 目录路径测试通过")
        finally:
            manager.project_root = original_root
    finally:
        shutil.rmtree(temp_dir)


def test_path_manager_file_paths():
    """测试路径管理器文件路径功能"""
    print("🧪 测试路径管理器文件路径功能...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建路径管理器并手动设置项目根目录
        manager = PathManager("test_user")
        original_root = manager.project_root
        manager.project_root = temp_dir
        
        try:
            # 测试文件路径
            assert manager.get_memory_buffer_path() == temp_dir / "data/users/test_user/memory/memory_buffer.pkl"
            assert manager.get_conversation_path("video_123") == temp_dir / "data/users/test_user/conversations/video_123_conversation_history.json"
            assert manager.get_transcript_path("video_123") == temp_dir / "data/users/test_user/transcripts/video_123_transcript.json"
            assert manager.get_vector_index_path("video_123") == temp_dir / "data/users/test_user/vectors/video_123_vector_index.pkl"
            assert manager.get_bm25_index_path("video_123") == temp_dir / "data/users/test_user/vectors/video_123_bm25_index.pkl"
            
            print("✅ 文件路径测试通过")
        finally:
            manager.project_root = original_root
    finally:
        shutil.rmtree(temp_dir)


def test_path_manager_ensure_directories():
    """测试目录创建功能"""
    print("🧪 测试目录创建功能...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建路径管理器并手动设置项目根目录
        manager = PathManager("test_user")
        original_root = manager.project_root
        manager.project_root = temp_dir
        
        try:
            # 确保目录存在
            manager.ensure_directories()
            
            # 验证目录已创建
            assert (temp_dir / "data/users/test_user/memory").exists()
            assert (temp_dir / "data/users/test_user/conversations").exists()
            assert (temp_dir / "data/users/test_user/transcripts").exists()
            assert (temp_dir / "data/users/test_user/vectors").exists()
            assert (temp_dir / "data/users/test_user/videos").exists()
            assert (temp_dir / "data/users/test_user/cache").exists()
            assert (temp_dir / "data/users/test_user/temp").exists()
            assert (temp_dir / "data/users/test_user/config").exists()
            
            print("✅ 目录创建测试通过")
        finally:
            manager.project_root = original_root
    finally:
        shutil.rmtree(temp_dir)


def test_path_manager_caching():
    """测试路径管理器缓存"""
    print("🧪 测试路径管理器缓存...")
    
    # 获取相同用户ID的路径管理器
    manager1 = get_path_manager("test_user")
    manager2 = get_path_manager("test_user")
    
    # 应该是同一个实例（缓存）
    assert manager1 is manager2
    print("✅ 路径管理器缓存测试通过")


def test_user_context_integration():
    """测试用户上下文集成"""
    print("🧪 测试用户上下文集成...")
    
    try:
        # 设置用户
        user_context.set_user("test_user", "testuser")
        
        # 验证用户设置
        assert get_current_user_id() == "test_user"
        
        # 获取路径管理器
        paths = get_current_user_paths()
        assert paths is not None
        assert isinstance(paths, PathManager)
        assert paths.user_id == "test_user"
        
        # 验证目录已创建
        assert paths.get_memory_dir().exists()
        assert paths.get_conversations_dir().exists()
        
        print("✅ 用户上下文集成测试通过")
    finally:
        user_context.clear_user()


def test_user_isolation():
    """测试用户隔离"""
    print("🧪 测试用户隔离...")
    
    try:
        # 设置第一个用户
        user_context.set_user("user_1", "user1")
        paths1 = get_current_user_paths()
        
        # 设置第二个用户
        user_context.set_user("user_2", "user2")
        paths2 = get_current_user_paths()
        
        # 验证路径隔离
        assert paths1.base_path != paths2.base_path
        assert "user_1" in str(paths1.base_path)
        assert "user_2" in str(paths2.base_path)
        
        print("✅ 用户隔离测试通过")
    finally:
        user_context.clear_user()


def test_path_manager_utility_methods():
    """测试路径管理器工具方法"""
    print("🧪 测试路径管理器工具方法...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建路径管理器并手动设置项目根目录
        manager = PathManager("test_user")
        original_root = manager.project_root
        manager.project_root = temp_dir
        
        try:
            # 测试相对路径
            full_path = manager.get_memory_dir() / "test.pkl"
            relative_path = manager.get_relative_path(full_path)
            assert "data/users/test_user/memory/test.pkl" in relative_path
            
            # 测试字符串表示
            str_repr = str(manager)
            assert "test_user" in str_repr
            assert "PathManager" in str_repr
            
            print("✅ 工具方法测试通过")
        finally:
            manager.project_root = original_root
    finally:
        shutil.rmtree(temp_dir)


def test_current_user_path_manager():
    """测试当前用户路径管理器获取"""
    print("🧪 测试当前用户路径管理器获取...")
    
    try:
        # 未登录时应该返回None
        result = get_current_user_path_manager()
        assert result is None
        
        # 登录后应该返回路径管理器
        user_context.set_user("test_user", "testuser")
        result = get_current_user_path_manager()
        assert result is not None
        assert isinstance(result, PathManager)
        assert result.user_id == "test_user"
        
        print("✅ 当前用户路径管理器获取测试通过")
    finally:
        user_context.clear_user()


def run_stage6_tests():
    """运行第六阶段所有测试"""
    print("🚀 开始第六阶段测试：路径系统重构\n")
    
    try:
        test_path_manager_creation()
        print()
        test_path_manager_directories()
        print()
        test_path_manager_file_paths()
        print()
        test_path_manager_ensure_directories()
        print()
        test_path_manager_caching()
        print()
        test_user_context_integration()
        print()
        test_user_isolation()
        print()
        test_path_manager_utility_methods()
        print()
        test_current_user_path_manager()
        print()
        
        print("🎉 第六阶段所有测试通过！")
        print("✅ 路径管理器创建和使用正常")
        print("✅ 用户隔离路径系统工作正常")
        print("✅ 用户上下文集成成功")
        print("✅ 路径缓存机制正常")
        print("✅ 目录自动创建功能正常")
        print("✅ 工具方法功能完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage6_tests()
    sys.exit(0 if success else 1)