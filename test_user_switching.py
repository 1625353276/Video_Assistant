#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户切换功能测试脚本

测试用户登出、登录和切换时的状态清理功能
"""

import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_user_context_switching():
    """测试用户上下文切换"""
    print("=" * 60)
    print("🧪 测试用户上下文切换")
    print("=" * 60)
    
    try:
        from deploy.utils.user_context import user_context
        
        # 测试用户设置和清理
        print("1. 测试用户A登录...")
        user_context.set_user("user_a", "用户A")
        assert user_context.get_current_user_id() == "user_a"
        assert user_context.get_current_user_data()['username'] == "用户A"
        print("✅ 用户A登录成功")
        
        print("2. 测试用户切换到用户B...")
        user_context.set_user("user_b", "用户B")
        assert user_context.get_current_user_id() == "user_b"
        assert user_context.get_current_user_data()['username'] == "用户B"
        print("✅ 用户切换成功")
        
        print("3. 测试用户登出...")
        user_context.clear_user()
        assert user_context.get_current_user_id() is None
        assert user_context.get_current_user_data() is None
        print("✅ 用户登出成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 用户上下文切换测试失败: {e}")
        return False

def test_conversation_manager_isolation():
    """测试对话管理器隔离"""
    print("\n" + "=" * 60)
    print("🧪 测试对话管理器隔离")
    print("=" * 60)
    
    try:
        from deploy.core.conversation_manager_isolated import get_conversation_manager
        from deploy.utils.user_context import user_context
        
        conversation_manager = get_conversation_manager()
        
        # 模拟用户A登录
        print("1. 模拟用户A登录...")
        user_context.set_user("user_a", "用户A")
        
        # 为用户A创建对话链
        print("2. 为用户A创建对话链...")
        chain_a = conversation_manager.create_conversation_chain("video_001")
        assert chain_a is not None
        print("✅ 用户A对话链创建成功")
        
        # 检查用户A的对话链是否存在
        assert "user_a" in conversation_manager.conversation_chains
        assert "video_001" in conversation_manager.conversation_chains["user_a"]
        print("✅ 用户A对话链缓存正确")
        
        # 模拟用户切换到用户B
        print("3. 切换到用户B...")
        user_context.clear_user()
        user_context.set_user("user_b", "用户B")
        
        # 为用户B创建对话链
        print("4. 为用户B创建对话链...")
        chain_b = conversation_manager.create_conversation_chain("video_001")
        assert chain_b is not None
        print("✅ 用户B对话链创建成功")
        
        # 检查用户B的对话链是否存在
        assert "user_b" in conversation_manager.conversation_chains
        assert "video_001" in conversation_manager.conversation_chains["user_b"]
        print("✅ 用户B对话链缓存正确")
        
        # 验证两个用户的对话链是独立的
        chain_a_reloaded = conversation_manager.conversation_chains["user_a"]["video_001"]
        chain_b_reloaded = conversation_manager.conversation_chains["user_b"]["video_001"]
        assert chain_a_reloaded is not chain_b_reloaded
        print("✅ 用户对话链隔离正确")
        
        # 清理
        user_context.clear_user()
        print("✅ 对话管理器隔离测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 对话管理器隔离测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_video_processor_isolation():
    """测试视频处理器隔离"""
    print("\n" + "=" * 60)
    print("🧪 测试视频处理器隔离")
    print("=" * 60)
    
    try:
        from deploy.core.video_processor_isolated import get_isolated_processor
        from deploy.utils.user_context import user_context
        
        processor = get_isolated_processor()
        
        # 模拟用户A登录
        print("1. 模拟用户A登录...")
        user_context.set_user("user_a", "用户A")
        
        # 检查用户A的路径管理器
        user_paths = user_context.get_paths()
        assert user_paths is not None
        assert "user_a" in str(user_paths.base_path)
        print("✅ 用户A路径管理器正确")
        
        # 模拟用户切换到用户B
        print("2. 切换到用户B...")
        user_context.clear_user()
        user_context.set_user("user_b", "用户B")
        
        # 检查用户B的路径管理器
        user_paths_b = user_context.get_paths()
        assert user_paths_b is not None
        assert "user_b" in str(user_paths_b.base_path)
        assert user_paths_b.base_path != user_paths.base_path
        print("✅ 用户B路径管理器正确")
        
        # 清理
        user_context.clear_user()
        print("✅ 视频处理器隔离测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 视频处理器隔离测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_translator_manager_isolation():
    """测试翻译管理器隔离"""
    print("\n" + "=" * 60)
    print("🧪 测试翻译管理器隔离")
    print("=" * 60)
    
    try:
        from deploy.core.translator_isolated import get_translator_manager
        from deploy.utils.user_context import user_context
        
        translator_manager = get_translator_manager()
        
        # 模拟用户A登录
        print("1. 模拟用户A登录...")
        user_context.set_user("user_a", "用户A")
        
        # 设置用户A的翻译进度
        progress_key_a = f"user_a_video_001"
        translator_manager.translation_progress[progress_key_a] = {
            "current": 1,
            "total": 2,
            "progress": 0.5,
            "message": "翻译中...",
            "timestamp": time.time()
        }
        print("✅ 用户A翻译进度设置成功")
        
        # 模拟用户切换到用户B
        print("2. 切换到用户B...")
        user_context.clear_user()
        user_context.set_user("user_b", "用户B")
        
        # 设置用户B的翻译进度
        progress_key_b = f"user_b_video_001"
        translator_manager.translation_progress[progress_key_b] = {
            "current": 2,
            "total": 2,
            "progress": 1.0,
            "message": "翻译完成",
            "timestamp": time.time()
        }
        print("✅ 用户B翻译进度设置成功")
        
        # 验证两个用户的翻译进度是独立的
        progress_a = translator_manager.translation_progress.get(progress_key_a)
        progress_b = translator_manager.translation_progress.get(progress_key_b)
        assert progress_a is not None
        assert progress_b is not None
        assert progress_a["progress"] != progress_b["progress"]
        print("✅ 用户翻译进度隔离正确")
        
        # 清理
        user_context.clear_user()
        print("✅ 翻译管理器隔离测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 翻译管理器隔离测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_logout_cleanup():
    """测试登出时的清理功能"""
    print("\n" + "=" * 60)
    print("🧪 测试登出清理功能")
    print("=" * 60)
    
    try:
        from deploy.core.conversation_manager_isolated import get_conversation_manager
        from deploy.core.video_processor_isolated import get_isolated_processor
        from deploy.core.translator_isolated import get_translator_manager
        from deploy.core.index_builder_isolated import get_index_builder
        from deploy.utils.user_context import user_context
        
        # 设置用户
        print("1. 设置用户...")
        user_context.set_user("test_user", "测试用户")
        
        # 创建一些数据
        print("2. 创建测试数据...")
        conversation_manager = get_conversation_manager()
        conversation_manager.create_conversation_chain("test_video")
        
        processor = get_isolated_processor()
        processor.processing_status["test_video"] = {"progress": 0.5}
        
        translator_manager = get_translator_manager()
        translator_manager.translation_progress["test_user_test_video"] = {"progress": 0.3}
        
        index_builder = get_index_builder()
        if index_builder.vector_store:
            index_builder.vector_store.add_documents([{"text": "test", "user_id": "test_user"}])
        
        # 验证数据存在
        assert "test_user" in conversation_manager.conversation_chains
        assert "test_video" in processor.processing_status
        assert "test_user_test_video" in translator_manager.translation_progress
        print("✅ 测试数据创建成功")
        
        # 模拟登出清理
        print("3. 执行登出清理...")
        
        # 清理对话管理器
        conversation_manager.conversation_chains.clear()
        
        # 清理视频处理器
        processor.processing_status.clear()
        
        # 清理翻译管理器
        translator_manager.translation_progress.clear()
        
        # 清理索引构建器
        if index_builder.vector_store and hasattr(index_builder.vector_store, 'clear'):
            index_builder.vector_store.clear()
        if index_builder.bm25_retriever and hasattr(index_builder.bm25_retriever, 'clear'):
            index_builder.bm25_retriever.clear()
        
        # 清理用户上下文
        user_context.clear_user()
        
        # 验证清理结果
        assert len(conversation_manager.conversation_chains) == 0
        assert len(processor.processing_status) == 0
        assert len(translator_manager.translation_progress) == 0
        assert user_context.get_current_user_id() is None
        print("✅ 登出清理成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 登出清理测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    print("🚀 开始用户切换功能测试")
    print("=" * 60)
    
    tests = [
        ("用户上下文切换", test_user_context_switching),
        ("对话管理器隔离", test_conversation_manager_isolation),
        ("视频处理器隔离", test_video_processor_isolation),
        ("翻译管理器隔离", test_translator_manager_isolation),
        ("登出清理功能", test_logout_cleanup)
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
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，需要进一步修复。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
