#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第四阶段测试：检索系统隔离

测试用户隔离的向量索引和BM25索引构建
"""

import sys
import os
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.user_context import user_context
from deploy.core.index_builder_isolated import IsolatedIndexBuilder, get_index_builder


def create_mock_transcript_data():
    """创建模拟转录数据"""
    return {
        "text": "这是测试转录文本，用于构建索引",
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "第一段测试内容"},
            {"id": 1, "start": 5.0, "end": 10.0, "text": "第二段测试内容"},
            {"id": 2, "start": 10.0, "end": 15.0, "text": "第三段测试内容"}
        ],
        "language": "zh"
    }


def test_index_builder_init():
    """测试索引构建器初始化"""
    print("🧪 测试索引构建器初始化...")
    
    builder = IsolatedIndexBuilder()
    
    assert builder.vector_store is not None or builder.bm25_retriever is not None
    
    print("✅ 索引构建器初始化测试通过")


def test_user_index_building():
    """测试用户索引构建"""
    print("🧪 测试用户索引构建...")
    
    test_user_id = "index_test_user"
    user_context.set_user(test_user_id, "indexuser")
    
    try:
        builder = IsolatedIndexBuilder()
        transcript_data = create_mock_transcript_data()
        video_id = "test_video_123"
        
        # Mock向量存储和BM25检索器
        with patch('modules.retrieval.vector_store.VectorStore') as mock_vector_store, \
             patch('modules.retrieval.bm25_retriever.BM25Retriever') as mock_bm25_retriever:
            
            mock_vs = Mock()
            mock_vs.clear = Mock()
            mock_vs.add_documents = Mock()
            mock_vs.save_index = Mock()
            mock_vs.get_stats = Mock(return_value={"document_count": 3})
            
            mock_bm25 = Mock()
            mock_bm25.clear = Mock()
            mock_bm25.add_documents = Mock()
            mock_bm25.save_index = Mock()
            mock_bm25.get_stats = Mock(return_value={"document_count": 3})
            
            mock_vector_store.return_value = mock_vs
            mock_bm25_retriever.return_value = mock_bm25
            
            builder.vector_store = mock_vs
            builder.bm25_retriever = mock_bm25
            
            # 构建索引
            result = builder.build_user_index(video_id, transcript_data)
            
            # 验证结果
            assert result["success"] is True
            assert result["document_count"] == 3
            assert "vector_stats" in result
            assert "bm25_stats" in result
            
            # 验证文件创建
            user_paths = user_context.get_paths()
            vector_path = user_paths.get_vector_index_path(video_id)
            bm25_path = user_paths.get_bm25_index_path(video_id)
            
            assert vector_path.exists()
            assert bm25_path.exists()
            
            print("✅ 用户索引构建测试通过")
            
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_user_index_loading():
    """测试用户索引加载"""
    print("🧪 测试用户索引加载...")
    
    test_user_id = "loading_test_user"
    user_context.set_user(test_user_id, "loadinguser")
    
    try:
        builder = IsolatedIndexBuilder()
        
        # 先创建索引文件
        transcript_data = create_mock_transcript_data()
        video_id = "load_test_video"
        
        with patch('modules.retrieval.vector_store.VectorStore') as mock_vector_store, \
             patch('modules.retrieval.bm25_retriever.BM25Retriever') as mock_bm25_retriever:
            
            mock_vs = Mock()
            mock_vs.clear = Mock()
            mock_vs.load_index = Mock()
            mock_vs.add_documents = Mock()
            
            mock_bm25 = Mock()
            mock_bm25.clear = Mock()
            mock_bm25.load_index = Mock()
            mock_bm25.add_documents = Mock()
            
            mock_vector_store.return_value = mock_vs
            mock_bm25_retriever.return_value = mock_bm25
            
            builder.vector_store = mock_vs
            builder.bm25_retriever = mock_bm25
            
            # 先构建索引
            builder.build_user_index(video_id, transcript_data)
            
            # 重置mock
            mock_vs.reset_mock()
            mock_bm25.reset_mock()
            
            # 加载索引
            result = builder.load_user_index(video_id)
            
            # 验证结果
            assert result["success"] is True
            assert result["user_id"] == test_user_id
            
            print("✅ 用户索引加载测试通过")
            
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_user_search():
    """测试用户搜索功能"""
    print("🧪 测试用户搜索功能...")
    
    test_user_id = "search_test_user"
    user_context.set_user(test_user_id, "searchuser")
    
    try:
        builder = IsolatedIndexBuilder()
        transcript_data = create_mock_transcript_data()
        video_id = "search_test_video"
        
        with patch('modules.retrieval.vector_store.VectorStore') as mock_vector_store, \
             patch('modules.retrieval.bm25_retriever.BM25Retriever') as mock_bm25_retriever:
            
            mock_vs = Mock()
            mock_vs.clear = Mock()
            mock_vs.add_documents = Mock()
            mock_vs.save_index = Mock()
            mock_vs.load_index = Mock()
            mock_vs.search = Mock(return_value=[
                {
                    "document": {
                        "text": "第一段测试内容",
                        "start": 0.0,
                        "end": 5.0,
                        "video_id": video_id,
                        "user_id": test_user_id
                    },
                    "similarity": 0.95
                }
            ])
            
            mock_bm25 = Mock()
            mock_bm25.clear = Mock()
            mock_bm25.add_documents = Mock()
            mock_bm25.save_index = Mock()
            mock_bm25.load_index = Mock()
            mock_bm25.search = Mock(return_value=[
                {
                    "document": {
                        "text": "第二段测试内容",
                        "start": 5.0,
                        "end": 10.0,
                        "video_id": video_id,
                        "user_id": test_user_id
                    },
                    "score": 0.85
                }
            ])
            
            mock_vector_store.return_value = mock_vs
            mock_bm25_retriever.return_value = mock_bm25
            
            builder.vector_store = mock_vs
            builder.bm25_retriever = mock_bm25
            
            # 构建索引
            builder.build_user_index(video_id, transcript_data)
            
            # 执行搜索
            vector_results = builder.search_user_documents(video_id, "测试", search_type="vector")
            bm25_results = builder.search_user_documents(video_id, "测试", search_type="bm25")
            
            # 验证结果
            assert len(vector_results) == 1
            assert len(bm25_results) == 1
            assert vector_results[0]["type"] == "vector"
            assert bm25_results[0]["type"] == "bm25"
            assert vector_results[0]["user_id"] == test_user_id
            assert bm25_results[0]["user_id"] == test_user_id
            
            print("✅ 用户搜索功能测试通过")
            
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_index_stats():
    """测试索引统计"""
    print("🧪 测试索引统计...")
    
    test_user_id = "stats_test_user"
    user_context.set_user(test_user_id, "statsuser")
    
    try:
        builder = IsolatedIndexBuilder()
        transcript_data = create_mock_transcript_data()
        video_id = "stats_test_video"
        
        with patch('modules.retrieval.vector_store.VectorStore') as mock_vector_store, \
             patch('modules.retrieval.bm25_retriever.BM25Retriever') as mock_bm25_retriever:
            
            mock_vs = Mock()
            mock_vs.clear = Mock()
            mock_vs.add_documents = Mock()
            mock_vs.save_index = Mock()
            mock_vs.load_index = Mock()
            mock_vs.get_stats = Mock(return_value={"document_count": 3, "index_size": 1024})
            
            mock_bm25 = Mock()
            mock_bm25.clear = Mock()
            mock_bm25.add_documents = Mock()
            mock_bm25.save_index = Mock()
            mock_bm25.load_index = Mock()
            mock_bm25.get_stats = Mock(return_value={"document_count": 3, "vocab_size": 100})
            
            mock_vector_store.return_value = mock_vs
            mock_bm25_retriever.return_value = mock_bm25
            
            builder.vector_store = mock_vs
            builder.bm25_retriever = mock_bm25
            
            # 构建索引
            builder.build_user_index(video_id, transcript_data)
            
            # 获取统计
            stats = builder.get_user_index_stats(video_id)
            
            # 验证结果
            assert stats["user_id"] == test_user_id
            assert stats["video_id"] == video_id
            assert stats["vector_index_exists"] is True
            assert stats["bm25_index_exists"] is True
            assert stats["vector_stats"]["document_count"] == 3
            assert stats["bm25_stats"]["document_count"] == 3
            
            print("✅ 索引统计测试通过")
            
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_index_deletion():
    """测试索引删除"""
    print("🧪 测试索引删除...")
    
    test_user_id = "delete_test_user"
    user_context.set_user(test_user_id, "deleteuser")
    
    try:
        builder = IsolatedIndexBuilder()
        transcript_data = create_mock_transcript_data()
        video_id = "delete_test_video"
        
        with patch('modules.retrieval.vector_store.VectorStore') as mock_vector_store, \
             patch('modules.retrieval.bm25_retriever.BM25Retriever') as mock_bm25_retriever:
            
            mock_vs = Mock()
            mock_vs.clear = Mock()
            mock_vs.add_documents = Mock()
            mock_vs.save_index = Mock()
            mock_vs.load_index = Mock()
            
            mock_bm25 = Mock()
            mock_bm25.clear = Mock()
            mock_bm25.add_documents = Mock()
            mock_bm25.save_index = Mock()
            mock_bm25.load_index = Mock()
            
            mock_vector_store.return_value = mock_vs
            mock_bm25_retriever.return_value = mock_bm25
            
            builder.vector_store = mock_vs
            builder.bm25_retriever = mock_bm25
            
            # 构建索引
            builder.build_user_index(video_id, transcript_data)
            
            # 验证文件存在
            user_paths = user_context.get_paths()
            vector_path = user_paths.get_vector_index_path(video_id)
            bm25_path = user_paths.get_bm25_index_path(video_id)
            
            assert vector_path.exists()
            assert bm25_path.exists()
            
            # 删除索引
            result = builder.delete_user_index(video_id)
            
            # 验证结果
            assert result["success"] is True
            assert "vector_index" in result["deleted_files"]
            assert "bm25_index" in result["deleted_files"]
            
            # 验证文件已删除
            assert not vector_path.exists()
            assert not bm25_path.exists()
            
            print("✅ 索引删除测试通过")
            
    finally:
        user_paths = user_context.get_paths()
        if user_paths and user_paths.base_path.exists():
            shutil.rmtree(user_paths.base_path)
        user_context.clear_user()


def test_global_index_builder():
    """测试全局索引构建器"""
    print("🧪 测试全局索引构建器...")
    
    builder1 = get_index_builder()
    builder2 = get_index_builder()
    
    # 验证是同一个实例
    assert builder1 is builder2
    assert isinstance(builder1, IsolatedIndexBuilder)
    
    print("✅ 全局索引构建器测试通过")


def test_user_index_isolation():
    """测试用户索引隔离"""
    print("🧪 测试用户索引隔离...")
    
    user1_id = "isolation_user_1"
    user2_id = "isolation_user_2"
    
    user_context.set_user(user1_id, "user1")
    user1_paths = user_context.get_paths()
    
    user_context.set_user(user2_id, "user2")
    user2_paths = user_context.get_paths()
    
    try:
        builder = IsolatedIndexBuilder()
        transcript_data = create_mock_transcript_data()
        video_id = "isolation_video"
        
        with patch('modules.retrieval.vector_store.VectorStore') as mock_vector_store, \
             patch('modules.retrieval.bm25_retriever.BM25Retriever') as mock_bm25_retriever:
            
            mock_vs = Mock()
            mock_vs.clear = Mock()
            mock_vs.add_documents = Mock()
            mock_vs.save_index = Mock()
            
            mock_bm25 = Mock()
            mock_bm25.clear = Mock()
            mock_bm25.add_documents = Mock()
            mock_bm25.save_index = Mock()
            
            mock_vector_store.return_value = mock_vs
            mock_bm25_retriever.return_value = mock_bm25
            
            builder.vector_store = mock_vs
            builder.bm25_retriever = mock_bm25
            
            # 为用户1构建索引
            user_context.set_user(user1_id, "user1")
            result1 = builder.build_user_index(video_id, transcript_data)
            
            # 为用户2构建同名索引
            user_context.set_user(user2_id, "user2")
            result2 = builder.build_user_index(video_id, transcript_data)
            
            # 验证隔离
            assert result1["success"] is True
            assert result2["success"] is True
            
            # 验证文件隔离
            vector_path1 = user1_paths.get_vector_index_path(video_id)
            vector_path2 = user2_paths.get_vector_index_path(video_id)
            
            assert vector_path1 != vector_path2
            assert vector_path1.exists()
            assert vector_path2.exists()
            
            print("✅ 用户索引隔离测试通过")
            
    finally:
        if user1_paths and user1_paths.base_path.exists():
            shutil.rmtree(user1_paths.base_path)
        if user2_paths and user2_paths.base_path.exists():
            shutil.rmtree(user2_paths.base_path)
        user_context.clear_user()


def run_stage4_tests():
    """运行第四阶段所有测试"""
    print("🚀 开始第四阶段测试：检索系统隔离\n")
    
    try:
        test_index_builder_init()
        print()
        test_user_index_building()
        print()
        test_user_index_loading()
        print()
        test_user_search()
        print()
        test_index_stats()
        print()
        test_index_deletion()
        print()
        test_global_index_builder()
        print()
        test_user_index_isolation()
        print()
        
        print("🎉 第四阶段所有测试通过！")
        print("✅ 索引构建器隔离实现完成")
        print("✅ 向量索引隔离实现完成")
        print("✅ BM25索引隔离实现完成")
        print("✅ 搜索功能隔离实现完成")
        print("✅ 索引统计实现完成")
        print("✅ 索引删除实现完成")
        print("✅ 用户索引隔离机制实现完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage4_tests()
    sys.exit(0 if success else 1)
