#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译模块 - translator.py

负责处理文本的语言转换，解决"视频语言 ≠ 模型语言"的问题：
- 中文视频 + 英文embedding模型
- 英文视频 + 中文问答
- 支持批量翻译和单句翻译
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
logging.getLogger("httpx").setLevel(logging.WARNING)


# 尝试导入翻译库
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from googletrans import Translator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False


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
    
    def __init__(self, default_method: str = "googletrans"):
        """
        初始化翻译器
        
        Args:
            default_method: 默认翻译方法 ("googletrans", "mock", "custom")
        """
        self.default_method = default_method
        self.translator = None
        self.translation_cache = {}

        if default_method == "googletrans":
            if not HAS_GOOGLETRANS:
                raise RuntimeError(
                    "googletrans 未安装，但 default_method=googletrans"
                )
            try:
                self.translator = Translator()
                self.default_method = "googletrans"
            except Exception as e:
                raise RuntimeError(f"初始化 Google 翻译失败: {e}")
    
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
        if self.default_method == "googletrans" and self.translator:
            result = self._translate_with_googletrans(text, source_lang, target_lang)
        else:
            result = self._translate_with_mock(text, source_lang, target_lang)
        
        # 缓存结果
        self.translation_cache[cache_key] = result
        
        return result
    
    def translate_segments(self, segments: List[Dict[str, Any]], 
                          target_lang: str = "en") -> List[Dict[str, Any]]:
        """
        批量翻译文本段落
        
        Args:
            segments: 文本段落列表
            target_lang: 目标语言
            
        Returns:
            翻译后的段落列表
        """
        translated_segments = []
        
        for segment in segments:
            translated_segment = segment.copy()
            
            # 翻译文本
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
        
        return translated_segments
    
    def translate_transcript(self, transcript: Dict[str, Any], 
                           target_lang: str = "en") -> Dict[str, Any]:
        """
        翻译完整的转录结果
        
        Args:
            transcript: Whisper转录结果
            target_lang: 目标语言
            
        Returns:
            翻译后的转录结果
        """
        if not transcript:
            return transcript
        
        # 复制原始结果
        translated_transcript = transcript.copy()
        
        # 翻译整体文本
        if "text" in transcript:
            translation_result = self.translate(transcript["text"], target_lang)
            translated_transcript["text"] = translation_result.translated_text
            translated_transcript["translation_metadata"] = {
                "original_text": translation_result.original_text,
                "source_lang": translation_result.source_lang,
                "target_lang": translation_result.target_lang,
                "confidence": translation_result.confidence,
                "method": translation_result.translation_method
            }
        
        # 翻译各个段落
        if "segments" in transcript:
            translated_transcript["segments"] = self.translate_segments(
                transcript["segments"], target_lang
            )
        
        return translated_transcript

    def _translate_with_googletrans(self, text: str, source_lang: str,
                                    target_lang: str) -> TranslationResult:
        """使用 Google 翻译进行翻译（稳定版，避免 event loop 关闭）"""
        try:
            lang_mapping = {"zh": "zh-cn", "en": "en"}
            src = lang_mapping.get(source_lang, source_lang)
            dest = lang_mapping.get(target_lang, target_lang)

            async def _do_translate():
                return await self.translator.translate(text, src=src, dest=dest)

            future = asyncio.run_coroutine_threadsafe(
                _do_translate(),
                self._loop
            )

            result = future.result()

            return TranslationResult(
                original_text=text,
                translated_text=result.text,
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=getattr(result, "confidence", None),
                translation_method="googletrans"
            )

        except Exception as e:
            print(f"Google翻译失败: {e}")
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
                "算法": "algorithm"
            },
            ("en", "zh"): {
                "deep learning": "深度学习",
                "neural network": "神经网络",
                "machine learning": "机器学习",
                "artificial intelligence": "人工智能",
                "data": "数据",
                "model": "模型",
                "training": "训练",
                "algorithm": "算法"
            }
        }
        
        translated_text = text
        translation_map = mock_translations.get((source_lang, target_lang), {})
        
        # 简单的词汇替换
        for original, translation in translation_map.items():
            translated_text = re.sub(
                re.escape(original), 
                translation, 
                translated_text, 
                flags=re.IGNORECASE
            )
        
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
    
    def batch_translate(self, texts: List[str], target_lang: str = "en",
                       source_lang: Optional[str] = None) -> List[TranslationResult]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译文本列表
            target_lang: 目标语言
            source_lang: 源语言
            
        Returns:
            翻译结果列表
        """
        results = []
        
        for text in texts:
            result = self.translate(text, target_lang, source_lang)
            results.append(result)
            
            # 添加延迟避免API限制
            if self.default_method == "googletrans":
                time.sleep(0.1)
        
        return results
    
    def save_translation_cache(self, file_path: str):
        """保存翻译缓存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存翻译缓存失败: {e}")
    
    def load_translation_cache(self, file_path: str):
        """加载翻译缓存"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translation_cache = json.load(f)
        except Exception as e:
            print(f"加载翻译缓存失败: {e}")


# 便捷函数
def translate_text(text: str, target_lang: str = "en", 
                  source_lang: Optional[str] = None) -> str:
    """
    便捷的文本翻译函数
    
    Args:
        text: 待翻译文本
        target_lang: 目标语言
        source_lang: 源语言
        
    Returns:
        翻译后的文本
    """
    translator = TextTranslator()
    result = translator.translate(text, target_lang, source_lang)
    return result.translated_text


def translate_for_embedding(text: str, embedding_lang: str = "en") -> str:
    """
    为embedding模型翻译文本
    
    Args:
        text: 输入文本
        embedding_lang: embedding模型支持的语言
        
    Returns:
        适合embedding的文本
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
    
    Args:
        transcript: 转录结果
        qa_lang: 问答系统使用的语言
        
    Returns:
        翻译后的转录结果
    """
    translator = TextTranslator()
    return translator.translate_transcript(transcript, qa_lang)