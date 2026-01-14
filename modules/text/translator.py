#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译模块 - translator.py
"""

import os
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import time
import json
import asyncio
import threading
import logging
import sys

logging.getLogger("httpx").setLevel(logging.WARNING)

# 尝试导入翻译库
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("警告: requests 未安装，部分功能可能不可用")

try:
    from googletrans import Translator

    HAS_GOOGLETRANS = True
    # 检查 googletrans 版本
    import googletrans

    GOOGLETRANS_VERSION = getattr(googletrans, '__version__', 'unknown')
except ImportError:
    HAS_GOOGLETRANS = False
    GOOGLETRANS_VERSION = None
    print("警告: googletrans 未安装，将使用模拟翻译")

try:
    from deep_translator import GoogleTranslator

    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False
    print("提示: 安装 deep-translator 可获得更稳定的翻译: pip install deep-translator")


@dataclass
class TranslationResult:
    """翻译结果数据结构"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: Optional[float] = None
    translation_method: str = "unknown"
    metadata: Optional[Dict[str, Any]] = None


class TextTranslator:
    """文本翻译器，支持多种翻译策略"""

    def __init__(self, default_method: str = "deep-translator", progress_callback=None):
        """
        初始化翻译器

        Args:
            default_method: 翻译方法 ("auto", "googletrans", "deep-translator", "mock")
            progress_callback: 进度回调函数，接收(current, total, message)参数
        """
        self.default_method = self._determine_best_method(default_method)
        self.translator = None
        self.translation_cache = {}
        self.progress_callback = progress_callback
        self._init_translator()

    def _determine_best_method(self, preferred_method: str) -> str:
        """确定最佳的翻译方法"""
        if preferred_method != "auto":
            return preferred_method

        # 自动选择最佳方法
        if HAS_DEEP_TRANSLATOR:
            return "deep-translator"
        elif HAS_GOOGLETRANS:
            return "googletrans"
        else:
            return "mock"

    def _init_translator(self):
        """初始化翻译器实例"""
        if self.default_method == "googletrans" and HAS_GOOGLETRANS:
            try:
                # 新版 googletrans 的初始化
                self.translator = Translator()
                print(f"✓ 使用 googletrans (版本: {GOOGLETRANS_VERSION})")
            except Exception as e:
                print(f"✗ 初始化 googletrans 失败: {e}")
                self.default_method = "mock"

        elif self.default_method == "deep-translator" and HAS_DEEP_TRANSLATOR:
            try:
                # deep-translator 不需要预初始化
                self.translator = "deep-translator"
                print("✓ 使用 deep-translator")
            except Exception as e:
                print(f"✗ 初始化 deep-translator 失败: {e}")
                self.default_method = "mock"

        else:
            print("⚠ 使用模拟翻译模式（仅支持有限词汇）")
            self.default_method = "mock"
    
    def _update_progress(self, current: int, total: int, message: str = ""):
        """更新翻译进度"""
        if self.progress_callback:
            self.progress_callback(current, total, message)
        
        # 同时在终端显示进度
        if total > 0:
            percent = int((current / total) * 100)
            print(f"翻译进度: {current}/{total} ({percent}%) {message}")
        else:
            print(f"翻译进度: {message}")

    def detect_language(self, text: str) -> str:
        """
        检测文本语言

        Args:
            text: 输入文本

        Returns:
            语言代码 ('zh', 'en', 'auto'等)
        """
        if not text or not text.strip():
            return "unknown"

        # 如果使用 googletrans，使用其检测功能
        if self.default_method == "googletrans" and self.translator:
            try:
                detection = self.translator.detect(text)
                if detection.confidence > 0.5:
                    lang = detection.lang
                    if lang.startswith('zh'):
                        return "zh"
                    elif lang.startswith('en'):
                        return "en"
            except Exception as e:
                print(f"语言检测失败: {e}")

        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > chinese_chars:
            return "en"
        else:
            return "unknown"

    def translate(self, text: str, target_lang: str = "en",
                  source_lang: Optional[str] = None) -> TranslationResult:
        """
        翻译单个文本

        Args:
            text: 待翻译文本
            target_lang: 目标语言 ('en', 'zh')
            source_lang: 源语言，None表示自动检测

        Returns:
            翻译结果
        """
        if not text or not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text="",
                source_lang=source_lang or "unknown",
                target_lang=target_lang,
                translation_method="empty"
            )

        # 检测源语言
        if source_lang is None:
            source_lang = self.detect_language(text)

        # 如果源语言和目标语言相同，直接返回
        if source_lang == target_lang:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=1.0,
                translation_method="same_language"
            )

        # 检查缓存
        cache_key = f"{text}_{source_lang}_{target_lang}"
        if cache_key in self.translation_cache:
            cached_result = self.translation_cache[cache_key]
            cached_result.translation_method = f"{cached_result.translation_method}_cached"
            return cached_result

        # 执行翻译
        translation_method = self.default_method

        if translation_method == "googletrans":
            result = self._translate_with_googletrans(text, source_lang, target_lang)
        elif translation_method == "deep-translator":
            result = self._translate_with_deeptranslator(text, source_lang, target_lang)
        else:
            result = self._translate_with_mock(text, source_lang, target_lang)

        # 缓存结果
        self.translation_cache[cache_key] = result

        return result

    def _translate_with_googletrans(self, text: str, source_lang: str,
                                    target_lang: str) -> TranslationResult:
        """使用 googletrans 进行翻译"""
        try:
            # 语言代码映射
            lang_mapping = {
                "zh": "zh-cn",
                "en": "en",
                "zh-CN": "zh-cn",
                "zh-TW": "zh-tw"
            }

            src = lang_mapping.get(source_lang, source_lang)
            dest = lang_mapping.get(target_lang, target_lang)

            # 同步调用（新版本）
            result = self.translator.translate(text, src=src, dest=dest)

            return TranslationResult(
                original_text=text,
                translated_text=result.text,
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=getattr(result, "confidence", 0.8),
                translation_method="googletrans"
            )

        except Exception as e:
            print(f"Google翻译失败: {e}")
            # 回退到模拟翻译
            return self._translate_with_mock(text, source_lang, target_lang)

    def _translate_with_deeptranslator(self, text: str, source_lang: str,
                                       target_lang: str) -> TranslationResult:
        """使用 deep-translator 进行翻译（更稳定）"""
        try:
            # 语言代码映射
            lang_mapping = {
                "zh": "zh-CN",
                "en": "en",
                "zh-CN": "zh-CN",
                "zh-TW": "zh-TW"
            }

            src = lang_mapping.get(source_lang, "auto")
            dest = lang_mapping.get(target_lang, "en")

            # 使用 deep-translator
            translated = GoogleTranslator(source=src, target=dest).translate(text)

            return TranslationResult(
                original_text=text,
                translated_text=translated,
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=0.9,  # deep-translator 通常很可靠
                translation_method="deep-translator"
            )

        except Exception as e:
            print(f"Deep-translator 翻译失败: {e}")
            # 回退到模拟翻译
            return self._translate_with_mock(text, source_lang, target_lang)

    def _translate_with_mock(self, text: str, source_lang: str,
                             target_lang: str) -> TranslationResult:
        """模拟翻译（用于测试和回退）"""
        # 简单的模拟翻译逻辑
        mock_translations = {
            ("zh", "en"): {
                "深度学习": "deep learning",
                "神经网络": "neural network",
                "机器学习": "machine learning",
                "人工智能": "artificial intelligence",
                "数据": "data",
                "模型": "model",
                "训练": "training",
                "算法": "algorithm",
                "视频": "video",
                "音频": "audio",
                "文本": "text",
                "翻译": "translation",
                "助手": "assistant",
                "系统": "system",
                "分析": "analysis"
            },
            ("en", "zh"): {
                "deep learning": "深度学习",
                "neural network": "神经网络",
                "machine learning": "机器学习",
                "artificial intelligence": "人工智能",
                "data": "数据",
                "model": "模型",
                "training": "训练",
                "algorithm": "算法",
                "video": "视频",
                "audio": "音频",
                "text": "文本",
                "translation": "翻译",
                "assistant": "助手",
                "system": "系统",
                "analysis": "分析"
            }
        }

        translated_text = text
        translation_map = mock_translations.get((source_lang, target_lang), {})

        # 简单的词汇替换
        for original, translation in translation_map.items():
            pattern = r'\b' + re.escape(original) + r'\b'
            translated_text = re.sub(pattern, translation, translated_text, flags=re.IGNORECASE)

        # 如果没有找到翻译，添加标记
        if translated_text == text:
            translated_text = f"[{target_lang.upper()}] {text}"

        return TranslationResult(
            original_text=text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=0.5,  # 模拟翻译的置信度
            translation_method="mock"
        )

    def translate_segments(self, segments: List[Dict[str, Any]],
                           target_lang: str = "en") -> List[Dict[str, Any]]:
        """
        批量翻译文本段落
        """
        translated_segments = []
        total_segments = len(segments)
        
        # 更新初始进度
        self._update_progress(0, total_segments, "开始翻译...")

        for i, segment in enumerate(segments):
            # 更新进度
            if i % 5 == 0 or i == total_segments - 1:  # 更频繁地更新进度
                self._update_progress(i + 1, total_segments, f"正在翻译第 {i + 1}/{total_segments} 段")

            translated_segment = segment.copy()

            if "text" in segment:
                translation_result = self.translate(segment["text"], target_lang)
                translated_segment["text"] = translation_result.translated_text
                translated_segment["translation_metadata"] = {
                    "original_text": translation_result.original_text,
                    "source_lang": translation_result.source_lang,
                    "target_lang": translation_result.target_lang,
                    "confidence": translation_result.confidence,
                    "method": translation_result.translation_method
                }

            translated_segments.append(translated_segment)

        # 更新完成进度
        self._update_progress(total_segments, total_segments, "翻译完成")
        return translated_segments

    def translate_transcript(self, transcript: Dict[str, Any],
                             target_lang: str = "en") -> Dict[str, Any]:
        """
        翻译完整的转录结果
        """
        if not transcript:
            return transcript

        translated_transcript = transcript.copy()
        
        # 更新进度
        self._update_progress(0, 0, "开始翻译转录结果...")

        if "text" in transcript:
            self._update_progress(0, 0, "翻译完整文本...")
            translation_result = self.translate(transcript["text"], target_lang)
            translated_transcript["text"] = translation_result.translated_text
            translated_transcript["translation_metadata"] = {
                "original_text": translation_result.original_text,
                "source_lang": translation_result.source_lang,
                "target_lang": translation_result.target_lang,
                "confidence": translation_result.confidence,
                "method": translation_result.translation_method
            }

        if "segments" in transcript:
            self._update_progress(0, 0, "翻译分段文本...")
            translated_transcript["segments"] = self.translate_segments(
                transcript["segments"], target_lang
            )

        return translated_transcript

    def batch_translate(self, texts: List[str], target_lang: str = "en",
                        source_lang: Optional[str] = None) -> List[TranslationResult]:
        """
        批量翻译文本
        """
        results = []
        total_texts = len(texts)
        
        # 更新初始进度
        self._update_progress(0, total_texts, "开始批量翻译...")

        for i, text in enumerate(texts):
            # 更新进度
            self._update_progress(i + 1, total_texts, f"正在翻译第 {i + 1}/{total_texts} 条文本")

            result = self.translate(text, target_lang, source_lang)
            results.append(result)

            # 添加延迟避免API限制
            if self.default_method in ["googletrans", "deep-translator"]:
                time.sleep(0.2)  # 200ms 延迟

        # 更新完成进度
        self._update_progress(total_texts, total_texts, "批量翻译完成")
        return results

    def save_translation_cache(self, file_path: str):
        """保存翻译缓存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 将字典转换为可序列化的格式
                serializable_cache = {}
                for key, result in self.translation_cache.items():
                    serializable_cache[key] = {
                        'original_text': result.original_text,
                        'translated_text': result.translated_text,
                        'source_lang': result.source_lang,
                        'target_lang': result.target_lang,
                        'confidence': result.confidence,
                        'translation_method': result.translation_method
                    }
                json.dump(serializable_cache, f, ensure_ascii=False, indent=2)
            print(f"✓ 翻译缓存已保存到: {file_path}")
        except Exception as e:
            print(f"✗ 保存翻译缓存失败: {e}")

    def load_translation_cache(self, file_path: str):
        """加载翻译缓存"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    for key, data in cache_data.items():
                        result = TranslationResult(
                            original_text=data['original_text'],
                            translated_text=data['translated_text'],
                            source_lang=data['source_lang'],
                            target_lang=data['target_lang'],
                            confidence=data.get('confidence'),
                            translation_method=data.get('translation_method', 'cached')
                        )
                        self.translation_cache[key] = result
                print(f"✓ 从 {file_path} 加载了 {len(cache_data)} 个翻译缓存")
        except Exception as e:
            print(f"✗ 加载翻译缓存失败: {e}")


