#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
索引构建器 - 用户隔离版本

支持用户专属的向量索引和BM25索引构建
"""

import os
import sys
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入用户上下文
from deploy.utils.user_context import get_current_user_id, get_current_user_paths, require_user_login

# 导入用户隔离的检索模块
try:
    from modules.retrieval.isolated_vector_store import IsolatedVectorStore, get_isolated_vector_store
    from modules.retrieval.isolated_bm25_retriever import IsolatedBM25Retriever, get_isolated_bm25_retriever
    from modules.retrieval.isolated_hybrid_retriever import IsolatedHybridRetriever, get_isolated_hybrid_retriever
    print("✓ 用户隔离检索模块导入成功")
except ImportError as e:
    print(f"⚠ 用户隔离检索模块导入失败: {e}")
    # 回退到原有模块
    try:
        from modules.retrieval.vector_store import VectorStore
        from modules.retrieval.bm25_retriever import BM25Retriever
        from modules.retrieval.hybrid_retriever import HybridRetriever
        print("✓ 回退到原有检索模块")
    except ImportError as e2:
        print(f"⚠ 原有检索模块导入失败: {e2}")


class IsolatedIndexBuilder:
    """用户隔离的索引构建器"""
    
    def __init__(self):
        """初始化索引构建器"""
        self.vector_store = None
        self.bm25_retriever = None
        self.hybrid_retriever = None
        self._init_components()
    
    def _init_components(self):
        """初始化组件"""
        try:
            # 尝试使用用户隔离的检索器
            self.vector_store = get_isolated_vector_store(mirror_site="tuna")
            print("✓ 用户隔离向量存储初始化成功")
        except Exception as e:
            print(f"⚠ 用户隔离向量存储初始化失败: {e}")
            try:
                # 回退到原有模块
                from modules.retrieval.vector_store import VectorStore
                self.vector_store = VectorStore(mirror_site="tuna")
                print("✓ 回退到原有向量存储")
            except Exception as e2:
                print(f"⚠ 原有向量存储初始化失败: {e2}")
        
        try:
            # 尝试使用用户隔离的检索器
            self.bm25_retriever = get_isolated_bm25_retriever()
            print("✓ 用户隔离BM25检索器初始化成功")
        except Exception as e:
            print(f"⚠ 用户隔离BM25检索器初始化失败: {e}")
            try:
                # 回退到原有模块
                from modules.retrieval.bm25_retriever import BM25Retriever
                self.bm25_retriever = BM25Retriever()
                print("✓ 回退到原有BM25检索器")
            except Exception as e2:
                print(f"⚠ 原有BM25检索器初始化失败: {e2}")
        
        try:
            # 尝试使用用户隔离的检索器
            self.hybrid_retriever = get_isolated_hybrid_retriever(
                vector_store=self.vector_store,
                bm25_retriever=self.bm25_retriever,
                vector_weight=0.6,
                bm25_weight=0.4,
                fusion_method="weighted_average"
            )
            print("✓ 用户隔离混合检索器初始化成功")
        except Exception as e:
            print(f"⚠ 用户隔离混合检索器初始化失败: {e}")
            try:
                # 回退到原有模块
                from modules.retrieval.hybrid_retriever import HybridRetriever
                self.hybrid_retriever = HybridRetriever(
                    self.vector_store,
                    self.bm25_retriever,
                    vector_weight=0.6,
                    bm25_weight=0.4,
                    fusion_method="weighted_average"
                )
                print("✓ 回退到原有混合检索器")
            except Exception as e2:
                print(f"⚠ 原有混合检索器初始化失败: {e2}")
    
    @require_user_login
    def build_user_index(self, video_id: str, transcript_data: Dict):
        """为用户构建索引
        
        Args:
            video_id: 视频ID
            transcript_data: 转录数据
        """
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        if not transcript_data or "segments" not in transcript_data:
            return {"error": "转录数据无效"}
        
        try:
            # 准备文档数据
            documents = []
            for segment in transcript_data.get("segments", []):
                doc = {
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "video_id": video_id,
                    "user_id": user_id
                }
                documents.append(doc)
            
            if not documents:
                return {"error": "没有可用的文档片段"}
            
            # 构建向量索引
            if self.vector_store:
                self.vector_store.clear()
                self.vector_store.add_documents(documents, text_field="text")
                
                # 使用用户隔离的保存方法（如果可用）
                if hasattr(self.vector_store, 'save_user_index'):
                    self.vector_store.save_user_index(video_id)
                else:
                    # 回退到原有方法
                    vector_index_path = user_paths.get_vector_index_path(video_id)
                    self.vector_store.save_index(vector_index_path)
            else:
                return {"error": "向量存储未初始化"}
            
            # 构建BM25索引
            if self.bm25_retriever:
                self.bm25_retriever.clear()
                self.bm25_retriever.add_documents(documents, text_field="text")
                
                # 使用用户隔离的保存方法（如果可用）
                if hasattr(self.bm25_retriever, 'save_user_index'):
                    self.bm25_retriever.save_user_index(video_id)
                else:
                    # 回退到原有方法
                    bm25_index_path = user_paths.get_bm25_index_path(video_id)
                    self.bm25_retriever.save_index(bm25_index_path)
            else:
                return {"error": "BM25检索器未初始化"}
            
            # 构建混合索引元数据
            hybrid_index_path = user_paths.get_hybrid_index_path(video_id)
            hybrid_index_data = {
                "video_id": video_id,
                "user_id": user_id,
                "vector_weight": 0.6,
                "bm25_weight": 0.4,
                "fusion_method": "weighted_average",
                "document_count": len(documents)
            }
            
            with open(hybrid_index_path, 'wb') as f:
                pickle.dump(hybrid_index_data, f)
            
            return {
                "success": True,
                "message": f"用户 {user_id} 的索引构建完成",
                "video_id": video_id,
                "document_count": len(documents)
            }
            
        except Exception as e:
            return {"error": f"索引构建失败: {str(e)}"}
    
    @require_user_login
    def search_in_video(self, video_id: str, query: str, search_type: str = "hybrid", top_k: int = 5):
        """在指定视频中搜索
        
        Args:
            video_id: 视频ID
            query: 搜索查询
            search_type: 搜索类型 ("vector", "bm25", "hybrid")
            top_k: 返回结果数量
        """
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        try:
            # 检查索引是否存在
            vector_index_path = user_paths.get_vector_index_path(video_id)
            bm25_index_path = user_paths.get_bm25_index_path(video_id)
            
            if not vector_index_path.exists() or not bm25_index_path.exists():
                return {"error": "索引不存在，请先构建索引"}
            
            # 加载索引
            if self.vector_store:
                self.vector_store.clear()
                self.vector_store.load_index(vector_index_path)
            
            if self.bm25_retriever:
                self.bm25_retriever.clear()
                self.bm25_retriever.load_index(bm25_index_path)
            
            # 执行搜索
            if search_type == "vector" and self.vector_store:
                results = self.vector_store.search(query, top_k=top_k)
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "type": "vector",
                        "text": result["document"]["text"],
                        "start": result["document"]["start"],
                        "end": result["document"]["end"],
                        "score": result["similarity"],
                        "timestamp": result["document"]["start"]
                    })
            elif search_type == "bm25" and self.bm25_retriever:
                results = self.bm25_retriever.search(query, top_k=top_k)
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "type": "bm25",
                        "text": result["document"]["text"],
                        "start": result["document"]["start"],
                        "end": result["document"]["end"],
                        "score": result["score"],
                        "timestamp": result["document"]["start"]
                    })
            elif search_type == "hybrid" and self.hybrid_retriever:
                results = self.hybrid_retriever.search(query, top_k=top_k)
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "type": "hybrid",
                        "text": result["text"],
                        "start": result["start"],
                        "end": result["end"],
                        "score": result["score"],
                        "timestamp": result["start"],
                        "vector_score": result.get("similarity", 0),
                        "bm25_score": result.get("bm25_score", 0)
                    })
            else:
                return {"error": f"不支持的搜索类型: {search_type}"}
            
            return {
                "success": True,
                "results": formatted_results,
                "query": query,
                "search_type": search_type,
                "total_results": len(formatted_results)
            }
            
        except Exception as e:
            return {"error": f"搜索失败: {str(e)}"}
    
    @require_user_login
    def delete_user_index(self, video_id: str):
        """删除用户索引
        
        Args:
            video_id: 视频ID
        """
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        try:
            deleted_files = []
            
            # 删除向量索引
            vector_index_path = user_paths.get_vector_index_path(video_id)
            if vector_index_path.exists():
                vector_index_path.unlink()
                deleted_files.append("向量索引")
            
            # 删除BM25索引
            bm25_index_path = user_paths.get_bm25_index_path(video_id)
            if bm25_index_path.exists():
                bm25_index_path.unlink()
                deleted_files.append("BM25索引")
            
            # 删除混合索引元数据
            hybrid_index_path = user_paths.get_hybrid_index_path(video_id)
            if hybrid_index_path.exists():
                hybrid_index_path.unlink()
                deleted_files.append("混合索引")
            
            return {
                "success": True,
                "message": f"已删除 {len(deleted_files)} 个索引文件",
                "deleted_files": deleted_files
            }
            
        except Exception as e:
            return {"error": f"删除索引失败: {str(e)}"}
    
    @require_user_login
    def get_user_indexes(self):
        """获取用户所有索引"""
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        try:
            indexes = []
            vectors_dir = user_paths.get_vectors_dir()
            
            if vectors_dir.exists():
                for file_path in vectors_dir.glob("*_vector_index.pkl"):
                    video_id = file_path.stem.replace("_vector_index", "")
                    
                    # 检查对应的BM25索引是否存在
                    bm25_index_path = user_paths.get_bm25_index_path(video_id)
                    hybrid_index_path = user_paths.get_hybrid_index_path(video_id)
                    
                    indexes.append({
                        "video_id": video_id,
                        "vector_index": file_path.exists(),
                        "bm25_index": bm25_index_path.exists(),
                        "hybrid_index": hybrid_index_path.exists(),
                        "complete": all([
                            file_path.exists(),
                            bm25_index_path.exists(),
                            hybrid_index_path.exists()
                        ])
                    })
            
            return {
                "success": True,
                "indexes": indexes,
                "total_count": len(indexes)
            }
            
        except Exception as e:
            return {"error": f"获取索引列表失败: {str(e)}"}


# 全局实例
_index_builder = None


def get_index_builder() -> IsolatedIndexBuilder:
    """获取索引构建器实例（单例）"""
    global _index_builder
    if _index_builder is None:
        _index_builder = IsolatedIndexBuilder()
    return _index_builder


if __name__ == "__main__":
    # 测试代码
    builder = get_index_builder()
    print("索引构建器初始化完成")