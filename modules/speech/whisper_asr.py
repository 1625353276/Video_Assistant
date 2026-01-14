#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper语音识别模块

职责：
- 加载Whisper预训练模型
- 执行语音转文本
- 输出结构化转写结果
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import whisper
import torch
import ssl

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ssl._create_default_https_context = ssl._create_unverified_context

class WhisperASR:
    """Whisper语音识别服务"""
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        """
        初始化Whisper ASR服务
        
        Args:
            model_size: 模型大小 (tiny/base/small/medium/large)
            device: 计算设备 (cuda/cpu)，自动检测如果未指定
        """
        self.model_size = model_size
        self.model = None
        self.device = self._determine_device(device)
        
        # 支持的模型大小
        self.supported_models = ["tiny", "base", "small", "medium", "large"]
        
        if model_size not in self.supported_models:
            raise ValueError(f"不支持的模型大小: {model_size}. 支持的模型: {self.supported_models}")
        
        logger.info(f"初始化Whisper ASR服务，模型: {model_size}, 设备: {self.device}")
    
    def _determine_device(self, device: Optional[str]) -> str:
        """
        确定计算设备
        
        Args:
            device: 指定的设备
            
        Returns:
            str: 使用的设备
        """
        if device:
            return device
        
        # 自动检测设备
        if torch.cuda.is_available():
            return "cuda"
        # 注意：Apple Silicon的MPS后端与Whisper模型存在兼容性问题
        # 临时解决方案：强制使用CPU而不是MPS
        # elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        #     return "mps"  # Apple Silicon GPU
        else:
            return "cpu"
    
    def load_model(self) -> None:
        """加载Whisper模型"""
        if self.model is not None:
            logger.info("模型已加载")
            return
        
        try:
            logger.info(f"正在加载Whisper模型: {self.model_size}")
            
            # 下载并加载模型
            self.model = whisper.load_model(
                self.model_size,
                device=self.device
            )
            
            logger.info(f"Whisper模型加载成功")
            
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise RuntimeError(f"Whisper模型加载失败: {str(e)}")
    
    def transcribe(self, audio_path: Path, 
                   language: Optional[str] = None,
                   task: str = "transcribe",
                   verbose: bool = False) -> Dict:
        """
        执行语音转文本
        
        Args:
            audio_path: 音频文件路径
            language: 指定语言代码（如'zh', 'en'），None为自动检测
            task: 任务类型 ('transcribe' 或 'translate')
            verbose: 是否显示详细输出
            
        Returns:
            Dict: 结构化转写结果
            
        Raises:
            RuntimeError: 转写失败时抛出异常
        """
        try:
            # 确保模型已加载
            if self.model is None:
                self.load_model()
            
            # 验证音频文件
            if not audio_path.exists():
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            logger.info(f"开始语音转文本: {audio_path}")
            
            # 执行转写
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                verbose=verbose,
                fp16=self.device == "cuda"  # GPU时使用半精度
            )
            
            # 构建结构化结果
            structured_result = self._format_result(result, audio_path)
            
            logger.info(f"语音转文本完成，共 {len(structured_result['segments'])} 个片段")
            
            return structured_result
            
        except Exception as e:
            logger.error(f"语音转文本失败: {str(e)}")
            raise RuntimeError(f"语音转文本失败: {str(e)}")
    
    def _format_result(self, raw_result: Dict, audio_path: Path) -> Dict:
        """
        格式化转写结果为标准结构
        
        Args:
            raw_result: Whisper原始结果
            audio_path: 音频文件路径
            
        Returns:
            Dict: 格式化后的结果
        """
        # 提取基本信息
        formatted_result = {
            "audio_file": str(audio_path),
            "audio_file_name": audio_path.name,
            "language": raw_result.get("language", "unknown"),
            "language_probability": raw_result.get("language_probability", 0.0),
            "text": raw_result.get("text", "").strip(),
            "segments": [],
            "words": [],
            "model_used": self.model_size,
            "device_used": self.device
        }
        
        # 处理片段信息
        for segment in raw_result.get("segments", []):
            formatted_segment = {
                "id": segment.get("id", 0),
                "start": round(segment.get("start", 0.0), 2),
                "end": round(segment.get("end", 0.0), 2),
                "text": segment.get("text", "").strip(),
                "confidence": round(segment.get("avg_logprob", 0.0), 3),
                "no_speech_prob": round(segment.get("no_speech_prob", 0.0), 3),
                "words": []
            }
            
            # 添加词级别信息（如果存在）
            if "words" in segment:
                for word in segment["words"]:
                    formatted_word = {
                        "word": word.get("word", ""),
                        "start": round(word.get("start", 0.0), 2),
                        "end": round(word.get("end", 0.0), 2),
                        "confidence": round(word.get("probability", 0.0), 3)
                    }
                    formatted_segment["words"].append(formatted_word)
                    formatted_result["words"].append(formatted_word)
            
            formatted_result["segments"].append(formatted_segment)
        
        # 计算统计信息
        if formatted_result["segments"]:
            total_duration = max(seg["end"] for seg in formatted_result["segments"])
            formatted_result["total_duration"] = round(total_duration, 2)
            
            # 计算平均置信度
            confidences = [seg["confidence"] for seg in formatted_result["segments"] if seg["confidence"] > -float('inf')]
            if confidences:
                formatted_result["avg_confidence"] = round(sum(confidences) / len(confidences), 3)
            else:
                formatted_result["avg_confidence"] = 0.0
            
            # 计算语音时长（排除静音）
            speech_duration = sum(seg["end"] - seg["start"] for seg in formatted_result["segments"])
            formatted_result["speech_duration"] = round(speech_duration, 2)
            
            # 计算语音占比
            if total_duration > 0:
                formatted_result["speech_ratio"] = round(speech_duration / total_duration, 3)
            else:
                formatted_result["speech_ratio"] = 0.0
        else:
            formatted_result["total_duration"] = 0.0
            formatted_result["avg_confidence"] = 0.0
            formatted_result["speech_duration"] = 0.0
            formatted_result["speech_ratio"] = 0.0
        
        return formatted_result
    
    def transcribe_with_timestamps(self, audio_path: Path,
                                 language: Optional[str] = None) -> Dict:
        """
        带时间戳的转写（强制输出词级别时间戳）
        
        Args:
            audio_path: 音频文件路径
            language: 指定语言代码
            
        Returns:
            Dict: 包含词级别时间戳的转写结果
        """
        # 确保模型已加载
        if self.model is None:
            self.load_model()
        
        try:
            logger.info(f"开始带时间戳的语音转文本: {audio_path}")
            
            # 使用word_timestamps选项
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=True,
                fp16=self.device == "cuda"
            )
            
            # 格式化结果
            formatted_result = self._format_result(result, audio_path)
            
            logger.info(f"带时间戳转写完成，共 {len(formatted_result['words'])} 个词")
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"带时间戳转写失败: {str(e)}")
            raise RuntimeError(f"带时间戳转写失败: {str(e)}")
    
    def detect_language(self, audio_path: Path) -> Dict:
        """
        检测音频语言
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Dict: 语言检测结果
        """
        try:
            # 确保模型已加载
            if self.model is None:
                self.load_model()
            
            logger.info(f"检测音频语言: {audio_path}")
            
            # 加载音频
            audio = whisper.load_audio(str(audio_path))
            
            # 检测语言
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.device)
            
            _, probs = self.model.detect_language(mel)
            
            # 获取最可能的语言
            detected_lang = max(probs, key=probs.get)
            confidence = probs[detected_lang]
            
            result = {
                "detected_language": detected_lang,
                "confidence": round(confidence, 3),
                "all_probabilities": {lang: round(prob, 3) for lang, prob in probs.items()}
            }
            
            logger.info(f"检测到语言: {detected_lang} (置信度: {confidence:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"语言检测失败: {str(e)}")
            raise RuntimeError(f"语言检测失败: {str(e)}")
    
    def get_model_info(self) -> Dict:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "model_size": self.model_size,
            "device": self.device,
            "model_loaded": self.model is not None,
            "supported_languages": list(whisper.LANGUAGES.keys()) if hasattr(whisper, 'LANGUAGES') else [],
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available()
        }
    
    def unload_model(self) -> None:
        """卸载模型以释放内存"""
        if self.model is not None:
            del self.model
            self.model = None
            
            # 清理GPU缓存
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            logger.info("Whisper模型已卸载")
    
    def __del__(self):
        """析构函数，确保模型被正确卸载"""
        self.unload_model()