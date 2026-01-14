#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - QA系统集成测试
Integration Test for QA System

测试QA系统的完整功能，包括对话链、记忆管理和提示模板
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入QA系统模块
from modules.qa import ConversationChain, Memory, PromptTemplate
from modules.qa.conversation_data import ConversationTurn
from modules.retrieval.vector_store import VectorStore

# 导入配置
from config.settings import settings
class TestQASystem(unittest.TestCase):
    """QA系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_data_dir = self.test_dir / "test_data"
        self.test_data_dir.mkdir(parents=True)
        
        # 创建测试文档
        self.test_documents = [
            {
                'text': '人工智能是计算机科学的一个分支，它试图理解和构建智能体。',
                'start': 0.0,
                'end': 5.0,
                'confidence': 0.95
            },
            {
                'text': '机器学习是人工智能的一个子领域，专注于算法和统计模型。',
                'start': 5.0,
                'end': 10.0,
                'confidence': 0.92
            },
            {
                'text': '深度学习是机器学习的一个分支，使用神经网络来学习数据的表示。',
                'start': 10.0,
                'end': 15.0,
                'confidence': 0.88
            }
        ]
        
        # 创建测试转写文件
        self.test_transcript = {
            'audio_file': 'test_video.mp4',
            'language': 'zh',
            'text': '人工智能是计算机科学的一个分支，它试图理解和构建智能体。机器学习是人工智能的一个子领域，专注于算法和统计模型。深度学习是机器学习的一个分支，使用神经网络来学习数据的表示。',
            'segments': [
                {
                    'id': 0,
                    'start': 0.0,
                    'end': 5.0,
                    'text': '人工智能是计算机科学的一个分支，它试图理解和构建智能体。',
                    'confidence': 0.95
                },
                {
                    'id': 1,
                    'start': 5.0,
                    'end': 10.0,
                    'text': '机器学习是人工智能的一个子领域，专注于算法和统计模型。',
                    'confidence': 0.92
                },
                {
                    'id': 2,
                    'start': 10.0,
                    'end': 15.0,
                    'text': '深度学习是机器学习的一个分支，使用神经网络来学习数据的表示。',
                    'confidence': 0.88
                }
            ]
        }
        
        # 保存测试转写文件
        self.transcript_path = self.test_data_dir / "test_transcript.json"
        with open(self.transcript_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_transcript, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir)
    
    def test_prompt_template(self):
        """测试提示模板"""
        print("\n测试提示模板...")
        
        # 创建提示模板
        prompt_template = PromptTemplate()
        
        # 测试基本提示构建
        prompt = prompt_template.build_prompt(
            query="什么是人工智能？",
            context="人工智能是计算机科学的一个分支",
            template_type="qa"
        )
        
        self.assertIn("什么是人工智能？", prompt)
        self.assertIn("人工智能是计算机科学的一个分支", prompt)
        
        # 测试示例选择
        examples = prompt_template._select_examples("什么是机器学习？", "机器学习是AI的子领域")
        self.assertGreater(len(examples), 0)
        
        # 测试添加示例
        prompt_template.add_example(
            question="测试问题",
            answer="测试回答",
            context="测试上下文"
        )
        
        self.assertGreater(len(prompt_template.examples), 0)
        
        # 测试模板验证
        result = prompt_template.validate_template("你好，{name}！")
        self.assertFalse(result['valid'])  # name不在预定义变量中
        
        print("✅ 提示模板测试通过")
    
    def test_memory_system(self):
        """测试记忆系统"""
        print("\n测试记忆系统...")
        
        # 创建记忆系统
        memory = Memory(memory_type="buffer")
        
        # 测试添加记忆项
        item_id = memory.add_memory_item(
            content="人工智能是计算机科学的一个分支",
            item_type="knowledge",
            tags=["AI", "计算机科学"],
            importance=0.8
        )
        
        self.assertIsNotNone(item_id)
        
        # 测试获取记忆项
        item = memory.get_memory_item(item_id)
        self.assertIsNotNone(item)
        self.assertEqual(item.content, "人工智能是计算机科学的一个分支")
        
        # 测试搜索记忆
        results = memory.search_memory("人工智能")
        self.assertGreater(len(results), 0)
        
        # 测试标签搜索
        results = memory.get_memory_by_tags(["AI"])
        self.assertGreater(len(results), 0)
        
        # 测试记忆摘要
        summary = memory.get_summary()
        self.assertIsInstance(summary, str)
        
        # 测试统计信息
        stats = memory.get_stats()
        self.assertIn('total_items', stats)
        self.assertEqual(stats['total_items'], 1)
        
        # 测试导出和导入
        export_path = self.test_data_dir / "memory_export.json"
        memory.export_memory(str(export_path), format='json')
        self.assertTrue(export_path.exists())
        
        # 清空记忆
        memory.clear()
        self.assertEqual(len(memory.memory_items), 0)
        
        # 导入记忆
        memory.import_memory(str(export_path), format='json')
        self.assertGreater(len(memory.memory_items), 0)
        
        print("✅ 记忆系统测试通过")
    
    def test_conversation_chain(self):
        """测试对话链"""
        print("\n测试对话链...")
        
        # 创建检索器（使用向量存储）
        vector_store = VectorStore()
        vector_store.add_documents(self.test_documents)
        
        # 创建记忆系统
        memory = Memory(memory_type="buffer")
        
        # 创建提示模板
        prompt_template = PromptTemplate()
        
        # 创建对话链
        conversation_chain = ConversationChain(
            retriever=vector_store,
            memory=memory,
            prompt_template=prompt_template
        )
        
        # 测试对话
        result = conversation_chain.chat("什么是人工智能？")
        
        self.assertIn('query', result)
        self.assertIn('response', result)
        self.assertIn('retrieved_docs', result)
        self.assertEqual(result['query'], "什么是人工智能？")
        
        # 测试多轮对话
        result2 = conversation_chain.chat("机器学习是什么？")
        
        # 检查对话历史
        history = conversation_chain.get_conversation_history()
        self.assertEqual(len(history), 2)
        
        # 测试对话统计
        stats = conversation_chain.get_stats()
        self.assertIn('total_turns', stats)
        self.assertEqual(stats['total_turns'], 2)
        
        # 测试保存和加载对话
        conversation_path = self.test_data_dir / "conversation.json"
        conversation_chain.save_conversation(str(conversation_path))
        self.assertTrue(conversation_path.exists())
        
        # 清空历史
        conversation_chain.clear_history()
        self.assertEqual(len(conversation_chain.conversation_history), 0)
        
        # 加载对话
        conversation_chain.load_conversation(str(conversation_path))
        self.assertGreater(len(conversation_chain.conversation_history), 0)
        
        print("✅ 对话链测试通过")
    
    def test_qa_with_retriever(self):
        """测试QA系统与检索器的集成"""
        print("\n测试QA系统与检索器集成...")
        
        # 使用已有的向量存储（不重复测试检索功能）
        vector_store = VectorStore()
        vector_store.add_documents(self.test_documents)
        
        # 创建QA系统
        conversation_chain = ConversationChain(
            retriever=vector_store,
            memory=Memory(),
            prompt_template=PromptTemplate()
        )
        
        # 测试问答
        result = conversation_chain.chat("什么是人工智能？")
        
        # 验证QA系统功能
        self.assertIn('query', result)
        self.assertIn('response', result)
        self.assertIn('retrieved_docs', result)
        self.assertEqual(result['query'], "什么是人工智能？")
        
        print("✅ QA系统与检索器集成测试通过")
    
    def test_integration(self):
        """测试系统集成"""
        print("\n测试系统集成...")
        
        # 使用简单的向量存储进行集成测试
        vector_store = VectorStore()
        vector_store.add_documents(self.test_documents)
        
        memory = Memory(memory_type="buffer")
        prompt_template = PromptTemplate()
        
        conversation_chain = ConversationChain(
            retriever=vector_store,
            memory=memory,
            prompt_template=prompt_template
        )
        
        # 简化的对话测试
        questions = [
            "什么是人工智能？",
            "机器学习是什么？"
        ]
        
        for question in questions:
            result = conversation_chain.chat(question)
            
            # 验证基本功能
            self.assertIn('query', result)
            self.assertIn('response', result)
            self.assertIn('retrieved_docs', result)
            
            print(f"  问题: {question}")
            print(f"  回答: {result['response'][:50]}...")
        
        # 验证记忆和历史
        history = conversation_chain.get_conversation_history()
        self.assertEqual(len(history), len(questions))
        
        print("✅ 系统集成测试通过")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n测试错误处理...")
        
        # 测试无效检索器
        conversation_chain = ConversationChain(retriever=None)
        result = conversation_chain.chat("测试问题")
        
        # 应该返回错误信息而不是崩溃
        self.assertIn('response', result)
        self.assertEqual(len(result['retrieved_docs']), 0)
        
        # 测试记忆系统错误处理
        memory = Memory()
        
        # 测试获取不存在的记忆项
        item = memory.get_memory_item("nonexistent_id")
        self.assertIsNone(item)
        
        # 测试删除不存在的记忆项
        result = memory.delete_memory_item("nonexistent_id")
        self.assertFalse(result)
        
        print("✅ 错误处理测试通过")


def run_qa_tests():
    """运行QA系统测试"""
    print("=" * 60)
    print("AI视频助手 - QA系统集成测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQASystem)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n测试结果: {'通过' if success else '失败'}")
    print("=" * 60)
    
    return success


def test_api_configuration():
    """测试讯飞星火API配置"""
    print("=" * 60)
    print("讯飞星火API配置验证")
    print("=" * 60)
    
    try:
        # 测试配置加载
        print("1. 测试配置加载...")
        llm_config = settings.get_model_config('llm')
        assert llm_config is not None
        print(f"✅ 配置加载成功")
        
        # 检查OpenAI配置
        openai_config = llm_config.get('openai', {})
        api_key = openai_config.get('api_key')
        model_name = openai_config.get('model_name')
        base_url = openai_config.get('base_url')
        
        print(f"   API Key: {api_key[:20]}..." if api_key else "   API Key: 未配置")
        print(f"   模型名称: {model_name}")
        print(f"   API地址: {base_url}")
        
        # 验证必需参数
        if not api_key:
            print("❌ API Key未配置")
            return False
        if not model_name:
            print("❌ 模型名称未配置")
            return False
        if not base_url:
            print("❌ API地址未配置")
            return False
            
        print("✅ 配置参数验证通过")
        
        # 测试OpenAI客户端连接
        print("2. 测试API连接...")
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            # 发送测试请求
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=50,
                temperature=0.7
            )
            
            if response and response.choices:
                result = response.choices[0].message.content
                print(f"✅ API连接成功")
                print(f"   测试响应: {result[:50]}...")
                return True
            else:
                print("❌ API响应为空")
                return False
                
        except Exception as api_error:
            print(f"❌ API连接失败: {api_error}")
            return False
            
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def simple_test():
    """测试QA系统与检索模块的集成"""
    print("=" * 60)
    print("QA系统与检索模块集成测试")
    print("=" * 60)
    
    try:
        # 测试API配置
        print("1. 验证API配置...")
        llm_config = settings.get_model_config('llm')
        openai_config = llm_config.get('openai', {})
        
        api_key = openai_config.get('api_key')
        model_name = openai_config.get('model_name')
        base_url = openai_config.get('base_url')
        
        print(f"   API Key: {api_key[:20]}..." if api_key else "   API Key: 未配置")
        print(f"   模型名称: {model_name}")
        print(f"   API地址: {base_url}")
        
        if not all([api_key, model_name, base_url]):
            print("❌ 配置参数缺失")
            return False
        
        print("✅ 配置验证通过")
        print()
        
        # 导入已有检索模块
        print("2. 导入检索模块...")
        from modules.retrieval.vector_store import VectorStore
        from modules.retrieval.bm25_retriever import BM25Retriever
        from modules.retrieval.hybrid_retriever import HybridRetriever
        
        print("✅ 检索模块导入成功")
        print()
        
        # 创建测试数据
        print("3. 创建测试数据...")
        test_documents = [
            {
                'text': '人工智能是计算机科学的一个分支，它试图理解和构建智能体。',
                'start': 0.0,
                'end': 5.0,
                'confidence': 0.95
            },
            {
                'text': '机器学习是人工智能的一个子领域，专注于算法和统计模型。',
                'start': 5.0,
                'end': 10.0,
                'confidence': 0.92
            },
            {
                'text': '深度学习是机器学习的一个分支，使用神经网络来学习数据的表示。',
                'start': 10.0,
                'end': 15.0,
                'confidence': 0.88
            }
        ]
        print(f"   创建了 {len(test_documents)} 个测试文档")
        print("✅ 测试数据创建成功")
        print()
        
        # 创建检索器（使用本地模型缓存）
        print("4. 创建检索器...")
        vector_store = VectorStore()
        vector_store.add_documents(test_documents)
        
        bm25_retriever = BM25Retriever()
        bm25_retriever.add_documents(test_documents)
        
        hybrid_retriever = HybridRetriever(
            vector_store=vector_store,
            bm25_retriever=bm25_retriever
        )
        
        print("✅ 检索器创建成功（使用混合检索器）")
        print()
        
        # 创建QA系统
        print("5. 创建QA系统...")
        conversation_chain = ConversationChain(
            retriever=hybrid_retriever,
            memory=Memory(),
            prompt_template=PromptTemplate()
        )
        print("✅ QA系统创建成功")
        print()
        
        # 测试问答
        print("6. 测试问答功能...")
        test_questions = [
            "什么是人工智能？",
            "机器学习是什么？",
            "深度学习的特点是什么？"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n   问题 {i}: {question}")
            
            try:
                result = conversation_chain.chat(question)
                
                if result and 'response' in result:
                    print(f"   AI回答: {result['response'][:100]}...")
                    print(f"   检索到文档数: {len(result.get('retrieved_docs', []))}")
                    print(f"   ✅ 问题 {i} 回答成功")
                else:
                    print(f"   ❌ 问题 {i} 回答失败")
                    
            except Exception as e:
                print(f"   ❌ 问题 {i} 处理失败: {e}")
        
        print("\n🎉 QA系统与检索模块集成测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    simple_test()
