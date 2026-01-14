#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多查询生成器单元测试

测试多查询生成器的所有核心功能
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.retrieval.multi_query import (
    MultiQueryGenerator,
    ModelBasedExpander,
    QueryWeightManager,
    GeneratedQuery,
    MultiQueryResult
)


class TestGeneratedQuery(unittest.TestCase):
    """测试GeneratedQuery数据结构"""
    
    def test_generated_query_creation(self):
        """测试GeneratedQuery创建"""
        query = GeneratedQuery(
            query="测试查询",
            method="test",
            weight=0.8,
            metadata={"test": True}
        )
        
        self.assertEqual(query.query, "测试查询")
        self.assertEqual(query.method, "test")
        self.assertEqual(query.weight, 0.8)
        self.assertEqual(query.metadata["test"], True)


class TestMultiQueryResult(unittest.TestCase):
    """测试MultiQueryResult数据结构"""
    
    def test_multi_query_result_creation(self):
        """测试MultiQueryResult创建"""
        queries = [
            GeneratedQuery("查询1", "method1", 0.5),
            GeneratedQuery("查询2", "method2", 0.3)
        ]
        
        result = MultiQueryResult(
            original_query="原始查询",
            generated_queries=queries,
            generation_time="2024-01-13 10:00:00",
            total_queries=2,
            generation_methods=["method1", "method2"]
        )
        
        self.assertEqual(result.original_query, "原始查询")
        self.assertEqual(len(result.generated_queries), 2)
        self.assertEqual(result.total_queries, 2)
        self.assertEqual(result.generation_methods, ["method1", "method2"])


class TestModelBasedExpander(unittest.TestCase):
    """测试基于模型的查询扩展器"""
    
    def setUp(self):
        """测试前准备"""
        # 创建扩展器实例，但不实际加载模型
        self.expander = ModelBasedExpander()
        self.expander.model = None  # 确保模型为None
    
    def test_method_name(self):
        """测试方法名称"""
        self.assertEqual(self.expander.get_method_name(), "model_based")
    
    def test_expand_without_model(self):
        """测试没有模型时的扩展"""
        expander = ModelBasedExpander()
        expander.model = None
        
        results = expander.expand("测试查询")
        self.assertEqual(len(results), 0)
    
    def test_keyword_expansion(self):
        """测试关键词扩展"""
        # 创建一个有模型的扩展器（mock）
        expander = ModelBasedExpander()
        expander.model = MagicMock()  # 避免实际模型加载
        
        query = "智能手机定位技术原理"
        results = expander._expand_by_keywords(query)
        
        # 应该生成部分查询
        self.assertGreater(len(results), 0)
        
        # 检查查询权重
        for result in results:
            self.assertEqual(result.method, "keyword")
            self.assertEqual(result.weight, 0.6)
            self.assertTrue(len(result.query) > 3)
    
    def test_candidate_query_generation_chinese(self):
        """测试中文候选查询生成"""
        expander = ModelBasedExpander()
        expander.model = MagicMock()  # 避免实际模型加载
        
        query = "人工智能"
        candidates = expander._generate_candidate_queries(query)
        
        # 应该生成多个候选查询
        self.assertGreater(len(candidates), 0)
        
        # 检查是否包含中文模板
        candidate_text = " ".join(candidates)
        self.assertIn("人工智能的工作原理", candidate_text)
        self.assertIn("人工智能是什么", candidate_text)
    
    def test_candidate_query_generation_english(self):
        """测试英文候选查询生成"""
        expander = ModelBasedExpander()
        expander.model = MagicMock()  # 避免实际模型加载
        
        query = "artificial intelligence"
        candidates = expander._generate_candidate_queries(query)
        
        # 应该生成多个候选查询
        self.assertGreater(len(candidates), 0)
        
        # 检查是否包含英文模板
        candidate_text = " ".join(candidates)
        self.assertIn("what is artificial intelligence", candidate_text)
        self.assertIn("how does artificial intelligence work", candidate_text)


