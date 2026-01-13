#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本清洗模块 - text_cleaner.py

负责对语音识别生成的文本进行清洗和规范化，包括：
- 去除口语填充词（"呃""嗯""那个"等）
- 去掉重复句
- 去掉异常符号
- 基本标点规范化
"""

import re
from typing import List, Dict, Any


class TextCleaner:
    """文本清洗器，处理语音识别后的原始文本"""
    
    def __init__(self):
        # 口语填充词列表
        self.filler_words = [
            "嗯", "呃", "啊", "那个", "这个", "就是", "然后", "就是说",
            "对吧", "你知道吧", "对吧", "那么", "这样子", "那样",
            "嗯嗯", "啊啊", "呃呃", "那个那个", "这个这个"
        ]
        
        # 构建填充词正则表达式
        self.filler_pattern = self._build_filler_pattern()
    
    def _build_filler_pattern(self) -> re.Pattern:
        """构建填充词的正则表达式模式"""
        # 转义特殊字符并按长度排序（优先匹配长词）
        escaped_words = sorted(
            [re.escape(word) for word in self.filler_words],
            key=len,
            reverse=True
        )
        pattern = r'\b(?:' + '|'.join(escaped_words) + r')\b'
        return re.compile(pattern, flags=re.IGNORECASE)
    
    def clean_text(self, text: str) -> str:
        """
        清洗单个文本字符串
        
        Args:
            text: 待清洗的文本
            
        Returns:
            清洗后的文本
        """
        if not text or not text.strip():
            return ""
        
        # 1. 去除填充词
        text = self._remove_filler_words(text)
        
        # 2. 去除异常符号
        text = self._remove_abnormal_symbols(text)
        
        # 3. 标点规范化
        text = self._normalize_punctuation(text)
        
        # 4. 去除多余空格
        text = self._remove_extra_spaces(text)
        
        # 5. 修复断句
        text = self._fix_sentence_breaks(text)
        
        return text.strip()
    
    def clean_transcript(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗完整的转录结果
        
        Args:
            transcript: Whisper转录结果字典
            
        Returns:
            清洗后的转录结果
        """
        if not transcript or "segments" not in transcript:
            return transcript
        
        # 复制原始结果，避免修改原数据
        cleaned_transcript = transcript.copy()
        cleaned_segments = []
        
        for segment in transcript["segments"]:
            cleaned_segment = segment.copy()
            
            # 清洗文本
            if "text" in cleaned_segment:
                cleaned_segment["text"] = self.clean_text(cleaned_segment["text"])
            
            cleaned_segments.append(cleaned_segment)
        
        cleaned_transcript["segments"] = cleaned_segments
        
        # 重新生成完整的清洗后文本
        cleaned_transcript["text"] = "\n".join(
            [seg["text"] for seg in cleaned_segments if seg["text"].strip()]
        )
        
        return cleaned_transcript
    
    def _remove_filler_words(self, text: str) -> str:
        """去除口语填充词"""
        return self.filler_pattern.sub("", text)
    
    def _remove_abnormal_symbols(self, text: str) -> str:
        """去除异常符号"""
        # 保留中文、英文、数字、基本标点
        # 这个模式会移除各种特殊符号，但保留常用的标点符号
        pattern = r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s.,!?;:：。，！？；：""''（）\[\]{}()\-]'
        return re.sub(pattern, '', text)
    
    def _normalize_punctuation(self, text: str) -> str:
        """标点符号规范化"""
        # 统一中英文标点
        punctuation_map = {
            ',': '，',
            '\.': '。',
            '!': '！',
            '\?': '？',
            ':': '：',
            ';': '；',
            '"': '"',
            "'": "'",
            '\(': '（',
            '\)': '）',
        }
        
        for en_punct, zh_punct in punctuation_map.items():
            text = re.sub(rf'\s*{re.escape(en_punct)}\s*', zh_punct, text)
        
        # 修复连续标点
        text = re.sub(r'([。，！？；：])\1+', r'\1', text)
        
        return text
    
    def _remove_extra_spaces(self, text: str) -> str:
        """去除多余空格"""
        # 将多个空格替换为单个空格
        text = re.sub(r'\s+', ' ', text)
        # 去除行首行尾空格
        text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
        return text
    
    def _fix_sentence_breaks(self, text: str) -> str:
        """修复句子断句"""
        # 确保句号后有适当空格
        text = re.sub(r'。(?=[^\s])', '。', text)
        text = re.sub(r'，(?=[^\s])', '，', text)
        
        return text
    
    def remove_duplicate_sentences(self, text: str, similarity_threshold: float = 0.9) -> str:
        """
        去除重复或高度相似的句子
        
        Args:
            text: 输入文本
            similarity_threshold: 相似度阈值，超过此值认为是重复
            
        Returns:
            去重后的文本
        """
        sentences = re.split(r'[。！？；]', text)
        unique_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 检查是否与已有句子重复
            is_duplicate = False
            for existing in unique_sentences:
                if self._calculate_similarity(sentence, existing) > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sentences.append(sentence)
        
        # 重新组合文本
        return '。'.join(unique_sentences) + ('。' if unique_sentences else '')
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        计算两个句子的相似度（简单实现）
        
        Args:
            s1, s2: 待比较的句子
            
        Returns:
            相似度分数 (0-1)
        """
        if not s1 or not s2:
            return 0.0
        
        # 简单的字符级相似度计算
        set1 = set(s1)
        set2 = set(s2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0


# 便捷函数
def clean_text(text: str) -> str:
    """便捷的文本清洗函数"""
    cleaner = TextCleaner()
    return cleaner.clean_text(text)


def clean_transcript(transcript: Dict[str, Any]) -> Dict[str, Any]:
    """便捷的转录结果清洗函数"""
    cleaner = TextCleaner()
    return cleaner.clean_transcript(transcript)