#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text模块 - 文本处理模块

负责对语音识别生成的文本进行清洗、分段和语言转换，使文本数据满足后续信息检索和对话式问答模块对输入格式与语义质量的要求。
"""

from .text_cleaner import TextCleaner, clean_text, clean_transcript
from .segmenter import TextSegmenter, TextSegment, segment_text
from .translator import TextTranslator, TranslationResult, translate_text, translate_for_embedding, translate_transcript_for_qa

__all__ = [
    # 文本清洗
    'TextCleaner',
    'clean_text',
    'clean_transcript',
    
    # 文本分段
    'TextSegmenter',
    'TextSegment',
    'segment_text',
    
    # 翻译
    'TextTranslator',
    'TranslationResult',
    'translate_text',
    'translate_for_embedding',
    'translate_transcript_for_qa'
]