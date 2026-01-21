#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试对话功能修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_conversation_creation():
    """测试对话链创建"""
    print("=== 测试对话链创建 ===")
    
    try:
        # 测试导入
        from modules.qa.conversation_chain import ConversationChain
        print("✅ ConversationChain 导入成功")
        
        # 测试创建对话链
        chain = ConversationChain()
        print("✅ ConversationChain 创建成功")
        
        # 测试基本对话
        result = chain.chat("测试问题")
        print(f"✅ 基本对话成功: {result['response'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_video_assistant_creation():
    """测试VideoAssistant创建"""
    print("\n=== 测试VideoAssistant创建 ===")
    
    try:
        from deploy.app import VideoAssistant
        print("✅ VideoAssistant 导入成功")
        
        assistant = VideoAssistant()
        print("✅ VideoAssistant 创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试对话功能修复")
    
    test1 = test_conversation_creation()
    test2 = test_video_assistant_creation()
    
    print("\n=== 测试总结 ===")
    print(f"ConversationChain创建: {'✅' if test1 else '❌'}")
    print(f"VideoAssistant创建: {'✅' if test2 else '❌'}")
    
    if test1 and test2:
        print("🎉 对话功能修复验证通过！")
    else:
        print("⚠️ 对话功能仍有问题")

if __name__ == "__main__":
    main()