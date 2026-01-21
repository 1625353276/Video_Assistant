#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API测试脚本

测试认证系统的API接口
"""

import sys
import time
import requests
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))


def test_api():
    """测试API接口"""
    print("=== 启动Flask服务 ===")
    
    # 启动Flask服务
    flask_process = subprocess.Popen([
        sys.executable, 
        str(project_root / 'deploy' / 'flask_app.py')
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # 等待服务启动
        time.sleep(5)
        
        base_url = "http://localhost:5001"
        
        # 测试健康检查
        print("\n=== 测试健康检查 ===")
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            print(f"健康检查状态码: {response.status_code}")
            print(f"健康检查响应: {response.json()}")
        except Exception as e:
            print(f"健康检查失败: {e}")
            return False
        
        # 测试用户注册
        print("\n=== 测试用户注册 ===")
        register_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            response = requests.post(f"{base_url}/api/auth/register", 
                                   json=register_data, timeout=5)
            print(f"注册状态码: {response.status_code}")
            print(f"注册响应: {response.json()}")
            
            if response.status_code == 201:
                register_result = response.json()
                if register_result.get('success'):
                    user_id = register_result['user_id']
                    username = register_result['username']
                    
                    # 测试用户登录
                    print("\n=== 测试用户登录 ===")
                    login_data = {
                        "username_or_email": username,
                        "password": "TestPassword123!"
                    }
                    
                    response = requests.post(f"{base_url}/api/auth/login", 
                                           json=login_data, timeout=5)
                    print(f"登录状态码: {response.status_code}")
                    print(f"登录响应: {response.json()}")
                    
                    if response.status_code == 200:
                        login_result = response.json()
                        if login_result.get('success'):
                            token = login_result['token']
                            
                            # 测试获取用户资料
                            print("\n=== 测试获取用户资料 ===")
                            headers = {"Authorization": f"Bearer {token}"}
                            response = requests.get(f"{base_url}/api/auth/profile", 
                                                 headers=headers, timeout=5)
                            print(f"获取资料状态码: {response.status_code}")
                            print(f"获取资料响应: {response.json()}")
                            
                            # 测试用户登出
                            print("\n=== 测试用户登出 ===")
                            response = requests.post(f"{base_url}/api/auth/logout", 
                                                   headers=headers, timeout=5)
                            print(f"登出状态码: {response.status_code}")
                            print(f"登出响应: {response.json()}")
                    
                    print("\n=== 所有API测试通过 ===")
                    return True
                else:
                    print(f"注册失败: {register_result.get('message')}")
                    return False
            else:
                print(f"注册请求失败: {response.json()}")
                return False
                
        except Exception as e:
            print(f"API测试异常: {e}")
            return False
    
    finally:
        # 停止Flask服务
        print("\n=== 停止Flask服务 ===")
        flask_process.terminate()
        flask_process.wait()


if __name__ == '__main__':
    success = test_api()
    sys.exit(0 if success else 1)