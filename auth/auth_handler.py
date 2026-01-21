#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证处理器

提供Flask认证中间件和装饰器
"""

import functools
import logging
from flask import request, jsonify, g
from typing import Dict, Optional, Any, Callable

from .user_manager import UserManager

logger = logging.getLogger(__name__)


class AuthHandler:
    """认证处理器"""
    
    def __init__(self, user_manager: UserManager):
        """
        初始化认证处理器
        
        Args:
            user_manager: 用户管理器
        """
        self.user_manager = user_manager
        logger.info("AuthHandler初始化完成")
    
    def require_auth(self, f: Callable) -> Callable:
        """
        认证装饰器
        
        Args:
            f: 被装饰的函数
            
        Returns:
            Callable: 装饰后的函数
        """
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取令牌
            token = self._get_token_from_request()
            if not token:
                return jsonify({
                    'success': False,
                    'message': '缺少认证令牌'
                }), 401
            
            # 验证令牌
            payload = self.user_manager.authenticate_token(token)
            if not payload:
                return jsonify({
                    'success': False,
                    'message': '无效的认证令牌'
                }), 401
            
            # 将用户信息存储到Flask的g对象中
            g.current_user = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def optional_auth(self, f: Callable) -> Callable:
        """
        可选认证装饰器
        
        Args:
            f: 被装饰的函数
            
        Returns:
            Callable: 装饰后的函数
        """
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取令牌
            token = self._get_token_from_request()
            
            # 验证令牌（可选）
            if token:
                payload = self.user_manager.authenticate_token(token)
                if payload:
                    g.current_user = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        获取当前用户信息
        
        Returns:
            Optional[Dict[str, Any]]: 当前用户信息
        """
        return getattr(g, 'current_user', None)
    
    def get_current_user_id(self) -> Optional[str]:
        """
        获取当前用户ID
        
        Returns:
            Optional[str]: 当前用户ID
        """
        current_user = self.get_current_user()
        return current_user.get('user_id') if current_user else None
    
    def get_current_username(self) -> Optional[str]:
        """
        获取当前用户名
        
        Returns:
            Optional[str]: 当前用户名
        """
        current_user = self.get_current_user()
        return current_user.get('username') if current_user else None
    
    def _get_token_from_request(self) -> Optional[str]:
        """
        从请求中获取令牌
        
        Returns:
            Optional[str]: JWT令牌
        """
        # 优先从Authorization头部获取
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = self.user_manager.token_manager.extract_token_from_header(auth_header)
            if token:
                return token
        
        # 从查询参数获取
        token = request.args.get('token')
        if token:
            return token
        
        # 从表单数据获取
        token = request.form.get('token')
        if token:
            return token
        
        return None


def create_error_response(message: str, status_code: int = 400, 
                         additional_data: Optional[Dict[str, Any]] = None):
    """
    创建标准错误响应
    
    Args:
        message: 错误消息
        status_code: HTTP状态码
        additional_data: 额外数据
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': False,
        'message': message
    }
    
    if additional_data:
        response.update(additional_data)
    
    return jsonify(response), status_code


def create_success_response(message: str, status_code: int = 200,
                           additional_data: Optional[Dict[str, Any]] = None):
    """
    创建标准成功响应
    
    Args:
        message: 成功消息
        status_code: HTTP状态码
        additional_data: 额外数据
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': True,
        'message': message
    }
    
    if additional_data:
        response.update(additional_data)
    
    return jsonify(response), status_code


def validate_json(required_fields: list = None, optional_fields: list = None):
    """
    JSON数据验证装饰器
    
    Args:
        required_fields: 必需字段列表
        optional_fields: 可选字段列表
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查Content-Type
            if not request.is_json:
                return create_error_response('请求必须是JSON格式', 400)
            
            # 获取JSON数据
            data = request.get_json()
            if not data:
                return create_error_response('无效的JSON数据', 400)
            
            # 验证必需字段
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return create_error_response(
                        f'缺少必需字段: {", ".join(missing_fields)}', 
                        400,
                        {'missing_fields': missing_fields}
                    )
            
            # 过滤字段（只保留允许的字段）
            allowed_fields = (required_fields or []) + (optional_fields or [])
            if allowed_fields:
                filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
                # 将过滤后的数据存储到request对象中
                request.validated_data = filtered_data
            else:
                request.validated_data = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit(max_requests: int = 100, window_seconds: int = 3600):
    """
    简单的速率限制装饰器
    
    Args:
        max_requests: 最大请求数
        window_seconds: 时间窗口（秒）
        
    Returns:
        Callable: 装饰器函数
    """
    # 简单的内存存储（生产环境应使用Redis等）
    rate_limit_store = {}
    
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取客户端标识
            client_id = request.remote_addr
            if hasattr(g, 'current_user') and g.current_user:
                client_id = g.current_user.get('user_id', client_id)
            
            # 检查速率限制
            now = int(time.time())
            window_start = now - window_seconds
            
            # 清理过期记录
            if client_id in rate_limit_store:
                rate_limit_store[client_id] = [
                    timestamp for timestamp in rate_limit_store[client_id]
                    if timestamp > window_start
                ]
            else:
                rate_limit_store[client_id] = []
            
            # 检查请求数量
            if len(rate_limit_store[client_id]) >= max_requests:
                return create_error_response(
                    '请求过于频繁，请稍后再试',
                    429,
                    {
                        'retry_after': window_seconds,
                        'max_requests': max_requests
                    }
                )
            
            # 记录当前请求
            rate_limit_store[client_id].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# 需要添加time导入
import time