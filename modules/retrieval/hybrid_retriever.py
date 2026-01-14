#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合检索器模块

职责：
- 实现向量检索和BM25检索的结果融合
- 支持多种融合策略(加权平均、排序融合等)
- 提供统一的检索接口
"""

import logging
from typing import List, Dict, Optional, Union, Tuple
import numpy as np

from .vector_store import VectorStore
from .bm25_retriever import BM25Retriever

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器实现，结合向量检索和BM25检索"""
    
    def __init__(self, 
                 vector_store: VectorStore,
                 bm25_retriever: BM25Retriever,
                 vector_weight: float = 0.5,
                 bm25_weight: float = 0.5,
                 fusion_method: str = "weighted_average"):
        """
        初始化混合检索器
        
        Args:
            vector_store: 向量存储实例
            bm25_retriever: BM25检索器实例
            vector_weight: 向量检索权重
            bm25_weight: BM25检索权重
            fusion_method: 融合方法 ("weighted_average", "rrf", "condorcet")
        """
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.fusion_method = fusion_method
        
        # 归一化权重
        total_weight = vector_weight + bm25_weight
        self.vector_weight = vector_weight / total_weight
        self.bm25_weight = bm25_weight / total_weight
        
        logger.info(f"初始化混合检索器，向量权重: {self.vector_weight:.2f}, "
                   f"BM25权重: {self.bm25_weight:.2f}, 融合方法: {fusion_method}")
    
    def add_documents(self, documents: List[Dict], 
                     text_field: str = "text",
                     metadata_fields: Optional[List[str]] = None) -> None:
        """
        添加文档到两个检索器
        
        Args:
            documents: 文档列表
            text_field: 文本字段名
            metadata_fields: 要保留的元数据字段列表
        """
        try:
            # 添加到向量存储
            self.vector_store.add_documents(documents, text_field, metadata_fields)
            
            # 添加到BM25检索器
            self.bm25_retriever.add_documents(documents, text_field, metadata_fields)
            
            logger.info(f"成功添加 {len(documents)} 个文档到混合检索器")
            
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            raise RuntimeError(f"添加文档失败: {str(e)}")
    
    def search(self, query: str, 
               top_k: int = 5,
               threshold: float = 0.0,
               vector_top_k: Optional[int] = None,
               bm25_top_k: Optional[int] = None) -> List[Dict]:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回的最相关文档数量
            threshold: 相关性阈值
            vector_top_k: 向量检索返回的文档数量(默认为top_k*2)
            bm25_top_k: BM25检索返回的文档数量(默认为top_k*2)
            
        Returns:
            List[Dict]: 相关文档列表
        """
        try:
            # 设置默认的检索数量
            if vector_top_k is None:
                vector_top_k = max(top_k * 2, 10)
            if bm25_top_k is None:
                bm25_top_k = max(top_k * 2, 10)
            
            logger.info(f"执行混合检索，查询: '{query}', top_k: {top_k}")
            
            # 执行向量检索
            vector_results = self.vector_store.search(query, top_k=vector_top_k, threshold=0.0)
            
            # 执行BM25检索
            bm25_results = self.bm25_retriever.search(query, top_k=bm25_top_k, threshold=0.0)
            
            logger.info(f"向量检索返回 {len(vector_results)} 个结果，BM25检索返回 {len(bm25_results)} 个结果")
            
            # 融合结果
            if self.fusion_method == "weighted_average":
                fused_results = self._weighted_average_fusion(vector_results, bm25_results)
            elif self.fusion_method == "rrf":
                fused_results = self._rrf_fusion(vector_results, bm25_results)
            elif self.fusion_method == "condorcet":
                fused_results = self._condorcet_fusion(vector_results, bm25_results)
            else:
                raise ValueError(f"未知的融合方法: {self.fusion_method}")
            
            # 应用阈值并返回top_k结果
            final_results = []
            for result in fused_results:
                if result["score"] >= threshold:
                    final_results.append(result)
                    if len(final_results) >= top_k:
                        break
            
            logger.info(f"混合检索完成，返回 {len(final_results)} 个结果")
            
            return final_results
            
        except Exception as e:
            logger.error(f"混合检索失败: {str(e)}")
            raise RuntimeError(f"混合检索失败: {str(e)}")
    
    def _weighted_average_fusion(self, vector_results: List[Dict], 
                                bm25_results: List[Dict]) -> List[Dict]:
        """
        加权平均融合
        
        Args:
            vector_results: 向量检索结果
            bm25_results: BM25检索结果
            
        Returns:
            List[Dict]: 融合后的结果
        """
        # 创建文档ID到结果的映射
        vector_map = {result["index"]: result for result in vector_results}
        bm25_map = {result["index"]: result for result in bm25_results}
        
        # 获取所有文档索引
        all_indices = set(vector_map.keys()).union(set(bm25_map.keys()))
        
        fused_results = []
        
        for idx in all_indices:
            vector_score = 0.0
            bm25_score = 0.0
            
            # 获取向量分数并进行归一化
            if idx in vector_map:
                vector_score = vector_map[idx]["similarity"]
            
            # 获取BM25分数并进行归一化
            if idx in bm25_map:
                bm25_score = bm25_map[idx]["score"]
                # BM25分数可能很大，需要进行归一化
                max_bm25_score = max(result["score"] for result in bm25_results) if bm25_results else 1.0
                if max_bm25_score > 0:
                    bm25_score = bm25_score / max_bm25_score
            
            # 计算加权平均分数
            fused_score = (self.vector_weight * vector_score + 
                          self.bm25_weight * bm25_score)
            
            # 使用向量检索的结果作为基础(包含更多元数据)
            if idx in vector_map:
                result = vector_map[idx].copy()
            else:
                result = bm25_map[idx].copy()
            
            # 更新分数
            result["score"] = fused_score
            result["vector_score"] = vector_score
            result["bm25_score"] = bm25_score
            
            # 将document中的常用字段提取到顶层，方便访问
            if "document" in result:
                for key in ["text", "id", "start", "end", "confidence"]:
                    if key in result["document"]:
                        result[key] = result["document"][key]
            
            fused_results.append(result)
        
        # 按分数排序
        fused_results.sort(key=lambda x: x["score"], reverse=True)
        
        return fused_results
    
    def _rrf_fusion(self, vector_results: List[Dict], 
                   bm25_results: List[Dict], 
                   k: int = 60) -> List[Dict]:
        """
        倒排序融合(Reciprocal Rank Fusion)
        
        Args:
            vector_results: 向量检索结果
            bm25_results: BM25检索结果
            k: RRF参数，通常设置为60
            
        Returns:
            List[Dict]: 融合后的结果
        """
        # 创建文档ID到排名的映射
        vector_ranks = {result["index"]: rank + 1 for rank, result in enumerate(vector_results)}
        bm25_ranks = {result["index"]: rank + 1 for rank, result in enumerate(bm25_results)}
        
        # 获取所有文档索引
        all_indices = set(vector_ranks.keys()).union(set(bm25_ranks.keys()))
        
        fused_results = []
        
        for idx in all_indices:
            # 计算RRF分数
            vector_rrf = 0.0
            bm25_rrf = 0.0
            
            if idx in vector_ranks:
                vector_rrf = 1.0 / (k + vector_ranks[idx])
            
            if idx in bm25_ranks:
                bm25_rrf = 1.0 / (k + bm25_ranks[idx])
            
            # 加权融合
            fused_score = self.vector_weight * vector_rrf + self.bm25_weight * bm25_rrf
            
            # 使用向量检索的结果作为基础
            if idx in {result["index"] for result in vector_results}:
                result = next(r for r in vector_results if r["index"] == idx)
            else:
                result = next(r for r in bm25_results if r["index"] == idx)
            
            # 更新分数
            result = result.copy()
            result["score"] = fused_score
            result["vector_rank"] = vector_ranks.get(idx, len(vector_results) + 1)
            result["bm25_rank"] = bm25_ranks.get(idx, len(bm25_results) + 1)
            
            # 将document中的常用字段提取到顶层，方便访问
            if "document" in result:
                for key in ["text", "id", "start", "end", "confidence"]:
                    if key in result["document"]:
                        result[key] = result["document"][key]
            
            fused_results.append(result)
        
        # 按分数排序
        fused_results.sort(key=lambda x: x["score"], reverse=True)
        
        return fused_results
    
    def _condorcet_fusion(self, vector_results: List[Dict], 
                         bm25_results: List[Dict]) -> List[Dict]:
        """
        Condorcet融合方法
        
        Args:
            vector_results: 向量检索结果
            bm25_results: BM25检索结果
            
        Returns:
            List[Dict]: 融合后的结果
        """
        # 创建文档ID到排名的映射
        vector_ranks = {result["index"]: rank + 1 for rank, result in enumerate(vector_results)}
        bm25_ranks = {result["index"]: rank + 1 for rank, result in enumerate(bm25_results)}
        
        # 获取所有文档索引
        all_indices = set(vector_ranks.keys()).union(set(bm25_ranks.keys()))
        
        # Condorcet投票：对于每对文档，比较它们在两个排名中的位置
        def condorcet_winner(doc_idx1, doc_idx2):
            """判断doc_idx1是否是Condorcet赢家"""
            vector_win = vector_ranks.get(doc_idx1, float('inf')) < vector_ranks.get(doc_idx2, float('inf'))
            bm25_win = bm25_ranks.get(doc_idx1, float('inf')) < bm25_ranks.get(doc_idx2, float('inf'))
            return vector_win and bm25_win
        
        # 简化的Condorcet实现：计算每个文档击败的其他文档数量
        win_counts = {}
        for idx in all_indices:
            win_count = 0
            for other_idx in all_indices:
                if idx != other_idx and condorcet_winner(idx, other_idx):
                    win_count += 1
            win_counts[idx] = win_count
        
        # 构建结果
        fused_results = []
        for idx in sorted(all_indices, key=lambda x: win_counts[x], reverse=True):
            # 使用向量检索的结果作为基础
            if idx in {result["index"] for result in vector_results}:
                result = next(r for r in vector_results if r["index"] == idx)
            else:
                result = next(r for r in bm25_results if r["index"] == idx)
            
            result = result.copy()
            result["score"] = win_counts[idx] / len(all_indices)  # 归一化分数
            result["condorcet_wins"] = win_counts[idx]
            
            # 将document中的常用字段提取到顶层，方便访问
            if "document" in result:
                for key in ["text", "id", "start", "end", "confidence"]:
                    if key in result["document"]:
                        result[key] = result["document"][key]
            
            fused_results.append(result)
        
        return fused_results
    
    def get_stats(self) -> Dict:
        """
        获取混合检索器统计信息
        
        Returns:
            Dict: 统计信息
        """
        vector_stats = self.vector_store.get_stats()
        bm25_stats = self.bm25_retriever.get_stats()
        
        stats = {
            "fusion_method": self.fusion_method,
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
            "vector_store": vector_stats,
            "bm25_retriever": bm25_stats
        }
        
        return stats
    
    def clear(self) -> None:
        """清空两个检索器"""
        self.vector_store.clear()
        self.bm25_retriever.clear()
        logger.info("混合检索器已清空")
    
    def save_indexes(self, vector_save_path: str, bm25_save_path: str) -> None:
        """
        保存两个检索器的索引
        
        Args:
            vector_save_path: 向量索引保存路径
            bm25_save_path: BM25索引保存路径
        """
        try:
            self.vector_store.save_index(vector_save_path)
            self.bm25_retriever.save_index(bm25_save_path)
            logger.info("混合检索器索引已保存")
        except Exception as e:
            logger.error(f"保存索引失败: {str(e)}")
            raise RuntimeError(f"保存索引失败: {str(e)}")
    
    def load_indexes(self, vector_load_path: str, bm25_load_path: str) -> None:
        """
        加载两个检索器的索引
        
        Args:
            vector_load_path: 向量索引加载路径
            bm25_load_path: BM25索引加载路径
        """
        try:
            self.vector_store.load_index(vector_load_path)
            self.bm25_retriever.load_index(bm25_load_path)
            logger.info("混合检索器索引已加载")
        except Exception as e:
            logger.error(f"加载索引失败: {str(e)}")
            raise RuntimeError(f"加载索引失败: {str(e)}")