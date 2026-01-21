#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一路径管理器

提供用户隔离的路径管理功能，替代硬编码路径
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache


class PathManager:
    """统一路径管理器"""
    
    def _get_current_user_id(self) -> Optional[str]:
        """获取当前用户ID"""
        try:
            from deploy.utils.user_context import get_current_user_id
            return get_current_user_id()
        except ImportError:
            return None
    
    def __init__(self, user_id: Optional[str] = None):
        """
        初始化路径管理器
        
        Args:
            user_id: 用户ID，如果为None则使用共享路径
        """
        self.user_id = user_id
        self.is_isolated = user_id is not None
        
        # 基础路径
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
    
    def get_memory_dir(self) -> Path:
        """获取记忆目录"""
        return self.base_path / "memory"
    
    def get_conversations_dir(self) -> Path:
        """获取对话目录"""
        return self.base_path / "conversations"
    
    def get_transcripts_dir(self) -> Path:
        """获取转录目录"""
        return self.base_path / "transcripts"
    
    def get_vectors_dir(self) -> Path:
        """获取向量索引目录"""
        return self.base_path / "vectors"
    
    def get_videos_dir(self) -> Path:
        """获取视频目录"""
        return self.base_path / "videos"
    
    def get_user_videos_dir(self) -> Path:
        """获取用户视频目录（别名方法）"""
        return self.get_videos_dir()
    
    def get_upload_path(self, video_id: str = None, filename: str = None) -> Path:
        """获取上传目录
        
        Args:
            video_id: 视频ID（可选）
            filename: 文件名（可选）
        """
        upload_dir = self.base_path / "uploads"
        if video_id and filename:
            return upload_dir / f"{video_id}_{filename}"
        elif video_id:
            return upload_dir / str(video_id)
        else:
            return upload_dir
    
    def get_cache_dir(self) -> Path:
        """获取缓存目录"""
        return self.base_path / "cache"
    
    def get_temp_dir(self) -> Path:
        """获取临时目录"""
        return self.base_path / "temp"
    
    def get_temp_path(self, filename: str = None) -> Path:
        """获取临时文件路径
        
        Args:
            filename: 文件名（可选）
        """
        temp_dir = self.get_temp_dir()
        if filename:
            return temp_dir / filename
        return temp_dir
    
    def get_user_data_path(self) -> Path:
        """获取用户数据目录"""
        return self.base_path / "data"
    
    def get_config_dir(self) -> Path:
        """获取配置目录"""
        if self.is_isolated:
            return self.base_path / "config"
        else:
            return self.project_root / "config"
    
    def get_logs_dir(self) -> Path:
        """获取日志目录"""
        if self.is_isolated:
            return self.base_path / "logs"
        else:
            return self.project_root / "logs"
    
    def get_memory_buffer_path(self) -> Path:
        """获取记忆缓冲区文件路径"""
        return self.get_memory_dir() / "memory_buffer.pkl"
    
    def get_conversation_path(self, video_id: str) -> Path:
        """获取对话历史文件路径"""
        return self.get_conversations_dir() / f"{video_id}_conversation_history.json"
    
    def get_transcript_path(self, video_id: str) -> Path:
        """获取转录文件路径"""
        return self.get_transcripts_dir() / f"{video_id}_transcript.json"
    
    def get_vector_index_path(self, video_id: str) -> Path:
        """获取向量索引文件路径"""
        return self.get_vectors_dir() / f"{video_id}_vector_index.pkl"
    
    def get_bm25_index_path(self, video_id: str) -> Path:
        """获取BM25索引文件路径"""
        return self.get_vectors_dir() / f"{video_id}_bm25_index.pkl"
    
    def get_hybrid_index_path(self, video_id: str) -> Path:
        """获取混合索引文件路径"""
        return self.get_vectors_dir() / f"{video_id}_hybrid_index.pkl"
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.get_memory_dir(),
            self.get_conversations_dir(),
            self.get_transcripts_dir(),
            self.get_vectors_dir(),
            self.get_videos_dir(),
            self.get_cache_dir(),
            self.get_temp_dir(),
            self.get_config_dir(),
            self.get_logs_dir()
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def base_path(self):
        """动态计算基础路径"""
        if self.is_isolated:
            return self.data_dir / "users" / self.user_id
        else:
            return self.data_dir
    
    def get_relative_path(self, full_path: Path) -> str:
        """获取相对于项目根目录的路径"""
        try:
            return str(full_path.relative_to(self.project_root))
        except ValueError:
            return str(full_path)
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.is_isolated:
            return f"PathManager(user_id={self.user_id})"
        else:
            return "PathManager(shared)"


@lru_cache(maxsize=128)
def get_path_manager(user_id: Optional[str] = None) -> PathManager:
    """
    获取路径管理器实例（带缓存）
    
    Args:
        user_id: 用户ID
        
    Returns:
        PathManager: 路径管理器实例
    """
    if user_id is None:
        # 尝试从用户上下文获取
        try:
            from deploy.utils.user_context import get_current_user_id
            user_id = get_current_user_id()
        except ImportError:
            user_id = None
    
    return PathManager(user_id)


def get_current_user_path_manager() -> Optional[PathManager]:
    """
    获取当前用户的路径管理器
    
    Returns:
        Optional[PathManager]: 当前用户的路径管理器，如果未登录则返回None
    """
    try:
        from deploy.utils.user_context import get_current_user_id
        user_id = get_current_user_id()
        if user_id:
            return get_path_manager(user_id)
        return None
    except ImportError:
        return None


def get_shared_path_manager() -> PathManager:
    """
    获取共享路径管理器
    
    Returns:
        PathManager: 共享路径管理器实例
    """
    return get_path_manager(None)