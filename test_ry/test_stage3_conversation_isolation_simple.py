#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三阶段测试：对话系统隔离（简化版）

测试用户隔离的对话管理和历史记录
"""

import sys
import os
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
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


def test_user_conversation_creation():
    """测试用户对话链创建"""
    print("🧪 测试用户对话链创建...")
    
    test_user_id = "conversation_test_user"
    user_context.set_user(test_user_id, "testuser")
    
    try:
        manager = IsolatedConversationManager()
        
        # Mock ConversationChain
        with patch('modules.qa.conversation_chain.ConversationChain') as mock_chain_class:
            mock_chain = Mock()
            mock_chain_class.return_value = mock_chain
            
            # 创建对话链
            video_id = "test_video_123"
            conversation = manager.create_conversation_chain(video_id)
            
            # 验证结果
            assert conversation is not None
            assert test_user_id in manager.conversation_chains
            assert video_id in manager.conversation_chains[test_user_id]
            
            print("✅ 用户对话链创建测试通过")
            
    finally:
        user_context.clear_user()


def test_conversation_history_saving():
    """测试对话历史保存"""
    print("🧪 测试对话历史保存...")
    
    test_user_id = "history_test_user"
    user_context.set_user(test_user_id, "historyuser")
    
    try:
        manager = IsolatedConversationManager()
        
        # Mock ConversationChain
        with patch('modules.qa.conversation_chain.ConversationChain') as mock_chain_class:
            mock_chain = Mock()
            mock_chain.save_conversation = Mock()
            mock_chain_class.return_value = mock_chain
            
            # 创建对话链并保存历史
            video_id = "history_video_456"
            manager.create_conversation_chain(video_id)
            manager.save_conversation_history(video_id)
            
            # 验证保存方法被调用
            mock_chain.save_conversation.assert_called_once()
            
            print("✅ 对话历史保存测试通过")
            
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_user_conversation_list():
    """测试用户对话列表"""
    print("🧪 测试用户对话列表...")
    
    test_user_id = "list_test_user"
    user_context.set_user(test_user_id, "listuser")
    
    try:
        user_paths = user_context.get_paths()
        conversations_dir = user_paths.get_user_conversations_dir()
        
        # 创建模拟对话文件
        conversation_data = {
            "session_id": "test_session",
            "created_at": datetime.now().isoformat(),
            "history": [
                {"role": "user", "content": "问题1"},
                {"role": "assistant", "content": "回答1"},
                {"role": "user", "content": "问题2"},
                {"role": "assistant", "content": "回答2"}
            ],
            "config": {}
        }
        
        conversation_file = conversations_dir / "video_1_conversation_history.json"
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        
        # 获取对话列表
        manager = IsolatedConversationManager()
        conversation_list = manager.get_user_conversation_list()
        
        # 验证结果
        assert len(conversation_list) == 1
        assert conversation_list[0]["video_id"] == "video_1"
        assert conversation_list[0]["user_id"] == test_user_id
        assert conversation_list[0]["message_count"] == 2
        
        print("✅ 用户对话列表测试通过")
        
    finally:
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_global_conversation_manager():
    """测试全局对话管理器"""
    print("🧪 测试全局对话管理器...")
    
    manager1 = get_conversation_manager()
    manager2 = get_conversation_manager()
    
    # 验证是同一个实例
    assert manager1 is manager2
    assert isinstance(manager1, IsolatedConversationManager)
    
    print("✅ 全局对话管理器测试通过")


def run_stage3_tests():
    """运行第三阶段所有测试"""
    print("🚀 开始第三阶段测试：对话系统隔离\n")
    
    try:
        test_conversation_manager_init()
        print()
        test_user_conversation_creation()
        print()
        test_conversation_history_saving()
        print()
        test_user_conversation_list()
        print()
        test_global_conversation_manager()
        print()
        
        print("🎉 第三阶段所有测试通过！")
        print("✅ 对话管理器隔离实现完成")
        print("✅ 用户对话历史隔离实现完成")
        print("✅ 对话链管理机制实现完成")
        print("✅ 全局管理器单例实现完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage3_tests()
    sys.exit(0 if success else 1)