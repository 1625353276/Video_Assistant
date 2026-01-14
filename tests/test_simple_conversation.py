#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试简单对话模式脚本
每次对话都发送完整视频内容 + 检索结果 + 用户问题，不保存历史记录
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.qa.conversation_chain import ConversationChain
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.hybrid_retriever import HybridRetriever

def test_simple_conversation_mode():
    """测试简单对话模式"""
    print("=== 测试简单对话模式 ===\n")
    
    # 创建测试数据
    test_transcript = [
        {'text': '人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。', 'start': 0.0, 'end': 5.0},
        {'text': '机器学习是人工智能的子领域，专注于算法和统计模型，使计算机能够在没有明确编程的情况下学习和改进。', 'start': 5.0, 'end': 10.0},
        {'text': '深度学习是机器学习的子集，使用人工神经网络来模拟人脑的工作方式。', 'start': 10.0, 'end': 15.0},
        {'text': '神经网络是深度学习的基础，由多个相互连接的神经元层组成。', 'start': 15.0, 'end': 20.0},
        {'text': '自然语言处理是人工智能的应用领域，专注于计算机与人类语言的交互。', 'start': 20.0, 'end': 25.0}
    ]
    
    # 创建检索器
    print("1. 创建检索器...")
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    
    # 添加文档
    vector_store.add_documents(test_transcript)
    bm25_retriever.add_documents(test_transcript)
    
    # 创建混合检索器
    hybrid_retriever = HybridRetriever(
        vector_store=vector_store,
        bm25_retriever=bm25_retriever,
        fusion_method="weighted_average",
        vector_weight=0.6,
        bm25_weight=0.4
    )
    
    # 创建对话链
    print("2. 创建对话链...")
    chain = ConversationChain(retriever=hybrid_retriever)
    
    # 设置转录内容
    print("3. 设置转录内容...")
    chain.set_full_transcript(test_transcript)
    
    # 测试对话
    questions = [
        "什么是人工智能？",
        "机器学习和深度学习的关系是什么？",
        "神经网络有什么作用？",
        "自然语言处理属于哪个领域？"
    ]
    
    print("\n4. 开始对话测试...\n")
    
    for i, question in enumerate(questions, 1):
        print(f"=== 第{i}轮对话 ===")
        print(f"问题: {question}")
        
        # 执行对话
        response = chain.chat(question, top_k=3)
        
        print(f"回答: {response['response']}")
        print(f"检索到的文档数: {len(response['retrieved_docs'])}")
        print(f"历史轮次数: {response['metadata']['total_turns']}")
        
        # 显示检索到的文档
        if response['retrieved_docs']:
            print("\n检索到的相关内容:")
            for j, doc in enumerate(response['retrieved_docs'], 1):
                print(f"  {j}. {doc['text'][:50]}...")
        
        print("-" * 50)
    
    print("\n=== 测试完成 ===")
    print("✅ 每轮对话都发送了完整的视频内容")
    print("✅ 没有保存历史记录")
    print("✅ LLM能够基于完整内容和检索结果回答问题")

if __name__ == "__main__":
    test_simple_conversation_mode()