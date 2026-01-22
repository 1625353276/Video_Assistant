#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一阶段测试：用户上下文管理

测试用户上下文管理器和路径管理器的功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.user_context import UserContext, UserPathManager, user_context, get_current_user_paths, get_current_user_id


def test_user_context():
    """测试用户上下文管理器"""
    print("🧪 测试用户上下文管理器...")
    
    # 创建测试用户上下文
    ctx = UserContext()
    
    # 测试初始状态
    assert ctx.get_current_user_id() is None
    assert not ctx.is_logged_in()
    assert ctx.get_paths() is None
    print("✅ 初始状态测试通过")
    
    # 测试设置用户
    test_user_id = "test_user_123"
    test_username = "testuser"
    ctx.set_user(test_user_id, test_username)
    
    assert ctx.get_current_user_id() == test_user_id
    assert ctx.is_logged_in()
    assert ctx.get_paths() is not None
    assert ctx.get_current_user_data()['username'] == test_username
    print("✅ 用户设置测试通过")
    
    # 测试清除用户
    ctx.clear_user()
    assert ctx.get_current_user_id() is None
    assert not ctx.is_logged_in()
    print("✅ 用户清除测试通过")
    
    print("✅ 用户上下文管理器测试完成")


def test_user_path_manager():
    """测试用户路径管理器"""
    print("🧪 测试用户路径管理器...")
    
    test_user_id = "test_user_456"
    path_manager = UserPathManager(test_user_id)
    
    # 测试基础路径
    expected_base = Path(f"data/users/{test_user_id}")
    assert path_manager.base_path == expected_base
    print("✅ 基础路径测试通过")
    
    # 测试目录创建
    assert path_manager.base_path.exists()
    assert (path_manager.base_path / "videos").exists()
    assert (path_manager.base_path / "transcripts").exists()
    assert (path_manager.base_path / "conversations").exists()
    assert (path_manager.base_path / "vectors").exists()
    print("✅ 目录创建测试通过")
    
    # 测试路径获取
    video_id = "video_789"
    filename = "test.mp4"
    
    upload_path = path_manager.get_upload_path(video_id, filename)
    assert upload_path.name == f"{video_id}.mp4"
    assert "videos" in str(upload_path)
    print("✅ 上传路径测试通过")
    
    transcript_path = path_manager.get_transcript_path(video_id)
    assert transcript_path.name == f"{video_id}_transcript.json"
    assert "transcripts" in str(transcript_path)
    print("✅ 转录路径测试通过")
    
    conversation_path = path_manager.get_conversation_path(video_id)
    assert conversation_path.name == f"{video_id}_conversation_history.json"
    assert "conversations" in str(conversation_path)
    print("✅ 对话路径测试通过")
    
    vector_path = path_manager.get_vector_index_path(video_id)
    assert vector_path.name == f"{video_id}_vector_index.pkl"
    assert "vectors" in str(vector_path)
    print("✅ 向量索引路径测试通过")
    
    # 清理测试数据
    shutil.rmtree(path_manager.base_path)
    print("✅ 测试数据清理完成")
    
    print("✅ 用户路径管理器测试完成")


def test_global_user_context():
    """测试全局用户上下文"""
    print("🧪 测试全局用户上下文...")
    
    # 确保初始状态
    user_context.clear_user()
    assert get_current_user_id() is None
    assert get_current_user_paths() is None
    print("✅ 全局初始状态测试通过")
    
    # 设置全局用户
    test_user_id = "global_test_user"
    user_context.set_user(test_user_id, "globaluser")
    
    assert get_current_user_id() == test_user_id
    paths = get_current_user_paths()
    assert paths is not None
    assert isinstance(paths, UserPathManager)
    print("✅ 全局用户设置测试通过")
    
    # 清理
    user_context.clear_user()
    shutil.rmtree(paths.base_path)
    print("✅ 全局测试数据清理完成")
    
    print("✅ 全局用户上下文测试完成")


def test_user_isolation():
    """测试用户隔离"""
    print("🧪 测试用户隔离...")
    
    # 创建两个用户
    user1_id = "user_isolation_1"
    user2_id = "user_isolation_2"
    
    ctx1 = UserContext()
    ctx2 = UserContext()
    
    ctx1.set_user(user1_id, "user1")
    ctx2.set_user(user2_id, "user2")
    
    paths1 = ctx1.get_paths()
    paths2 = ctx2.get_paths()
    
    # 测试路径隔离
    assert paths1.base_path != paths2.base_path
    assert str(paths1.base_path).endswith(user1_id)
    assert str(paths2.base_path).endswith(user2_id)
    print("✅ 用户路径隔离测试通过")
    
    # 测试文件隔离
    video_id = "isolation_test"
    path1 = paths1.get_transcript_path(video_id)
    path2 = paths2.get_transcript_path(video_id)
    
    assert path1 != path2
    assert user1_id in str(path1)
    assert user2_id in str(path2)
    print("✅ 文件路径隔离测试通过")
    
    # 清理测试数据
    shutil.rmtree(paths1.base_path)
    shutil.rmtree(paths2.base_path)
    print("✅ 隔离测试数据清理完成")
    
    print("✅ 用户隔离测试完成")


def run_stage1_tests():
    """运行第一阶段所有测试"""
    print("🚀 开始第一阶段测试：用户上下文管理\n")
    
    try:
        test_user_context()
        print()
        test_user_path_manager()
        print()
        test_global_user_context()
        print()
        test_user_isolation()
        print()
        
        print("🎉 第一阶段所有测试通过！")
        print("✅ 用户上下文管理器实现完成")
        print("✅ 路径管理器实现完成")
        print("✅ 用户隔离机制实现完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage1_tests()
    sys.exit(0 if success else 1)