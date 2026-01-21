#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户上下文管理器

管理当前登录用户的状态和数据路径
"""

import threading
from pathlib import Path
from typing import Optional, Dict
from functools import wraps
from .path_manager import get_path_manager


class UserContext:
    """用户上下文管理器"""
    
    def __init__(self):
        self._current_user_id: Optional[str] = None
        self._user_data: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def set_user(self, user_id: str, username: str = None):
        """设置当前用户"""
        with self._lock:
            self._current_user_id = user_id
            if user_id not in self._user_data:
                # 确保用户目录存在
                path_manager = get_path_manager(user_id)
                path_manager.ensure_directories()
                
                self._user_data[user_id] = {
                    'username': username or user_id,
                    'login_time': None,
                    'path_manager': path_manager
                }
            self._user_data[user_id]['login_time'] = threading.current_thread().ident
    
    def get_current_user_id(self) -> Optional[str]:
        """获取当前用户ID"""
        with self._lock:
            return self._current_user_id
    
    def get_current_user_data(self) -> Optional[Dict]:
        """获取当前用户数据"""
        with self._lock:
            if self._current_user_id:
                return self._user_data.get(self._current_user_id)
            return None
    
    def clear_user(self):
        """清除当前用户"""
        with self._lock:
            current_user_id = self._current_user_id
            self._current_user_id = None
            
            # 清除当前用户的缓存数据（可选，根据需要）
            if current_user_id and current_user_id in self._user_data:
                del self._user_data[current_user_id]
    
    def get_paths(self) -> Optional['PathManager']:
        """获取当前用户的路径管理器"""
        user_data = self.get_current_user_data()
        if user_data:
            return user_data['path_manager']
        return None
    
    def is_logged_in(self) -> bool:
        """检查是否有用户登录"""
        return self.get_current_user_id() is not None
    
    def sync_user_state(self, auth_bridge_current_user=None) -> bool:
        """同步用户状态，确保前后端一致
        
        Args:
            auth_bridge_current_user: Flask层面的当前用户对象
            
        Returns:
            bool: 状态是否一致
        """
        with self._lock:
            gradio_user_id = self._current_user_id
            flask_user_id = auth_bridge_current_user.get('user_id') if auth_bridge_current_user else None
            
            # 如果状态不一致，以Gradio为准（因为这是当前实际的用户界面状态）
            if gradio_user_id != flask_user_id:
                if gradio_user_id:
                    # Gradio有用户但Flask没有，清理Flask状态
                    print(f"状态不一致：Gradio用户={gradio_user_id}, Flask用户={flask_user_id}，以Gradio为准")
                    return False
                else:
                    # 两者都没有用户，状态一致
                    return True
            else:
                # 状态一致
                return True


def get_user_path_manager(user_id: str) -> 'PathManager':
        """获取指定用户的路径管理器"""
        with self._lock:
            if user_id in self._user_data:
                return self._user_data[user_id]['path_manager']
            else:
                # 创建新的路径管理器
                from .path_manager import get_path_manager
                path_manager = get_path_manager(user_id)
                path_manager.ensure_directories()
                return path_manager


# 全局用户上下文实例
user_context = UserContext()


def require_user_login(func):
    """装饰器：要求用户登录才能执行函数"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not user_context.is_logged_in():
            raise ValueError("用户未登录，长时间未活动的用户数据将被清理")
        return func(*args, **kwargs)
    return wrapper


def cleanup_inactive_users(max_inactive_hours: int = 24):
    """清理长时间未活动的用户数据
    
    Args:
        max_inactive_hours: 最大不活跃时间（小时）
    """
    with user_context._lock:
        current_time = threading.current_thread().ident
        inactive_users = []
        
        for user_id, user_data in list(user_context._user_data.items()):
            login_time = user_data.get('login_time', 0)
            
            # 检查用户是否长时间未活动
            if current_time - login_time > max_inactive_hours * 3600:
                inactive_users.append(user_id)
        
        # 清理不活跃用户数据
        for user_id in inactive_users:
            del user_context._user_data[user_id]
            print(f"✅ 清理长时间未活跃用户: {user_id}")
        
        if inactive_users:
            print(f"✅ 已清理 {len(inactive_users)} 个长时间未活跃用户")


def get_user_count():
    """获取当前用户数量"""
    with user_context._lock:
        return len(user_context._user_data)


def get_user_memory_usage():
    """获取用户内存使用情况"""
    with user_context._lock:
        user_count = len(user_context._user_data)
        total_size = 0
        
        for user_id, user_data in user_context._user_data.items():
            # 简单估算内存使用
            total_size += len(str(user_data))
        
        return {
            'user_count': user_count,
            'estimated_size_bytes': total_size,
            'estimated_size_mb': round(total_size / 1024 / 1024, 2)
        }


def get_current_user_paths() -> Optional['PathManager']:
    """获取当前用户的路径管理器"""
    return user_context.get_paths()


def get_current_user_id() -> Optional[str]:
    """获取当前用户ID"""
    return user_context.get_current_user_id()