class TestQueryWeightManager(unittest.TestCase):
    """测试查询权重管理器"""
    
    def test_default_initialization(self):
        """测试默认初始化"""
        manager = QueryWeightManager()
        
        # 检查默认权重（只保留模型扩展相关的权重）
        self.assertEqual(manager.method_weights["semantic"], 0.8)
        self.assertEqual(manager.method_weights["keyword"], 0.6)
        self.assertEqual(manager.method_weights["original"], 1.0)
    
    def test_custom_initialization(self):
        """测试自定义初始化"""
        custom_weights = {
            "semantic": 0.5,
            "keyword": 0.6,
            "original": 0.7
        }
        
        manager = QueryWeightManager(custom_weights)
        
        self.assertEqual(manager.method_weights["semantic"], 0.5)
        self.assertEqual(manager.method_weights["keyword"], 0.6)
        self.assertEqual(manager.method_weights["original"], 0.7)
    
    def test_weight_normalization(self):
        """测试权重归一化"""
        manager = QueryWeightManager()
        
        queries = [
            GeneratedQuery("查询1", "method1", 2.0),
            GeneratedQuery("查询2", "method2", 3.0),
            GeneratedQuery("查询3", "method3", 5.0)
        ]
        
        normalized = manager.normalize_weights(queries)
        
        # 检查权重总和为1
        total_weight = sum(q.weight for q in normalized)
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # 检查相对比例保持不变
        self.assertAlmostEqual(normalized[0].weight, 0.2, places=5)
        self.assertAlmostEqual(normalized[1].weight, 0.3, places=5)
        self.assertAlmostEqual(normalized[2].weight, 0.5, places=5)
    
    def test_weight_adjustment(self):
        """测试权重调整"""
        custom_weights = {"method1": 0.5, "method2": 0.8}
        manager = QueryWeightManager(custom_weights)
        
        queries = [
            GeneratedQuery("查询1", "method1", 0.8),
            GeneratedQuery("查询2", "method2", 0.7),
            GeneratedQuery("查询3", "method3", 0.9)
        ]
        
        adjusted = manager.adjust_weights(queries)
        
        # 检查权重应用
        self.assertEqual(adjusted[0].weight, 0.8 * 0.5)  # 0.4
        self.assertEqual(adjusted[1].weight, 0.7 * 0.8)  # 0.56
        self.assertEqual(adjusted[2].weight, 0.9 * 0.5)  # 默认权重0.5
    
    def test_empty_queries(self):
        """测试空查询列表"""
        manager = QueryWeightManager()
        
        # 归一化空列表
        normalized = manager.normalize_weights([])
        self.assertEqual(len(normalized), 0)
        
        # 调整空列表
        adjusted = manager.adjust_weights([])
        self.assertEqual(len(adjusted), 0)


