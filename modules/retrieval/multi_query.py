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


class RuleBasedExpander(QueryExpander):
    """基于规则的查询扩展器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化基于规则的扩展器
        
        Args:
            config_path: 同义词词典配置文件路径
        """
        self.synonym_dict = {}
        self.domain_terms = {}
        self.load_dictionaries(config_path)
    
    def load_dictionaries(self, config_path: Optional[str] = None):
        """加载同义词词典和领域术语"""
        # 默认同义词词典
        self.synonym_dict = {
            # 中文同义词
            "智能手机": ["手机", "移动设备", "手持设备", "智能终端"],
            "定位": ["位置", "位置服务", "定位服务", "导航"],
            "原理": ["机制", "工作原理", "工作方式", "实现方式"],
            "技术": ["科技", "技术方案", "技术手段", "方法"],
            "系统": ["体系", "框架", "架构", "平台"],
            
            # 英文同义词
            "smartphone": ["phone", "mobile device", "handheld device", "cell phone"],
            "location": ["position", "positioning", "gps", "navigation"],
            "technology": ["tech", "technique", "method", "approach"],
            "system": ["framework", "platform", "architecture", "structure"]
        }
        
        # 领域术语映射
        self.domain_terms = {
            # 技术术语映射
            "GPS": ["全球定位系统", "卫星定位", "Global Positioning System"],
            "AI": ["人工智能", "机器学习", "深度学习", "artificial intelligence"],
            "API": ["应用程序接口", "接口", "application programming interface"],
            
            # 通用术语映射
            "如何": ["怎样", "怎么", "how to"],
            "什么": ["啥", "是什么", "what is"],
            "为什么": ["为何", "why", "原因"]
        }
        
        # 如果提供了配置文件，从文件加载
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.synonym_dict.update(config.get('synonyms', {}))
                    self.domain_terms.update(config.get('domain_terms', {}))
                logger.info(f"从 {config_path} 加载了自定义词典")
            except Exception as e:
                logger.warning(f"加载词典配置失败: {e}")
    
    def get_method_name(self) -> str:
        return "rule_based"
    
    def expand(self, query: str, **kwargs) -> List[GeneratedQuery]:
        """基于规则扩展查询"""
        queries = []
        
        # 1. 同义词替换
        synonym_queries = self._expand_by_synonyms(query)
        queries.extend(synonym_queries)
        
        # 2. 领域术语映射
        domain_queries = self._expand_by_domain_terms(query)
        queries.extend(domain_queries)
        
        # 3. 句式变化
        pattern_queries = self._expand_by_patterns(query)
        queries.extend(pattern_queries)
        
        return queries
    
    def _expand_by_synonyms(self, query: str) -> List[GeneratedQuery]:
        """基于同义词扩展"""
        queries = []
        
        for term, synonyms in self.synonym_dict.items():
            if term in query:
                for synonym in synonyms:
                    new_query = query.replace(term, synonym)
                    if new_query != query:
                        weight = 0.9  # 同义词替换权重较高
                        queries.append(GeneratedQuery(
                            query=new_query,
                            method="synonym",
                            weight=weight,
                            metadata={"original_term": term, "synonym": synonym}
                        ))
        
        return queries
    
    def _expand_by_domain_terms(self, query: str) -> List[GeneratedQuery]:
        """基于领域术语扩展"""
        queries = []
        
        for term, mappings in self.domain_terms.items():
            if term.lower() in query.lower():
                for mapping in mappings:
                    # 保持大小写
                    if term.isupper():
                        new_term = mapping.upper()
                    elif term[0].isupper():
                        new_term = mapping[0].upper() + mapping[1:]
                    else:
                        new_term = mapping
                    
                    new_query = query.replace(term, new_term)
                    if new_query != query:
                        weight = 0.8  # 领域术语映射权重中等
                        queries.append(GeneratedQuery(
                            query=new_query,
                            method="domain_term",
                            weight=weight,
                            metadata={"original_term": term, "mapping": mapping}
                        ))
        
        return queries
    
    def _expand_by_patterns(self, query: str) -> List[GeneratedQuery]:
        """基于句式模式扩展"""
        queries = []
        
        # 问句模式变化
        question_patterns = [
            (r"什么是(.+)", r"\1是什么"),
            (r"如何(.+)", r"\1的方法"),
            (r"为什么(.+)", r"\1的原因"),
            (r"(.+)是什么", r"什么是\1"),
            (r"(.+)如何工作", r"\1的工作原理"),
        ]
        
        import re
        for pattern, replacement in question_patterns:
            match = re.search(pattern, query)
            if match:
                new_query = re.sub(pattern, replacement, query)
                if new_query != query:
                    weight = 0.7  # 句式变化权重较低
                    queries.append(GeneratedQuery(
                        query=new_query,
                        method="pattern",
                        weight=weight,
                        metadata={"pattern": pattern, "replacement": replacement}
                    ))
        
        return queries


class ModelBasedExpander(QueryExpander):
    """基于语言模型的查询扩展器"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.7):
        """
        初始化基于模型的扩展器
        
        Args:
            model_name: 句子变换器模型名称
            similarity_threshold: 相似度阈值
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载语言模型"""
        try:
            from sentence_transformers import SentenceTransformer
            # 使用与VectorStore相同的模型
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"加载模型: {self.model_name}")
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
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
            "synonym": 0.9,
            "domain_term": 0.8,
            "pattern": 0.7,
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
                 config_path: Optional[str] = None,
                 enable_rule_based: bool = True,
                 enable_model_based: bool = True,
                 max_queries: int = 10):
        """
        初始化多查询生成器
        
        Args:
            config_path: 配置文件路径
            enable_rule_based: 是否启用基于规则的扩展
            enable_model_based: 是否启用基于模型的扩展
            max_queries: 最大生成查询数量
        """
        self.config_path = config_path
        self.enable_rule_based = enable_rule_based
        self.enable_model_based = enable_model_based
        self.max_queries = max_queries
        
        # 初始化扩展器
        self.expanders = []
        self.weight_manager = QueryWeightManager()
        
        if enable_rule_based:
            self.expanders.append(RuleBasedExpander(config_path))
        
        if enable_model_based:
            self.expanders.append(ModelBasedExpander())
        
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
            "enable_rule_based": self.enable_rule_based,
            "enable_model_based": self.enable_model_based,
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
            
            self.enable_rule_based = config.get('enable_rule_based', True)
            self.enable_model_based = config.get('enable_model_based', True)
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
            "rule_based_enabled": self.enable_rule_based,
            "model_based_enabled": self.enable_model_based,
            "method_weights": self.weight_manager.method_weights
        }