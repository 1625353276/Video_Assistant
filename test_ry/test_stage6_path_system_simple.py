#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第六阶段测试：路径系统重构（简化版）

测试新的路径管理系统和用户上下文
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.path_manager import PathManager, get_path_manager
from deploy.utils.user_context import user_context, get_current_user_paths, get_current_user_id


def test_basic_path_manager():
    """测试基本路径管理器功能"""
    print("🧪 测试基本路径管理器功能...")
    
    # 测试共享路径管理器
    shared_manager = PathManager()
    assert shared_manager.user_id is None
    assert not shared_manager.is_isolated
    assert shared_manager.base_path.name == "data"
    print("✅ 共享路径管理器创建成功")
    
    # 测试用户路径管理器
    user_manager = PathManager("test_user_123")
    assert user_manager.user_id == "test_user_123"
    assert user_manager.is_isolated
    assert "test_user_123" in str(user_manager.base_path)
    assert "users" in str(user_manager.base_path)
    print("✅ 用户路径管理器创建成功")


def test_path_manager_caching():
    """测试路径管理器缓存"""
    print("🧪 测试路径管理器缓存...")
    
    # 获取相同用户ID的路径管理器
    manager1 = get_path_manager("test_user")
    manager2 = get_path_manager("test_user")
    
    # 应该是同一个实例（缓存）
    assert manager1 is manager2
    print("✅ 路径管理器缓存测试通过")


def test_user_context_integration():
    """测试用户上下文集成"""
    print("🧪 测试用户上下文集成...")
    
    try:
        # 设置用户
        user_context.set_user("test_user", "testuser")
        
        # 验证用户设置
        assert get_current_user_id() == "test_user"
        
        # 获取路径管理器
        paths = get_current_user_paths()
        assert paths is not None
        assert isinstance(paths, PathManager)
        assert paths.user_id == "test_user"
        
        print("✅ 用户上下文集成测试通过")
    finally:
        user_context.clear_user()


def test_user_isolation():
    """测试用户隔离"""
    print("🧪 测试用户隔离...")
    
    try:
        # 设置第一个用户
        user_context.set_user("user_1", "user1")
        paths1 = get_current_user_paths()
        
        # 设置第二个用户
        user_context.set_user("user_2", "user2")
        paths2 = get_current_user_paths()
        
        # 验证路径隔离
        assert paths1.base_path != paths2.base_path
        assert "user_1" in str(paths1.base_path)
        assert "user_2" in str(paths2.base_path)
        
        print("✅ 用户隔离测试通过")
    finally:
        user_context.clear_user()


def run_stage6_tests_simple():
    """运行第六阶段简化测试"""
    print("🚀 开始第六阶段测试：路径系统重构（简化版）\n")
    
    try:
        test_basic_path_manager()
        print()
        test_path_manager_caching()
        print()
        test_user_context_integration()
        print()
        test_user_isolation()
        print()
        
        print("🎉 第六阶段所有测试通过！")
        print("✅ 路径管理器创建和使用正常")
        print("✅ 用户隔离路径系统工作正常")
        print("✅ 用户上下文集成成功")
        print("✅ 路径缓存机制正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage6_tests_simple()
    sys.exit(0 if success else 1)