# 测试函数
def test_translator():
    """测试翻译器功能"""
    print("=== 翻译器测试 ===")

    # 测试数据
    test_texts_zh = [
        "你好，世界！",
        "深度学习是人工智能的一个重要分支",
        "今天天气很好"
    ]

    test_texts_en = [
        "Hello, world!",
        "Machine learning is changing the world",
        "The weather is nice today"
    ]

    # 初始化翻译器
    print("\n1. 初始化翻译器...")
    translator = TextTranslator()
    print(f"使用的翻译方法: {translator.default_method}")

    # 测试中译英
    print("\n2. 测试中文翻译为英文:")
    for text in test_texts_zh:
        result = translator.translate(text, "en")
        print(f"  '{text}' => '{result.translated_text}' (方法: {result.translation_method})")

    # 测试英译中
    print("\n3. 测试英文翻译为中文:")
    for text in test_texts_en:
        result = translator.translate(text, "zh")
        print(f"  '{text}' => '{result.translated_text}' (方法: {result.translation_method})")

    # 测试批量翻译
    print("\n4. 测试批量翻译:")
    results = translator.batch_translate(test_texts_zh, "en")
    for i, result in enumerate(results):
        print(f"  {i + 1}. {result.translated_text}")

    print("\n=== 测试完成 ===")
    return translator


# 便捷函数
def translate_text(text: str, target_lang: str = "en",
                   source_lang: Optional[str] = None) -> str:
    """
    便捷的文本翻译函数
    """
    translator = TextTranslator()
    result = translator.translate(text, target_lang, source_lang)
    return result.translated_text


def translate_for_embedding(text: str, embedding_lang: str = "en") -> str:
    """
    为embedding模型翻译文本
    """
    translator = TextTranslator()
    source_lang = translator.detect_language(text)

    if source_lang != embedding_lang:
        result = translator.translate(text, embedding_lang, source_lang)
        return result.translated_text

    return text


def translate_transcript_for_qa(transcript: Dict[str, Any],
                                qa_lang: str = "zh") -> Dict[str, Any]:
    """
    为问答系统翻译转录结果
    """
    translator = TextTranslator()
    return translator.translate_transcript(transcript, qa_lang)


if __name__ == "__main__":
    # 运行测试
    test_translator()