#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检索系统集成测试脚本

测试向量存储和BM25检索器的协同工作
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.multi_query import MultiQueryGenerator


def load_test_transcript():
    """加载测试转录数据"""
    # 使用测试转录数据
    transcript_files = [
        "data/transcripts/test_transcript.json"
    ]
    
    base_path = Path(__file__).parent.parent
    
    for file_path in transcript_files:
        full_path = base_path / file_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'segments' in data:
                    return data['segments']
    
    # 如果没有找到，返回模拟数据
    return [
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
            "text": "The answer lies in a network of satellites orbiting the Earth.",
            "confidence": 0.92
        },
        {
            "id": 2,
            "start": 10.4,
            "end": 15.6,
            "text": "GPS receivers in your phone detect signals from these satellites.",
            "confidence": 0.88
        },
        {
            "id": 3,
            "start": 15.6,
            "end": 20.8,
            "text": "By measuring the time delay of signals from multiple satellites,",
            "confidence": 0.90
        },
        {
            "id": 4,
            "start": 20.8,
            "end": 26.0,
            "text": "your phone can calculate its precise location on Earth.",
            "confidence": 0.93
        }
    ]


def test_vector_store_vs_bm25():
    """测试向量存储和BM25检索器的对比"""
    print("=" * 60)
    print("测试向量存储和BM25检索器对比")
    print("=" * 60)
    
    try:
        # 加载测试数据
        segments = load_test_transcript()
        print(f"加载了 {len(segments)} 个视频片段")
        
        # 创建检索器
        vector_store = VectorStore()
        bm25_retriever = BM25Retriever()
        
        # 添加文档
        print("\n添加文档到检索器...")
        vector_store.add_documents(segments)
        bm25_retriever.add_documents(segments)
        
        # 获取统计信息
        vs_stats = vector_store.get_stats()
        bm25_stats = bm25_retriever.get_stats()
        
        print("\n向量存储统计信息:")
        print(f"  文档数: {vs_stats['document_count']}")
        print(f"  向量维度: {vs_stats['vector_dimension']}")
        print(f"  存储大小: {vs_stats['storage_size_mb']} MB")
        
        print("\nBM25检索器统计信息:")
        print(f"  文档数: {bm25_stats['document_count']}")
        print(f"  词汇表大小: {bm25_stats['vocabulary_size']}")
        print(f"  平均文档长度: {bm25_stats['avg_doc_length']}")
        
        # 测试不同类型的查询
        test_queries = [
            ("GPS", "精确关键词匹配"),
            ("location", "语义相关词汇"),
            ("phone position", "组合查询"),
            ("卫星定位", "中文查询"),
            ("how phone works", "完整句子查询")
        ]
        
        print("\n" + "=" * 40)
        print("查询结果对比")
        print("=" * 40)
        
        for query, description in test_queries:
            print(f"\n查询: '{query}' ({description})")
            print("-" * 40)
            
            # 向量存储结果
            print("\n向量存储结果:")
            try:
                vs_results = vector_store.search(query, top_k=3)
                for i, result in enumerate(vs_results):
                    doc = result["document"]
                    similarity = result["similarity"]
                    text = doc["text"][:50] + "..." if len(doc["text"]) > 50 else doc["text"]
                    print(f"  {i+1}: [相似度: {similarity:.4f}] {text}")
            except Exception as e:
                print(f"  错误: {str(e)}")
            
            # BM25结果
            print("\nBM25检索结果:")
            try:
                bm25_results = bm25_retriever.search(query, top_k=3)
                for i, result in enumerate(bm25_results):
                    doc = result["document"]
                    score = result["score"]
                    text = doc["text"][:50] + "..." if len(doc["text"]) > 50 else doc["text"]
                    print(f"  {i+1}: [BM25分数: {score:.4f}] {text}")
            except Exception as e:
                print(f"  错误: {str(e)}")
        
        print("\n✅ 向量存储和BM25检索器对比测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False
    
    return True


def test_hybrid_retrieval_concept():
    """测试混合检索概念（模拟）"""
    print("\n" + "=" * 60)
    print("测试混合检索概念（模拟）")
    print("=" * 60)
    
    try:
        # 加载测试数据
        segments = load_test_transcript()
        
        # 创建检索器
        vector_store = VectorStore()
        bm25_retriever = BM25Retriever()
        
        # 添加文档
        vector_store.add_documents(segments)
        bm25_retriever.add_documents(segments)
        
        # 测试查询
        query = "GPS satellite location"
        print(f"测试查询: '{query}'")
        
        # 获取检索结果
        vs_results = vector_store.search(query, top_k=5)
        bm25_results = bm25_retriever.search(query, top_k=5)
        
        # 简单的混合检索：合并并重新排序
        all_docs = {}
        
        # 添加向量存储结果
        for result in vs_results:
            doc_id = result["document"]["id"]
            all_docs[doc_id] = {
                "document": result["document"],
                "vector_similarity": result["similarity"],
                "bm25_score": 0.0
            }
        
        # 添加BM25结果
        for result in bm25_results:
            doc_id = result["document"]["id"]
            if doc_id in all_docs:
                all_docs[doc_id]["bm25_score"] = result["score"]
            else:
                all_docs[doc_id] = {
                    "document": result["document"],
                    "vector_similarity": 0.0,
                    "bm25_score": result["score"]
                }
        
        # 计算混合分数（简单加权）
        hybrid_results = []
        for doc_id, doc_data in all_docs.items():
            # 归一化分数
            vector_score = min(doc_data["vector_similarity"], 1.0)
            bm25_score = min(doc_data["bm25_score"] / 10.0, 1.0)  # 简单归一化
            
            # 混合分数（可调整权重）
            hybrid_score = 0.6 * vector_score + 0.4 * bm25_score
            
            hybrid_results.append({
                "document": doc_data["document"],
                "vector_similarity": doc_data["vector_similarity"],
                "bm25_score": doc_data["bm25_score"],
                "hybrid_score": hybrid_score
            })
        
        # 按混合分数排序
        hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        # 显示结果
        print("\n混合检索结果:")
        print("-" * 60)
        print(f"{'排名':<4} {'混合分数':<10} {'向量相似度':<12} {'BM25分数':<10} {'文本片段'}")
        print("-" * 60)
        
        for i, result in enumerate(hybrid_results[:5]):
            doc = result["document"]
            text = doc["text"][:40] + "..." if len(doc["text"]) > 40 else doc["text"]
            print(f"{i+1:<4} {result['hybrid_score']:<10.4f} {result['vector_similarity']:<12.4f} "
                  f"{result['bm25_score']:<10.4f} {text}")
        
        print("\n✅ 混合检索概念测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False
    
    return True


def test_performance_comparison():
    """测试性能对比"""
    print("\n" + "=" * 60)
    print("测试性能对比")
    print("=" * 60)
    
    try:
        import time
        
        # 加载测试数据
        segments = load_test_transcript()
        
        # 创建检索器
        vector_store = VectorStore()
        bm25_retriever = BM25Retriever()
        
        # 测试索引构建时间
        print("测试索引构建时间:")
        
        start_time = time.time()
        vector_store.add_documents(segments)
        vs_index_time = time.time() - start_time
        print(f"  向量存储索引构建: {vs_index_time:.4f} 秒")
        
        start_time = time.time()
        bm25_retriever.add_documents(segments)
        bm25_index_time = time.time() - start_time
        print(f"  BM25索引构建: {bm25_index_time:.4f} 秒")
        
        # 测试查询时间
        test_queries = ["GPS", "location", "satellite", "phone"]
        
        print("\n测试查询时间:")
        print(f"{'查询':<12} {'向量存储':<12} {'BM25':<12}")
        print("-" * 36)
        
        for query in test_queries:
            # 向量存储查询时间
            start_time = time.time()
            vector_store.search(query, top_k=3)
            vs_query_time = time.time() - start_time
            
            # BM25查询时间
            start_time = time.time()
            bm25_retriever.search(query, top_k=3)
            bm25_query_time = time.time() - start_time
            
            print(f"{query:<12} {vs_query_time:<12.4f} {bm25_query_time:<12.4f}")
        
        print("\n✅ 性能对比测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False
    
    return True


def test_multi_query_integration():
    """测试多查询生成器与检索系统的集成"""
    print("\n" + "=" * 60)
    print("测试多查询生成器集成")
    print("=" * 60)
    
    try:
        # 加载测试数据
        segments = load_test_transcript()
        print(f"加载了 {len(segments)} 个视频片段")
        
        # 创建检索器和多查询生成器
        vector_store = VectorStore()
        bm25_retriever = BM25Retriever()
        multi_query_generator = MultiQueryGenerator(
            max_queries=5
        )
        
        # 添加文档
        print("\n添加文档到检索器...")
        vector_store.add_documents(segments)
        bm25_retriever.add_documents(segments)
        
        # 测试查询
        test_queries = [
            "GPS定位技术",
            "smartphone location", 
            "卫星导航系统"
        ]
        
        print("\n多查询生成和检索测试:")
        print("=" * 60)
        
        for query in test_queries:
            print(f"\n原始查询: '{query}'")
            print("-" * 40)
            
            # 生成多查询
            multi_result = multi_query_generator.generate_queries(query)
            print(f"生成了 {len(multi_result.generated_queries)} 个查询:")
            
            for i, q in enumerate(multi_result.generated_queries):
                print(f"  {i+1}. {q.query} [权重: {q.weight:.3f}] [方法: {q.method}]")
            
            # 对每个生成的查询进行检索
            print("\n检索结果:")
            print(f"{'查询':<20} {'向量结果':<8} {'BM25结果':<8} {'最佳匹配'}")
            print("-" * 60)
            
            all_results = {}
            
            for q in multi_result.generated_queries:
                # 向量存储检索
                try:
                    vs_results = vector_store.search(q.query, top_k=1)
                    vs_count = len(vs_results)
                    vs_best = vs_results[0]["document"]["text"][:30] + "..." if vs_results else "无"
                except:
                    vs_count = 0
                    vs_best = "错误"
                
                # BM25检索
                try:
                    bm25_results = bm25_retriever.search(q.query, top_k=1)
                    bm25_count = len(bm25_results)
                    bm25_best = bm25_results[0]["document"]["text"][:30] + "..." if bm25_results else "无"
                except:
                    bm25_count = 0
                    bm25_best = "错误"
                
                # 记录结果
                all_results[q.query] = {
                    "weight": q.weight,
                    "vs_count": vs_count,
                    "bm25_count": bm25_count,
                    "vs_best": vs_best,
                    "bm25_best": bm25_best
                }
                
                print(f"{q.query[:20]:<20} {vs_count:<8} {bm25_count:<8} {vs_best}")
            
            # 分析多查询效果
            print(f"\n多查询效果分析:")
            total_vs_results = sum(r["vs_count"] for r in all_results.values())
            total_bm25_results = sum(r["bm25_count"] for r in all_results.values())
            
            print(f"  总向量检索结果: {total_vs_results}")
            print(f"  总BM25检索结果: {total_bm25_results}")
            print(f"  平均每查询向量结果: {total_vs_results/len(all_results):.1f}")
            print(f"  平均每查询BM25结果: {total_bm25_results/len(all_results):.1f}")
        
        print("\n✅ 多查询生成器集成测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False
    
    return True


def test_multi_query_enhanced_retrieval():
    """测试多查询增强检索效果"""
    print("\n" + "=" * 60)
    print("测试多查询增强检索效果")
    print("=" * 60)
    
    try:
        # 加载测试数据
        segments = load_test_transcript()
        
        # 创建检索器和多查询生成器
        vector_store = VectorStore()
        bm25_retriever = BM25Retriever()
        multi_query_generator = MultiQueryGenerator(
            max_queries=8
        )
        
        # 添加文档
        vector_store.add_documents(segments)
        bm25_retriever.add_documents(segments)
        
        # 测试查询
        test_query = "手机定位原理"
        
        print(f"测试查询: '{test_query}'")
        print("=" * 40)
        
        # 单查询检索
        print("\n单查询检索结果:")
        vs_single = vector_store.search(test_query, top_k=5)
        bm25_single = bm25_retriever.search(test_query, top_k=5)
        
        print(f"向量存储: {len(vs_single)} 个结果")
        for i, result in enumerate(vs_single):
            text = result["document"]["text"][:50] + "..."
            print(f"  {i+1}. [相似度: {result['similarity']:.3f}] {text}")
        
        print(f"\nBM25检索: {len(bm25_single)} 个结果")
        for i, result in enumerate(bm25_single):
            text = result["document"]["text"][:50] + "..."
            print(f"  {i+1}. [分数: {result['score']:.3f}] {text}")
        
        # 多查询增强检索
        print(f"\n多查询增强检索结果:")
        multi_result = multi_query_generator.generate_queries(test_query)
        
        # 收集所有检索结果
        all_vs_docs = {}
        all_bm25_docs = {}
        
        for q in multi_result.generated_queries:
            # 向量存储检索
            vs_results = vector_store.search(q.query, top_k=3)
            for result in vs_results:
                doc_id = result["document"]["id"]
                if doc_id not in all_vs_docs:
                    all_vs_docs[doc_id] = {
                        "document": result["document"],
                        "max_similarity": result["similarity"],
                        "query_hits": []
                    }
                else:
                    all_vs_docs[doc_id]["max_similarity"] = max(
                        all_vs_docs[doc_id]["max_similarity"], 
                        result["similarity"]
                    )
                all_vs_docs[doc_id]["query_hits"].append(q.query)
            
            # BM25检索
            bm25_results = bm25_retriever.search(q.query, top_k=3)
            for result in bm25_results:
                doc_id = result["document"]["id"]
                if doc_id not in all_bm25_docs:
                    all_bm25_docs[doc_id] = {
                        "document": result["document"],
                        "max_score": result["score"],
                        "query_hits": []
                    }
                else:
                    all_bm25_docs[doc_id]["max_score"] = max(
                        all_bm25_docs[doc_id]["max_score"], 
                        result["score"]
                    )
                all_bm25_docs[doc_id]["query_hits"].append(q.query)
        
        # 排序并显示结果
        print(f"\n增强向量检索: {len(all_vs_docs)} 个唯一结果")
        sorted_vs = sorted(all_vs_docs.values(), key=lambda x: x["max_similarity"], reverse=True)
        for i, doc_data in enumerate(sorted_vs[:5]):
            text = doc_data["document"]["text"][:50] + "..."
            print(f"  {i+1}. [相似度: {doc_data['max_similarity']:.3f}] {text}")
            print(f"      匹配查询: {', '.join(doc_data['query_hits'])}")
        
        print(f"\n增强BM25检索: {len(all_bm25_docs)} 个唯一结果")
        sorted_bm25 = sorted(all_bm25_docs.values(), key=lambda x: x["max_score"], reverse=True)
        for i, doc_data in enumerate(sorted_bm25[:5]):
            text = doc_data["document"]["text"][:50] + "..."
            print(f"  {i+1}. [分数: {doc_data['max_score']:.3f}] {text}")
            print(f"      匹配查询: {', '.join(doc_data['query_hits'])}")
        
        # 效果对比
        print(f"\n检索效果对比:")
        print(f"  单查询向量检索: {len(vs_single)} 个结果")
        print(f"  多查询向量检索: {len(all_vs_docs)} 个结果")
        print(f"  召回率提升: {((len(all_vs_docs) - len(vs_single)) / len(vs_single) * 100):.1f}%")
        print(f"  单查询BM25检索: {len(bm25_single)} 个结果")
        print(f"  多查询BM25检索: {len(all_bm25_docs)} 个结果")
        print(f"  召回率提升: {((len(all_bm25_docs) - len(bm25_single)) / max(len(bm25_single), 1) * 100):.1f}%")
        
        print("\n✅ 多查询增强检索效果测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False
    
    return True


def main():
    """运行所有集成测试"""
    print("开始检索系统集成测试")
    print("=" * 60)
    
    tests = [
        test_vector_store_vs_bm25,
        test_hybrid_retrieval_concept,
        test_performance_comparison,
        test_multi_query_integration,
        test_multi_query_enhanced_retrieval
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print("集成测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有检索系统集成测试通过！")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)