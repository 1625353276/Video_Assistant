#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API路由

提供用户注册、登录、登出等API端点
"""

import logging
from flask import Blueprint, request, g
from typing import Dict, Any

from .user_manager import UserManager
from .auth_handler import AuthHandler, create_error_response, create_success_response, validate_json, rate_limit

logger = logging.getLogger(__name__)

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def create_auth_routes(user_manager: UserManager, auth_handler: AuthHandler) -> Blueprint:
    """
    创建认证路由
    
    Args:
        user_manager: 用户管理器
        auth_handler: 认证处理器
        
    Returns:
        Blueprint: 认证蓝图
    """
    
    @auth_bp.route('/register', methods=['POST'])
    @rate_limit(max_requests=5, window_seconds=300)  # 5分钟内最多5次注册请求
    @validate_json(
        required_fields=['username', 'email', 'password'],
        optional_fields=['metadata']
    )
    def register():
        """用户注册"""
        try:
            data = request.validated_data
            
            result = user_manager.register_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                metadata=data.get('metadata')
            )
            
            if result['success']:
                return create_success_response(
                    result['message'],
                    201,
                    {
                        'user_id': result['user_id'],
                        'username': result['username']
                    }
                )
            else:
                return create_error_response(
                    result['message'],
                    400,
                    {'errors': result.get('errors', [])}
                )
                
        except Exception as e:
            logger.error(f"注册API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/login', methods=['POST'])
    @rate_limit(max_requests=10, window_seconds=300)  # 5分钟内最多10次登录请求
    @validate_json(
        required_fields=['username_or_email', 'password'],
        optional_fields=['user_agent', 'ip_address']
    )
    def login():
        """用户登录"""
        try:
            data = request.validated_data
            
            result = user_manager.login_user(
                username_or_email=data['username_or_email'],
                password=data['password'],
                user_agent=data.get('user_agent', ''),
                ip_address=data.get('ip_address', '')
            )
            
            if result['success']:
                return create_success_response(
                    result['message'],
                    200,
                    {
                        'token': result['token'],
                        'user_id': result['user_id'],
                        'username': result['username'],
                        'session_id': result.get('session_id')
                    }
                )
            else:
                return create_error_response(result['message'], 401)
                
        except Exception as e:
            logger.error(f"登录API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/logout', methods=['POST'])
    @auth_handler.require_auth
    def logout():
        """用户登出"""
        try:
            token = auth_handler._get_token_from_request()
            
            result = user_manager.logout_user(token)
            
            if result['success']:
                return create_success_response(result['message'])
            else:
                return create_error_response(result['message'], 400)
                
        except Exception as e:
            logger.error(f"登出API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/refresh', methods=['POST'])
    @rate_limit(max_requests=5, window_seconds=300)  # 5分钟内最多5次刷新请求
    @validate_json(required_fields=['token'])
    def refresh_token():
        """刷新令牌"""
        try:
            data = request.validated_data
            
            result = user_manager.refresh_token(data['token'])
            
            if result['success']:
                return create_success_response(
                    result['message'],
                    200,
                    {'token': result['token']}
                )
            else:
                return create_error_response(result['message'], 401)
                
        except Exception as e:
            logger.error(f"刷新令牌API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/profile', methods=['GET'])
    @auth_handler.require_auth
    def get_profile():
        """获取用户资料"""
        try:
            user_id = auth_handler.get_current_user_id()
            
            result = user_manager.get_user_profile(user_id)
            
            if result['success']:
                return create_success_response(
                    '获取用户资料成功',
                    200,
                    result
                )
            else:
                return create_error_response(result['message'], 404)
                
        except Exception as e:
            logger.error(f"获取用户资料API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/profile', methods=['PUT'])
    @auth_handler.require_auth
    @validate_json(
        optional_fields=['username', 'email', 'password', 'metadata']
    )
    def update_profile():
        """更新用户资料"""
        try:
            user_id = auth_handler.get_current_user_id()
            data = request.validated_data
            
            result = user_manager.update_user_profile(user_id, data)
            
            if result['success']:
                return create_success_response(result['message'])
            else:
                return create_error_response(
                    result['message'],
                    400,
                    {'errors': result.get('errors', [])}
                )
                
        except Exception as e:
            logger.error(f"更新用户资料API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/verify', methods=['POST'])
    @rate_limit(max_requests=20, window_seconds=300)  # 5分钟内最多20次验证请求
    @validate_json(required_fields=['token'])
    def verify_token():
        """验证令牌"""
        try:
            data = request.validated_data
            
            payload = user_manager.authenticate_token(data['token'])
            
            if payload:
                return create_success_response(
                    '令牌有效',
                    200,
                    {
                        'user_id': payload['user_id'],
                        'username': payload['username']
                    }
                )
            else:
                return create_error_response('令牌无效', 401)
                
        except Exception as e:
            logger.error(f"验证令牌API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/delete', methods=['DELETE'])
    @auth_handler.require_auth
    def delete_account():
        """删除账户"""
        try:
            user_id = auth_handler.get_current_user_id()
            
            result = user_manager.delete_user(user_id)
            
            if result['success']:
                return create_success_response(result['message'])
            else:
                return create_error_response(result['message'], 400)
                
        except Exception as e:
            logger.error(f"删除账户API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    # 管理员路由（需要管理员权限）
    @auth_bp.route('/admin/users', methods=['GET'])
    @auth_handler.require_auth
    def list_users():
        """列出用户（管理员）"""
        try:
            # 检查是否为管理员（这里简化处理，实际应该有角色系统）
            current_user = auth_handler.get_current_user()
            if not current_user or current_user.get('username') != 'admin':
                return create_error_response('权限不足', 403)
            
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            result = user_manager.list_users(limit, offset)
            
            if result['success']:
                return create_success_response(
                    '获取用户列表成功',
                    200,
                    result
                )
            else:
                return create_error_response(result['message'], 400)
                
        except Exception as e:
            logger.error(f"列出用户API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    @auth_bp.route('/admin/stats', methods=['GET'])
    @auth_handler.require_auth
    def get_system_stats():
        """获取系统统计（管理员）"""
        try:
            # 检查是否为管理员
            current_user = auth_handler.get_current_user()
            if not current_user or current_user.get('username') != 'admin':
                return create_error_response('权限不足', 403)
            
            # 这里需要访问storage获取系统统计
            # 由于UserManager没有直接提供这个方法，我们需要扩展
            return create_error_response('功能待实现', 501)
                
        except Exception as e:
            logger.error(f"获取系统统计API错误: {e}")
            return create_error_response('服务器内部错误', 500)
    
    logger.info("认证路由初始化完成")
    return auth_bp