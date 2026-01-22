#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段3：对话链系统重构测试
测试对话链系统的用户隔离功能
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.qa.conversation_chain import ConversationChain
from modules.qa.memory import Memory
from modules.qa.prompt import PromptTemplate
from deploy.utils.user_context import user_context
from deploy.utils.path_manager import get_path_manager


def create_test_conversation_chain(user_id: str = None, session_id: str = None):
    """创建测试用对话链"""
    # 创建模拟的检索器
    mock_retriever = MagicMock()
    mock_retriever.search.return_value = []
    
    # 创建记忆管理器
    memory = Memory("buffer", user_id)
    
    # 创建提示模板
    prompt_template = PromptTemplate()
    
    # 创建对话链
    chain = ConversationChain(
        retriever=mock_retriever,
        memory=memory,
        prompt_template=prompt_template,
        session_id=session_id,
        user_id=user_id
    )
    
    return chain


def test_conversation_chain_creation():
    """测试对话链创建"""
    print("🧪 测试对话链创建...")
    
    try:
        # 测试共享对话链
        chain1 = create_test_conversation_chain()
        assert chain1.memory.user_id is None
        assert not chain1.memory.is_isolated
        print("✅ 共享对话链创建成功")
        
        # 测试用户隔离对话链
        chain2 = create_test_conversation_chain("test_user")
        assert chain2.memory.user_id == "test_user"
        assert chain2.memory.is_isolated
        print("✅ 用户隔离对话链创建成功")
        
        print("✅ 对话链创建测试通过")
        
    except Exception as e:
        print(f"❌ 对话链创建失败: {e}")
        raise


def test_conversation_session_isolation():
    """测试对话会话隔离"""
    print("🧪 测试对话会话隔离...")
    
    try:
        # 创建两个不同用户的对话链
        chain1 = create_test_conversation_chain("user1", "session1")
        chain2 = create_test_conversation_chain("user2", "session1")  # 相同session_id，不同用户
        
        # 测试会话路径隔离
        path1 = chain1.sessions_dir
        path2 = chain2.sessions_dir
        
        print(f"调试: user1 sessions_dir = {path1}")
        print(f"调试: user2 sessions_dir = {path2}")
        
        # 验证路径不同
        assert path1 != path2, f"路径相同: {path1} == {path2}"
        
        # 验证路径包含用户ID
        assert "user1" in str(path1), f"user1路径不包含user1: {path1}"
        assert "user2" in str(path2), f"user2路径不包含user2: {path2}"
        
        print("✅ 对话会话隔离测试通过")
        
    except Exception as e:
        print(f"❌ 对话会话隔离失败: {e}")
        raise


