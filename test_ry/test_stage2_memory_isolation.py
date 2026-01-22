#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二阶段测试：记忆管理系统重构

测试用户隔离的记忆管理系统
"""

import sys
import os
import tempfile
import shutil
import pickle
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.qa.memory import Memory, MemoryItem
from deploy.utils.user_context import user_context
from deploy.utils.path_manager import get_path_manager


def create_test_memory_item(item_id: str, content: str, item_type: str = "conversation"):
    """创建测试记忆项"""
    return MemoryItem(
        item_id=item_id,
        content=content,
        item_type=item_type,
        importance=1.0,
        tags=["test"],
        metadata={"test": True}
    )


def test_memory_creation():
    """测试记忆管理器创建"""
    print("🧪 测试记忆管理器创建...")
    
    try:
        # 测试共享记忆管理器
        shared_memory = Memory("buffer")
        assert shared_memory.memory_type == "buffer"
        assert not shared_memory.is_isolated
        assert shared_memory.user_id is None
        print("✅ 共享记忆管理器创建成功")
        
        # 测试用户隔离记忆管理器
        user_memory = Memory("buffer", "test_user_123")
        assert user_memory.memory_type == "buffer"
        assert user_memory.is_isolated
        assert user_memory.user_id == "test_user_123"
        print("✅ 用户隔离记忆管理器创建成功")
        
    except Exception as e:
        print(f"❌ 记忆管理器创建失败: {e}")
        raise


def test_memory_path_isolation():
    """测试记忆路径隔离"""
    print("🧪 测试记忆路径隔离...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Mock项目根目录
        with patch('modules.qa.memory.settings') as mock_settings:
            mock_settings.MEMORY_DIR = temp_dir / "data" / "memory"
            
            # 创建两个用户的记忆管理器
            memory1 = Memory("buffer", "user1")
            memory2 = Memory("buffer", "user2")
            
            # 验证路径隔离
            assert memory1.storage_path != memory2.storage_path
            assert "user1" in str(memory1.storage_path)
            assert "user2" in str(memory2.storage_path)
            
            print("✅ 记忆路径隔离测试通过")
            
    finally:
        shutil.rmtree(temp_dir)


def test_memory_persistence_isolation():
    """测试记忆持久化隔离"""
    print("🧪 测试记忆持久化隔离...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Mock项目根目录
        with patch('modules.qa.memory.settings') as mock_settings:
            mock_settings.MEMORY_DIR = temp_dir / "data" / "memory"
            
            # 创建用户记忆管理器
            memory1 = Memory("buffer", "user1")
            memory2 = Memory("buffer", "user2")
            
            # 添加记忆项
            item1_id = memory1.add_memory_item("用户1的内容", "conversation", ["test"], {"test": True})
            item2_id = memory2.add_memory_item("用户2的内容", "conversation", ["test"], {"test": True})
            
            # 保存记忆
            memory1._save_memory()
            memory2._save_memory()
            
            # 验证文件分离
            user1_file = memory1.storage_path / "memory_buffer_user1.pkl"
            user2_file = memory2.storage_path / "memory_buffer_user2.pkl"
            
            assert user1_file.exists()
            assert user2_file.exists()
            assert user1_file != user2_file
            
            # 验证数据内容
            with open(user1_file, 'rb') as f:
                data1 = pickle.load(f)
                assert data1['user_id'] == "user1"
                assert len(data1['memory_items']) == 1
                assert data1['memory_items'][0]['content'] == "用户1的内容"
            
            with open(user2_file, 'rb') as f:
                data2 = pickle.load(f)
                assert data2['user_id'] == "user2"
                assert len(data2['memory_items']) == 1
                assert data2['memory_items'][0]['content'] == "用户2的内容"
            
            print("✅ 记忆持久化隔离测试通过")
            
    finally:
        shutil.rmtree(temp_dir)


def test_memory_item_management():
    """测试记忆项管理"""
    print("🧪 测试记忆项管理...")
    
    try:
        memory = Memory("buffer", "test_user")
        
        # 清理之前的测试数据
        memory.clear()
        
        # 添加记忆项
        item1_id = memory.add_memory_item("内容1", "conversation", ["test"], {"test": True})
        item2_id = memory.add_memory_item("内容2", "conversation", ["test"], {"test": True})
        
        # 验证记忆项数量
        print(f"调试: memory_items长度={len(memory.memory_items)}, buffer_size={memory.buffer_size}, total_items={memory.total_items}")
        print(f"调试: 记忆项列表={[item.content for item in memory.memory_items]}")
        assert len(memory.memory_items) == 2
        assert memory.total_items == 2
        
        # 测试检索
        retrieved_item1 = memory.get_memory_item(item1_id)
        assert retrieved_item1 is not None
        assert retrieved_item1.content == "内容1"
        
        # 测试删除
        result = memory.delete_memory_item(item1_id)
        assert result is True
        assert memory.get_memory_item(item1_id) is None
        assert len(memory.memory_items) == 1
        
        print("✅ 记忆项管理测试通过")
        
    except Exception as e:
        print(f"❌ 记忆项管理失败: {e}")
        raise


def test_conversation_buffer():
    """测试对话缓冲区"""
    print("🧪 测试对话缓冲区...")
    
    try:
        memory = Memory("buffer", "test_user")
        
        # 清理之前的测试数据
        memory.clear()
        
        # 模拟对话轮次
        from modules.qa.conversation_data import ConversationTurn
        
        turn1 = ConversationTurn(
            turn_id=1,
            user_query="用户消息1"
        )
        
        turn2 = ConversationTurn(
            turn_id=2,
            user_query="用户消息2"
        )
        
        memory.add_conversation_turn(turn1)
        memory.add_conversation_turn(turn2)
        
        # 验证对话缓冲区
        assert len(memory.conversation_buffer) == 2
        assert memory.total_conversations == 2
        
        # 测试清空缓冲区
        memory.conversation_buffer.clear()
        memory.total_conversations = 0
        assert len(memory.conversation_buffer) == 0
        
        print("✅ 对话缓冲区测试通过")
        
    except Exception as e:
        print(f"❌ 对话缓冲区测试失败: {e}")
        raise


def test_memory_search():
    """测试记忆搜索功能"""
    print("🧪 测试记忆搜索功能...")
    
    try:
        memory = Memory("buffer", "test_user")
        
        # 清理之前的测试数据
        memory.clear()
        
        # 添加多个记忆项
        item_ids = [
            memory.add_memory_item("人工智能", "conversation", ["ai"]),
            memory.add_memory_item("机器学习", "conversation", ["ml"]),
            memory.add_memory_item("深度学习", "knowledge", ["dl"]),
            memory.add_memory_item("神经网络", "knowledge", ["nn"])
        ]
        
        # 测试内容搜索
        results = memory.search_memory("人工智能")
        assert len(results) == 1
        assert results[0].content == "人工智能"
        
        # 测试标签搜索
        results = memory.get_memory_by_tags(["ai"])
        assert len(results) == 1
        
        # 测试类型搜索
        results = memory.search_memory("", item_type="conversation")
        assert len(results) == 2
        
        print("✅ 记忆搜索功能测试通过")
        
    except Exception as e:
        print(f"❌ 记忆搜索功能测试失败: {e}")
        raise


def test_user_context_memory_integration():
    """测试用户上下文集成"""
    print("🧪 测试用户上下文集成...")
    
    try:
        # 设置用户
        user_context.set_user("test_user", "testuser")
        
        # 创建记忆管理器（应该自动使用当前用户ID）
        memory = Memory()
        
        # 验证用户隔离
        assert memory.is_isolated
        assert memory.user_id == "test_user"
        
        # 添加记忆项
        item_id = memory.add_memory_item("用户内容", "conversation", ["test"], {"test": True})
        
        # 验证记忆项属于当前用户
        retrieved_item = memory.get_memory_item(item_id)
        assert retrieved_item is not None
        assert retrieved_item.content == "用户内容"
        
        print("✅ 用户上下文集成测试通过")
        
    finally:
        user_context.clear_user()


def test_memory_statistics():
    """测试记忆统计功能"""
    print("🧪 测试记忆统计功能...")
    
    try:
        memory = Memory("buffer", "test_user")
        
        # 清理之前的测试数据
        memory.clear()
        
        # 添加记忆项
        item_ids = [
            memory.add_memory_item("内容1", "conversation", ["test"]),
            memory.add_memory_item("内容2", "conversation", ["test"]),
            memory.add_memory_item("内容3", "conversation", ["test"])
        ]
        
        # 验证统计信息
        assert memory.total_items == 3
        assert memory.total_conversations == 0  # 没有对话缓冲区
        
        # 添加对话轮次
        from modules.qa.conversation_data import ConversationTurn
        turn = ConversationTurn(
            turn_id=1,
            user_query="测试对话"
        )
        memory.add_conversation_turn(turn)
        
        assert memory.total_conversations == 1
        
        print("✅ 记忆统计功能测试通过")
        
    except Exception as e:
        print(f"❌ 记忆统计功能测试失败: {e}")
        raise


def run_stage2_tests():
    """运行第二阶段所有测试"""
    print("🚀 开始第二阶段测试：记忆管理系统重构\n")
    
    try:
        test_memory_creation()
        print()
        test_memory_path_isolation()
        print()
        test_memory_persistence_isolation()
        print()
        test_memory_item_management()
        print()
        test_conversation_buffer()
        print()
        test_memory_search()
        print()
        test_user_context_memory_integration()
        print()
        test_memory_statistics()
        print()
        
        print("🎉 第二阶段所有测试通过！")
        print("✅ 记忆管理器创建和使用正常")
        print("✅ 用户隔离记忆系统工作正常")
        print("✅ 记忆持久化隔离成功")
        print("✅ 记忆项管理功能完整")
        print("✅ 对话缓冲区功能正常")
        print("✅ 记忆搜索功能正常")
        print("✅ 用户上下文集成成功")
        print("✅ 记忆统计功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage2_tests()
    sys.exit(0 if success else 1)