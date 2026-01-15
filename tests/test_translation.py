#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译功能测试

测试文本翻译模块的各种功能：
- 语言检测
- 单句翻译
- 批量翻译
- 转录结果翻译
- 翻译缓存
"""

import os
import sys
import unittest
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.text.translator import TextTranslator, TranslationResult, translate_text, translate_for_embedding


class TestTranslation(unittest.TestCase):
    """翻译功能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.test_data_dir = Path(__file__).parent.parent / "data"
        cls.test_output_dir = cls.test_data_dir / "test_outputs"
        cls.test_cache_dir = cls.test_data_dir / "test_cache"
        
        # 创建测试目录
        cls.test_output_dir.mkdir(exist_ok=True)
        cls.test_cache_dir.mkdir(exist_ok=True)
        
        # 初始化翻译器
        cls.translator = TextTranslator(default_method="mock")  # 使用mock模式避免API依赖
        
        # 测试文本
        cls.test_texts = {
            "zh": [
                "深度学习是机器学习的一个分支",
                "神经网络是深度学习的基础",
                "人工智能正在改变世界"
            ],
            "en": [
                "Deep learning is a branch of machine learning",
                "Neural networks are the foundation of deep learning",
                "Artificial intelligence is changing the world"
            ],
            "mixed": [
                "深度学习 deep learning 很重要",
                "神经网络 neural network 是基础",
                "AI 人工智能 将改变未来"
            ]
        }
        
        # 测试转录结果
        cls.test_transcript = {
            "text": "深度学习是机器学习的一个重要分支。它使用多层神经网络来学习数据的表示。",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "深度学习是机器学习的一个重要分支。"
                },
                {
                    "id": 1,
                    "start": 5.0,
                    "end": 10.0,
                    "text": "它使用多层神经网络来学习数据的表示。"
                }
            ],
            "language": "zh"
        }
    
    def test_language_detection(self):
        """测试语言检测功能"""
        print("\n=== 测试语言检测 ===")
        
        # 测试中文检测
        zh_text = "深度学习是人工智能的重要分支"
        detected_lang = self.translator.detect_language(zh_text)
        self.assertEqual(detected_lang, "zh")
        print(f"中文文本检测: {detected_lang} ✅")
        
        # 测试英文检测
        en_text = "Deep learning is an important branch of AI"
        detected_lang = self.translator.detect_language(en_text)
        self.assertEqual(detected_lang, "en")
        print(f"英文文本检测: {detected_lang} ✅")
        
        # 测试混合文本检测
        mixed_text = "深度学习 deep learning 很重要"
        detected_lang = self.translator.detect_language(mixed_text)
        self.assertIn(detected_lang, ["zh", "en", "unknown"])
        print(f"混合文本检测: {detected_lang} ✅")
        
        # 测试空文本检测
        empty_text = ""
        detected_lang = self.translator.detect_language(empty_text)
        self.assertEqual(detected_lang, "unknown")
        print(f"空文本检测: {detected_lang} ✅")
        
        print("✅ 语言检测测试通过")
    
    def test_single_text_translation(self):
        """测试单句翻译功能"""
        print("\n=== 测试单句翻译 ===")
        
        # 测试中译英
        zh_text = "深度学习"
        result = self.translator.translate(zh_text, target_lang="en")
        
        self.assertIsInstance(result, TranslationResult)
        self.assertEqual(result.original_text, zh_text)
        self.assertEqual(result.source_lang, "zh")
        self.assertEqual(result.target_lang, "en")
        self.assertIsNotNone(result.translated_text)
        self.assertEqual(result.translation_method, "mock")
        
        print(f"中译英: '{zh_text}' -> '{result.translated_text}' ✅")
        
        # 测试英译中
        en_text = "neural network"
        result = self.translator.translate(en_text, target_lang="zh")
        
        self.assertEqual(result.original_text, en_text)
        self.assertEqual(result.source_lang, "en")
        self.assertEqual(result.target_lang, "zh")
        
        print(f"英译中: '{en_text}' -> '{result.translated_text}' ✅")
        
        # 测试相同语言（应该返回原文）
        zh_text = "深度学习"
        result = self.translator.translate(zh_text, target_lang="zh")
        
        self.assertEqual(result.translated_text, zh_text)
        self.assertEqual(result.translation_method, "same_language")
        
        print(f"相同语言: '{zh_text}' -> '{result.translated_text}' ✅")
        
        print("✅ 单句翻译测试通过")
    
    def test_batch_translation(self):
        """测试批量翻译功能"""
        print("\n=== 测试批量翻译 ===")
        
        # 测试中文文本批量翻译
        zh_texts = self.test_texts["zh"]
        results = self.translator.batch_translate(zh_texts, target_lang="en")
        
        self.assertEqual(len(results), len(zh_texts))
        
        for i, result in enumerate(results):
            self.assertIsInstance(result, TranslationResult)
            self.assertEqual(result.original_text, zh_texts[i])
            self.assertEqual(result.source_lang, "zh")
            self.assertEqual(result.target_lang, "en")
            print(f"  {i+1}. '{zh_texts[i]}' -> '{result.translated_text}'")
        
        print(f"批量翻译完成: {len(results)} 条 ✅")
        
        # 测试英文文本批量翻译
        en_texts = self.test_texts["en"]
        results = self.translator.batch_translate(en_texts, target_lang="zh")
        
        self.assertEqual(len(results), len(en_texts))
        
        for i, result in enumerate(results):
            self.assertEqual(result.original_text, en_texts[i])
            self.assertEqual(result.source_lang, "en")
            self.assertEqual(result.target_lang, "zh")
        
        print(f"英文批量翻译完成: {len(results)} 条 ✅")
        
        print("✅ 批量翻译测试通过")
    
    def test_transcript_translation(self):
        """测试转录结果翻译功能"""
        print("\n=== 测试转录结果翻译 ===")
        
        # 翻译转录结果
        translated_transcript = self.translator.translate_transcript(
            self.test_transcript, 
            target_lang="en"
        )
        
        # 验证整体文本翻译
        self.assertIn("text", translated_transcript)
        self.assertIn("translation_metadata", translated_transcript)
        self.assertNotEqual(
            translated_transcript["text"], 
            self.test_transcript["text"]
        )
        
        metadata = translated_transcript["translation_metadata"]
        self.assertEqual(metadata["source_lang"], "zh")
        self.assertEqual(metadata["target_lang"], "en")
        self.assertEqual(metadata["original_text"], self.test_transcript["text"])
        
        print(f"原文: {self.test_transcript['text']}")
        print(f"译文: {translated_transcript['text']}")
        print("✅ 整体文本翻译验证通过")
        
        # 验证段落翻译
        self.assertIn("segments", translated_transcript)
        self.assertEqual(
            len(translated_transcript["segments"]), 
            len(self.test_transcript["segments"])
        )
        
        for i, segment in enumerate(translated_transcript["segments"]):
            self.assertIn("translation_metadata", segment)
            self.assertIn("original_text", segment["translation_metadata"])
            self.assertEqual(
                segment["translation_metadata"]["source_lang"], 
                "zh"
            )
            self.assertEqual(
                segment["translation_metadata"]["target_lang"], 
                "en"
            )
            
            print(f"段落 {i+1}: {segment['text']}")
        
        print("✅ 段落翻译验证通过")
        print("✅ 转录结果翻译测试通过")
    
    def test_translation_caching(self):
        """测试翻译缓存功能"""
        print("\n=== 测试翻译缓存 ===")
        
        # 测试缓存文件路径
        cache_file = self.test_cache_dir / "test_translation_cache.json"
        
        # 第一次翻译
        text = "深度学习"
        result1 = self.translator.translate(text, target_lang="en")
        
        # 保存缓存
        self.translator.save_translation_cache(str(cache_file))
        self.assertTrue(cache_file.exists())
        print(f"缓存已保存: {cache_file}")
        
        # 清空内存中的缓存
        self.translator.translation_cache = {}
        
        # 加载缓存
        self.translator.load_translation_cache(str(cache_file))
        
        # 第二次翻译（应该使用缓存）
        result2 = self.translator.translate(text, target_lang="en")
        
        # 验证缓存结果
        self.assertEqual(result1.translated_text, result2.translated_text)
        self.assertIn("cached", result2.translation_method)
        
        print(f"缓存命中: {result2.translation_method} ✅")
        
        # 清理测试文件
        cache_file.unlink()
        
        print("✅ 翻译缓存测试通过")
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        print("\n=== 测试便捷函数 ===")
        
        # 测试translate_text函数
        zh_text = "机器学习"
        translated = translate_text(zh_text, target_lang="en")
        self.assertIsInstance(translated, str)
        self.assertNotEqual(translated, zh_text)
        print(f"translate_text: '{zh_text}' -> '{translated}' ✅")
        
        # 测试translate_for_embedding函数
        mixed_text = "深度学习很重要"
        embedding_ready = translate_for_embedding(mixed_text, embedding_lang="en")
        self.assertIsInstance(embedding_ready, str)
        print(f"translate_for_embedding: '{mixed_text}' -> '{embedding_ready}' ✅")
        
        print("✅ 便捷函数测试通过")
    
    def test_edge_cases(self):
        """测试边缘情况"""
        print("\n=== 测试边缘情况 ===")
        
        # 测试空文本
        empty_result = self.translator.translate("", target_lang="en")
        self.assertEqual(empty_result.translated_text, "")
        self.assertEqual(empty_result.translation_method, "empty")
        print("空文本处理 ✅")
        
        # 测试只有空格的文本
        space_result = self.translator.translate("   ", target_lang="en")
        self.assertEqual(space_result.translated_text, "")
        print("空格文本处理 ✅")
        
        # 测试非常长的文本
        long_text = "深度学习 " * 100
        long_result = self.translator.translate(long_text, target_lang="en")
        self.assertIsInstance(long_result.translated_text, str)
        self.assertGreater(len(long_result.translated_text), 0)
        print(f"长文本处理 ({len(long_text)} 字符) ✅")
        
        # 测试特殊字符
        special_text = "深度学习@#$%^&*()_+"
        special_result = self.translator.translate(special_text, target_lang="en")
        self.assertIsInstance(special_result.translated_text, str)
        print("特殊字符处理 ✅")
        
        print("✅ 边缘情况测试通过")


def run_translation_tests():
    """运行翻译功能测试"""
    print("=" * 60)
    print("翻译功能测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTranslation)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
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


if __name__ == "__main__":
    run_translation_tests()
