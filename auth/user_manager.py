#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理器

提供用户注册、登录、认证等功能
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List

from storage import StorageAdapter, User, Session
from .auth_utils import PasswordManager, TokenManager, AuthUtils

logger = logging.getLogger(__name__)


class UserManager:
    """用户管理器"""
    
    def __init__(self, storage: StorageAdapter, jwt_secret: str, 
                 jwt_expire_hours: int = 24):
        """
        初始化用户管理器
        
        Args:
            storage: 存储适配器
            jwt_secret: JWT密钥
            jwt_expire_hours: JWT过期时间（小时）
        """
        self.storage = storage
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager(jwt_secret, token_expire_hours=jwt_expire_hours)
        logger.info("UserManager初始化完成")
    
    def register_user(self, username: str, email: str, password: str, 
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            metadata: 元数据
            
        Returns:
            Dict[str, Any]: 注册结果
        """
        try:
            # 验证输入
            validation_result = self._validate_registration_input(username, email, password)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': validation_result['message'],
                    'errors': validation_result['errors']
                }
            
            # 检查用户名和邮箱是否已存在
            if self.storage.get_user_by_username(username):
                return {
                    'success': False,
                    'message': '用户名已存在'
                }
            
            if self.storage.get_user_by_email(email):
                return {
                    'success': False,
                    'message': '邮箱已被注册'
                }
            
            # 创建用户
            user_id = AuthUtils.generate_user_id()
            now = datetime.utcnow()
            password_hash = self.password_manager.hash_password(password)
            
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=now,
                updated_at=now,
                is_active=True,
                metadata=metadata
            )
            
            # 保存用户
            if not self.storage.create_user(user):
                return {
                    'success': False,
                    'message': '用户创建失败'
                }
            
            logger.info(f"用户注册成功: {username}")
            return {
                'success': True,
                'message': '注册成功',
                'user_id': user_id,
                'username': username
            }
            
        except Exception as e:
            logger.error(f"用户注册失败: {e}")
            return {
                'success': False,
                'message': f'注册失败: {str(e)}'
            }
    
    def login_user(self, username_or_email: str, password: str, 
                  user_agent: str = '', ip_address: str = '') -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
            user_agent: 用户代理
            ip_address: IP地址
            
        Returns:
            Dict[str, Any]: 登录结果
        """
        try:
            # 查找用户
            user = None
            if AuthUtils.validate_email(username_or_email):
                user = self.storage.get_user_by_email(username_or_email)
            else:
                user = self.storage.get_user_by_username(username_or_email)
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            if not user.is_active:
                return {
                    'success': False,
                    'message': '账户已被禁用'
                }
            
            # 验证密码
            if not self.password_manager.verify_password(password, user.password_hash):
                logger.warning(f"密码验证失败: {username_or_email}")
                return {
                    'success': False,
                    'message': '密码错误'
                }
            
            # 生成JWT令牌
            token = self.token_manager.generate_token(
                user_id=user.user_id,
                username=user.username
            )
            
            # 创建会话
            session_id = AuthUtils.generate_session_id()
            session_data = AuthUtils.create_session_data(
                user_id=user.user_id,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            session = Session(
                session_id=session_id,
                user_id=user.user_id,
                session_data=session_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            # 保存会话
            if not self.storage.create_session(session):
                logger.warning(f"会话创建失败，但登录成功: {user.username}")
            
            logger.info(f"用户登录成功: {user.username}")
            return {
                'success': True,
                'message': '登录成功',
                'token': token,
                'user_id': user.user_id,
                'username': user.username,
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            return {
                'success': False,
                'message': f'登录失败: {str(e)}'
            }
    
    def logout_user(self, token: str) -> Dict[str, Any]:
        """
        用户登出
        
        Args:
            token: JWT令牌
            
        Returns:
            Dict[str, Any]: 登出结果
        """
        try:
            # 验证令牌
            payload = self.token_manager.verify_token(token)
            if not payload:
                return {
                    'success': False,
                    'message': '无效的令牌'
                }
            
            # 删除会话
            user_id = payload.get('user_id')
            sessions = self.storage.get_user_sessions(user_id)
            
            for session in sessions:
                self.storage.delete_session(session.session_id)
            
            logger.info(f"用户登出成功: {payload.get('username')}")
            return {
                'success': True,
                'message': '登出成功'
            }
            
        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            return {
                'success': False,
                'message': f'登出失败: {str(e)}'
            }
    
    def authenticate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 令牌载荷，验证失败返回None
        """
        try:
            return self.token_manager.verify_token(token)
        except Exception as e:
            logger.error(f"令牌验证失败: {e}")
            return None
    
    def refresh_token(self, token: str) -> Dict[str, Any]:
        """
        刷新JWT令牌
        
        Args:
            token: 原始令牌
            
        Returns:
            Dict[str, Any]: 刷新结果
        """
        try:
            new_token = self.token_manager.refresh_token(token)
            if new_token:
                return {
                    'success': True,
                    'message': '令牌刷新成功',
                    'token': new_token
                }
            else:
                return {
                    'success': False,
                    'message': '令牌刷新失败'
                }
        except Exception as e:
            logger.error(f"令牌刷新失败: {e}")
            return {
                'success': False,
                'message': f'令牌刷新失败: {str(e)}'
            }
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 用户资料
        """
        try:
            user = self.storage.get_user(user_id)
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 获取用户统计信息
            stats = self.storage.get_user_stats(user_id)
            
            return {
                'success': True,
                'user': {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'is_active': user.is_active,
                    'metadata': user.metadata
                },
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return {
                'success': False,
                'message': f'获取用户资料失败: {str(e)}'
            }
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            updates: 更新数据
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            user = self.storage.get_user(user_id)
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 更新允许的字段
            if 'username' in updates:
                new_username = updates['username']
                if not AuthUtils.validate_username(new_username):
                    return {
                        'success': False,
                        'message': '用户名格式无效'
                    }
                
                # 检查用户名是否已存在
                existing_user = self.storage.get_user_by_username(new_username)
                if existing_user and existing_user.user_id != user_id:
                    return {
                        'success': False,
                        'message': '用户名已存在'
                    }
                
                user.username = new_username
            
            if 'email' in updates:
                new_email = updates['email']
                if not AuthUtils.validate_email(new_email):
                    return {
                        'success': False,
                        'message': '邮箱格式无效'
                    }
                
                # 检查邮箱是否已存在
                existing_user = self.storage.get_user_by_email(new_email)
                if existing_user and existing_user.user_id != user_id:
                    return {
                        'success': False,
                        'message': '邮箱已被注册'
                    }
                
                user.email = new_email
            
            if 'password' in updates:
                new_password = updates['password']
                validation_result = AuthUtils.validate_password(new_password)
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'message': '密码强度不足',
                        'errors': validation_result['errors']
                    }
                
                user.password_hash = self.password_manager.hash_password(new_password)
            
            if 'metadata' in updates:
                user.metadata = updates['metadata']
            
            user.updated_at = datetime.utcnow()
            
            # 保存更新
            if not self.storage.update_user(user):
                return {
                    'success': False,
                    'message': '更新失败'
                }
            
            logger.info(f"用户资料更新成功: {user.username}")
            return {
                'success': True,
                'message': '更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新用户资料失败: {e}")
            return {
                'success': False,
                'message': f'更新失败: {str(e)}'
            }
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            user = self.storage.get_user(user_id)
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 清理用户的所有数据
            if not self.storage.cleanup_user_data(user_id):
                logger.warning(f"用户数据清理不完整: {user.username}")
            
            logger.info(f"用户删除成功: {user.username}")
            return {
                'success': True,
                'message': '用户删除成功'
            }
            
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return {
                'success': False,
                'message': f'删除失败: {str(e)}'
            }
    
    def list_users(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            Dict[str, Any]: 用户列表
        """
        try:
            users = self.storage.list_users(limit, offset)
            
            user_list = []
            for user in users:
                user_list.append({
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'is_active': user.is_active
                })
            
            return {
                'success': True,
                'users': user_list,
                'count': len(user_list)
            }
            
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return {
                'success': False,
                'message': f'列出用户失败: {str(e)}'
            }
    
    def _validate_registration_input(self, username: str, email: str, 
                                   password: str) -> Dict[str, Any]:
        """
        验证注册输入
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            'valid': True,
            'message': '验证通过',
            'errors': []
        }
        
        # 验证用户名
        if not AuthUtils.validate_username(username):
            result['valid'] = False
            result['errors'].append('用户名格式无效（3-30位，只能包含字母、数字、下划线）')
        
        # 验证邮箱
        if not AuthUtils.validate_email(email):
            result['valid'] = False
            result['errors'].append('邮箱格式无效')
        
        # 验证密码
        password_validation = AuthUtils.validate_password(password)
        if not password_validation['valid']:
            result['valid'] = False
            result['errors'].extend(password_validation['errors'])
        
        if not result['valid']:
            result['message'] = '输入验证失败'
        
        return result