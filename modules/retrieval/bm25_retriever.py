#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25检索器模块

职责：
- 实现BM25算法进行关键词匹配检索
- 支持中英文分词
- 构建倒排索引
- 计算BM25相关性分数
"""

import os
import re
import pickle
import math
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from collections import Counter, defaultdict

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入中文分词库
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    logger.warning("jieba未安装，中文分词功能将受限")

# 尝试导入英文分词库
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    HAS_NLTK = True
    
    # 设置NLTK数据路径
    import os
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    nltk_data_path = os.path.join(current_dir, 'nltk_data')
    if os.path.exists(nltk_data_path):
        nltk.data.path.append(nltk_data_path)
        logger.info(f"添加NLTK数据路径: {nltk_data_path}")
    
    # 检查必要的数据是否存在
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.warning("NLTK punkt数据未找到，英文分词功能将受限")
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        logger.warning("NLTK stopwords数据未找到，英文停用词功能将受限")
        
except ImportError:
    HAS_NLTK = False
    logger.warning("nltk未安装，英文分词功能将受限")


class BM25Retriever:
    """BM25检索器实现"""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75, epsilon: float = 0.25, 
                 language: str = 'auto', stop_words: Optional[List[str]] = None):
        """
        初始化BM25检索器
        
        Args:
            k1: 控制词频饱和度的参数，通常在1.2-2.0之间
            b: 控制文档长度归一化的参数，通常在0.75左右
            epsilon: IDF下限，防止IDF过小
            language: 分词语言 ('zh', 'en', 'auto')
            stop_words: 自定义停用词列表
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.language = language
        
        # 初始化停用词
        self.stop_words = set(stop_words) if stop_words else set()
        self._init_stop_words()
        
        # 核心数据结构
        self.documents = []  # 原始文档
        self.metadata = []   # 文档元数据
        self.corpus = []     # 分词后的文档
        self.word_doc_freq = defaultdict(int)  # 词-文档频率
        self.doc_lengths = []  # 文档长度
        self.avg_doc_length = 0.0  # 平均文档长度
        self.idf = {}  # 逆文档频率
        
        logger.info(f"初始化BM25检索器，参数: k1={k1}, b={b}, language={language}")
    
    def _init_stop_words(self):
        """初始化停用词表"""
        # 中文停用词
        chinese_stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '就是', '还', '把', '比', '或者', '因为', '所以',
            '但是', '然后', '如果', '虽然', '可是', '然而', '因此', '这样', '那样'
        }
        
        # 英文停用词
        english_stop_words = set()
        if HAS_NLTK:
            try:
                english_stop_words = set(stopwords.words('english'))
            except:
                english_stop_words = {
                    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
                    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
                    'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
                    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
                    'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
                    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
                    'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
                    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for',
                    'with', 'through', 'during', 'before', 'after', 'above', 'below',
                    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
                    'further', 'then', 'once'
                }
        
        # 合并停用词
        self.stop_words.update(chinese_stop_words)
        self.stop_words.update(english_stop_words)
    
    def _detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 输入文本
            
        Returns:
            str: 检测到的语言 ('zh', 'en')
        """
        # 简单的语言检测：统计中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
        
        if total_chars == 0:
            return 'en'  # 默认英文
        
        chinese_ratio = chinese_chars / total_chars
        return 'zh' if chinese_ratio > 0.3 else 'en'
    
    def _tokenize(self, text: str, language: Optional[str] = None) -> List[str]:
        """
        文本分词
        
        Args:
            text: 输入文本
            language: 指定语言，None表示自动检测
            
        Returns:
            List[str]: 分词结果
        """
        if not text or not text.strip():
            return []
        
        # 检测语言
        if language is None:
            language = self._detect_language(text)
        elif language == 'auto':
            language = self._detect_language(text)
        
        tokens = []
        
        if language == 'zh':
            # 中文分词
            if HAS_JIEBA:
                tokens = list(jieba.cut(text))
            else:
                # 简单的中文分词：按字符分割
                tokens = list(re.findall(r'[\u4e00-\u9fff]+', text))
        else:
            # 英文分词 - 使用简单正则表达式避免NLTK依赖
            # 改进的英文分词：处理标点符号和特殊字符
            text = text.lower()
            # 将标点符号替换为空格
            text = re.sub(r'[^\w\s]', ' ', text)
            # 分割单词
            tokens = text.split()
            # 过滤掉非字母的token
            tokens = [token for token in tokens if re.match(r'^[a-zA-Z]+$', token)]
        
        # 过滤停用词和短词
        filtered_tokens = []
        for token in tokens:
            token = token.strip()
            if (len(token) >= 2 and 
                token not in self.stop_words and 
                not token.isspace()):
                filtered_tokens.append(token)
        
        return filtered_tokens
    
    def _calculate_idf(self):
        """计算逆文档频率(IDF)"""
        corpus_size = len(self.corpus)
        
        # 计算每个词的IDF
        for word, freq in self.word_doc_freq.items():
            idf = math.log((corpus_size - freq + 0.5) / (freq + 0.5))
            self.idf[word] = max(idf, self.epsilon)
        
        logger.info(f"计算IDF完成，词汇表大小: {len(self.idf)}")
    
    def add_documents(self, documents: List[Dict], 
                     text_field: str = "text",
                     metadata_fields: Optional[List[str]] = None) -> None:
        """
        添加文档并构建索引
        
        Args:
            documents: 文档列表，每个文档是字典格式
            text_field: 文本字段名
            metadata_fields: 要保留的元数据字段列表
        """
        try:
            if not documents:
                logger.warning("文档列表为空")
                return
            
            logger.info(f"开始添加 {len(documents)} 个文档到BM25索引")
            
            # 处理每个文档
            for doc in documents:
                if text_field not in doc:
                    raise ValueError(f"文档中缺少文本字段: {text_field}")
                
                # 提取文本并分词
                text = doc[text_field]
                tokens = self._tokenize(text)
                
                # 存储文档和元数据
                self.documents.append(doc)
                self.corpus.append(tokens)
                self.doc_lengths.append(len(tokens))
                
                # 处理元数据
                if metadata_fields:
                    meta = {field: doc.get(field) for field in metadata_fields if field in doc}
                else:
                    # 保留除文本字段外的所有字段
                    meta = {k: v for k, v in doc.items() if k != text_field}
                self.metadata.append(meta)
                
                # 更新词频统计
                unique_tokens = set(tokens)
                for token in unique_tokens:
                    self.word_doc_freq[token] += 1
            
            # 计算平均文档长度
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
            
            # 计算IDF
            self._calculate_idf()
            
            logger.info(f"BM25索引构建完成，文档数: {len(self.documents)}, "
                       f"平均文档长度: {self.avg_doc_length:.2f}")
            
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            raise RuntimeError(f"添加文档失败: {str(e)}")
    
    def _calculate_bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """
        计算文档对查询的BM25分数
        
        Args:
            query_tokens: 查询分词结果
            doc_idx: 文档索引
            
        Returns:
            float: BM25分数
        """
        doc_tokens = self.corpus[doc_idx]
        doc_length = self.doc_lengths[doc_idx]
        
        # 计算归一化因子
        normalization_factor = self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
        
        score = 0.0
        
        # 计算每个查询词的BM25贡献
        for token in query_tokens:
            if token not in self.idf:
                continue
            
            # 词频
            tf = doc_tokens.count(token)
            if tf == 0:
                continue
            
            # BM25公式
            idf = self.idf[token]
            tf_component = (tf * (self.k1 + 1)) / (tf + normalization_factor)
            score += idf * tf_component
        
        return score
    
    def search(self, query: str, 
               top_k: int = 5,
               threshold: float = 0.0) -> List[Dict]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回的最相关文档数量
            threshold: 相关性阈值
            
        Returns:
            List[Dict]: 相关文档列表，包含BM25分数
        """
        try:
            if not self.documents:
                logger.warning("BM25索引为空")
                return []
            
            # 查询分词
            query_tokens = self._tokenize(query)
            if not query_tokens:
                logger.warning("查询分词结果为空")
                return []
            
            logger.info(f"执行BM25检索，查询: '{query}', 分词: {query_tokens}")
            
            # 计算所有文档的分数
            scores = []
            for doc_idx in range(len(self.documents)):
                score = self._calculate_bm25_score(query_tokens, doc_idx)
                if score > threshold:
                    scores.append((doc_idx, score))
            
            # 按分数排序
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # 构建结果
            results = []
            for doc_idx, score in scores[:top_k]:
                result = {
                    "document": self.documents[doc_idx],
                    "metadata": self.metadata[doc_idx] if doc_idx < len(self.metadata) else {},
                    "score": float(score),
                    "index": int(doc_idx)
                }
                results.append(result)
            
            logger.info(f"BM25检索完成，返回 {len(results)} 个结果")
            
            return results
            
        except Exception as e:
            logger.error(f"BM25检索失败: {str(e)}")
            raise RuntimeError(f"BM25检索失败: {str(e)}")
    
    def save_index(self, save_path: Union[str, Path]) -> None:
        """
        保存BM25索引到文件
        
        Args:
            save_path: 保存路径
        """
        try:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 准备保存数据
            index_data = {
                "documents": self.documents,
                "metadata": self.metadata,
                "corpus": self.corpus,
                "word_doc_freq": dict(self.word_doc_freq),
                "doc_lengths": self.doc_lengths,
                "avg_doc_length": self.avg_doc_length,
                "idf": self.idf,
                "k1": self.k1,
                "b": self.b,
                "epsilon": self.epsilon,
                "language": self.language,
                "stop_words": list(self.stop_words)
            }
            
            # 保存到文件
            with open(save_path, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.info(f"BM25索引已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存BM25索引失败: {str(e)}")
            raise RuntimeError(f"保存BM25索引失败: {str(e)}")
    
    def load_index(self, load_path: Union[str, Path]) -> None:
        """
        从文件加载BM25索引
        
        Args:
            load_path: 加载路径
        """
        try:
            load_path = Path(load_path)
            
            if not load_path.exists():
                raise FileNotFoundError(f"BM25索引文件不存在: {load_path}")
            
            # 加载数据
            with open(load_path, 'rb') as f:
                index_data = pickle.load(f)
            
            # 恢复状态
            self.documents = index_data["documents"]
            self.metadata = index_data["metadata"]
            self.corpus = index_data["corpus"]
            self.word_doc_freq = defaultdict(int, index_data["word_doc_freq"])
            self.doc_lengths = index_data["doc_lengths"]
            self.avg_doc_length = index_data["avg_doc_length"]
            self.idf = index_data["idf"]
            self.k1 = index_data["k1"]
            self.b = index_data["b"]
            self.epsilon = index_data["epsilon"]
            self.language = index_data["language"]
            self.stop_words = set(index_data["stop_words"])
            
            logger.info(f"BM25索引已从 {load_path} 加载，包含 {len(self.documents)} 个文档")
            
        except Exception as e:
            logger.error(f"加载BM25索引失败: {str(e)}")
            raise RuntimeError(f"加载BM25索引失败: {str(e)}")
    
    def get_stats(self) -> Dict:
        """
        获取BM25检索器统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            "document_count": len(self.documents),
            "vocabulary_size": len(self.word_doc_freq),
            "avg_doc_length": round(self.avg_doc_length, 2),
            "total_tokens": sum(self.doc_lengths),
            "parameters": {
                "k1": self.k1,
                "b": self.b,
                "epsilon": self.epsilon,
                "language": self.language
            },
            "stop_words_count": len(self.stop_words),
            "has_jieba": HAS_JIEBA,
            "has_nltk": HAS_NLTK
        }
        
        return stats
    
    def clear(self) -> None:
        """清空BM25索引"""
        self.documents = []
        self.metadata = []
        self.corpus = []
        self.word_doc_freq = defaultdict(int)
        self.doc_lengths = []
        self.avg_doc_length = 0.0
        self.idf = {}
        
        logger.info("BM25索引已清空")