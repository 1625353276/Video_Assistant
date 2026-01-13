#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25检索器模块测试脚本

测试BM25Retriever类的各项功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.retrieval.bm25_retriever import BM25Retriever


def test_bm25_basic():
    """测试BM25检索器基本功能"""
    print("=" * 50)
    print("测试BM25检索器基本功能")
    print("=" * 50)
    
    try:
        # 创建BM25Retriever实例
        bm25 = BM25Retriever()
        
        # 获取初始统计信息
        stats = bm25.get_stats()
        print("初始统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 创建测试文档（模拟视频转写数据的segments）
        test_documents = [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.2,
                "text": "智能手机通过GPS卫星信号确定位置",
                "confidence": 0.95
            },
            {
                "id": 1,
                "start": 5.2,
                "end": 10.4,
                "text": "GPS系统使用三角测量法计算设备坐标",
                "confidence": 0.92
            },
            {
                "id": 2,
                "start": 10.4,
                "end": 15.6,
                "text": "手机还可以通过WiFi和基站进行定位",
                "confidence": 0.88
            },
            {
                "id": 3,
                "start": 15.6,
                "end": 20.8,
                "text": "北斗导航系统是中国自主研发的全球定位系统",
                "confidence": 0.90
            },
            {
                "id": 4,
                "start": 20.8,
                "end": 26.0,
                "text": "Deep learning is a subset of machine learning",
                "confidence": 0.93
            }
        ]
        
        # 添加文档到索引
        print("\n添加文档到BM25索引...")
        bm25.add_documents(test_documents)
        
        # 获取添加后的统计信息
        stats = bm25.get_stats()
        print("\n添加文档后的统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 测试检索功能
        print("\n测试BM25检索功能:")
        
        # 测试中文关键词检索
        queries = [
            "智能手机定位",
            "GPS系统",
            "北斗导航",
            "WiFi定位",
            "deep learning"
        ]
        
        for query in queries:
            print(f"\n查询: '{query}'")
            results = bm25.search(query, top_k=3)
            
            for i, result in enumerate(results):
                doc = result["document"]
                score = result["score"]
                print(f"  结果 {i+1}: [分数: {score:.4f}] {doc['text']}")
        
        print("\n✅ BM25检索器基本功能测试通过")
        
    except Exception as e:
        print(f"\n❌ BM25检索器基本功能测试失败: {str(e)}")
        return False
    
    return True


def test_bm25_persistence():
    """测试BM25索引持久化功能"""
    print("\n" + "=" * 50)
    print("测试BM25索引持久化功能")
    print("=" * 50)
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_bm25_index.pkl"
            
            # 创建第一个BM25实例并添加文档
            bm25_1 = BM25Retriever(k1=1.5, b=0.8)
            
            test_docs = [
                {"id": 1, "text": "人工智能技术正在快速发展"},
                {"id": 2, "text": "机器学习是人工智能的重要分支"},
                {"id": 3, "text": "深度学习推动了AI技术的突破"}
            ]
            
            bm25_1.add_documents(test_docs)
            
            # 保存索引
            print("保存BM25索引...")
            bm25_1.save_index(index_path)
            
            # 创建第二个BM25实例并加载索引
            bm25_2 = BM25Retriever()
            print("加载BM25索引...")
            bm25_2.load_index(index_path)
            
            # 验证加载的索引
            stats_1 = bm25_1.get_stats()
            stats_2 = bm25_2.get_stats()
            
            print("\n验证索引一致性:")
            print(f"原始索引文档数: {stats_1['document_count']}")
            print(f"加载索引文档数: {stats_2['document_count']}")
            print(f"原始索引词汇数: {stats_1['vocabulary_size']}")
            print(f"加载索引词汇数: {stats_2['vocabulary_size']}")
            
            # 测试检索结果一致性
            query = "人工智能"
            results_1 = bm25_1.search(query, top_k=3)
            results_2 = bm25_2.search(query, top_k=3)
            
            print(f"\n查询: '{query}'")
            print("原始索引结果:")
            for i, result in enumerate(results_1):
                print(f"  {i+1}: [分数: {result['score']:.4f}] {result['document']['text']}")
            
            print("加载索引结果:")
            for i, result in enumerate(results_2):
                print(f"  {i+1}: [分数: {result['score']:.4f}] {result['document']['text']}")
            
            # 验证结果是否一致
            if len(results_1) == len(results_2):
                scores_match = all(
                    abs(r1['score'] - r2['score']) < 1e-6 
                    for r1, r2 in zip(results_1, results_2)
                )
                if scores_match:
                    print("\n✅ BM25索引持久化功能测试通过")
                    return True
                else:
                    print("\n❌ BM25检索分数不一致")
                    return False
            else:
                print("\n❌ BM25检索结果数量不一致")
                return False
        
    except Exception as e:
        print(f"\n❌ BM25索引持久化功能测试失败: {str(e)}")
        return False


def test_bm25_parameters():
    """测试BM25参数调优功能"""
    print("\n" + "=" * 50)
    print("测试BM25参数调优功能")
    print("=" * 50)
    
    try:
        # 测试文档
        test_docs = [
            {"id": 1, "text": "机器学习算法包括监督学习和无监督学习"},
            {"id": 2, "text": "深度学习是机器学习的一个重要领域"},
            {"id": 3, "text": "机器学习在人工智能中扮演重要角色"},
            {"id": 4, "text": "人工智能技术改变着我们的生活方式"},
            {"id": 5, "text": "学习机器需要掌握相关算法知识"}
        ]
        
        # 测试不同参数组合
        parameter_sets = [
            {"k1": 1.2, "b": 0.75, "name": "默认参数"},
            {"k1": 1.5, "b": 0.75, "name": "较高k1"},
            {"k1": 1.2, "b": 0.5, "name": "较低b"},
            {"k1": 2.0, "b": 0.9, "name": "高k1高b"}
        ]
        
        query = "机器学习"
        
        print(f"测试查询: '{query}'")
        print("\n不同参数组合的检索结果:")
        
        for params in parameter_sets:
            bm25 = BM25Retriever(k1=params["k1"], b=params["b"])
            bm25.add_documents(test_docs)
            
            results = bm25.search(query, top_k=3)
            
            print(f"\n{params['name']} (k1={params['k1']}, b={params['b']}):")
            for i, result in enumerate(results):
                doc = result["document"]
                score = result["score"]
                print(f"  {i+1}: [分数: {score:.4f}] {doc['text']}")
        
        print("\n✅ BM25参数调优功能测试通过")
        
    except Exception as e:
        print(f"\n❌ BM25参数调优功能测试失败: {str(e)}")
        return False
    
    return True


def test_bm25_multilingual():
    """测试BM25多语言支持"""
    print("\n" + "=" * 50)
    print("测试BM25多语言支持")
    print("=" * 50)
    
    try:
        # 多语言测试文档
        test_docs = [
            {"id": 1, "text": "智能手机定位技术"},
            {"id": 2, "text": "Smartphone positioning technology"},
            {"id": 3, "text": "GPS全球定位系统"},
            {"id": 4, "text": "GPS global positioning system"},
            {"id": 5, "text": "北斗导航系统Beidou navigation system"}
        ]
        
        # 测试中文检索
        print("测试中文检索:")
        bm25_zh = BM25Retriever(language='zh')
        bm25_zh.add_documents(test_docs)
        
        zh_queries = ["智能手机", "定位系统", "北斗导航"]
        for query in zh_queries:
            results = bm25_zh.search(query, top_k=2)
            print(f"\n查询: '{query}'")
            for i, result in enumerate(results):
                doc = result["document"]
                score = result["score"]
                print(f"  {i+1}: [分数: {score:.4f}] {doc['text']}")
        
        # 测试英文检索
        print("\n测试英文检索:")
        bm25_en = BM25Retriever(language='en')
        bm25_en.add_documents(test_docs)
        
        en_queries = ["smartphone", "positioning", "GPS"]
        for query in en_queries:
            results = bm25_en.search(query, top_k=2)
            print(f"\n查询: '{query}'")
            for i, result in enumerate(results):
                doc = result["document"]
                score = result["score"]
                print(f"  {i+1}: [分数: {score:.4f}] {doc['text']}")
        
        # 测试自动语言检测
        print("\n测试自动语言检测:")
        bm25_auto = BM25Retriever(language='auto')
        bm25_auto.add_documents(test_docs)
        
        auto_queries = ["智能手机", "smartphone", "GPS", "定位"]
        for query in auto_queries:
            results = bm25_auto.search(query, top_k=2)
            print(f"\n查询: '{query}'")
            for i, result in enumerate(results):
                doc = result["document"]
                score = result["score"]
                print(f"  {i+1}: [分数: {score:.4f}] {doc['text']}")
        
        print("\n✅ BM25多语言支持测试通过")
        
    except Exception as e:
        print(f"\n❌ BM25多语言支持测试失败: {str(e)}")
        return False
    
    return True


def main():
    """运行所有测试"""
    print("开始BM25检索器测试")
    print("=" * 60)
    
    tests = [
        test_bm25_basic,
        test_bm25_persistence,
        test_bm25_parameters,
        test_bm25_multilingual
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有BM25检索器测试通过！")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
