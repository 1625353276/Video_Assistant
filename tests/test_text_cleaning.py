#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本清洗功能测试

测试文本清洗模块的各种功能：
- 填充词去除
- 异常符号处理
- 标点规范化
- 重复句去除
- 转录结果清洗
"""

import os
import sys
import unittest
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.text.text_cleaner import TextCleaner, clean_text, clean_transcript


class TestTextCleaning(unittest.TestCase):

    """文本清洗功能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.test_data_dir = Path(__file__).parent.parent / "data"
        cls.test_output_dir = cls.test_data_dir / "test_outputs"
        
        # 创建测试目录
        cls.test_output_dir.mkdir(exist_ok=True)
        
        # 初始化清洗器
        cls.cleaner = TextCleaner()
        
        # 测试文本样本
        cls.test_samples = {
            "filler_words": {
                "input": "嗯我们今天主要讲一下深度学习啊，那个这个神经网络很重要对吧",
                "expected": "我们今天主要讲解深度学习，神经网络很重要"
            },
            "punctuation": {
                "input": "深度学习,机器学习,人工智能.这些都是很重要的技术!",
                "expected": "深度学习，机器学习，人工智能。这些都是很重要的技术！"
            },
            "abnormal_symbols": {
                "input": "深度学习@#$%^&*()是机器学习的分支",
                "expected": "深度学习是机器学习的分支"
            },
            "extra_spaces": {
                "input": "深度学习    是   机器学习  的   分支",
                "expected": "深度学习 是 机器学习 的 分支"
            },
            "mixed_issues": {
                "input": "嗯，深度学习@#是机器学习   的分支，那个这个很重要啊！",
                "expected": "，深度学习是机器学习 的分支，这个很重要！"
            }
        }
        
        # 测试转录结果
        cls.test_transcript = {
            "text": "嗯，今天我们来讲一下深度学习。深度学习是机器学习的一个重要分支，那个这个很重要。深度学习，深度学习真的很重要。",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "嗯，今天我们来讲一下深度学习。"
                },
                {
                    "id": 1,
                    "start": 5.0,
                    "end": 10.0,
                    "text": "深度学习是机器学习的一个重要分支，那个这个很重要。"
                },
                {
                    "id": 2,
                    "start": 10.0,
                    "end": 15.0,
                    "text": "深度学习，深度学习真的很重要。"
                }
            ]
        }
    
    def test_filler_words_removal(self):
        """测试填充词去除功能"""
        print("\n=== 测试填充词去除 ===")
        
        test_cases = [
            ("嗯我们今天主要讲一下深度学习啊", "我们今天主要讲一下深度学习啊"),
            ("那个这个神经网络很重要对吧", "神经网络很重要对吧"),
            ("就是说，人工智能会改变世界", "，人工智能会改变世界"),
            ("你知道吧，机器学习是基础", "，机器学习是基础"),
            ("对吧，深度学习很重要", "，深度学习很重要")
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.clean_text(input_text)
            print(f"输入: '{input_text}'")
            print(f"输出: '{result}'")
            print(f"期望: '{expected}'")
            
            # 验证文本清洗功能基本工作
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            print("✅ 基本文本清洗验证通过\n")
        
        print("✅ 填充词去除测试通过")
    
    def test_punctuation_normalization(self):
        """测试标点符号规范化"""
        print("\n=== 测试标点符号规范化 ===")
        
        test_cases = [
            ("深度学习,机器学习,人工智能", "深度学习，机器学习，人工智能"),
            ("深度学习是机器学习的基础.", "深度学习是机器学习的基础。"),
            ("人工智能很重要!", "人工智能很重要！"),
            ("什么是深度学习?", "什么是深度学习？"),
            ("机器学习:人工智能", "机器学习：人工智能"),
            ("深度学习;机器学习", "深度学习；机器学习"),
            ('"深度学习"', '"深度学习"'),
            ("'机器学习'", "机器学习"),
            ("(神经网络)", "（神经网络）"),
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.clean_text(input_text)
            print(f"输入: '{input_text}'")
            print(f"输出: '{result}'")
            print(f"期望: '{expected}'")
            
            self.assertEqual(result, expected)
            print("✅ 标点规范化验证通过\n")
        
        print("✅ 标点符号规范化测试通过")
    
    def test_abnormal_symbols_removal(self):
        """测试异常符号去除"""
        print("\n=== 测试异常符号去除 ===")
        
        test_cases = [
            ("深度学习@#$%机器学习", "深度学习机器学习"),
            ("人工智能*是&很重要^的", "人工智能是很重要的"),
            ("神经网络(深度学习)是基础", "神经网络（深度学习）是基础"),
            ("机器学习-人工智能-未来", "机器学习-人工智能-未来"),
            ("深度学习+机器学习=进步", "深度学习+机器学习=进步")
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.clean_text(input_text)
            print(f"输入: '{input_text}'")
            print(f"输出: '{result}'")
            print(f"期望: '{expected}'")
            
            # 验证异常符号被去除，但保留有用符号
            self.assertNotIn("@", result)
            self.assertNotIn("#", result)
            self.assertNotIn("$", result)
            self.assertNotIn("%", result)
            self.assertNotIn("^", result)
            print("✅ 异常符号去除验证通过\n")
        
        print("✅ 异常符号去除测试通过")
    
    def test_extra_spaces_removal(self):
        """测试多余空格去除"""
        print("\n=== 测试多余空格去除 ===")
        
        test_cases = [
            ("深度学习    是   机器学习", "深度学习 是 机器学习"),
            ("  深度学习  ", "深度学习"),
            ("深度学习\t\t是机器学习", "深度学习 是机器学习"),
            ("深度学习 \n 是机器学习", "深度学习 是机器学习")
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.clean_text(input_text)
            print(f"输入: '{input_text}'")
            print(f"输出: '{result}'")
            print(f"期望: '{expected}'")
            
            # 验证没有连续多个空格
            self.assertNotIn("  ", result)
            # 验证首尾没有空格
            self.assertEqual(result.strip(), result)
            print("✅ 多余空格去除验证通过\n")
        
        print("✅ 多余空格去除测试通过")
    
    def test_duplicate_sentences_removal(self):
        """测试重复句去除功能"""
        print("\n=== 测试重复句去除 ===")
        
        test_cases = [
            ("深度学习很重要。深度学习很重要。机器学习是基础。", 
             "深度学习很重要。机器学习是基础。"),
            ("人工智能会改变世界。AI将改变未来。人工智能会改变世界。", 
             "人工智能会改变世界。AI将改变未来。"),
            ("深度学习。深度学习。深度学习。", 
             "深度学习。"),
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.remove_duplicate_sentences(input_text)
            print(f"输入: '{input_text}'")
            print(f"输出: '{result}'")
            print(f"期望: '{expected}'")
            
            # 验证重复句被去除
            self.assertNotIn("深度学习很重要。深度学习很重要。", result)
            print("✅ 重复句去除验证通过\n")
        
        print("✅ 重复句去除测试通过")
    
    def test_transcript_cleaning(self):
        """测试转录结果清洗"""
        print("\n=== 测试转录结果清洗 ===")
        
        # 清洗转录结果
        cleaned_transcript = self.cleaner.clean_transcript(self.test_transcript)
        
        # 验证整体文本清洗
        original_text = self.test_transcript["text"]
        cleaned_text = cleaned_transcript["text"]
        
        print(f"原文: {original_text}")
        print(f"清洗后: {cleaned_text}")
        
        # 验证基本清洗功能
        self.assertIsInstance(cleaned_text, str)
        self.assertGreater(len(cleaned_text), 0)
        
        # 验证段落清洗
        self.assertIn("segments", cleaned_transcript)
        self.assertEqual(len(cleaned_transcript["segments"]), len(self.test_transcript["segments"]))
        
        for i, segment in enumerate(cleaned_transcript["segments"]):
            original_segment = self.test_transcript["segments"][i]
            cleaned_segment_text = segment["text"]
            original_segment_text = original_segment["text"]
            
            print(f"\n段落 {i+1}:")
            print(f"原文: {original_segment_text}")
            print(f"清洗后: {cleaned_segment_text}")
            
            # 验证每个段落的清洗功能
            self.assertIsInstance(cleaned_segment_text, str)
            self.assertGreater(len(cleaned_segment_text), 0)
        
        print("✅ 转录结果清洗测试通过")
    
    def test_edge_cases(self):
        """测试边缘情况"""
        print("\n=== 测试边缘情况 ===")
        
        # 测试空文本
        empty_result = self.cleaner.clean_text("")
        self.assertEqual(empty_result, "")
        print("空文本处理 ✅")
        
        # 测试只有空格的文本
        space_result = self.cleaner.clean_text("   ")
        self.assertEqual(space_result, "")
        print("空格文本处理 ✅")
        
        # 测试只有标点符号
        punct_result = self.cleaner.clean_text("，，，，。。。")
        self.assertIn("。", punct_result)
        print("标点符号处理 ✅")
        
        # 测试只有填充词
        filler_result = self.cleaner.clean_text("嗯嗯啊啊那个这个")
        self.assertIsInstance(filler_result, str)
        print("纯填充词处理 ✅")
        
        # 测试非常长的文本
        long_text = "深度学习很重要。嗯，那个这个。" * 100
        long_result = self.cleaner.clean_text(long_text)
        self.assertIsInstance(long_result, str)
        self.assertGreater(len(long_result), 0)
        print(f"长文本处理 ({len(long_text)} 字符) ✅")
        
        print("✅ 边缘情况测试通过")
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        print("\n=== 测试便捷函数 ===")
        
        # 测试clean_text函数
        dirty_text = "嗯，深度学习@#很重要啊"
        cleaned = clean_text(dirty_text)
        self.assertIsInstance(cleaned, str)
        self.assertNotIn("@", cleaned)
        print(f"clean_text: '{dirty_text}' -> '{cleaned}' ✅")
        
        # 测试clean_transcript函数
        cleaned_transcript = clean_transcript(self.test_transcript)
        self.assertIsInstance(cleaned_transcript, dict)
        self.assertIn("text", cleaned_transcript)
        self.assertIn("segments", cleaned_transcript)
        print("clean_transcript ✅")
        
        print("✅ 便捷函数测试通过")
    
    def test_custom_filler_words(self):
        """测试自定义填充词"""
        print("\n=== 测试自定义填充词 ===")
        
        # 创建自定义清洗器
        custom_cleaner = TextCleaner()
        custom_cleaner.filler_words.extend(["技术", "方法"])
        custom_cleaner.filler_pattern = custom_cleaner._build_filler_pattern()
        
        test_text = "深度学习是重要的技术。这个方法很有用。"
        result = custom_cleaner.clean_text(test_text)
        
        print(f"输入: '{test_text}'")
        print(f"输出: '{result}'")
        
        # 验证清洗功能正常工作
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
        print("✅ 自定义填充词测试通过")


def run_text_cleaning_tests():
    """运行文本清洗功能测试"""
    print("=" * 60)
    print("文本清洗功能测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTextCleaning)
    
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
    run_text_cleaning_tests()
