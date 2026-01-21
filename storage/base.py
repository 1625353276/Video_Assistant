#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储适配器基础类

定义了用户数据存储的统一接口，支持多种数据库后端
"""

import abc
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass


@dataclass
class User:
    """用户数据模型"""
    user_id: str
    username: str
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Session:
    """会话数据模型"""
    session_id: str
    user_id: str
    session_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class Video:
    """视频数据模型"""
    video_id: str
    user_id: str
    filename: str
    file_path: str
    file_size: int
    duration: float
    language: str
    resolution: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Conversation:
    """对话数据模型"""
    conversation_id: str
    user_id: str
    video_id: str
    session_id: str
    conversation_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class StorageAdapter(abc.ABC):
    """存储适配器抽象基类"""
    
    @abc.abstractmethod
    def connect(self) -> bool:
        """连接到数据库"""
        pass
    
    @abc.abstractmethod
    def disconnect(self) -> bool:
        """断开数据库连接"""
        pass
    
    @abc.abstractmethod
    def initialize_schema(self) -> bool:
        """初始化数据库表结构"""
        pass
    
    # 用户管理方法
    @abc.abstractmethod
    def create_user(self, user: User) -> bool:
        """创建新用户"""
        pass
    
    @abc.abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        pass
    
    @abc.abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        pass
    
    @abc.abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        pass
    
    @abc.abstractmethod
    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        pass
    
    @abc.abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        pass
    
    @abc.abstractmethod
    def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """列出用户"""
        pass
    
    # 会话管理方法
    @abc.abstractmethod
    def create_session(self, session: Session) -> bool:
        """创建新会话"""
        pass
    
    @abc.abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        pass
    
    @abc.abstractmethod
    def update_session(self, session: Session) -> bool:
        """更新会话"""
        pass
    
    @abc.abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass
    
    @abc.abstractmethod
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """获取用户的所有会话"""
        pass
    
    @abc.abstractmethod
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话，返回清理数量"""
        pass
    
    # 视频管理方法
    @abc.abstractmethod
    def create_video(self, video: Video) -> bool:
        """创建视频记录"""
        pass
    
    @abc.abstractmethod
    def get_video(self, video_id: str) -> Optional[Video]:
        """获取视频"""
        pass
    
    @abc.abstractmethod
    def update_video(self, video: Video) -> bool:
        """更新视频信息"""
        pass
    
    @abc.abstractmethod
    def delete_video(self, video_id: str) -> bool:
        """删除视频"""
        pass
    
    @abc.abstractmethod
    def get_user_videos(self, user_id: str) -> List[Video]:
        """获取用户的所有视频"""
        pass
    
    # 对话管理方法
    @abc.abstractmethod
    def create_conversation(self, conversation: Conversation) -> bool:
        """创建对话记录"""
        pass
    
    @abc.abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        pass
    
    @abc.abstractmethod
    def update_conversation(self, conversation: Conversation) -> bool:
        """更新对话"""
        pass
    
    @abc.abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        pass
    
    @abc.abstractmethod
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """获取用户的所有对话"""
        pass
    
    @abc.abstractmethod
    def get_video_conversations(self, video_id: str) -> List[Conversation]:
        """获取视频的所有对话"""
        pass
    
    # 统计方法
    @abc.abstractmethod
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        pass
    
    @abc.abstractmethod
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        pass
    
    # 数据清理方法
    @abc.abstractmethod
    def cleanup_user_data(self, user_id: str) -> bool:
        """清理用户的所有数据"""
        pass
    
    @abc.abstractmethod
    def backup_data(self, backup_path: str) -> bool:
        """备份数据"""
        pass
    
    @abc.abstractmethod
    def restore_data(self, backup_path: str) -> bool:
        """恢复数据"""
        pass