class TestMultiQueryGenerator(unittest.TestCase):
    """测试多查询生成器主类"""
    
    def setUp(self):
        """测试前准备"""
        # 使用模拟的模型扩展器来避免实际加载模型
        with patch('modules.retrieval.multi_query.ModelBasedExpander') as mock_expander:
            # 创建模拟扩展器
            mock_instance = MagicMock()
            mock_instance.expand.return_value = []
            mock_instance.get_method_name.return_value = "model_based"
            mock_expander.return_value = mock_instance
            
            self.generator = MultiQueryGenerator(
                max_queries=5
            )
            
            # 保存模拟引用以便后续测试使用
            self.mock_expander_instance = mock_instance
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.generator.max_queries, 5)
        self.assertEqual(len(self.generator.expanders), 1)  # 只有模型扩展器
    
    def test_generate_queries_basic(self):
        """测试基本查询生成"""
        query = "智能手机定位"
        result = self.generator.generate_queries(query)
        
        # 显示扩展后的内容
        print(f"\n原始查询: '{query}'")
        print(f"生成查询数量: {len(result.generated_queries)}")
        print(f"使用的方法: {result.generation_methods}")
        print("\n生成的查询详情:")
        print(f"{'序号':<4} {'查询内容':<25} {'权重':<8} {'方法':<12}")
        print("-" * 55)
        
        for i, q in enumerate(result.generated_queries):
            display_query = q.query[:23] + "..." if len(q.query) > 23 else q.query
            print(f"{i+1:<4} {display_query:<25} {q.weight:<8.3f} {q.method:<12}")
        
        # 检查结果结构
        self.assertIsInstance(result, MultiQueryResult)
        self.assertEqual(result.original_query, query)
        self.assertGreater(len(result.generated_queries), 0)
        self.assertLessEqual(len(result.generated_queries), 5)
        
        # 检查包含原始查询
        query_texts = [q.query for q in result.generated_queries]
        self.assertIn(query, query_texts)
        
        # 检查权重归一化
        total_weight = sum(q.weight for q in result.generated_queries)
        self.assertAlmostEqual(total_weight, 1.0, places=5)
    
    def test_generate_queries_with_model_disabled(self):
        """测试模型扩展失败时的查询生成"""
        # 模拟模型扩展失败
        self.mock_expander_instance.expand.return_value = []
        
        result = self.generator.generate_queries("GPS定位技术")
        
        # 应该只有原始查询
        self.assertEqual(len(result.generated_queries), 1)
        self.assertEqual(result.generated_queries[0].method, "original")
    
    def test_max_queries_limit(self):
        """测试最大查询数量限制"""
        generator = MultiQueryGenerator(max_queries=3)
        
        # 使用mock生成大量查询
        with patch.object(generator.expanders[0], 'expand') as mock_expand:
            mock_expand.return_value = [
                GeneratedQuery(f"查询{i}", "test", 0.5) 
                for i in range(10)
            ]
            
            result = generator.generate_queries("测试查询")
            
            # 应该限制在最大数量
            self.assertLessEqual(len(result.generated_queries), 3)
    
    def test_config_save_and_load(self):
        """测试配置保存和加载"""
        config_path = "test_generator_config.json"
        
        try:
            # 保存配置
            self.generator.save_config(config_path)
            self.assertTrue(os.path.exists(config_path))
            
            # 加载配置
            new_generator = MultiQueryGenerator()
            new_generator.load_config(config_path)
            
            # 检查配置是否正确加载
            self.assertEqual(new_generator.max_queries, self.generator.max_queries)
            
        finally:
            # 清理临时文件
            if os.path.exists(config_path):
                os.remove(config_path)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        stats = self.generator.get_stats()
        
        self.assertIn("enabled_expanders", stats)
        self.assertIn("max_queries", stats)
        self.assertIn("model_based_enabled", stats)
        self.assertIn("method_weights", stats)
        
        self.assertEqual(stats["enabled_expanders"], 1)
        self.assertEqual(stats["max_queries"], 5)
        self.assertTrue(stats["model_based_enabled"])
    
    def test_error_handling(self):
        """测试错误处理"""
        # 创建一个会抛出异常的扩展器
        faulty_expander = MagicMock()
        faulty_expander.expand.side_effect = Exception("测试异常")
        faulty_expander.get_method_name.return_value = "faulty"
        
        self.generator.expanders.append(faulty_expander)
        
        # 应该能够处理异常而不崩溃
        result = self.generator.generate_queries("测试查询")
        
        # 仍然应该有结果（来自正常的扩展器）
        self.assertGreater(len(result.generated_queries), 0)
        
        # 错误的扩展器不应该出现在方法列表中
        self.assertNotIn("faulty", result.generation_methods)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_end_to_end_chinese_query(self):
        """端到端中文查询测试"""
        # 使用模拟的模型扩展器
        with patch('modules.retrieval.multi_query.ModelBasedExpander') as mock_expander:
            # 创建模拟扩展器，返回一些测试查询
            mock_instance = MagicMock()
            mock_instance.expand.return_value = [
                GeneratedQuery("智能手机定位原理", "semantic", 0.8),
                GeneratedQuery("手机定位", "keyword", 0.6),
                GeneratedQuery("定位技术", "keyword", 0.6)
            ]
            mock_instance.get_method_name.return_value = "model_based"
            mock_expander.return_value = mock_instance
            
            generator = MultiQueryGenerator(max_queries=8)
        
        query = "智能手机定位原理"
        result = generator.generate_queries(query)
        
        # 显示扩展后的内容
        print(f"\n=== 中文查询扩展演示 ===")
        print(f"原始查询: '{query}'")
        print(f"生成查询数量: {len(result.generated_queries)}")
        print(f"使用方法: {', '.join(result.generation_methods)}")
        print("\n生成的查询:")
        print(f"{'序号':<4} {'查询内容':<20} {'权重':<8} {'方法':<12}")
        print("-" * 50)
        
        for i, q in enumerate(result.generated_queries):
            display_query = q.query[:18] + "..." if len(q.query) > 18 else q.query
            print(f"{i+1:<4} {display_query:<20} {q.weight:<8.3f} {q.method:<12}")
        
        # 显示权重分布
        method_weights = {}
        for q in result.generated_queries:
            method_weights[q.method] = method_weights.get(q.method, 0) + q.weight
        
        print(f"\n权重分布:")
        for method, weight in method_weights.items():
            print(f"  {method}: {weight:.3f} ({weight*100:.1f}%)")
        
        # 验证结果
        self.assertIsInstance(result, MultiQueryResult)
        self.assertEqual(result.original_query, query)
        self.assertGreater(len(result.generated_queries), 1)
        self.assertLessEqual(len(result.generated_queries), 8)
        
        # 验证包含不同类型的查询
        methods = set(q.method for q in result.generated_queries)
        self.assertIn("original", methods)
        
        # 验证权重归一化
        total_weight = sum(q.weight for q in result.generated_queries)
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # 验证包含原始查询
        query_texts = [q.query for q in result.generated_queries]
        self.assertTrue(any("手机" in text for text in query_texts))
        self.assertTrue(any("定位" in text for text in query_texts))
        
        print("✅ 中文查询扩展测试通过")
    
    def test_end_to_end_english_query(self):
        """端到端英文查询测试"""
        # 使用模拟的模型扩展器
        with patch('modules.retrieval.multi_query.ModelBasedExpander') as mock_expander:
            # 创建模拟扩展器，返回一些测试查询
            mock_instance = MagicMock()
            mock_instance.expand.return_value = [
                GeneratedQuery("smartphone GPS technology", "semantic", 0.8),
                GeneratedQuery("phone GPS", "keyword", 0.6),
                GeneratedQuery("GPS navigation", "keyword", 0.6)
            ]
            mock_instance.get_method_name.return_value = "model_based"
            mock_expander.return_value = mock_instance
            
            generator = MultiQueryGenerator(max_queries=8)
        
        query = "smartphone GPS technology"
        result = generator.generate_queries(query)
        
        # 显示扩展后的内容
        print(f"\n=== 英文查询扩展演示 ===")
        print(f"原始查询: '{query}'")
        print(f"生成查询数量: {len(result.generated_queries)}")
        print(f"使用方法: {', '.join(result.generation_methods)}")
        print("\n生成的查询:")
        print(f"{'序号':<4} {'查询内容':<25} {'权重':<8} {'方法':<12}")
        print("-" * 55)
        
        for i, q in enumerate(result.generated_queries):
            display_query = q.query[:23] + "..." if len(q.query) > 23 else q.query
            print(f"{i+1:<4} {display_query:<25} {q.weight:<8.3f} {q.method:<12}")
        
        # 显示权重分布
        method_weights = {}
        for q in result.generated_queries:
            method_weights[q.method] = method_weights.get(q.method, 0) + q.weight
        
        print(f"\n权重分布:")
        for method, weight in method_weights.items():
            print(f"  {method}: {weight:.3f} ({weight*100:.1f}%)")
        
        # 验证结果
        self.assertIsInstance(result, MultiQueryResult)
        self.assertEqual(result.original_query, query)
        self.assertGreater(len(result.generated_queries), 1)
        
        # 验证包含不同类型的查询
        methods = set(q.method for q in result.generated_queries)
        self.assertIn("original", methods)
        
        # 验证权重归一化
        total_weight = sum(q.weight for q in result.generated_queries)
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # 验证查询质量
        query_texts = [q.query for q in result.generated_queries]
        self.assertTrue(any("phone" in text or "GPS" in text for text in query_texts))
        
        print("✅ 英文查询扩展测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("多查询生成器单元测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestGeneratedQuery,
        TestMultiQueryResult,
        TestModelBasedExpander,
        TestQueryWeightManager,
        TestMultiQueryGenerator,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
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
    
    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)