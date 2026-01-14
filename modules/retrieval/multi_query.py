#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多查询生成器模块

职责：
- 实现查询扩展和多样化生成
- 支持基于规则的查询扩展
- 支持基于语言模型的查询生成
- 提供查询权重分配和结果格式化
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import defaultdict

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GeneratedQuery:
    """生成的查询数据结构"""
    query: str
    method: str
    weight: float
    metadata: Optional[Dict] = None


@dataclass
class MultiQueryResult:
    """多查询生成结果"""
    original_query: str
    generated_queries: List[GeneratedQuery]
    generation_time: str
    total_queries: int
    generation_methods: List[str]


class QueryExpander(ABC):
    """查询扩展器抽象基类"""
    
    @abstractmethod
    def expand(self, query: str, **kwargs) -> List[GeneratedQuery]:
        """扩展查询的抽象方法"""
        pass
    
    @abstractmethod
    def get_method_name(self) -> str:
        """获取扩展方法名称"""
        pass


class ModelBasedExpander(QueryExpander):
    """基于语言模型的查询扩展器"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.7,
                 cache_dir: Optional[str] = None):
        """
        初始化基于模型的扩展器
        
        Args:
            model_name: 句子变换器模型名称
            similarity_threshold: 相似度阈值
            cache_dir: 模型缓存目录
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.model = None
        
        # 设置缓存目录
        if cache_dir is None:
            # 获取项目根目录
            current_dir = Path(__file__).parent.parent.parent
            self.cache_dir = current_dir / "models"
        else:
            self.cache_dir = Path(cache_dir)
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_model()
    
    def _load_model(self):
        """加载语言模型"""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            # 确定设备
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            # 设置模型缓存目录
            cache_folder = self.cache_dir / "sentence-transformers"
            cache_folder.mkdir(parents=True, exist_ok=True)
            
            # 检查模型是否已在本地缓存
            model_cache_path = cache_folder / ("models--" + self.model_name.replace("/", "--"))
            snapshots_path = model_cache_path / "snapshots"
            
            # 检查模型缓存是否存在且包含快照
            has_valid_cache = False
            if model_cache_path.exists() and snapshots_path.exists():
                snapshot_dirs = [d for d in snapshots_path.iterdir() if d.is_dir()]
                if snapshot_dirs:
                    snapshot_path = snapshot_dirs[0]
                    required_files = ["config.json", "modules.json", "model.safetensors"]
                    missing_files = [f for f in required_files if not (snapshot_path / f).exists()]
                    
                    if not missing_files:
                        has_valid_cache = True
                        logger.info(f"发现本地模型缓存: {model_cache_path}")
            
            # 优先使用本地缓存
            if has_valid_cache:
                try:
                    logger.info("尝试使用本地模型缓存，禁用网络下载")
                    self.model = SentenceTransformer(
                        self.model_name,
                        device=device,
                        cache_folder=str(cache_folder),
                        local_files_only=True
                    )
                    logger.info(f"模型加载成功（本地缓存）")
                    return
                except Exception as e:
                    logger.warning(f"本地缓存加载失败: {str(e)}")
            
            # 如果本地缓存不可用，尝试网络下载
            logger.warning("本地模型不可用，尝试从网络下载...")
            try:
                self.model = SentenceTransformer(
                    self.model_name,
                    device=device,
                    cache_folder=str(cache_folder)
                )
                logger.info(f"模型加载成功（网络下载）")
                logger.info(f"模型文件已保存到: {cache_folder}")
                return
            except Exception as e:
                logger.error(f"模型加载失败: {str(e)}")
                self.model = None
                
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self.model = None
    
    def get_method_name(self) -> str:
        return "model_based"
    
    def expand(self, query: str, **kwargs) -> List[GeneratedQuery]:
        """基于模型扩展查询"""
        if self.model is None:
            logger.warning("模型未加载，跳过基于模型的扩展")
            return []
        
        queries = []
        
        # 1. 语义相似查询生成
        semantic_queries = self._expand_by_semantics(query, **kwargs)
        queries.extend(semantic_queries)
        
        # 2. 关键词扩展
        keyword_queries = self._expand_by_keywords(query, **kwargs)
        queries.extend(keyword_queries)
        
        return queries
    
    def _expand_by_semantics(self, query: str, candidate_queries: Optional[List[str]] = None, **kwargs) -> List[GeneratedQuery]:
        """基于语义相似度扩展"""
        if not candidate_queries:
            # 如果没有提供候选查询，使用预定义的模板
            candidate_queries = self._generate_candidate_queries(query)
        
        queries = []
        
        try:
            # 计算原始查询的向量
            query_embedding = self.model.encode([query], convert_to_tensor=True)
            
            # 计算候选查询的向量
            candidate_embeddings = self.model.encode(candidate_queries, convert_to_tensor=True)
            
            # 计算相似度
            from sentence_transformers import util
            similarities = util.cos_sim(query_embedding, candidate_embeddings)[0]
            
            # 选择相似度高于阈值的查询
            for i, similarity in enumerate(similarities):
                if similarity >= self.similarity_threshold:
                    weight = float(similarity) * 0.8  # 模型生成的权重
                    queries.append(GeneratedQuery(
                        query=candidate_queries[i],
                        method="semantic",
                        weight=weight,
                        metadata={"similarity": float(similarity)}
                    ))
        
        except Exception as e:
            logger.error(f"语义扩展失败: {e}")
        
        return queries
    
    def _expand_by_keywords(self, query: str, **kwargs) -> List[GeneratedQuery]:
        """基于关键词扩展"""
        queries = []
        
        # 智能分词：支持中英文
        words = self._smart_tokenize(query)
        if len(words) > 1:  # 降低要求，只要多于1个词就尝试扩展
            # 生成部分查询
            for i in range(len(words) - 1):
                partial_query = "".join(words[i:i+2]) if self._is_chinese(words[i]) else " ".join(words[i:i+2])
                if len(partial_query) > 2:  # 过滤太短的查询
                    weight = 0.6
                    queries.append(GeneratedQuery(
                        query=partial_query,
                        method="keyword",
                        weight=weight,
                        metadata={"type": "partial", "indices": [i, i+1]}
                    ))
        
        return queries
    
    def _smart_tokenize(self, text: str) -> List[str]:
        """智能分词，支持中英文"""
        import re
        
        # 检测是否包含中文
        if self._is_chinese(text):
            # 中文按字符分词（简单实现，实际可以使用jieba等分词库）
            # 这里按2-4个字符一组进行分词
            words = []
            for i in range(len(text)):
                # 2字符词
                if i + 1 < len(text):
                    words.append(text[i:i+2])
                # 3字符词
                if i + 2 < len(text):
                    words.append(text[i:i+3])
                # 4字符词
                if i + 3 < len(text):
                    words.append(text[i:i+4])
            return list(set(words))  # 去重
        else:
            # 英文按空格分词
            return text.split()
    
    def _is_chinese(self, text: str) -> bool:
        """检测文本是否包含中文"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def _generate_candidate_queries(self, query: str) -> List[str]:
        """生成候选查询"""
        candidates = []
        
        # 基于查询模板生成
        templates = [
            f"{query}的工作原理",
            f"{query}的实现方法",
            f"如何理解{query}",
            f"{query}的特点",
            f"{query}的应用",
        ]
        
        # 检测语言并生成相应的模板
        if any('\u4e00' <= char <= '\u9fff' for char in query):
            # 中文查询
            templates.extend([
                f"{query}是什么",
                f"为什么需要{query}",
                f"{query}的优势",
                f"{query}的缺点",
            ])
        else:
            # 英文查询
            templates.extend([
                f"what is {query}",
                f"how does {query} work",
                f"advantages of {query}",
                f"disadvantages of {query}",
            ])
        
        return templates


class QueryWeightManager:
    """查询权重管理器"""
    
    def __init__(self, method_weights: Optional[Dict[str, float]] = None):
        """
        初始化权重管理器
        
        Args:
            method_weights: 不同扩展方法的权重配置
        """
        self.method_weights = method_weights or {
            "semantic": 0.8,
            "keyword": 0.6,
            "original": 1.0
        }
    
    def normalize_weights(self, queries: List[GeneratedQuery]) -> List[GeneratedQuery]:
        """归一化查询权重"""
        if not queries:
            return queries
        
        # 计算权重总和
        total_weight = sum(q.weight for q in queries)
        
        # 归一化
        normalized_queries = []
        for query in queries:
            normalized_weight = query.weight / total_weight
            normalized_queries.append(GeneratedQuery(
                query=query.query,
                method=query.method,
                weight=normalized_weight,
                metadata=query.metadata
            ))
        
        return normalized_queries
    
    def adjust_weights(self, queries: List[GeneratedQuery]) -> List[GeneratedQuery]:
        """调整查询权重"""
        adjusted_queries = []
        
        for query in queries:
            # 应用方法权重
            method_weight = self.method_weights.get(query.method, 0.5)
            adjusted_weight = query.weight * method_weight
            
            adjusted_queries.append(GeneratedQuery(
                query=query.query,
                method=query.method,
                weight=adjusted_weight,
                metadata=query.metadata
            ))
        
        return adjusted_queries


class MultiQueryGenerator:
    """多查询生成器主类"""
    
    def __init__(self, 
                 max_queries: int = 10,
                 cache_dir: Optional[str] = None):
        """
        初始化多查询生成器
        
        Args:
            max_queries: 最大生成查询数量
            cache_dir: 模型缓存目录
        """
        self.max_queries = max_queries
        
        # 初始化扩展器
        self.expanders = []
        self.weight_manager = QueryWeightManager()
        
        # 只使用模型扩展器
        self.expanders.append(ModelBasedExpander(cache_dir=cache_dir))
        
        logger.info(f"多查询生成器初始化完成，启用了 {len(self.expanders)} 个扩展器")
    
    def generate_queries(self, query: str, **kwargs) -> MultiQueryResult:
        """
        生成多个查询
        
        Args:
            query: 原始查询
            **kwargs: 其他参数
            
        Returns:
            MultiQueryResult: 多查询生成结果
        """
        start_time = time.time()
        
        # 生成查询列表
        all_queries = []
        generation_methods = []
        
        # 添加原始查询
        original_query = GeneratedQuery(
            query=query,
            method="original",
            weight=1.0,
            metadata={"is_original": True}
        )
        all_queries.append(original_query)
        
        # 使用各个扩展器生成查询
        for expander in self.expanders:
            try:
                expanded_queries = expander.expand(query, **kwargs)
                all_queries.extend(expanded_queries)
                generation_methods.append(expander.get_method_name())
            except Exception as e:
                logger.error(f"扩展器 {expander.get_method_name()} 失败: {e}")
        
        # 调整权重
        all_queries = self.weight_manager.adjust_weights(all_queries)
        
        # 归一化权重
        all_queries = self.weight_manager.normalize_weights(all_queries)
        
        # 按权重排序并限制数量
        all_queries.sort(key=lambda x: x.weight, reverse=True)
        final_queries = all_queries[:self.max_queries]
        
        # 重新归一化权重（因为限制了数量）
        if len(final_queries) > 0:
            final_queries = self.weight_manager.normalize_weights(final_queries)
        
        # 创建结果
        generation_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        result = MultiQueryResult(
            original_query=query,
            generated_queries=final_queries,
            generation_time=generation_time,
            total_queries=len(final_queries),
            generation_methods=generation_methods
        )
        
        logger.info(f"生成了 {len(final_queries)} 个查询，耗时 {time.time() - start_time:.2f}s")
        
        return result
    
    def save_config(self, config_path: str):
        """保存配置"""
        config = {
            "max_queries": self.max_queries,
            "method_weights": self.weight_manager.method_weights
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到 {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def load_config(self, config_path: str):
        """加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.max_queries = config.get('max_queries', 10)
            
            if 'method_weights' in config:
                self.weight_manager.method_weights = config['method_weights']
            
            logger.info(f"配置已从 {config_path} 加载")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "enabled_expanders": len(self.expanders),
            "max_queries": self.max_queries,
            "model_based_enabled": True,
            "method_weights": self.weight_manager.method_weights
        }