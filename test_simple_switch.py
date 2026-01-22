#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的用户切换测试
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_basic_user_context():
    """测试基本用户上下文"""
    print("测试基本用户上下文...")
    
    try:
        from deploy.utils.user_context import user_context
        
        # 测试用户设置
        user_context.set_user("user_a", "用户A")
        current_id = user_context.get_current_user_id()
        print(f"当前用户ID: {current_id}")
        
        # 清理
        user_context.clear_user()
        current_id_after = user_context.get_current_user_id()
        print(f"清理后用户ID: {current_id_after}")
        
        return True
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_manager():
    """测试对话管理器"""
    print("\n测试对话管理器...")
    
    try:
        from deploy.core.conversation_manager_isolated import get_conversation_manager
        from deploy.utils.user_context import user_context
        
        conversation_manager = get_conversation_manager()
        print(f"对话管理器类型: {type(conversation_manager)}")
        
        # 设置用户
        user_context.set_user("test_user", "测试用户")
        
        # 创建对话链
        chain = conversation_manager.create_conversation_chain("test_video")
        print(f"对话链创建: {chain is not None}")
        
        # 检查缓存
        chains_count = len(conversation_manager.conversation_chains)
        print(f"缓存中的对话链数量: {chains_count}")
        
        # 清理
        user_context.clear_user()
        conversation_manager.conversation_chains.clear()
        
        return True
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始简化测试...")
    
    tests = [
        test_basic_user_context,
        test_conversation_manager
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
    
    print(f"\n结果: {passed}/{len(tests)} 通过")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)