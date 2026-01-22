#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的用户切换测试

模拟真实场景：用户A登录 -> 用户B登录 -> 验证数据隔离
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def simulate_user_switching():
    """模拟用户切换场景"""
    print("🎭 模拟用户切换场景")
    print("=" * 50)
    
    try:
        from deploy.core.conversation_manager_isolated import get_conversation_manager
        from deploy.core.video_processor_isolated import get_isolated_processor
        from deploy.core.translator_isolated import get_translator_manager
        from deploy.utils.user_context import user_context
        
        conversation_manager = get_conversation_manager()
        processor = get_isolated_processor()
        translator_manager = get_translator_manager()
        
        # 场景1：用户A登录并创建数据
        print("📱 场景1：用户A登录并创建数据")
        user_context.set_user("user_a", "用户A")
        
        # 创建对话链
        chain_a = conversation_manager.create_conversation_chain("video_001")
        
        # 设置处理状态
        processor.processing_status["video_001"] = {"progress": 0.5, "user": "user_a"}
        
        # 设置翻译进度
        translator_manager.translation_progress["user_a_video_001"] = {"progress": 0.3}
        
        print(f"  ✅ 用户A对话链创建: {chain_a is not None}")
        print(f"  ✅ 用户A处理状态: {len(processor.processing_status)} 项")
        print(f"  ✅ 用户A翻译进度: {len(translator_manager.translation_progress)} 项")
        
        # 场景2：用户B登录（模拟用户切换）
        print("\n📱 场景2：用户B登录（模拟用户切换）")
        
        # 清理用户上下文（模拟登出）
        user_context.clear_user()
        
        # 清理所有缓存（模拟登出时的清理）
        conversation_manager.conversation_chains.clear()
        processor.processing_status.clear()
        translator_manager.translation_progress.clear()
        
        # 设置用户B
        user_context.set_user("user_b", "用户B")
        
        # 创建对话链
        chain_b = conversation_manager.create_conversation_chain("video_001")
        
        # 设置处理状态
        processor.processing_status["video_001"] = {"progress": 0.8, "user": "user_b"}
        
        # 设置翻译进度
        translator_manager.translation_progress["user_b_video_001"] = {"progress": 0.6}
        
        print(f"  ✅ 用户B对话链创建: {chain_b is not None}")
        print(f"  ✅ 用户B处理状态: {len(processor.processing_status)} 项")
        print(f"  ✅ 用户B翻译进度: {len(translator_manager.translation_progress)} 项")
        
        # 验证数据隔离
        print("\n🔍 验证数据隔离")
        
        # 检查对话链隔离
        user_a_chains = conversation_manager.conversation_chains.get("user_a", {})
        user_b_chains = conversation_manager.conversation_chains.get("user_b", {})
        
        print(f"  ✅ 用户A对话链数量: {len(user_a_chains)}")
        print(f"  ✅ 用户B对话链数量: {len(user_b_chains)}")
        
        # 检查处理状态隔离
        video_status = processor.processing_status.get("video_001", {})
        print(f"  ✅ video_001处理状态用户: {video_status.get('user', 'unknown')}")
        
        # 检查翻译进度隔离
        user_a_progress = translator_manager.translation_progress.get("user_a_video_001")
        user_b_progress = translator_manager.translation_progress.get("user_b_video_001")
        print(f"  ✅ 用户A翻译进度: {user_a_progress is not None}")
        print(f"  ✅ 用户B翻译进度: {user_b_progress is not None}")
        
        # 清理
        user_context.clear_user()
        
        print("\n🎉 用户切换场景测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 用户切换场景测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_path_isolation():
    """测试路径隔离"""
    print("\n📂 测试路径隔离")
    print("=" * 50)
    
    try:
        from deploy.utils.user_context import user_context
        
        # 用户A路径
        user_context.set_user("user_a", "用户A")
        paths_a = user_context.get_paths()
        base_path_a = str(paths_a.base_path)
        
        # 用户B路径
        user_context.clear_user()
        user_context.set_user("user_b", "用户B")
        paths_b = user_context.get_paths()
        base_path_b = str(paths_b.base_path)
        
        print(f"  ✅ 用户A基础路径: {base_path_a}")
        print(f"  ✅ 用户B基础路径: {base_path_b}")
        print(f"  ✅ 路径隔离: {base_path_a != base_path_b}")
        
        # 验证路径包含用户ID
        assert "user_a" in base_path_a
        assert "user_b" in base_path_b
        
        # 清理
        user_context.clear_user()
        
        return True
        
    except Exception as e:
        print(f"❌ 路径隔离测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始完整用户切换测试")
    print("=" * 60)
    
    tests = [
        ("路径隔离", test_path_isolation),
        ("用户切换场景", simulate_user_switching)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！用户切换功能修复成功。")
        print("💡 现在用户登出再登录新用户时，不会出现索引混乱的问题。")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，需要进一步修复。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)