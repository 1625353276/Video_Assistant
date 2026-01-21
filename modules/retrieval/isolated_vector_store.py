#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户隔离的向量存储模块

基于原有 VectorStore，添加用户隔离支持
"""

import logging
from typing import List, Dict, Optional, Union
from pathlib import Path

# 导入原有模块
from .vector_store import VectorStore
# 导入用户上下文
try:
    from deploy.utils.user_context import get_current_user_id, get_current_user_paths
except ImportError:
    # 如果不在部署环境中，使用原有模块
    get_current_user_id = lambda: None
    get_current_user_paths = lambda: None

logger = logging.getLogger(__name__)


class IsolatedVectorStore(VectorStore):
    """用户隔离的向量存储和检索服务"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None,
                 mirror_site: str = "official",
                 user_id: Optional[str] = None):
        """
        初始化用户隔离的向量存储
        
        Args:
            model_name: 句子转换器模型名称
            device: 计算设备 (cuda/cpu)，自动检测如果未指定
            cache_dir: 模型缓存目录，默认使用项目下的models目录
            mirror_site: 使用的镜像站点 (official/tuna/bfsu/aliyun)
            user_id: 用户ID，如果为None则使用当前用户
        """
        # 获取用户ID
        if user_id is None:
            user_id = get_current_user_id()
        
        self.user_id = user_id
        
        # 获取用户路径管理器
        self.user_paths = get_current_user_paths()
        if not self.user_paths:
            raise ValueError("无法获取用户路径管理器，请确保用户已登录")
        
        # 调用父类初始化，但不传递缓存目录（使用默认）
        super().__init__(model_name, device, cache_dir, mirror_site)
        
        logger.info(f"初始化用户隔离向量存储，用户ID: {self.user_id}")
    
    def get_user_vector_index_path(self, video_id: str) -> Path:
        """
        获取用户专属的向量索引文件路径
        
        Args:
            video_id: 视频ID
            
        Returns:
            Path: 向量索引文件路径
        """
        if not self.user_paths:
            raise ValueError("用户路径管理器不可用")
        
        return self.user_paths.get_vector_index_path(video_id)
    
    def save_user_index(self, video_id: str) -> None:
        """
        保存向量索引到用户专属目录
        
        Args:
            video_id: 视频ID
        """
        try:
            index_path = self.get_user_vector_index_path(video_id)
            self.save_index(index_path)
            logger.info(f"用户 {self.user_id} 的向量索引已保存到: {index_path}")
        except Exception as e:
            logger.error(f"保存用户向量索引失败: {str(e)}")
            raise RuntimeError(f"保存用户向量索引失败: {str(e)}")
    
    def load_user_index(self, video_id: str) -> bool:
        """
        从用户专属目录加载向量索引
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: 是否成功加载
        """
        try:
            index_path = self.get_user_vector_index_path(video_id)
            
            if not index_path.exists():
                logger.info(f"用户 {self.user_id} 的向量索引不存在: {index_path}")
                return False
            
            self.load_index(index_path)
            logger.info(f"用户 {self.user_id} 的向量索引已从 {index_path} 加载")
            return True
        except Exception as e:
            logger.error(f"加载用户向量索引失败: {str(e)}")
            return False
    
    def user_index_exists(self, video_id: str) -> bool:
        """
        检查用户专属的向量索引是否存在
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: 索引是否存在
        """
        try:
            index_path = self.get_user_vector_index_path(video_id)
            return index_path.exists()
        except Exception as e:
            logger.error(f"检查用户向量索引存在性失败: {str(e)}")
            return False
    
    def delete_user_index(self, video_id: str) -> bool:
        """
        删除用户专属的向量索引
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            index_path = self.get_user_vector_index_path(video_id)
            
            if index_path.exists():
                index_path.unlink()
                logger.info(f"用户 {self.user_id} 的向量索引已删除: {index_path}")
                return True
            else:
                logger.info(f"用户 {self.user_id} 的向量索引不存在，无需删除: {index_path}")
                return True
        except Exception as e:
            logger.error(f"删除用户向量索引失败: {str(e)}")
            return False
    
    def get_user_stats(self) -> Dict:
        """
        获取用户隔离向量存储的统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = self.get_stats()
        stats.update({
            "user_id": self.user_id,
            "user_isolated": True,
            "user_paths": str(self.user_paths) if self.user_paths else None
        })
        return stats


def get_isolated_vector_store(user_id: Optional[str] = None, **kwargs) -> IsolatedVectorStore:
    """
    获取用户隔离的向量存储实例
    
    Args:
        user_id: 用户ID，如果为None则使用当前用户
        **kwargs: 其他初始化参数
        
    Returns:
        IsolatedVectorStore: 用户隔离的向量存储实例
    """
    return IsolatedVectorStore(user_id=user_id, **kwargs)