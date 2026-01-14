#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA系统集成测试脚本
测试讯飞星火API集成和完整对话流程
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.qa import ConversationChain, Memory, PromptTemplate
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.hybrid_retriever import HybridRetriever
from config.settings import settings


def test_llm_integration():
    """测试LLM集成"""
    print("=" * 50)
    print("测试LLM集成")
    print("=" * 50)
    
    try:
        # 创建对话链
        conversation_chain = ConversationChain()
        
        # 测试简单对话
        test_query = "你好，请介绍一下自己。"
        print(f"用户问题: {test_query}")
        
        # 模拟检索结果
        mock_retrieved_docs = [
            {
                'text': '这是一个测试视频内容，介绍了AI视频助手的功能。',
                'start': 0.0,
                'end': 5.0,
                'similarity': 0.9
            }
        ]
        
        # 手动设置检索结果（用于测试）
        conversation_chain.retriever = None  # 暂时不使用检索器
        
        # 直接测试LLM调用
        response = conversation_chain._call_openai(test_query, "")
        print(f"AI回答: {response}")
        
        print("\n✅ LLM集成测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM集成测试失败: {e}")
        return False


def test_conversation_memory():
    """测试对话记忆功能"""
    print("\n" + "=" * 50)
    print("测试对话记忆功能")
    print("=" * 50)
    
    try:
        # 创建对话链
        conversation_chain = ConversationChain()
        
        # 模拟多轮对话
        questions = [
            "什么是人工智能？",
            "人工智能有哪些应用？",
            "刚才提到的应用中，哪个最重要？"
        ]
        
        for i, question in enumerate(questions):
            print(f"\n第{i+1}轮对话:")
            print(f"用户: {question}")
            
            # 模拟检索结果
            context = f"这是第{i+1}个问题的相关视频内容。"
            
            # 生成回答
            result = conversation_chain.chat(question, top_k=3)
            print(f"AI: {result['response']}")
            
            # 显示对话历史
            print(f"对话轮数: {len(conversation_chain.conversation_history)}")
        
        print("\n✅ 对话记忆功能测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 对话记忆功能测试失败: {e}")
        return False


def test_context_management():
    """测试上下文管理"""
    print("\n" + "=" * 50)
    print("测试上下文管理")
    print("=" * 50)
    
    try:
        # 创建对话链
        conversation_chain = ConversationChain()
        
        # 创建长文本上下文
        long_context = """
        这是一个很长的视频内容，用于测试上下文管理功能。
        视频内容包含了很多信息，比如人工智能的定义、历史、应用等。
        人工智能（AI）是计算机科学的一个分支，它试图理解和构建智能体。
        这些智能体能够感知环境并采取行动以最大化其成功的机会。
        AI的发展历史可以追溯到1950年代，经历了多次发展浪潮。
        当前，AI已经在多个领域得到广泛应用，包括医疗诊断、自动驾驶、金融风控等。
        机器学习是AI的一个重要子领域，专注于算法和统计模型。
        深度学习是机器学习的一个分支，使用神经网络来模拟人脑的学习过程。
        自然语言处理是AI的另一个重要领域，致力于让计算机理解和生成人类语言。
        计算机视觉则专注于让计算机能够理解和分析图像和视频。
        强化学习是一种通过与环境交互来学习最优策略的方法。
        专家系统是早期AI的一种形式，使用规则和知识库来解决问题。
        随着技术的发展，AI正在变得越来越智能和普及。
        未来，AI可能会在更多领域发挥重要作用，改变我们的生活方式。
        """
        
        # 测试消息构建
        test_query = "请总结这个视频的主要内容。"
        messages = conversation_chain._build_messages(test_query, long_context)
        
        print(f"构建的消息数量: {len(messages)}")
        print(f"系统提示长度: {len(messages[0]['content'])}")
        
        if len(messages) > 1:
            print(f"视频内容长度: {len(messages[1]['content'])}")
        
        # 测试token管理
        managed_messages = conversation_chain._manage_token_limit(messages)
        print(f"管理后的消息数量: {len(managed_messages)}")
        
        print("\n✅ 上下文管理测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 上下文管理测试失败: {e}")
        return False


def test_complete_flow():
    """测试完整流程"""
    print("\n" + "=" * 50)
    print("测试完整QA流程")
    print("=" * 50)
    
    try:
        # 创建测试文档
        test_docs = [
            {
                'text': '人工智能是计算机科学的一个分支，它试图理解和构建智能体。',
                'start': 0.0,
                'end': 5.0,
                'similarity': 0.9
            },
            {
                'text': '机器学习是人工智能的一个子领域，专注于算法和统计模型。',
                'start': 5.0,
                'end': 10.0,
                'similarity': 0.8
            },
            {
                'text': '深度学习是机器学习的一个分支，使用神经网络来模拟人脑。',
                'start': 10.0,
                'end': 15.0,
                'similarity': 0.7
            }
        ]
        
        # 创建检索器（模拟）
        class MockRetriever:
            def search(self, query, top_k=5):
                return test_docs[:top_k]
        
        # 创建对话链
        conversation_chain = ConversationChain(retriever=MockRetriever())
        
        # 测试问答
        test_query = "什么是机器学习？"
        print(f"用户问题: {test_query}")
        
        result = conversation_chain.chat(test_query, top_k=3)
        print(f"AI回答: {result['response']}")
        print(f"检索到的文档数量: {len(result['retrieved_docs'])}")
        
        print("\n✅ 完整流程测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 完整流程测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始QA系统集成测试...")
    print("=" * 50)
    
    # 显示配置信息
    print("配置信息:")
    print(f"LLM提供商: {settings.get_model_config('llm', 'provider')}")
    print(f"模型名称: {settings.get_model_config('llm', 'openai', 'model_name')}")
    print(f"API地址: {settings.get_model_config('llm', 'openai', 'base_url')}")
    print(f"最大token: {settings.get_model_config('llm', 'openai', 'max_tokens')}")
    print(f"上下文长度: {settings.get_model_config('qa_system', 'max_context_length')}")
    print(f"对话历史长度: {settings.get_model_config('qa_system', 'history_length')}")
    
    # 运行测试
    tests = [
        test_llm_integration,
        test_conversation_memory,
        test_context_management,
        test_complete_flow
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
        print("🎉 所有测试通过！QA系统集成成功！")
    else:
        print("⚠️ 部分测试失败，请检查配置和实现。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)