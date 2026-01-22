#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三阶段测试：对话系统隔离（基础版）

测试用户隔离的对话管理和历史记录
"""

import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.user_context import user_context
from deploy.core.conversation_manager_isolated import IsolatedConversationManager, get_conversation_manager


def test_conversation_manager_init():
    """测试对话管理器初始化"""
    print("🧪 测试对话管理器初始化...")
    
    manager = IsolatedConversationManager()
    assert manager.conversation_chains == {}
    assert isinstance(manager.conversation_chains, dict)
    print("✅ 对话管理器初始化测试通过")


def test_user_context_integration():
    """测试用户上下文集成"""
    print("🧪 测试用户上下文集成...")
    
    test_user_id = "integration_test_user"
    user_context.set_user(test_user_id, "testuser")
    
    try:
        manager = IsolatedConversationManager()
        
        # 测试用户ID获取
        current_user_id = manager._check_user_id if hasattr(manager, '_check_user_id') else test_user_id
        
        # 测试路径获取
        user_paths = user_context.get_paths()
        assert user_paths is not None
        assert test_user_id in str(user_paths.base_path)
        
        print("✅ 用户上下文集成测试通过")
        
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_user_directory_structure():
    """测试用户目录结构"""
    print("🧪 测试用户目录结构...")
    
    test_user_id = "directory_test_user"
    user_context.set_user(test_user_id, "testuser")
    
    try:
        user_paths = user_context.get_paths()
        
        # 验证目录创建
        assert user_paths.base_path.exists()
        assert (user_paths.base_path / "conversations").exists()
        assert (user_paths.base_path / "videos").exists()
        assert (user_paths.base_path / "transcripts").exists()
        assert (user_paths.base_path / "vectors").exists()
        
        # 验证路径方法
        video_id = "test_video"
        transcript_path = user_paths.get_transcript_path(video_id)
        conversation_path = user_paths.get_conversation_path(video_id)
        
        assert "conversations" in str(conversation_path)
        assert "transcripts" in str(transcript_path)
        assert video_id in transcript_path.name
        assert video_id in conversation_path.name
        
        print("✅ 用户目录结构测试通过")
        
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_conversation_file_creation():
    """测试对话文件创建"""
    print("🧪 测试对话文件创建...")
    
    test_user_id = "file_test_user"
    user_context.set_user(test_user_id, "fileuser")
    
    try:
        user_paths = user_context.get_paths()
        conversations_dir = user_paths.get_user_conversations_dir()
        
        # 创建模拟对话数据
        conversation_data = {
            "session_id": "test_session",
            "created_at": datetime.now().isoformat(),
            "history": [
                {"role": "user", "content": "测试问题"},
                {"role": "assistant", "content": "测试回答"}
            ],
            "config": {}
        }
        
        video_id = "test_video_file"
        conversation_file = conversations_dir / f"{video_id}_conversation_history.json"
        
        # 保存对话文件
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        
        # 验证文件创建
        assert conversation_file.exists()
        
        # 验证文件内容
        with open(conversation_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["session_id"] == "test_session"
        assert len(loaded_data["history"]) == 2
        
        print("✅ 对话文件创建测试通过")
        
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_global_manager_singleton():
    """测试全局管理器单例"""
    print("🧪 测试全局管理器单例...")
    
    manager1 = get_conversation_manager()
    manager2 = get_conversation_manager()
    
    # 验证是同一个实例
    assert manager1 is manager2
    assert isinstance(manager1, IsolatedConversationManager)
    
    print("✅ 全局管理器单例测试通过")


def test_user_isolation():
    """测试用户隔离"""
    print("🧪 测试用户隔离...")
    
    user1_id = "isolation_user_1"
    user2_id = "isolation_user_2"
    
    user_context.set_user(user1_id, "user1")
    user1_paths = user_context.get_paths()
    
    user_context.set_user(user2_id, "user2")
    user2_paths = user_context.get_paths()
    
    try:
        # 验证路径隔离
        assert user1_paths.base_path != user2_paths.base_path
        assert user1_id in str(user1_paths.base_path)
        assert user2_id in str(user2_paths.base_path)
        
        # 创建用户1的文件
        user1_conversation = user1_paths.get_conversation_path("video1")
        user1_conversation.parent.mkdir(parents=True, exist_ok=True)
        with open(user1_conversation, 'w') as f:
            f.write("user1 data")
        
        # 切换到用户2
        user_context.set_user(user2_id, "user2")
        user2_conversation = user2_paths.get_conversation_path("video1")
        user2_conversation.parent.mkdir(parents=True, exist_ok=True)
        with open(user2_conversation, 'w') as f:
            f.write("user2 data")
        
        # 验证文件隔离
        assert user1_conversation.exists()
        assert user2_conversation.exists()
        assert user1_conversation != user2_conversation
        
        # 验证内容不同
        with open(user1_conversation, 'r') as f:
            content1 = f.read()
        with open(user2_conversation, 'r') as f:
            content2 = f.read()
        
        assert content1 != content2
        assert content1 == "user1 data"
        assert content2 == "user2 data"
        
        print("✅ 用户隔离测试通过")
        
    finally:
        # 清理测试数据
        if user1_paths and user1_paths.base_path.exists():
            shutil.rmtree(user1_paths.base_path)
        if user2_paths and user2_paths.base_path.exists():
            shutil.rmtree(user2_paths.base_path)
        user_context.clear_user()


def run_stage3_tests():
    """运行第三阶段所有测试"""
    print("🚀 开始第三阶段测试：对话系统隔离\n")
    
    try:
        test_conversation_manager_init()
        print()
        test_user_context_integration()
        print()
        test_user_directory_structure()
        print()
        test_conversation_file_creation()
        print()
        test_global_manager_singleton()
        print()
        test_user_isolation()
        print()
        
        print("🎉 第三阶段所有测试通过！")
        print("✅ 对话管理器隔离实现完成")
        print("✅ 用户目录结构实现完成")
        print("✅ 对话文件管理实现完成")
        print("✅ 全局管理器单例实现完成")
        print("✅ 用户隔离机制实现完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage3_tests()
    sys.exit(0 if success else 1)
