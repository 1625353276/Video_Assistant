#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 get_temp_path 修复
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from deploy.utils.user_context import UserContext
from deploy.utils.path_manager import get_path_manager


def test_temp_path_fix():
    """测试 get_temp_path 方法修复"""
    print("🔧 测试 get_temp_path 方法修复...")
    
    # 1. 测试 PathManager 直接调用
    print("\n1. 测试 PathManager 直接调用:")
    try:
        pm = get_path_manager('test_user')
        print(f"   ✅ PathManager 创建成功: {pm}")
        
        # 测试 get_temp_dir 方法
        temp_dir = pm.get_temp_dir()
        print(f"   ✅ get_temp_dir(): {temp_dir}")
        
        # 测试 get_temp_path 方法（新添加的）
        temp_path = pm.get_temp_path('test.wav')
        print(f"   ✅ get_temp_path('test.wav'): {temp_path}")
        
        # 测试不带参数的 get_temp_path
        temp_path_no_param = pm.get_temp_path()
        print(f"   ✅ get_temp_path(): {temp_path_no_param}")
        
    except Exception as e:
        print(f"   ❌ PathManager 测试失败: {e}")
        return False
    
    # 2. 测试通过用户上下文调用
    print("\n2. 测试通过用户上下文调用:")
    try:
        # 设置用户上下文（使用全局实例）
        from deploy.utils.user_context import user_context
        user_context.set_user('test_user')
        print(f"   ✅ 用户上下文设置成功")
        
        # 获取当前用户路径管理器
        from deploy.utils.user_context import get_current_user_paths
        user_paths = get_current_user_paths()
        print(f"   ✅ 获取用户路径管理器成功: {user_paths}")
        
        # 测试 get_temp_path 方法
        temp_path = user_paths.get_temp_path('audio_test.wav')
        print(f"   ✅ get_temp_path('audio_test.wav'): {temp_path}")
        
        # 验证路径结构
        expected_parts = ['data', 'users', 'test_user', 'temp', 'audio_test.wav']
        actual_parts = str(temp_path).split('/')
        if all(part in actual_parts for part in expected_parts):
            print(f"   ✅ 路径结构验证通过")
        else:
            print(f"   ❌ 路径结构验证失败: 期望包含 {expected_parts}, 实际 {actual_parts}")
            return False
            
    except Exception as e:
        print(f"   ❌ 用户上下文测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 所有测试通过！get_temp_path 方法修复成功！")
    return True


if __name__ == "__main__":
    success = test_temp_path_fix()
    sys.exit(0 if success else 1)