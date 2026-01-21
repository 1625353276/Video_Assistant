#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
索引构建功能
"""

import os
import time
from typing import Dict, List, Any, Optional


class IndexBuilder:
    """索引构建器"""
    
    def __init__(self):
        """初始化索引构建器"""
        self._init_retrievers()
    
    def _init_retrievers(self):
        """初始化检索器"""
        try:
            from modules.retrieval.vector_store import VectorStore
            from modules.retrieval.bm25_retriever import BM25Retriever
            from modules.retrieval.hybrid_retriever import HybridRetriever
            
            self.vector_store = VectorStore(mirror_site="tuna")
            self.bm25_retriever = BM25Retriever(language='auto')
            self.hybrid_retriever = HybridRetriever(
                vector_store=self.vector_store,
                bm25_retriever=self.bm25_retriever,
                vector_weight=0.6,
                bm25_weight=0.4,
                fusion_method="weighted_average"
            )
            self.mock_mode = False
            print("✓ 索引构建器初始化成功")
            
        except ImportError as e:
            print(f"⚠ 索引构建器初始化失败，使用模拟模式: {e}")
            self.mock_mode = True
            self.vector_store = None
            self.bm25_retriever = None
            self.hybrid_retriever = None
    
    def build_vector_index(self, video_id):
        """
        为视频内容构建向量索引和BM25索引
        """
        from .video_processor import get_video_data
        video_data = get_video_data()
        
        if video_id not in video_data:
            return {"error": "视频不存在"}
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return {"error": "视频尚未处理完成"}
        
        if not self.vector_store or not self.bm25_retriever:
            return {"error": "检索器未初始化"}
        
        try:
            transcript = video_info["transcript"]
            
            # 准备文档数据
            documents = []
            for segment in transcript.get("segments", []):
                doc = {
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "video_id": video_id
                }
                documents.append(doc)
            
            # 构建向量索引
            self.vector_store.clear()
            self.vector_store.add_documents(documents, text_field="text")
            vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
            self.vector_store.save_index(vector_index_path)
            
            # 构建BM25索引
            self.bm25_retriever.clear()
            self.bm25_retriever.add_documents(documents, text_field="text")
            bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
            self.bm25_retriever.save_index(bm25_index_path)
            
            # 如果有混合检索器，也添加文档
            if self.hybrid_retriever:
                self.hybrid_retriever.clear()
                self.hybrid_retriever.add_documents(documents, text_field="text")
                hybrid_index_path = f"data/vectors/{video_id}_hybrid_index.pkl"
                self.hybrid_retriever.save_indexes(vector_index_path, bm25_index_path)
            
            video_info["vector_index_built"] = True
            video_info["vector_index_path"] = vector_index_path
            video_info["bm25_index_path"] = bm25_index_path
            
            return {
                "success": True,
                "document_count": len(documents),
                "vector_stats": self.vector_store.get_stats(),
                "bm25_stats": self.bm25_retriever.get_stats(),
                "message": f"成功构建向量索引和BM25索引，包含 {len(documents)} 个文档片段"
            }
        except Exception as e:
            return {"error": f"构建索引失败: {str(e)}"}
    
    def build_index_background(self, video_id):
        """后台构建向量索引"""
        from .video_processor import get_video_data
        video_data = get_video_data()
        
        if video_id not in video_data:
            return {"error": "视频不存在"}
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return {"error": "视频尚未处理完成"}
        
        if not self.vector_store or not self.bm25_retriever:
            return {"error": "检索器未初始化"}
        
        try:
            transcript = video_info["transcript"]
            
            # 准备文档数据
            documents = []
            for segment in transcript.get("segments", []):
                doc = {
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "video_id": video_id
                }
                documents.append(doc)
            
            # 构建向量索引
            self.vector_store.clear()
            self.vector_store.add_documents(documents, text_field="text")
            vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
            self.vector_store.save_index(vector_index_path)
            
            # 构建BM25索引
            self.bm25_retriever.clear()
            self.bm25_retriever.add_documents(documents, text_field="text")
            bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
            self.bm25_retriever.save_index(bm25_index_path)
            
            # 如果有混合检索器，也添加文档
            if self.hybrid_retriever:
                self.hybrid_retriever.clear()
                self.hybrid_retriever.add_documents(documents, text_field="text")
                hybrid_index_path = f"data/vectors/{video_id}_hybrid_index.pkl"
                self.hybrid_retriever.save_indexes(vector_index_path, bm25_index_path)
            
            video_info["vector_index_built"] = True
            video_info["vector_index_path"] = vector_index_path
            video_info["bm25_index_path"] = bm25_index_path
            video_info["index_building"] = False
            
            return {
                "success": True,
                "document_count": len(documents),
                "vector_stats": self.vector_store.get_stats(),
                "bm25_stats": self.bm25_retriever.get_stats(),
                "message": f"成功构建向量索引和BM25索引，包含 {len(documents)} 个文档片段"
            }
        except Exception as e:
            video_info["index_building"] = False
            return {"error": f"构建索引失败: {str(e)}"}
    
    def search_in_video(self, video_id, query, max_results=5, threshold=0.3, search_type="hybrid"):
        """
        搜索视频内容
        
        Args:
            video_id: 视频ID
            query: 搜索查询
            max_results: 最大结果数
            threshold: 相关性阈值
            search_type: 搜索类型 ("vector", "bm25", "hybrid")
        """
        from .video_processor import get_video_data
        video_data = get_video_data()
        
        if video_id not in video_data:
            return []
        
        video_info = video_data[video_id]
        
        if not video_info.get("vector_index_built"):
            # 如果没有构建索引，先尝试构建
            if video_info.get("transcript"):
                self.build_vector_index(video_id)
            else:
                return [{"text": "视频尚未处理完成，无法搜索", "timestamp": 0.0, "score": 0.0, "type": "error"}]
        
        try:
            results = []
            
            # 根据搜索类型执行不同的搜索
            if search_type == "vector" and self.vector_store:
                # 向量搜索
                vector_results = self.vector_store.search(query, top_k=max_results, threshold=threshold)
                for result in vector_results:
                    doc = result["document"]
                    results.append({
                        "text": doc["text"],
                        "timestamp": doc["start"],
                        "score": round(result["similarity"], 3),
                        "end": doc["end"],
                        "type": "vector",
                        "similarity": round(result["similarity"], 3)
                    })
            
            elif search_type == "bm25" and self.bm25_retriever:
                # BM25搜索
                bm25_results = self.bm25_retriever.search(query, top_k=max_results, threshold=threshold)
                for result in bm25_results:
                    doc = result["document"]
                    results.append({
                        "text": doc["text"],
                        "timestamp": doc["start"],
                        "score": round(result["score"], 3),
                        "end": doc["end"],
                        "type": "bm25",
                        "bm25_score": round(result["score"], 3)
                    })
            
            elif search_type == "hybrid" and self.hybrid_retriever:
                # 混合搜索
                hybrid_results = self.hybrid_retriever.search(query, top_k=max_results, threshold=threshold)
                for result in hybrid_results:
                    doc = result["document"]
                    results.append({
                        "text": doc["text"],
                        "timestamp": doc["start"],
                        "score": round(result["score"], 3),
                        "end": doc["end"],
                        "type": "hybrid",
                        "vector_score": round(result.get("vector_score", 0), 3),
                        "bm25_score": round(result.get("bm25_score", 0), 3)
                    })
            
            else:
                return [{"text": f"检索器未初始化或不支持搜索类型: {search_type}", "timestamp": 0.0, "score": 0.0, "type": "error"}]
            
            return results
            
        except Exception as e:
            return [{"text": f"搜索失败: {str(e)}", "timestamp": 0.0, "score": 0.0, "type": "error"}]


# 全局索引构建器实例
index_builder = IndexBuilder()


def get_index_builder():
    """获取索引构建器实例"""
    return index_builder