def test_conversation_persistence_isolation():
    """测试对话持久化隔离"""
    print("🧪 测试对话持久化隔离...")
    
    try:
        # 创建两个不同用户的对话链
        chain1 = create_test_conversation_chain("user1", "test_session")
        chain2 = create_test_conversation_chain("user2", "test_session")
        
        # 设置视频信息
        chain1.set_video_info("test_video1.mp4", 120.0, "zh")
        chain2.set_video_info("test_video2.mp4", 150.0, "zh")
        
        # 创建会话
        transcript = [{"text": "测试转录内容", "start": 0.0, "end": 5.0}]
        chain1.create_session(transcript)
        chain2.create_session(transcript)
        
        # 添加对话历史到用户1
        from modules.qa.conversation_data import ConversationTurn
        turn = ConversationTurn(
            turn_id=1,
            user_query="用户1的问题"
        )
        turn.response = "用户1的回答"
        chain1.conversation_history.append(turn)
        
        # 保存用户1的会话
        result = chain1.save_session()
        assert result == True
        
        # 验证文件分离
        user1_session_file = chain1.sessions_dir / "test_session.json"
        user2_session_file = chain2.sessions_dir / "test_session.json"
        
        assert user1_session_file.exists()
        
        # 验证文件内容隔离
        with open(user1_session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        assert session_data['session_id'] == "test_session"
        assert session_data['video_info']['filename'] == "test_video1.mp4"
        
        print("✅ 对话持久化隔离测试通过")
        
    except Exception as e:
        print(f"❌ 对话持久化隔离失败: {e}")
        raise


def test_conversation_context_integration():
    """测试对话链与用户上下文集成"""
    print("🧪 测试对话链与用户上下文集成...")
    
    try:
        # 设置用户上下文
        user_context.set_user("test_user", "测试用户")
        
        # 创建对话链（应该自动使用当前用户）
        chain = create_test_conversation_chain()
        
        # 验证用户隔离
        assert chain.memory.user_id == "test_user"
        assert chain.memory.is_isolated
        
        # 验证路径管理器集成
        paths = get_path_manager("test_user")
        expected_sessions_dir = paths.get_conversations_dir() / "sessions"
        assert chain.sessions_dir == expected_sessions_dir
        
        print("✅ 对话链与用户上下文集成测试通过")
        
    finally:
        user_context.clear_user()


def test_conversation_multi_user():
    """测试多用户对话功能"""
    print("🧪 测试多用户对话功能...")
    
    try:
        # 创建多个用户的对话链
        chains = {}
        for user_id in ["user1", "user2", "user3"]:
            chains[user_id] = create_test_conversation_chain(user_id, f"session_{user_id}")
        
        # 为每个用户设置视频信息和创建会话
        for user_id, chain in chains.items():
            chain.set_video_info(f"video_{user_id}.mp4", 100.0, "zh")
            transcript = [{"text": f"{user_id}的转录内容", "start": 0.0, "end": 5.0}]
            chain.create_session(transcript)
            
            # 添加对话历史
            from modules.qa.conversation_data import ConversationTurn
            turn = ConversationTurn(
                turn_id=1,
                user_query=f"{user_id}的问题"
            )
            turn.response = f"{user_id}的回答"
            chain.conversation_history.append(turn)
            chain.save_session()
        
        # 验证每个用户的会话独立
        for user_id, chain in chains.items():
            session_file = chain.sessions_dir / f"session_{user_id}.json"
            assert session_file.exists()
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            assert session_data['session_id'] == f"session_{user_id}"
            assert len(session_data['conversation_history']) == 1
            assert session_data['conversation_history'][0]['user_query'] == f"{user_id}的问题"
        
        print("✅ 多用户对话功能测试通过")
        
    except Exception as e:
        print(f"❌ 多用户对话功能测试失败: {e}")
        raise


def test_conversation_memory_integration():
    """测试对话链与记忆系统集成"""
    print("🧪 测试对话链与记忆系统集成...")
    
    try:
        # 创建用户隔离的对话链
        chain = create_test_conversation_chain("test_user")
        
        # 添加记忆项到记忆系统
        memory_item_id = chain.memory.add_memory_item(
            "测试记忆内容", 
            "conversation", 
            ["test"], 
            {"test": True}
        )
        
        # 验证记忆项在用户隔离的记忆系统中
        retrieved_item = chain.memory.get_memory_item(memory_item_id)
        assert retrieved_item is not None
        assert retrieved_item.content == "测试记忆内容"
        
        # 验证记忆路径隔离
        assert chain.memory.is_isolated
        assert chain.memory.user_id == "test_user"
        
        print("✅ 对话链与记忆系统集成测试通过")
        
    except Exception as e:
        print(f"❌ 对话链与记忆系统集成测试失败: {e}")
        raise


def run_stage3_tests():
    """运行阶段3所有测试"""
    print("🚀 开始第三阶段测试：对话链系统重构\n")
    
    test_functions = [
        test_conversation_chain_creation,
        test_conversation_session_isolation,
        test_conversation_persistence_isolation,
        test_conversation_context_integration,
        test_conversation_multi_user,
        test_conversation_memory_integration
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
    
    print(f"🎉 第三阶段测试完成！")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed == 0:
        print("\n🎊 所有对话链系统重构测试通过！")
        print("✅ 对话链创建和使用正常")
        print("✅ 用户隔离对话系统工作正常")
        print("✅ 对话持久化隔离成功")
        print("✅ 用户上下文集成成功")
        print("✅ 多用户对话功能正常")
        print("✅ 对话链与记忆系统集成成功")
    
    return failed == 0


if __name__ == "__main__":
    run_stage3_tests()
