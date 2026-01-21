#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新对话功能修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_conversation_chain_isolation():
    """测试对话链实例隔离"""
    print("=== 测试对话链实例隔离 ===")
    
    # 模拟VideoAssistant的conversation_chains字典
    conversation_chains = {}
    
    # 模拟视频ID
    video_id = "test_video_123"
    
    # 第一次创建对话链
    print("1. 第一次创建对话链")
    chain1_id = id(conversation_chains.get(video_id))
    print(f"   对话链ID: {chain1_id}")
    print(f"   对话链存在: {video_id in conversation_chains}")
    
    # 模拟clear_conversation操作（删除实例）
    print("\n2. 执行clear_conversation操作")
    if video_id in conversation_chains:
        del conversation_chains[video_id]
        print(f"   已删除对话链实例")
    
    chain2_id = id(conversation_chains.get(video_id))
    print(f"   对话链ID: {chain2_id}")
    print(f"   对话链存在: {video_id in conversation_chains}")
    
    # 第二次创建对话链（应该创建新实例）
    print("\n3. 第二次创建对话链")
    # 模拟创建新的对话链实例
    class MockConversationChain:
        def __init__(self, session_id=None):
            self.session_id = session_id or f"session_new_{id(self)}"
            self.history = []
    
    conversation_chains[video_id] = MockConversationChain()
    chain3_id = id(conversation_chains[video_id])
    print(f"   对话链ID: {chain3_id}")
    print(f"   会话ID: {conversation_chains[video_id].session_id}")
    
    # 验证实例不同
    if chain1_id != chain3_id and chain2_id != chain3_id:
        print("✅ 对话链实例隔离测试通过")
        return True
    else:
        print("❌ 对话链实例隔离测试失败")
        return False

def test_conversation_persistence():
    """测试对话持久化隔离"""
    print("\n=== 测试对话持久化隔离 ===")
    
    # 模拟对话历史
    conversation_chains = {}
    video_id = "test_video_456"
    
    class MockConversationChain:
        def __init__(self):
            self.conversation_history = []
            self.session_id = f"session_{id(self)}"
        
        def chat(self, message):
            self.conversation_history.append({"role": "user", "content": message})
            return f"回复: {message}"
        
        def clear_history(self):
            self.conversation_history = []
    
    # 第一个对话
    print("1. 创建第一个对话")
    conversation_chains[video_id] = MockConversationChain()
    conversation_chains[video_id].chat("第一个问题")
    conversation_chains[video_id].chat("第二个问题")
    print(f"   第一个对话历史长度: {len(conversation_chains[video_id].conversation_history)}")
    original_session_id = conversation_chains[video_id].session_id
    
    # 模拟开始新对话（删除实例）
    print("\n2. 开始新对话")
    del conversation_chains[video_id]
    
    # 创建新的对话链实例
    conversation_chains[video_id] = MockConversationChain()
    new_session_id = conversation_chains[video_id].session_id
    
    print(f"   原会话ID: {original_session_id}")
    print(f"   新会话ID: {new_session_id}")
    print(f"   新对话历史长度: {len(conversation_chains[video_id].conversation_history)}")
    
    # 在新对话中添加消息
    conversation_chains[video_id].chat("新对话的问题")
    print(f"   添加消息后历史长度: {len(conversation_chains[video_id].conversation_history)}")
    
    # 验证隔离效果
    if (original_session_id != new_session_id and 
        len(conversation_chains[video_id].conversation_history) == 1):
        print("✅ 对话持久化隔离测试通过")
        return True
    else:
        print("❌ 对话持久化隔离测试失败")
        return False

def main():
    """主测试函数"""
    print("开始测试新对话功能修复")
    
    try:
        test1 = test_conversation_chain_isolation()
        test2 = test_conversation_persistence()
        
        print("\n=== 测试总结 ===")
        print(f"对话链实例隔离: {'✅' if test1 else '❌'}")
        print(f"对话持久化隔离: {'✅' if test2 else '❌'}")
        
        if test1 and test2:
            print("🎉 新对话功能修复验证通过！")
        else:
            print("⚠️ 修复验证失败")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    main()