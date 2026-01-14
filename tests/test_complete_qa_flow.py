#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整QA流程测试脚本
测试多查询生成→混合检索→QA的完整流程
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.qa import ConversationChain, Memory, PromptTemplate
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.hybrid_retriever import HybridRetriever
from config.settings import settings


def create_test_documents():
    """创建测试文档"""
    return [
        {
            'text': '人工智能（AI）是计算机科学的一个分支，它试图理解和构建智能体，这些智能体能够感知环境并采取行动以最大化其成功的机会。',
            'start': 0.0,
            'end': 10.0,
            'confidence': 0.95
        },
        {
            'text': '机器学习是人工智能的一个子领域，专注于算法和统计模型，使计算机能够从数据中学习并做出预测或决策。',
            'start': 10.0,
            'end': 20.0,
            'confidence': 0.93
        },
        {
            'text': '深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程，在图像识别、自然语言处理等领域取得了突破性进展。',
            'start': 20.0,
            'end': 30.0,
            'confidence': 0.91
        },
        {
            'text': '自然语言处理（NLP）是AI的重要应用领域，致力于让计算机能够理解、解释和生成人类语言。',
            'start': 30.0,
            'end': 40.0,
            'confidence': 0.89
        },
        {
            'text': '计算机视觉是另一个重要的AI应用，专注于让计算机能够从图像或视频中获取、处理和理解视觉信息。',
            'start': 40.0,
            'end': 50.0,
            'confidence': 0.87
        },
        {
            'text': '强化学习是一种通过与环境交互来学习最优策略的机器学习方法，在游戏、机器人控制等领域有广泛应用。',
            'start': 50.0,
            'end': 60.0,
            'confidence': 0.85
        },
        {
            'text': 'AI在医疗领域的应用包括疾病诊断、药物发现、个性化治疗等，大大提高了医疗效率和准确性。',
            'start': 60.0,
            'end': 70.0,
            'confidence': 0.88
        },
        {
            'text': '自动驾驶汽车是AI技术的重要应用之一，通过传感器和算法实现车辆的自主导航和驾驶决策。',
            'start': 70.0,
            'end': 80.0,
            'confidence': 0.86
        },
        {
            'text': '金融风控利用AI技术分析大量交易数据，识别欺诈行为，评估信用风险，提高金融系统的安全性。',
            'start': 80.0,
            'end': 90.0,
            'confidence': 0.84
        },
        {
            'text': '智能客服系统使用自然语言处理技术，能够理解用户问题并提供准确的回答，大大提高了客户服务效率。',
            'start': 90.0,
            'end': 100.0,
            'confidence': 0.82
        }
    ]


def setup_retrievers():
    """设置检索器"""
    print("设置检索器...")
    
    # 创建测试文档
    documents = create_test_documents()
    
    # 创建向量存储
    vector_store = VectorStore()
    vector_store.add_documents(documents, text_field="text")
    
    # 创建BM25检索器
    bm25_retriever = BM25Retriever(language='auto')
    bm25_retriever.add_documents(documents, text_field="text")
    
    # 创建混合检索器
    hybrid_retriever = HybridRetriever(
        vector_store=vector_store,
        bm25_retriever=bm25_retriever,
        vector_weight=0.6,
        bm25_weight=0.4,
        fusion_method="weighted_average"
    )
    
    print(f"✓ 检索器设置完成，包含 {len(documents)} 个文档")
    return hybrid_retriever


def test_multi_query_generation():
    """测试多查询生成"""
    print("\n" + "=" * 50)
    print("测试多查询生成")
    print("=" * 50)
    
    try:
        from modules.retrieval.multi_query import MultiQueryGenerator
        
        # 创建多查询生成器
        models_dir = settings.PROJECT_ROOT / "models"
        generator = MultiQueryGenerator(cache_dir=str(models_dir))
        
        # 测试查询
        test_query = "人工智能有哪些应用领域？"
        print(f"原始查询: {test_query}")
        
        # 生成扩展查询
        result = generator.generate_queries(test_query)
        
        print(f"\n生成了 {len(result.generated_queries)} 个扩展查询:")
        for i, generated_query in enumerate(result.generated_queries):
            print(f"{i+1}. {generated_query.query} [权重: {generated_query.weight:.3f}]")
        
        print("\n✅ 多查询生成测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 多查询生成测试失败: {e}")
        return False


