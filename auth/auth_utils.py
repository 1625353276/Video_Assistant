#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证工具类

提供密码加密、JWT令牌生成和验证等认证相关工具
"""

import hashlib
import secrets
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class PasswordManager:
    """密码管理器"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt对密码进行哈希加密
        
        Args:
            password: 原始密码
            
        Returns:
            str: 加密后的密码哈希
        """
        try:
            import bcrypt
            # 生成盐值并加密
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except ImportError:
            logger.warning("bcrypt未安装，使用SHA-256作为备选方案")
            # 备选方案：使用SHA-256 + 盐值
            salt = secrets.token_hex(16)
            hashed = hashlib.sha256((password + salt).encode()).hexdigest()
            return f"sha256:{salt}:{hashed}"
        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            raise
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            password: 原始密码
            hashed_password: 加密后的密码哈希
            
        Returns:
            bool: 密码是否匹配
        """
        try:
            if hashed_password.startswith('sha256:'):
                # 备选方案：SHA-256验证
                _, salt, stored_hash = hashed_password.split(':')
                computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                return computed_hash == stored_hash
            else:
                # bcrypt验证
                import bcrypt
                return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ImportError:
            logger.error("bcrypt未安装，无法验证密码")
            return False
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False


class TokenManager:
    """JWT令牌管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256', 
                 token_expire_hours: int = 24):
        """
        初始化令牌管理器
        
        Args:
            secret_key: JWT密钥
            algorithm: 加密算法
            token_expire_hours: 令牌过期时间（小时）
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_hours = token_expire_hours
        logger.info("TokenManager初始化完成")
    
    def generate_token(self, user_id: str, username: str, 
                      additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        生成JWT令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            additional_claims: 额外的声明信息
            
        Returns:
            str: JWT令牌
        """
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=self.token_expire_hours)
            
            # 基础声明
            payload = {
                'user_id': user_id,
                'username': username,
                'iat': now,
                'exp': expires_at,
                'type': 'access'
            }
            
            # 添加额外声明
            if additional_claims:
                payload.update(additional_claims)
            
            # 生成令牌
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"JWT令牌生成成功，用户: {username}")
            return token
            
        except Exception as e:
            logger.error(f"JWT令牌生成失败: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 令牌载荷，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get('type') != 'access':
                logger.warning("令牌类型不正确")
                return None
            
            logger.info(f"JWT令牌验证成功，用户: {payload.get('username')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT令牌无效: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT令牌验证失败: {e}")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        刷新JWT令牌
        
        Args:
            token: 原始令牌
            
        Returns:
            Optional[str]: 新的令牌，失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get('type') != 'access':
                logger.warning("令牌类型不正确，无法刷新")
                return None
            
            # 生成新令牌
            new_token = self.generate_token(
                user_id=payload['user_id'],
                username=payload['username'],
                additional_claims={k: v for k, v in payload.items() 
                                 if k not in ['iat', 'exp', 'type']}
            )
            
            logger.info(f"JWT令牌刷新成功，用户: {payload.get('username')}")
            return new_token
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期，无法刷新")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT令牌无效，无法刷新: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT令牌刷新失败: {e}")
            return None
    
    def extract_token_from_header(self, auth_header: str) -> Optional[str]:
        """
        从Authorization头部提取令牌
        
        Args:
            auth_header: Authorization头部值
            
        Returns:
            Optional[str]: JWT令牌，格式错误返回None
        """
        if not auth_header:
            return None
        
        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return None
            return parts[1]
        except Exception as e:
            logger.error(f"提取令牌失败: {e}")
            return None


class AuthUtils:
    """认证工具类"""
    
    @staticmethod
    def generate_user_id() -> str:
        """
        生成用户ID
        
        Returns:
            str: 唯一的用户ID
        """
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_session_id() -> str:
        """
        生成会话ID
        
        Returns:
            str: 唯一的会话ID
        """
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 邮箱格式是否有效
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        验证用户名格式
        
        Args:
            username: 用户名
            
        Returns:
            bool: 用户名格式是否有效
        """
        import re
        # 用户名长度3-30，只能包含字母、数字、下划线
        pattern = r'^[a-zA-Z0-9_]{3,30}$'
        return re.match(pattern, username) is not None
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """
        验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            'valid': False,
            'score': 0,
            'errors': [],
            'suggestions': []
        }
        
        # 长度检查
        if len(password) < 6:
            result['errors'].append('密码长度至少6位')
        elif len(password) >= 8:
            result['score'] += 2
        else:
            result['score'] += 1
        
        # 包含大写字母
        if any(c.isupper() for c in password):
            result['score'] += 1
        else:
            result['suggestions'].append('建议包含大写字母')
        
        # 包含小写字母
        if any(c.islower() for c in password):
            result['score'] += 1
        else:
            result['suggestions'].append('建议包含小写字母')
        
        # 包含数字
        if any(c.isdigit() for c in password):
            result['score'] += 1
        else:
            result['suggestions'].append('建议包含数字')
        
        # 包含特殊字符
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        if any(c in special_chars for c in password):
            result['score'] += 1
        else:
            result['suggestions'].append('建议包含特殊字符')
        
        # 判断是否有效
        result['valid'] = len(result['errors']) == 0 and result['score'] >= 3
        
        return result
    
    @staticmethod
    def get_client_ip(request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: Flask请求对象
            
        Returns:
            str: 客户端IP地址
        """
        # 尝试从各种头部获取真实IP
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        elif request.headers.get('X-Client-IP'):
            return request.headers.get('X-Client-IP')
        else:
            return request.remote_addr or 'unknown'
    
    @staticmethod
    def create_session_data(user_id: str, user_agent: str = '', 
                          ip_address: str = '') -> Dict[str, Any]:
        """
        创建会话数据
        
        Args:
            user_id: 用户ID
            user_agent: 用户代理字符串
            ip_address: IP地址
            
        Returns:
            Dict[str, Any]: 会话数据
        """
        return {
            'user_id': user_id,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'login_time': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'is_active': True
        }