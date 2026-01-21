#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户隔离的混合检索器模块

基于原有 HybridRetriever，添加用户隔离支持
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

# 导入原有模块
from .hybrid_retriever import HybridRetriever
from .isolated_vector_store import IsolatedVectorStore, get_isolated_vector_store
from .isolated_bm25_retriever import IsolatedBM25Retriever, get_isolated_bm25_retriever
# 导入用户上下文
try:
    from deploy.utils.user_context import get_current_user_id, get_current_user_paths
except ImportError:
    # 如果不在部署环境中，使用原有模块
    get_current_user_id = lambda: None
    get_current_user_paths = lambda: None

logger = logging.getLogger(__name__)


class IsolatedHybridRetriever(HybridRetriever):
    """用户隔离的混合检索器实现"""
    
    def __init__(self, 
                 vector_store: Optional[IsolatedVectorStore] = None,
                 bm25_retriever: Optional[IsolatedBM25Retriever] = None,
                 vector_weight: float = 0.6,
                 bm25_weight: float = 0.4,
                 fusion_method: str = "weighted_average",
                 user_id: Optional[str] = None):
        """
        初始化用户隔离的混合检索器
        
        Args:
            vector_store: 用户隔离的向量存储实例
            bm25_retriever: 用户隔离的BM25检索器实例
            vector_weight: 向量检索权重
            bm25_weight: BM25检索权重
            fusion_method: 融合方法 ("weighted_average", "rrf", "condorcet")
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
        
        # 如果没有提供检索器，创建用户隔离的实例
        if vector_store is None:
            vector_store = get_isolated_vector_store(user_id=user_id)
        
        if bm25_retriever is None:
            bm25_retriever = get_isolated_bm25_retriever(user_id=user_id)
        
        # 确保是用户隔离的实例
        if not isinstance(vector_store, IsolatedVectorStore):
            raise ValueError("vector_store 必须是 IsolatedVectorStore 实例")
        
        if not isinstance(bm25_retriever, IsolatedBM25Retriever):
            raise ValueError("bm25_retriever 必须是 IsolatedBM25Retriever 实例")
        
        # 调用父类初始化
        super().__init__(vector_store, bm25_retriever, vector_weight, bm25_weight, fusion_method)
        
        logger.info(f"初始化用户隔离混合检索器，用户ID: {self.user_id}")
    
    def get_user_hybrid_index_path(self, video_id: str) -> Path:
        """
        获取用户专属的混合索引文件路径
        
        Args:
            video_id: 视频ID
            
        Returns:
            Path: 混合索引文件路径
        """
        if not self.user_paths:
            raise ValueError("用户路径管理器不可用")
        
        return self.user_paths.get_hybrid_index_path(video_id)
    
    def save_user_indexes(self, video_id: str) -> None:
        """
        保存所有索引到用户专属目录
        
        Args:
            video_id: 视频ID
        """
        try:
            # 保存向量索引
            self.vector_store.save_user_index(video_id)
            
            # 保存BM25索引
            self.bm25_retriever.save_user_index(video_id)
            
            # 保存混合索引元数据
            hybrid_index_path = self.get_user_hybrid_index_path(video_id)
            hybrid_index_data = {
                "video_id": video_id,
                "user_id": self.user_id,
                "vector_weight": self.vector_weight,
                "bm25_weight": self.bm25_weight,
                "fusion_method": self.fusion_method,
                "created_at": str(Path().cwd())
            }
            
            import pickle
            with open(hybrid_index_path, 'wb') as f:
                pickle.dump(hybrid_index_data, f)
            
            logger.info(f"用户 {self.user_id} 的混合索引已保存到: {hybrid_index_path}")
            
        except Exception as e:
            logger.error(f"保存用户混合索引失败: {str(e)}")
            raise RuntimeError(f"保存用户混合索引失败: {str(e)}")
    
    def load_user_indexes(self, video_id: str) -> bool:
        """
        从用户专属目录加载所有索引
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: 是否成功加载
        """
        try:
            # 加载向量索引
            vector_loaded = self.vector_store.load_user_index(video_id)
            
            # 加载BM25索引
            bm25_loaded = self.bm25_retriever.load_user_index(video_id)
            
            # 检查混合索引元数据
            hybrid_index_path = self.get_user_hybrid_index_path(video_id)
            hybrid_loaded = hybrid_index_path.exists()
            
            success = vector_loaded and bm25_loaded and hybrid_loaded
            
            if success:
                logger.info(f"用户 {self.user_id} 的混合索引已从 {video_id} 加载")
            else:
                logger.info(f"用户 {self.user_id} 的混合索引不完整: 向量={vector_loaded}, BM25={bm25_loaded}, 混合={hybrid_loaded}")
            
            return success
            
        except Exception as e:
            logger.error(f"加载用户混合索引失败: {str(e)}")
            return False
    
    def user_indexes_exist(self, video_id: str) -> bool:
        """
        检查用户专属的所有索引是否存在
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: 所有索引是否存在
        """
        try:
            vector_exists = self.vector_store.user_index_exists(video_id)
            bm25_exists = self.bm25_retriever.user_index_exists(video_id)
            hybrid_exists = self.get_user_hybrid_index_path(video_id).exists()
            
            return vector_exists and bm25_exists and hybrid_exists
        except Exception as e:
            logger.error(f"检查用户混合索引存在性失败: {str(e)}")
            return False
    
    def delete_user_indexes(self, video_id: str) -> bool:
        """
        删除用户专属的所有索引
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 删除向量索引
            vector_deleted = self.vector_store.delete_user_index(video_id)
            
            # 删除BM25索引
            bm25_deleted = self.bm25_retriever.delete_user_index(video_id)
            
            # 删除混合索引元数据
            hybrid_index_path = self.get_user_hybrid_index_path(video_id)
            if hybrid_index_path.exists():
                hybrid_index_path.unlink()
                hybrid_deleted = True
            else:
                hybrid_deleted = True
            
            success = vector_deleted and bm25_deleted and hybrid_deleted
            
            if success:
                logger.info(f"用户 {self.user_id} 的混合索引已删除: {video_id}")
            else:
                logger.warning(f"用户 {self.user_id} 的混合索引删除不完整: 向量={vector_deleted}, BM25={bm25_deleted}, 混合={hybrid_deleted}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除用户混合索引失败: {str(e)}")
            return False
    
    def build_user_index(self, video_id: str, documents: List[Dict]) -> None:
        """
        为用户构建专属的混合索引
        
        Args:
            video_id: 视频ID
            documents: 文档列表
        """
        try:
            logger.info(f"为用户 {self.user_id} 构建混合索引，视频ID: {video_id}")
            
            # 清空现有索引
            self.clear()
            
            # 添加文档
            self.add_documents(documents)
            
            # 保存索引
            self.save_user_indexes(video_id)
            
            logger.info(f"用户 {self.user_id} 的混合索引构建完成，包含 {len(documents)} 个文档")
            
        except Exception as e:
            logger.error(f"构建用户混合索引失败: {str(e)}")
            raise RuntimeError(f"构建用户混合索引失败: {str(e)}")
    
    def get_user_stats(self) -> Dict:
        """
        获取用户隔离混合检索器的统计信息
        
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


def get_isolated_hybrid_retriever(user_id: Optional[str] = None, **kwargs) -> IsolatedHybridRetriever:
    """
    获取用户隔离的混合检索器实例
    
    Args:
        user_id: 用户ID，如果为None则使用当前用户
        **kwargs: 其他初始化参数
        
    Returns:
        IsolatedHybridRetriever: 用户隔离的混合检索器实例
    """
    return IsolatedHybridRetriever(user_id=user_id, **kwargs)