#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储模块测试脚本

测试VectorStore类的各项功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.retrieval.vector_store import VectorStore


def test_vector_store_basic():
    """测试向量存储基本功能"""
    print("=" * 50)
    print("测试向量存储基本功能")
    print("=" * 50)
    
    try:
        # 创建VectorStore实例
        vector_store = VectorStore()
        
        # 测试模型加载
        print("正在加载模型...")
        vector_store.load_model()
        
        # 获取统计信息
        stats = vector_store.get_stats()
        print("初始统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 创建测试文档（模拟JSON转写数据的segments）
        test_documents = [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.2,
                "text": "How does your smartphone know exactly where you are?",
                "confidence": 0.95
            },
            {
                "id": 1,
                "start": 5.2,
                "end": 10.4,
                "text": "The answer lies 12,000 miles over your head, in an orbiting satellite.",
                "confidence": 0.92
            },
            {
                "id": 2,
                "start": 10.4,
                "end": 15.6,
                "text": "Atomic clocks work because of quantum physics principles.",
                "confidence": 0.88
            },
            {
                "id": 3,
                "start": 15.6,
                "end": 20.8,
                "text": "GPS technology uses multiple satellites to determine location.",
                "confidence": 0.94
            },
            {
                "id": 4,
                "start": 20.8,
                "end": 26.0,
                "text": "Machine learning algorithms can improve speech recognition accuracy.",
                "confidence": 0.91
            }
        ]
        
        # 添加文档
        print(f"\n添加 {len(test_documents)} 个测试文档...")
        vector_store.add_documents(test_documents, text_field="text")
        
        # 获取更新后的统计信息
        stats = vector_store.get_stats()
        print("\n添加文档后的统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        return vector_store, test_documents
        
    except Exception as e:
        print(f"基本功能测试失败: {str(e)}")
        return None, None


def test_vector_search(vector_store, test_documents):
    """测试向量搜索功能"""
    print("\n" + "=" * 50)
    print("测试向量搜索功能")
    print("=" * 50)
    
    try:
        # 测试查询
        test_queries = [
            "smartphone location",
            "quantum physics",
            "GPS satellites",
            "machine learning",
            "speech recognition"
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            print("-" * 30)
            
            # 执行搜索
            results = vector_store.search(query, top_k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    doc = result["document"]
                    similarity = result["similarity"]
                    
                    print(f"结果 {i} (相似度: {similarity:.3f}):")
                    print(f"  文本: {doc['text']}")
                    print(f"  时间: {doc['start']:.1f}s - {doc['end']:.1f}s")
                    print(f"  置信度: {doc['confidence']}")
            else:
                print("未找到相关结果")
        
        return True
        
    except Exception as e:
        print(f"搜索功能测试失败: {str(e)}")
        return False


def test_index_save_load(vector_store):
    """测试索引保存和加载功能"""
    print("\n" + "=" * 50)
    print("测试索引保存和加载功能")
    print("=" * 50)
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            index_path = temp_path / "test_vector_index.pkl"
            
            # 保存索引
            print(f"保存索引到: {index_path}")
            vector_store.save_index(index_path)
            
            # 获取保存前的统计信息
            stats_before = vector_store.get_stats()
            doc_count_before = stats_before["document_count"]
            
            # 清空当前存储
            vector_store.clear()
            stats_after_clear = vector_store.get_stats()
            print(f"清空后文档数量: {stats_after_clear['document_count']}")
            
            # 加载索引
            print("加载索引...")
            vector_store.load_index(index_path)
            
            # 验证加载后的数据
            stats_after_load = vector_store.get_stats()
            doc_count_after = stats_after_load["document_count"]
            
            print(f"加载后文档数量: {doc_count_after}")
            
            # 验证数据完整性
            if doc_count_before == doc_count_after:
                print("✓ 索引保存和加载成功")
                
                # 测试加载后的搜索功能
                results = vector_store.search("smartphone", top_k=1)
                if results:
                    print("✓ 加载后的搜索功能正常")
                    return True
                else:
                    print("✗ 加载后的搜索功能异常")
                    return False
            else:
                print("✗ 索引保存和加载失败")
                return False
        
    except Exception as e:
        print(f"索引保存加载测试失败: {str(e)}")
        return False


def test_with_real_data():
    """使用真实的转写数据进行测试"""
    print("\n" + "=" * 50)
    print("使用真实转写数据进行测试")
    print("=" * 50)
    
    try:
        # 检查是否有真实的转写数据
        transcripts_dir = Path("data/transcripts")
        if not transcripts_dir.exists():
            print("未找到转写数据目录，跳过真实数据测试")
            return True
        
        # 查找JSON文件
        json_files = list(transcripts_dir.glob("*.json"))
        if not json_files:
            print("未找到JSON格式的转写文件，跳过真实数据测试")
            return True
        
        # 使用第一个JSON文件进行测试
        json_file = json_files[0]
        print(f"使用文件: {json_file}")
        
        # 加载JSON数据
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # 提取segments
        segments = transcript_data.get("segments", [])
        if not segments:
            print("文件中没有segments数据，跳过真实数据测试")
            return True
        
        print(f"找到 {len(segments)} 个segments")
        
        # 创建向量存储
        vector_store = VectorStore()
        vector_store.load_model()
        
        # 添加segments
        vector_store.add_documents(segments, text_field="text")
        
        # 执行一些测试查询
        test_queries = [
            "satellite",
            "quantum",
            "technology",
            "time"
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            results = vector_store.search(query, top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    doc = result["document"]
                    similarity = result["similarity"]
                    print(f"  结果 {i} (相似度: {similarity:.3f}): {doc['text'][:50]}...")
            else:
                print("  未找到相关结果")
        
        print("✓ 真实数据测试完成")
        return True
        
    except Exception as e:
        print(f"真实数据测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("向量存储模块测试")
    print("=" * 50)
    
    # 检查依赖
    try:
        import sentence_transformers
        import torch
        print(f"✓ sentence-transformers版本: {sentence_transformers.__version__}")
        print(f"✓ PyTorch版本: {torch.__version__}")
        print(f"✓ CUDA可用: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install sentence-transformers torch")
        return 1
    
    print("\n")
    
    # 基本功能测试
    vector_store, test_documents = test_vector_store_basic()
    if vector_store is None:
        return 1
    
    # 搜索功能测试
    if not test_vector_search(vector_store, test_documents):
        return 1
    
    # 索引保存加载测试
    if not test_index_save_load(vector_store):
        return 1
    
    # 真实数据测试
    if not test_with_real_data():
        return 1
    
    # 清理资源
    vector_store.unload_model()
    
    print("\n" + "=" * 50)
    print("所有测试完成！")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
