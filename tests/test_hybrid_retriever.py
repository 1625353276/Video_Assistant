#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合检索器模块测试脚本

测试HybridRetriever类的各项功能
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.retrieval.hybrid_retriever import HybridRetriever
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever


class TestHybridRetriever(unittest.TestCase):
    """混合检索器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试文档
        self.test_documents = [
            {
                "id": 0,
                "text": "智能手机通过GPS卫星信号确定位置",
                "start": 0.0,
                "end": 5.2,
                "confidence": 0.95
            },
            {
                "id": 1,
                "text": "GPS系统使用三角测量法计算设备坐标",
                "start": 5.2,
                "end": 10.4,
                "confidence": 0.92
            },
            {
                "id": 2,
                "text": "手机还可以通过WiFi和基站进行定位",
                "start": 10.4,
                "end": 15.6,
                "confidence": 0.88
            },
            {
                "id": 3,
                "text": "北斗导航系统是中国自主研发的全球定位系统",
                "start": 15.6,
                "end": 20.8,
                "confidence": 0.90
            },
            {
                "id": 4,
                "text": "Deep learning is a subset of machine learning",
                "start": 20.8,
                "end": 26.0,
                "confidence": 0.93
            }
        ]
        
        # 创建检索器实例
        self.vector_store = VectorStore()
        self.bm25_retriever = BM25Retriever()
        self.hybrid_retriever = HybridRetriever(
            vector_store=self.vector_store,
            bm25_retriever=self.bm25_retriever,
            vector_weight=0.6,
            bm25_weight=0.4,
            fusion_method="weighted_average"
        )
        
        # 添加测试文档
        self.hybrid_retriever.add_documents(self.test_documents)
    
    def test_initialization(self):
        """测试混合检索器初始化"""
        # 测试默认参数
        hybrid_default = HybridRetriever(
            self.vector_store, 
            self.bm25_retriever
        )
        self.assertEqual(hybrid_default.vector_weight, 0.5)
        self.assertEqual(hybrid_default.bm25_weight, 0.5)
        self.assertEqual(hybrid_default.fusion_method, "weighted_average")
        
        # 测试自定义参数
        hybrid_custom = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            vector_weight=0.7,
            bm25_weight=0.3,
            fusion_method="rrf"
        )
        self.assertEqual(hybrid_custom.vector_weight, 0.7)
        self.assertEqual(hybrid_custom.bm25_weight, 0.3)
        self.assertEqual(hybrid_custom.fusion_method, "rrf")
        
        # 测试权重归一化
        hybrid_normalize = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            vector_weight=2.0,
            bm25_weight=1.0
        )
        self.assertAlmostEqual(hybrid_normalize.vector_weight, 0.67, places=2)
        self.assertAlmostEqual(hybrid_normalize.bm25_weight, 0.33, places=2)
    
    def test_add_documents(self):
        """测试添加文档功能"""
        # 创建新的向量存储和BM25检索器实例
        new_vector_store = VectorStore()
        new_bm25_retriever = BM25Retriever()
        
        # 创建新的混合检索器
        new_hybrid = HybridRetriever(
            new_vector_store,
            new_bm25_retriever
        )
        
        # 添加文档
        new_hybrid.add_documents(self.test_documents)
        
        # 验证文档数量
        stats = new_hybrid.get_stats()
        self.assertEqual(stats["vector_store"]["document_count"], len(self.test_documents))
        self.assertEqual(stats["bm25_retriever"]["document_count"], len(self.test_documents))
    
    def test_weighted_average_fusion(self):
        """测试加权平均融合方法"""
        # 使用加权平均融合的检索器
        hybrid_weighted = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            vector_weight=0.6,
            bm25_weight=0.4,
            fusion_method="weighted_average"
        )
        hybrid_weighted.add_documents(self.test_documents)
        
        # 执行检索
        results = hybrid_weighted.search("智能手机定位", top_k=3)
        
        # 验证结果
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 3)
        
        # 验证结果结构
        for result in results:
            self.assertIn("score", result)
            self.assertIn("vector_score", result)
            self.assertIn("bm25_score", result)
            self.assertIn("text", result)
            
            # 验证分数计算
            expected_score = 0.6 * result["vector_score"] + 0.4 * result["bm25_score"]
            self.assertAlmostEqual(result["score"], expected_score, places=3)
    
    def test_rrf_fusion(self):
        """测试RRF融合方法"""
        # 使用RRF融合的检索器
        hybrid_rrf = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            fusion_method="rrf"
        )
        hybrid_rrf.add_documents(self.test_documents)
        
        # 执行检索
        results = hybrid_rrf.search("GPS系统", top_k=3)
        
        # 验证结果
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 3)
        
        # 验证结果结构
        for result in results:
            self.assertIn("score", result)
            self.assertIn("vector_rank", result)
            self.assertIn("bm25_rank", result)
            self.assertIn("text", result)
            
            # 验证排名是正整数
            self.assertGreaterEqual(result["vector_rank"], 1)
            self.assertGreaterEqual(result["bm25_rank"], 1)
    
    def test_condorcet_fusion(self):
        """测试Condorcet融合方法"""
        # 使用Condorcet融合的检索器
        hybrid_condorcet = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            fusion_method="condorcet"
        )
        hybrid_condorcet.add_documents(self.test_documents)
        
        # 执行检索
        results = hybrid_condorcet.search("北斗导航", top_k=3)
        
        # 验证结果
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 3)
        
        # 验证结果结构
        for result in results:
            self.assertIn("score", result)
            self.assertIn("condorcet_wins", result)
            self.assertIn("text", result)
            
            # 验证Condorcet获胜次数是非负整数
            self.assertGreaterEqual(result["condorcet_wins"], 0)
            self.assertIsInstance(result["condorcet_wins"], int)
    
    def test_different_fusion_methods(self):
        """测试不同融合方法的结果差异"""
        query = "手机定位"
        top_k = 3
        
        # 加权平均融合
        hybrid_weighted = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            fusion_method="weighted_average"
        )
        hybrid_weighted.add_documents(self.test_documents)
        weighted_results = hybrid_weighted.search(query, top_k=top_k)
        
        # RRF融合
        hybrid_rrf = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            fusion_method="rrf"
        )
        hybrid_rrf.add_documents(self.test_documents)
        rrf_results = hybrid_rrf.search(query, top_k=top_k)
        
        # Condorcet融合
        hybrid_condorcet = HybridRetriever(
            self.vector_store,
            self.bm25_retriever,
            fusion_method="condorcet"
        )
        hybrid_condorcet.add_documents(self.test_documents)
        condorcet_results = hybrid_condorcet.search(query, top_k=top_k)
        
        # 验证所有方法都返回结果
        self.assertGreater(len(weighted_results), 0)
        self.assertGreater(len(rrf_results), 0)
        self.assertGreater(len(condorcet_results), 0)
        
        # 验证结果数量一致
        self.assertEqual(len(weighted_results), len(rrf_results))
        self.assertEqual(len(rrf_results), len(condorcet_results))
        
        # 验证结果文档可能不同（不同融合方法可能有不同排序）
        weighted_texts = [r["text"] for r in weighted_results]
        rrf_texts = [r["text"] for r in rrf_results]
        condorcet_texts = [r["text"] for r in condorcet_results]
        
        # 至少应该有一些重叠
        self.assertTrue(set(weighted_texts) & set(rrf_texts))
        self.assertTrue(set(rrf_texts) & set(condorcet_texts))
    
    def test_threshold_filtering(self):
        """测试阈值过滤功能"""
        # 使用低阈值确保有结果
        results_low = self.hybrid_retriever.search("智能手机", top_k=5, threshold=0.0)
        self.assertGreater(len(results_low), 0)
        
        # 使用高阈值可能减少结果
        results_high = self.hybrid_retriever.search("智能手机", top_k=5, threshold=0.8)
        self.assertLessEqual(len(results_high), len(results_low))
        
        # 验证所有结果都满足阈值要求
        for result in results_high:
            self.assertGreaterEqual(result["score"], 0.8)
    
    def test_custom_top_k_parameters(self):
        """测试自定义top_k参数"""
        # 测试不同的top_k设置
        results_3 = self.hybrid_retriever.search("定位", top_k=3)
        results_5 = self.hybrid_retriever.search("定位", top_k=5)
        
        # 验证结果数量
        self.assertLessEqual(len(results_3), 3)
        self.assertLessEqual(len(results_5), 5)
        self.assertGreaterEqual(len(results_5), len(results_3))
        
        # 验证前3个结果相同（如果有的话）
        if len(results_3) > 0 and len(results_5) >= 3:
            for i in range(3):
                self.assertEqual(results_3[i]["text"], results_5[i]["text"])
    
    def test_multilingual_queries(self):
        """测试多语言查询"""
        # 中文查询
        chinese_results = self.hybrid_retriever.search("智能手机定位", top_k=3)
        self.assertGreater(len(chinese_results), 0)
        
        # 英文查询
        english_results = self.hybrid_retriever.search("deep learning", top_k=3)
        self.assertGreater(len(english_results), 0)
        
        # 验证结果包含相应语言的内容
        chinese_texts = " ".join([r["text"] for r in chinese_results])
        english_texts = " ".join([r["text"] for r in english_results])
        
        # 中文结果应该包含中文内容
        self.assertTrue(any(char in chinese_texts for char in "智能手机定位"))
        
        # 英文结果应该包含英文内容
        self.assertIn("deep learning", english_texts.lower())
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效的融合方法
        with self.assertRaises(RuntimeError):
            hybrid_invalid = HybridRetriever(
                self.vector_store,
                self.bm25_retriever,
                fusion_method="invalid_method"
            )
            hybrid_invalid.search("test")
        
        # 测试空文档列表
        empty_vector_store = VectorStore()
        empty_bm25_retriever = BM25Retriever()
        hybrid_empty = HybridRetriever(
            empty_vector_store,
            empty_bm25_retriever
        )
        hybrid_empty.add_documents([])
        
        # 空检索应该返回空结果
        results = hybrid_empty.search("test")
        self.assertEqual(len(results), 0)
    
    def test_get_stats(self):
        """测试统计信息获取"""
        stats = self.hybrid_retriever.get_stats()
        
        # 验证统计信息结构
        self.assertIn("fusion_method", stats)
        self.assertIn("vector_weight", stats)
        self.assertIn("bm25_weight", stats)
        self.assertIn("vector_store", stats)
        self.assertIn("bm25_retriever", stats)
        
        # 验证统计信息内容
        self.assertEqual(stats["fusion_method"], "weighted_average")
        self.assertEqual(stats["vector_weight"], 0.6)
        self.assertEqual(stats["bm25_weight"], 0.4)
        self.assertEqual(stats["vector_store"]["document_count"], len(self.test_documents))
        self.assertEqual(stats["bm25_retriever"]["document_count"], len(self.test_documents))
    
    def test_clear_functionality(self):
        """测试清空功能"""
        # 验证有文档
        stats_before = self.hybrid_retriever.get_stats()
        self.assertGreater(stats_before["vector_store"]["document_count"], 0)
        self.assertGreater(stats_before["bm25_retriever"]["document_count"], 0)
        
        # 清空检索器
        self.hybrid_retriever.clear()
        
        # 验证已清空
        stats_after = self.hybrid_retriever.get_stats()
        self.assertEqual(stats_after["vector_store"]["document_count"], 0)
        self.assertEqual(stats_after["bm25_retriever"]["document_count"], 0)
        
        # 清空后检索应该返回空结果
        results = self.hybrid_retriever.search("test")
        self.assertEqual(len(results), 0)
    
    def test_index_persistence(self):
        """测试索引持久化功能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_index_path = Path(temp_dir) / "test_vector_index.pkl"
            bm25_index_path = Path(temp_dir) / "test_bm25_index.pkl"
            
            # 保存索引
            self.hybrid_retriever.save_indexes(
                str(vector_index_path),
                str(bm25_index_path)
            )
            
            # 验证文件存在
            self.assertTrue(vector_index_path.exists())
            self.assertTrue(bm25_index_path.exists())
            
            # 创建新的混合检索器并加载索引
            new_vector_store = VectorStore()
            new_bm25_retriever = BM25Retriever()
            new_hybrid = HybridRetriever(
                new_vector_store,
                new_bm25_retriever
            )
            
            new_hybrid.load_indexes(
                str(vector_index_path),
                str(bm25_index_path)
            )
            
            # 验证加载后的统计信息
            stats = new_hybrid.get_stats()
            self.assertEqual(stats["vector_store"]["document_count"], len(self.test_documents))
            self.assertEqual(stats["bm25_retriever"]["document_count"], len(self.test_documents))
            
            # 验证加载后的检索功能
            results = new_hybrid.search("智能手机", top_k=3)
            self.assertGreater(len(results), 0)


def run_hybrid_retriever_tests():
    """运行混合检索器测试"""
    print("=" * 60)
    print("开始混合检索器测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHybridRetriever)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
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
    success = run_hybrid_retriever_tests()
    sys.exit(0 if success else 1)