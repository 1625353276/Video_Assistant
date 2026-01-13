#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本分段模块 - segmenter.py

负责将长文本切分成适合模型处理的小段，支持多种分段策略：
- 按句子分段
- 按时间戳分段（基于Whisper转录结果）
- 按固定token长度分段
- 智能语义分段
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class TextSegment:
    """文本段落数据结构"""
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    segment_id: Optional[int] = None
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TextSegmenter:
    """文本分段器，支持多种分段策略"""
    
    def __init__(self, max_tokens: int = 400, overlap_tokens: int = 50):
        """
        初始化分段器
        
        Args:
            max_tokens: 每段最大token数（粗略估计，1个中文≈1个token）
            overlap_tokens: 段落间重叠token数
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
    
    def segment_by_sentences(self, text: str, max_sentences: int = 5) -> List[TextSegment]:
        """
        按句子进行分段
        
        Args:
            text: 输入文本
            max_sentences: 每段最大句子数
            
        Returns:
            分段结果列表
        """
        # 按句号、问号、感叹号等分割句子
        sentences = re.split(r'[。！？；]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        segments = []
        for i in range(0, len(sentences), max_sentences):
            segment_sentences = sentences[i:i + max_sentences]
            segment_text = '。'.join(segment_sentences) + '。'
            
            segment = TextSegment(
                text=segment_text,
                segment_id=len(segments),
                token_count=self._estimate_tokens(segment_text)
            )
            segments.append(segment)
        
        return segments
    
    def segment_by_timestamp(self, transcript: Dict[str, Any], 
                           max_duration: float = 30.0) -> List[TextSegment]:
        """
        按时间戳进行分段（基于Whisper转录结果）
        
        Args:
            transcript: Whisper转录结果
            max_duration: 每段最大时长（秒）
            
        Returns:
            分段结果列表
        """
        if "segments" not in transcript:
            return self.segment_by_sentences(transcript.get("text", ""))
        
        segments = []
        current_segment_texts = []
        current_start_time = None
        current_end_time = None
        segment_id = 0
        
        for segment in transcript["segments"]:
            start_time = segment.get("start", 0)
            end_time = segment.get("end", 0)
            text = segment.get("text", "").strip()
            
            if not text:
                continue
            
            # 如果是第一个segment，记录开始时间
            if current_start_time is None:
                current_start_time = start_time
            
            # 检查是否需要分段
            duration = end_time - current_start_time if current_start_time else 0
            
            if duration >= max_duration and current_segment_texts:
                # 创建当前段落
                segment_text = ''.join(current_segment_texts)
                text_segment = TextSegment(
                    text=segment_text,
                    start_time=current_start_time,
                    end_time=current_end_time or start_time,
                    segment_id=segment_id,
                    token_count=self._estimate_tokens(segment_text)
                )
                segments.append(text_segment)
                
                # 重置状态
                current_segment_texts = []
                current_start_time = start_time
                current_end_time = None
                segment_id += 1
            
            # 添加当前文本
            current_segment_texts.append(text)
            current_end_time = end_time
        
        # 处理最后一段
        if current_segment_texts:
            segment_text = ''.join(current_segment_texts)
            text_segment = TextSegment(
                text=segment_text,
                start_time=current_start_time,
                end_time=current_end_time,
                segment_id=segment_id,
                token_count=self._estimate_tokens(segment_text)
            )
            segments.append(text_segment)
        
        return segments
    
    def segment_by_tokens(self, text: str, max_tokens: Optional[int] = None) -> List[TextSegment]:
        """
        按token数量进行分段
        
        Args:
            text: 输入文本
            max_tokens: 每段最大token数，默认使用初始化值
            
        Returns:
            分段结果列表
        """
        max_tokens = max_tokens or self.max_tokens
        
        # 按字符分割（粗略估计token）
        chars = list(text)
        segments = []
        segment_id = 0
        
        i = 0
        while i < len(chars):
            # 计算当前段的结束位置
            end_pos = min(i + max_tokens, len(chars))
            
            # 如果不是最后一段，尝试在句号等位置分割
            if end_pos < len(chars):
                # 向前查找最近的句号、问号、感叹号
                for j in range(end_pos, max(i, end_pos - 50), -1):
                    if chars[j] in '。！？；':
                        end_pos = j + 1
                        break
            
            # 提取段落文本
            segment_text = ''.join(chars[i:end_pos])
            
            # 创建段落
            segment = TextSegment(
                text=segment_text,
                segment_id=segment_id,
                token_count=self._estimate_tokens(segment_text)
            )
            segments.append(segment)
            
            # 计算下一段开始位置（考虑重叠）
            i = end_pos - self.overlap_tokens if end_pos < len(chars) else end_pos
            segment_id += 1
        
        return segments
    
    def segment_by_semantic(self, text: str, similarity_threshold: float = 0.3) -> List[TextSegment]:
        """
        按语义进行智能分段
        
        Args:
            text: 输入文本
            similarity_threshold: 语义相似度阈值，低于此值时进行分段
            
        Returns:
            分段结果列表
        """
        # 先按句子分割
        sentences = re.split(r'[。！？；]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return [TextSegment(text=text, segment_id=0, token_count=self._estimate_tokens(text))]
        
        segments = []
        current_segment_sentences = [sentences[0]]
        segment_id = 0
        
        for i in range(1, len(sentences)):
            current_sentence = sentences[i]
            prev_sentence = sentences[i-1]
            
            # 计算相邻句子的语义相似度（简单实现）
            similarity = self._calculate_semantic_similarity(prev_sentence, current_sentence)
            
            # 如果相似度低于阈值，进行分段
            if similarity < similarity_threshold and len(current_segment_sentences) >= 2:
                # 创建当前段落
                segment_text = '。'.join(current_segment_sentences) + '。'
                segment = TextSegment(
                    text=segment_text,
                    segment_id=segment_id,
                    token_count=self._estimate_tokens(segment_text)
                )
                segments.append(segment)
                
                # 开始新段落
                current_segment_sentences = [current_sentence]
                segment_id += 1
            else:
                current_segment_sentences.append(current_sentence)
        
        # 处理最后一段
        if current_segment_sentences:
            segment_text = '。'.join(current_segment_sentences) + '。'
            segment = TextSegment(
                text=segment_text,
                segment_id=segment_id,
                token_count=self._estimate_tokens(segment_text)
            )
            segments.append(segment)
        
        return segments
    
    def hybrid_segment(self, text: str, transcript: Optional[Dict[str, Any]] = None) -> List[TextSegment]:
        """
        混合分段策略，优先使用时间戳，回退到其他策略
        
        Args:
            text: 输入文本
            transcript: 可选的转录结果
            
        Returns:
            分段结果列表
        """
        if transcript and "segments" in transcript:
            # 尝试按时间戳分段
            timestamp_segments = self.segment_by_timestamp(transcript)
            
            # 检查每段的token数，如果过长则进一步分割
            final_segments = []
            for ts_segment in timestamp_segments:
                if ts_segment.token_count and ts_segment.token_count > self.max_tokens:
                    # 对过长的段进行token分割
                    token_segments = self.segment_by_tokens(ts_segment.text)
                    # 保留时间戳信息
                    for i, token_seg in enumerate(token_segments):
                        if i == 0:
                            token_seg.start_time = ts_segment.start_time
                        if i == len(token_segments) - 1:
                            token_seg.end_time = ts_segment.end_time
                    final_segments.extend(token_segments)
                else:
                    final_segments.append(ts_segment)
            
            return final_segments
        else:
            # 没有时间戳信息，使用token分段
            return self.segment_by_tokens(text)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        粗略估算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            估算的token数量
        """
        # 简单估算：中文字符按1个token计算，英文单词按0.75个token计算
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        return chinese_chars + int(english_words * 0.75)
    
    def _calculate_semantic_similarity(self, s1: str, s2: str) -> float:
        """
        计算两个句子的语义相似度（简单实现）
        
        Args:
            s1, s2: 待比较的句子
            
        Returns:
            相似度分数 (0-1)
        """
        if not s1 or not s2:
            return 0.0
        
        # 简单的关键词重叠度计算
        words1 = set(re.findall(r'[\w\u4e00-\u9fff]+', s1.lower()))
        words2 = set(re.findall(r'[\w\u4e00-\u9fff]+', s2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_segment_statistics(self, segments: List[TextSegment]) -> Dict[str, Any]:
        """
        获取分段统计信息
        
        Args:
            segments: 分段结果列表
            
        Returns:
            统计信息字典
        """
        if not segments:
            return {}
        
        token_counts = [s.token_count for s in segments if s.token_count]
        
        stats = {
            "total_segments": len(segments),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_segment": sum(token_counts) / len(token_counts) if token_counts else 0,
            "min_tokens": min(token_counts) if token_counts else 0,
            "max_tokens": max(token_counts) if token_counts else 0,
            "has_timestamps": any(s.start_time is not None for s in segments)
        }
        
        return stats


# 便捷函数
def segment_text(text: str, strategy: str = "tokens", 
                max_tokens: int = 400, transcript: Optional[Dict[str, Any]] = None) -> List[TextSegment]:
    """
    便捷的文本分段函数
    
    Args:
        text: 输入文本
        strategy: 分段策略 ("sentences", "tokens", "timestamp", "semantic", "hybrid")
        max_tokens: 最大token数
        transcript: 转录结果（用于时间戳分段）
        
    Returns:
        分段结果列表
    """
    segmenter = TextSegmenter(max_tokens=max_tokens)
    
    if strategy == "sentences":
        return segmenter.segment_by_sentences(text)
    elif strategy == "tokens":
        return segmenter.segment_by_tokens(text)
    elif strategy == "timestamp" and transcript:
        return segmenter.segment_by_timestamp(transcript)
    elif strategy == "semantic":
        return segmenter.segment_by_semantic(text)
    elif strategy == "hybrid":
        return segmenter.hybrid_segment(text, transcript)
    else:
        # 默认使用token分段
        return segmenter.segment_by_tokens(text)