#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储模块

职责：
- 实现文本向量化功能
- 实现向量相似度计算和检索
- 实现向量索引的创建、保存和加载
- 添加向量存储的配置管理
"""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储和检索服务"""
    
    # 国内镜像配置
    MIRROR_SITES = {
        "official": "https://huggingface.co",
        "tuna": "https://mirrors.tuna.tsinghua.edu.cn/hugging-face-models",
        "bfsu": "https://mirrors.bfsu.edu.cn/hugging-face-models",
        "aliyun": "https://mirrors.aliyun.com/hugging-face-models"
    }
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None,
                 mirror_site: str = "official"):
        """
        初始化向量存储
        
        Args:
            model_name: 句子转换器模型名称
            device: 计算设备 (cuda/cpu)，自动检测如果未指定
            cache_dir: 模型缓存目录，默认使用项目下的models目录
            mirror_site: 使用的镜像站点 (official/tuna/bfsu/aliyun)
        """
        self.model_name = model_name
        self.model = None
        self.device = self._determine_device(device)
        self.documents = []  # 存储原始文档
        self.embeddings = None  # 存储向量
        self.metadata = []  # 存储元数据
        
        # 设置镜像站点
        if mirror_site not in self.MIRROR_SITES:
            logger.warning(f"未知的镜像站点: {mirror_site}，使用默认镜像")
            mirror_site = "tuna"
        
        self.mirror_site = mirror_site
        self.mirror_url = self.MIRROR_SITES[mirror_site]
        
        # 设置模型缓存目录
        if cache_dir is None:
            # 获取项目根目录
            current_dir = Path(__file__).parent.parent.parent
            self.cache_dir = current_dir / "models"
        else:
            self.cache_dir = Path(cache_dir)
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置环境变量，让sentence-transformers使用我们的缓存目录
        os.environ['TRANSFORMERS_CACHE'] = str(self.cache_dir / "transformers")
        os.environ['HF_HOME'] = str(self.cache_dir / "huggingface")
        
        # 设置镜像站点环境变量
        if mirror_site != "official":
            os.environ['HF_ENDPOINT'] = self.mirror_url
            logger.info(f"使用镜像站点: {mirror_site} ({self.mirror_url})")
        
        logger.info(f"初始化向量存储，模型: {model_name}, 设备: {self.device}")
        logger.info(f"模型缓存目录: {self.cache_dir}")
    
    def _determine_device(self, device: Optional[str]) -> str:
        """
        确定计算设备
        
        Args:
            device: 指定的设备
            
        Returns:
            str: 使用的设备
        """
        if device:
            return device
        
        # 自动检测设备
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"  # Apple Silicon GPU
        else:
            return "cpu"
    
    def load_model(self) -> None:
        """加载句子转换器模型"""
        if self.model is not None:
            logger.info("模型已加载")
            return
        
        logger.info(f"正在加载句子转换器模型: {self.model_name}")
        logger.info(f"使用镜像站点: {self.mirror_site} ({self.mirror_url})")
        logger.info(f"模型将缓存到: {self.cache_dir}")
        
        # 确保缓存目录存在
        cache_folder = self.cache_dir / "sentence-transformers"
        cache_folder.mkdir(parents=True, exist_ok=True)
        
        # 第一次尝试：使用当前镜像
        try:
            self.model = SentenceTransformer(
                self.model_name, 
                device=self.device,
                cache_folder=str(cache_folder)
            )
            logger.info(f"句子转换器模型加载成功")
            logger.info(f"模型文件已保存到: {cache_folder}")
            return
        except Exception as e:
            logger.warning(f"使用 {self.mirror_site} 镜像加载失败: {str(e)}")
            
            # 第二次尝试：使用官方源（仅当当前不是官方源时）
            if self.mirror_site != "official":
                logger.info("尝试使用官方源重新下载...")
                try:
                    # 临时移除镜像设置
                    original_endpoint = os.environ.get('HF_ENDPOINT')
                    if original_endpoint:
                        os.environ.pop('HF_ENDPOINT', None)
                    
                    self.model = SentenceTransformer(
                        self.model_name, 
                        device=self.device,
                        cache_folder=str(cache_folder)
                    )
                    
                    # 恢复镜像设置
                    if original_endpoint:
                        os.environ['HF_ENDPOINT'] = original_endpoint
                    
                    logger.info("使用官方源加载模型成功")
                    return
                except Exception as e2:
                    logger.error(f"官方源也加载失败: {str(e2)}")
                    raise RuntimeError(f"模型加载失败，镜像源: {str(e)}, 官方源: {str(e2)}")
            else:
                raise RuntimeError(f"句子转换器模型加载失败: {str(e)}")
    
    def encode_texts(self, texts: List[str], 
                    batch_size: int = 32,
                    show_progress: bool = True) -> np.ndarray:
        """
        将文本列表编码为向量
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度
            
        Returns:
            np.ndarray: 文本向量矩阵
        """
        try:
            # 确保模型已加载
            if self.model is None:
                self.load_model()
            
            logger.info(f"开始编码 {len(texts)} 个文本")
            
            # 编码文本
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                device=self.device
            )
            
            logger.info(f"文本编码完成，向量维度: {embeddings.shape}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"文本编码失败: {str(e)}")
            raise RuntimeError(f"文本编码失败: {str(e)}")
    
    def add_documents(self, documents: List[Dict], 
                     text_field: str = "text",
                     metadata_fields: Optional[List[str]] = None) -> None:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表，每个文档是字典格式
            text_field: 文本字段名
            metadata_fields: 要保留的元数据字段列表
        """
        try:
            if not documents:
                logger.warning("文档列表为空")
                return
            
            # 提取文本内容
            texts = []
            for doc in documents:
                if text_field not in doc:
                    raise ValueError(f"文档中缺少文本字段: {text_field}")
                texts.append(doc[text_field])
            
            # 编码文本
            embeddings = self.encode_texts(texts)
            
            # 存储文档和向量
            self.documents.extend(documents)
            
            # 合并向量
            if self.embeddings is None:
                self.embeddings = embeddings
            else:
                self.embeddings = np.vstack([self.embeddings, embeddings])
            
            # 处理元数据
            for doc in documents:
                if metadata_fields:
                    meta = {field: doc.get(field) for field in metadata_fields if field in doc}
                else:
                    # 保留除文本字段外的所有字段
                    meta = {k: v for k, v in doc.items() if k != text_field}
                self.metadata.append(meta)
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量存储")
            
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            raise RuntimeError(f"添加文档失败: {str(e)}")
    
    def search(self, query: str, 
               top_k: int = 5,
               threshold: float = 0.0) -> List[Dict]:
        """
        在向量存储中搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回的最相似文档数量
            threshold: 相似度阈值
            
        Returns:
            List[Dict]: 相似文档列表，包含相似度分数
        """
        try:
            if self.embeddings is None or len(self.documents) == 0:
                logger.warning("向量存储为空")
                return []
            
            # 编码查询
            query_embedding = self.encode_texts([query])[0]
            
            # 计算相似度
            similarities = self._compute_similarity(query_embedding, self.embeddings)
            
            # 获取最相似的文档索引
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # 构建结果
            results = []
            for idx in top_indices:
                similarity = float(similarities[idx])
                
                # 应用阈值过滤
                if similarity < threshold:
                    continue
                
                result = {
                    "document": self.documents[idx],
                    "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
                    "similarity": similarity,
                    "index": int(idx)
                }
                results.append(result)
            
            logger.info(f"搜索完成，返回 {len(results)} 个结果")
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            raise RuntimeError(f"搜索失败: {str(e)}")
    
    def _compute_similarity(self, query_embedding: np.ndarray, 
                          document_embeddings: np.ndarray) -> np.ndarray:
        """
        计算查询向量与文档向量的相似度
        
        Args:
            query_embedding: 查询向量
            document_embeddings: 文档向量矩阵
            
        Returns:
            np.ndarray: 相似度分数数组
        """
        # 使用余弦相似度
        query_norm = np.linalg.norm(query_embedding)
        doc_norms = np.linalg.norm(document_embeddings, axis=1)
        
        # 避免除零
        similarities = np.dot(document_embeddings, query_embedding) / (doc_norms * query_norm + 1e-8)
        
        return similarities
    
    def save_index(self, save_path: Union[str, Path]) -> None:
        """
        保存向量索引到文件
        
        Args:
            save_path: 保存路径
        """
        try:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 准备保存数据
            index_data = {
                "model_name": self.model_name,
                "documents": self.documents,
                "embeddings": self.embeddings,
                "metadata": self.metadata,
                "device": self.device
            }
            
            # 保存到文件
            with open(save_path, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.info(f"向量索引已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存索引失败: {str(e)}")
            raise RuntimeError(f"保存索引失败: {str(e)}")
    
    def load_index(self, load_path: Union[str, Path]) -> None:
        """
        从文件加载向量索引
        
        Args:
            load_path: 加载路径
        """
        try:
            load_path = Path(load_path)
            
            if not load_path.exists():
                raise FileNotFoundError(f"索引文件不存在: {load_path}")
            
            # 加载数据
            with open(load_path, 'rb') as f:
                index_data = pickle.load(f)
            
            # 恢复状态
            self.model_name = index_data["model_name"]
            self.documents = index_data["documents"]
            self.embeddings = index_data["embeddings"]
            self.metadata = index_data["metadata"]
            self.device = index_data.get("device", "cpu")
            
            # 重新加载模型
            self.model = None  # 重置模型，下次使用时会重新加载
            
            logger.info(f"向量索引已从 {load_path} 加载，包含 {len(self.documents)} 个文档")
            
        except Exception as e:
            logger.error(f"加载索引失败: {str(e)}")
            raise RuntimeError(f"加载索引失败: {str(e)}")
    
    def get_available_mirrors(self) -> Dict[str, str]:
        """
        获取可用的镜像站点列表
        
        Returns:
            Dict[str, str]: 镜像站点字典
        """
        return self.MIRROR_SITES.copy()
    
    def switch_mirror(self, mirror_site: str) -> None:
        """
        切换镜像站点
        
        Args:
            mirror_site: 新的镜像站点名称
        """
        if mirror_site not in self.MIRROR_SITES:
            raise ValueError(f"未知的镜像站点: {mirror_site}，可用站点: {list(self.MIRROR_SITES.keys())}")
        
        self.mirror_site = mirror_site
        self.mirror_url = self.MIRROR_SITES[mirror_site]
        
        # 更新环境变量
        if mirror_site != "official":
            os.environ['HF_ENDPOINT'] = self.mirror_url
        else:
            os.environ.pop('HF_ENDPOINT', None)
        
        logger.info(f"已切换到镜像站点: {mirror_site} ({self.mirror_url})")
    
    def get_stats(self) -> Dict:
        """
        获取向量存储统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            "model_name": self.model_name,
            "device": self.device,
            "model_loaded": self.model is not None,
            "document_count": len(self.documents),
            "vector_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "storage_size_mb": round(self.embeddings.nbytes / (1024 * 1024), 2) if self.embeddings is not None else 0,
            "cache_dir": str(self.cache_dir),
            "mirror_site": self.mirror_site,
            "mirror_url": self.mirror_url
        }
        
        # 添加缓存目录大小信息
        if self.cache_dir.exists():
            total_size = 0
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            stats["cache_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return stats
    
    def clear(self) -> None:
        """清空向量存储"""
        self.documents = []
        self.embeddings = None
        self.metadata = []
        logger.info("向量存储已清空")
    
    def unload_model(self) -> None:
        """卸载模型以释放内存"""
        if self.model is not None:
            del self.model
            self.model = None
            
            # 清理GPU缓存
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            logger.info("句子转换器模型已卸载")
    
    def __del__(self):
        """析构函数，确保模型被正确卸载"""
        self.unload_model()