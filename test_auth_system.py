#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证系统测试脚本

测试用户注册、登录、令牌验证等功能
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入认证相关模块
from storage.sqlite_adapter import SQLiteAdapter
from auth.user_manager import UserManager
from auth.auth_utils import AuthUtils, PasswordManager


def test_storage_adapter():
    """测试存储适配器"""
    logger.info("=== 测试存储适配器 ===")
    
    # 创建SQLite适配器
    storage = SQLiteAdapter("data/test_auth.db")
    
    # 连接数据库
    if not storage.connect():
        logger.error("数据库连接失败")
        return False
    
    # 初始化表结构
    if not storage.initialize_schema():
        logger.error("数据库初始化失败")
        return False
    
    logger.info("存储适配器测试通过")
    return storage


def test_user_manager(storage):
    """测试用户管理器"""
    logger.info("=== 测试用户管理器 ===")
    
    # 创建用户管理器
    user_manager = UserManager(storage, "test-jwt-secret-key")
    
    # 测试用户注册
    test_username = f"testuser_{int(time.time())}"
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "TestPassword123!"
    
    logger.info(f"测试用户注册: {test_username}")
    register_result = user_manager.register_user(
        username=test_username,
        email=test_email,
        password=test_password
    )
    
    if not register_result['success']:
        logger.error(f"用户注册失败: {register_result['message']}")
        return False
    
    user_id = register_result['user_id']
    logger.info(f"用户注册成功，ID: {user_id}")
    
    # 测试用户登录
    logger.info("测试用户登录")
    login_result = user_manager.login_user(
        username_or_email=test_username,
        password=test_password
    )
    
    if not login_result['success']:
        logger.error(f"用户登录失败: {login_result['message']}")
        return False
    
    token = login_result['token']
    logger.info(f"用户登录成功，令牌: {token[:50]}...")
    
    # 测试令牌验证
    logger.info("测试令牌验证")
    payload = user_manager.authenticate_token(token)
    
    if not payload:
        logger.error("令牌验证失败")
        return False
    
    logger.info(f"令牌验证成功，用户: {payload['username']}")
    
    # 测试获取用户资料
    logger.info("测试获取用户资料")
    profile_result = user_manager.get_user_profile(user_id)
    
    if not profile_result['success']:
        logger.error(f"获取用户资料失败: {profile_result['message']}")
        return False
    
    logger.info(f"用户资料获取成功: {profile_result['user']['username']}")
    
    # 测试用户登出
    logger.info("测试用户登出")
    logout_result = user_manager.logout_user(token)
    
    if not logout_result['success']:
        logger.error(f"用户登出失败: {logout_result['message']}")
        return False
    
    logger.info("用户登出成功")
    
    # 清理测试数据
    logger.info("清理测试数据")
    storage.delete_user(user_id)
    
    logger.info("用户管理器测试通过")
    return True


def test_auth_utils():
    """测试认证工具"""
    logger.info("=== 测试认证工具 ===")
    
    # 测试密码管理器
    password = "TestPassword123!"
    logger.info("测试密码加密")
    hashed_password = PasswordManager.hash_password(password)
    logger.info(f"密码加密成功: {hashed_password[:50]}...")
    
    logger.info("测试密码验证")
    is_valid = PasswordManager.verify_password(password, hashed_password)
    if not is_valid:
        logger.error("密码验证失败")
        return False
    
    logger.info("密码验证成功")
    
    # 测试用户ID生成
    logger.info("测试用户ID生成")
    user_id = AuthUtils.generate_user_id()
    logger.info(f"用户ID生成成功: {user_id}")
    
    # 测试邮箱验证
    logger.info("测试邮箱验证")
    valid_email = "test@example.com"
    invalid_email = "invalid-email"
    
    if not AuthUtils.validate_email(valid_email):
        logger.error("有效邮箱验证失败")
        return False
    
    if AuthUtils.validate_email(invalid_email):
        logger.error("无效邮箱验证通过（应该失败）")
        return False
    
    logger.info("邮箱验证测试通过")
    
    # 测试用户名验证
    logger.info("测试用户名验证")
    valid_username = "testuser123"
    invalid_username = "test@user"
    
    if not AuthUtils.validate_username(valid_username):
        logger.error("有效用户名验证失败")
        return False
    
    if AuthUtils.validate_username(invalid_username):
        logger.error("无效用户名验证通过（应该失败）")
        return False
    
    logger.info("用户名验证测试通过")
    
    # 测试密码强度验证
    logger.info("测试密码强度验证")
    strong_password = "StrongP@ssw0rd!"
    weak_password = "weak"
    
    strong_result = AuthUtils.validate_password(strong_password)
    if not strong_result['valid']:
        logger.error("强密码验证失败")
        return False
    
    weak_result = AuthUtils.validate_password(weak_password)
    if weak_result['valid']:
        logger.error("弱密码验证通过（应该失败）")
        return False
    
    logger.info("密码强度验证测试通过")
    
    logger.info("认证工具测试通过")
    return True


def main():
    """主函数"""
    logger.info("=== 认证系统测试开始 ===")
    
    try:
        # 测试认证工具
        if not test_auth_utils():
            logger.error("认证工具测试失败")
            return False
        
        # 测试存储适配器
        storage = test_storage_adapter()
        if not storage:
            logger.error("存储适配器测试失败")
            return False
        
        # 测试用户管理器
        if not test_user_manager(storage):
            logger.error("用户管理器测试失败")
            return False
        
        # 断开数据库连接
        storage.disconnect()
        
        # 清理测试数据库
        test_db_path = Path("data/test_auth.db")
        if test_db_path.exists():
            test_db_path.unlink()
            logger.info("测试数据库已清理")
        
        logger.info("=== 认证系统测试全部通过 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)