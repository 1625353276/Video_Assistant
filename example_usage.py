#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证系统使用示例

演示如何使用认证系统的各项功能
"""

import sys
import time
import requests
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from integration.gradio_bridge import GradioBridge


def main():
    """主函数"""
    print("=== 认证系统使用示例 ===\n")
    
    # 创建桥接器
    bridge = GradioBridge("http://localhost:5001")
    
    # 测试连接
    print("1. 测试Flask连接...")
    if bridge.test_connection():
        print("✓ Flask连接成功\n")
    else:
        print("✗ Flask连接失败，请先启动Flask服务\n")
        return
    
    # 用户注册
    print("2. 用户注册...")
    username = f"demo_user_{int(time.time())}"
    email = f"demo_{int(time.time())}@example.com"
    password = "DemoPassword123!"
    
    register_result = bridge.register_user(username, email, password)
    if register_result['success']:
        print(f"✓ 用户注册成功: {username}")
        print(f"  用户ID: {register_result['user_id']}\n")
    else:
        print(f"✗ 用户注册失败: {register_result['message']}\n")
        return
    
    # 用户登录
    print("3. 用户登录...")
    login_result = bridge.login_user(username, password)
    if login_result['success']:
        print(f"✓ 用户登录成功")
        print(f"  令牌: {login_result['token'][:50]}...\n")
    else:
        print(f"✗ 用户登录失败: {login_result['message']}\n")
        return
    
    # 获取用户资料
    print("4. 获取用户资料...")
    profile_result = bridge.get_user_profile()
    if profile_result['success']:
        print("✓ 用户资料获取成功")
        user = profile_result['user']
        stats = profile_result['stats']
        print(f"  用户名: {user['username']}")
        print(f"  邮箱: {user['email']}")
        print(f"  注册时间: {user['created_at']}")
        print(f"  视频数量: {stats['video_count']}")
        print(f"  会话数量: {stats['session_count']}")
        print(f"  对话数量: {stats['conversation_count']}\n")
    else:
        print(f"✗ 用户资料获取失败: {profile_result['message']}\n")
    
    # 更新用户资料
    print("5. 更新用户资料...")
    update_data = {
        "metadata": {
            "preferences": {
                "theme": "dark",
                "language": "zh-CN"
            }
        }
    }
    
    update_result = bridge.update_user_profile(update_data)
    if update_result['success']:
        print("✓ 用户资料更新成功\n")
    else:
        print(f"✗ 用户资料更新失败: {update_result['message']}\n")
    
    # 创建用户数据目录
    print("6. 创建用户数据目录...")
    user_id = login_result['user_id']
    user_data_dir = bridge.create_user_data_dir(user_id)
    print(f"✓ 用户数据目录创建成功: {user_data_dir}\n")
    
    # 验证令牌
    print("7. 验证令牌...")
    verify_result = bridge.verify_token()
    if verify_result['success']:
        print("✓ 令牌验证成功\n")
    else:
        print(f"✗ 令牌验证失败: {verify_result['message']}\n")
    
    # 用户登出
    print("8. 用户登出...")
    logout_result = bridge.logout_user()
    if logout_result['success']:
        print("✓ 用户登出成功\n")
    else:
        print(f"✗ 用户登出失败: {logout_result['message']}\n")
    
    print("=== 示例完成 ===")


if __name__ == '__main__':
    main()