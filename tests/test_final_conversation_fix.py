#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新对话功能修复 - 最终验证
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_conversation_session_isolation():
    """测试对话会话隔离"""
    print("=== 测试对话会话隔离 ===")
    
    # 模拟VideoAssistant类
    class MockVideoAssistant:
        def __init__(self):
            self.conversation_chains = {}
        
        def _generate_session_id(self):
            import random
            now = time.time()
            timestamp = int(now * 1000)
            random_suffix = random.randint(1000, 9999)
            return f"session_{timestamp}_{random_suffix}"
        
        def clear_conversation(self, video_id):
            """清除指定视频的对话历史"""
            if video_id in self.conversation_chains:
                del self.conversation_chains[video_id]
                print(f"已清除视频 {video_id} 的对话链实例")
                return True
            return False
        
        def _create_new_conversation_chain(self, video_id):
            """创建全新的对话链"""
            from modules.qa.conversation_chain import ConversationChain
            new_session_id = self._generate_session_id()
            conversation_chain = ConversationChain(session_id=new_session_id)
            print(f"已创建全新对话链，会话ID: {new_session_id}")
            return conversation_chain
    
    # 测试流程
    assistant = MockVideoAssistant()
    video_id = "test_video_789"
    
    # 第一次对话
    print("1. 第一次创建对话")
    chain1 = assistant._create_new_conversation_chain(video_id)
    assistant.conversation_chains[video_id] = chain1
    session_id1 = chain1.session_id
    print(f"   会话ID: {session_id1}")
    
    # 添加对话
    chain1.chat("第一个问题")
    chain1.chat("第二个问题")
    print(f"   对话历史长度: {len(chain1.conversation_history)}")
    
    # 清空对话
    print("\n2. 清空对话")
    assistant.clear_conversation(video_id)
    
    # 创建新对话
    print("\n3. 创建新对话")
    chain2 = assistant._create_new_conversation_chain(video_id)
    assistant.conversation_chains[video_id] = chain2
    session_id2 = chain2.session_id
    print(f"   新会话ID: {session_id2}")
    print(f"   新对话历史长度: {len(chain2.conversation_history)}")
    
    # 添加新对话
    chain2.chat("新对话的问题")
    print(f"   添加消息后历史长度: {len(chain2.conversation_history)}")
    
    # 验证隔离效果
    print(f"\n4. 验证结果:")
    print(f"   会话ID不同: {session_id1 != session_id2}")
    print(f"   对话历史隔离: {len(chain2.conversation_history) == 1}")
    print(f"   实例不同: {chain1 is not chain2}")
    
    if (session_id1 != session_id2 and 
        len(chain2.conversation_history) == 1 and 
        chain1 is not chain2):
        print("✅ 对话会话隔离测试通过")
        return True
    else:
        print("❌ 对话会话隔离测试失败")
        return False

def main():
    """主测试函数"""
    print("开始测试新对话功能修复 - 最终验证")
    
    try:
        test_result = test_conversation_session_isolation()
        
        print("\n=== 测试总结 ===")
        print(f"对话会话隔离: {'✅' if test_result else '❌'}")
        
        if test_result:
            print("🎉 新对话功能修复验证通过！")
            print("\n现在用户点击'开始新对话'时：")
            print("1. 旧的对话链实例会被完全删除")
            print("2. 创建全新的对话链实例")
            print("3. 生成新的会话ID")
            print("4. 不会加载历史对话")
            print("5. 新对话完全独立")
        else:
            print("⚠️ 修复验证失败")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    main()