def test_hybrid_retrieval():
    """测试混合检索"""
    print("\n" + "=" * 50)
    print("测试混合检索")
    print("=" * 50)
    
    try:
        # 设置检索器
        hybrid_retriever = setup_retrievers()
        
        # 测试查询
        test_queries = [
            "什么是机器学习？",
            "AI在医疗领域的应用",
            "深度学习和机器学习的关系",
            "自然语言处理的应用"
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            
            # 执行混合检索
            results = hybrid_retriever.search(query, top_k=3)
            
            print(f"检索到 {len(results)} 个结果:")
            for i, result in enumerate(results):
                print(f"{i+1}. [分数: {result['score']:.3f}] {result['text']}")
                print(f"   时间: {result['start']:.1f}s - {result['end']:.1f}s")
        
        print("\n✅ 混合检索测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 混合检索测试失败: {e}")
        return False


def test_complete_qa_flow():
    """测试完整QA流程"""
    print("\n" + "=" * 50)
    print("测试完整QA流程")
    print("=" * 50)
    
    try:
        # 设置检索器
        hybrid_retriever = setup_retrievers()
        
        # 创建对话链
        conversation_chain = ConversationChain(retriever=hybrid_retriever)
        
        # 测试多轮对话
        test_conversations = [
            "你好，我想了解人工智能的基本概念",
            "机器学习和深度学习有什么区别？",
            "AI在医疗领域有哪些具体应用？",
            "刚才提到的应用中，哪个最有前景？",
            "你能总结一下AI技术的发展趋势吗？"
        ]
        
        for i, question in enumerate(test_conversations):
            print(f"\n第{i+1}轮对话:")
            print(f"用户: {question}")
            
            # 执行完整的QA流程
            result = conversation_chain.chat(question, top_k=5)
            
            print(f"AI: {result['response']}")
            print(f"检索到的文档数量: {len(result['retrieved_docs'])}")
            print(f"上下文长度: {len(result['context'])}")
            
            # 显示检索到的文档
            if result['retrieved_docs']:
                print("相关文档:")
                for j, doc in enumerate(result['retrieved_docs'][:3]):
                    print(f"  {j+1}. [相似度: {doc.get('similarity', 0):.3f}] {doc.get('text', doc.get('document', {}).get('text', ''))[:50]}...")
        
        print("\n✅ 完整QA流程测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 完整QA流程测试失败: {e}")
        return False


def test_performance_metrics():
    """测试性能指标"""
    print("\n" + "=" * 50)
    print("测试性能指标")
    print("=" * 50)
    
    try:
        import time
        
        # 设置检索器
        hybrid_retriever = setup_retrievers()
        
        # 创建对话链
        conversation_chain = ConversationChain(retriever=hybrid_retriever)
        
        # 测试查询
        test_query = "人工智能的主要应用领域有哪些？"
        
        # 测试各环节耗时
        start_time = time.time()
        
        # 1. 多查询生成
        multi_query_start = time.time()
        multi_query_result = conversation_chain.multi_query.generate_queries(test_query)
        multi_query_time = time.time() - multi_query_start
        
        # 2. 检索
        retrieval_start = time.time()
        retrieved_docs = conversation_chain._retrieve_documents(test_query, top_k=5)
        retrieval_time = time.time() - retrieval_start
        
        # 3. 上下文构建
        context_start = time.time()
        context = conversation_chain._build_context(retrieved_docs, test_query)
        context_time = time.time() - context_start
        
        # 4. LLM生成
        llm_start = time.time()
        response = conversation_chain._call_openai(test_query, context)
        llm_time = time.time() - llm_start
        
        total_time = time.time() - start_time
        
        # 输出性能指标
        print(f"查询: {test_query}")
        print(f"\n性能指标:")
        print(f"多查询生成: {multi_query_time:.3f}s ({len(multi_query_result.generated_queries)} 个查询)")
        print(f"文档检索: {retrieval_time:.3f}s ({len(retrieved_docs)} 个文档)")
        print(f"上下文构建: {context_time:.3f}s ({len(context)} 字符)")
        print(f"LLM生成: {llm_time:.3f}s ({len(response)} 字符)")
        print(f"总耗时: {total_time:.3f}s")
        
        print("\n✅ 性能指标测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 性能指标测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始完整QA流程测试...")
    print("=" * 50)
    
    # 显示配置信息
    print("配置信息:")
    print(f"LLM提供商: {settings.get_model_config('llm', 'provider')}")
    print(f"模型名称: {settings.get_model_config('llm', 'openai', 'model_name')}")
    print(f"融合方法: weighted_average")
    print(f"向量权重: 0.6, BM25权重: 0.4")
    
    # 运行测试
    tests = [
        test_multi_query_generation,
        test_hybrid_retrieval,
        test_complete_qa_flow,
        test_performance_metrics
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    if passed == total:
        print("🎉 所有测试通过！完整QA流程实现成功！")
    else:
        print("⚠️ 部分测试失败，请检查实现。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)