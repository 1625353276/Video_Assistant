#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译功能模块
"""

import time
from typing import Dict, Any, Optional


class TranslatorManager:
    """翻译管理器"""
    
    def __init__(self):
        """初始化翻译管理器"""
        self._init_translator()
    
    def _init_translator(self):
        """初始化翻译器"""
        try:
            from modules.text.translator import TextTranslator
            self.translator = TextTranslator(
                default_method="deep-translator",
                progress_callback=self._on_translation_progress
            )
            self.mock_mode = False
            print("✓ 翻译器初始化成功")
            
        except ImportError as e:
            print(f"⚠ 翻译器初始化失败，使用模拟模式: {e}")
            self.mock_mode = True
            self.translator = None
    
    def _on_translation_progress(self, current: int, total: int, message: str):
        """翻译进度回调函数"""
        # 这里需要获取当前正在翻译的视频ID
        if hasattr(self, '_current_translating_video_id'):
            video_id = self._current_translating_video_id
            update_translation_progress(video_id, current, total, message)
    
    def translate_transcript(self, video_id, target_lang):
        """
        翻译转录文本
        """
        from .video_processor import get_video_data
        video_data = get_video_data()
        
        if video_id not in video_data:
            return {"error": "视频不存在"}
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return {"error": "视频尚未处理完成"}
        
        if not self.translator:
            return {"error": "翻译器未初始化"}
        
        try:
            # 设置当前正在翻译的视频ID，用于进度回调
            self._current_translating_video_id = video_id
            
            # 初始化翻译进度
            video_info["translation_progress"] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": "准备翻译...",
                "timestamp": time.time()
            }
            
            transcript = video_info["transcript"]
            translated_transcript = self.translator.translate_transcript(transcript, target_lang)
            
            # 保存翻译结果
            video_info[f"translated_transcript_{target_lang}"] = translated_transcript
            
            # 更新翻译完成状态
            video_info["translation_progress"] = {
                "current": 1,
                "total": 1,
                "progress": 1.0,
                "message": "翻译完成",
                "timestamp": time.time()
            }
            
            return {
                "success": True,
                "translated_text": translated_transcript.get("text", ""),
                "segments": translated_transcript.get("segments", []),
                "metadata": translated_transcript.get("translation_metadata", {})
            }
        except Exception as e:
            # 更新错误状态
            video_info["translation_progress"] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": f"翻译失败: {str(e)}",
                "timestamp": time.time()
            }
            return {"error": f"翻译失败: {str(e)}"}
    
    def translate_background(self, video_id, target_lang):
        """后台翻译处理"""
        from .video_processor import get_video_data
        video_data = get_video_data()
        
        if video_id not in video_data:
            return {"error": "视频不存在"}
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return {"error": "视频尚未处理完成"}
        
        if not self.translator:
            return {"error": "翻译器未初始化"}
        
        try:
            # 设置当前正在翻译的视频ID，用于进度回调
            self._current_translating_video_id = video_id
            
            # 初始化翻译进度
            video_info["translation_progress"] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": "准备翻译...",
                "timestamp": time.time()
            }
            
            transcript = video_info["transcript"]
            translated_transcript = self.translator.translate_transcript(transcript, target_lang)
            
            # 保存翻译结果
            video_info[f"translated_transcript_{target_lang}"] = translated_transcript
            video_info["translating"] = False
            
            # 更新翻译完成状态
            video_info["translation_progress"] = {
                "current": 1,
                "total": 1,
                "progress": 1.0,
                "message": "翻译完成",
                "timestamp": time.time()
            }
            
            return {
                "success": True,
                "translated_text": translated_transcript.get("text", ""),
                "segments": translated_transcript.get("segments", []),
                "metadata": translated_transcript.get("translation_metadata", {}),
                "message": "翻译完成"
            }
        except Exception as e:
            video_info["translating"] = False
            # 更新错误状态
            video_info["translation_progress"] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": f"翻译失败: {str(e)}",
                "timestamp": time.time()
            }
            return {"error": f"翻译失败: {str(e)}"}
    
    def get_translation_progress(self, video_id):
        """获取翻译进度"""
        from .video_processor import get_video_data
        video_data = get_video_data()
        
        if video_id not in video_data:
            return {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": "视频不存在",
                "timestamp": time.time()
            }
        
        video_info = video_data[video_id]
        return video_info.get("translation_progress", {
            "current": 0,
            "total": 0,
            "progress": 0.0,
            "message": "尚未开始翻译",
            "timestamp": time.time()
        })


# 全局翻译管理器实例
translator_manager = TranslatorManager()


def get_translator_manager():
    """获取翻译管理器实例"""
    return translator_manager


# 翻译进度回调函数
def update_translation_progress(video_id, current, total, message):
    """更新翻译进度"""
    from .video_processor import get_video_data
    video_data = get_video_data()
    
    if video_id not in video_data:
        return
    
    # 计算进度百分比
    if total > 0:
        progress = min(current / total, 1.0)
    else:
        progress = 0.0
    
    # 更新视频数据中的翻译进度
    video_data[video_id]["translation_progress"] = {
        "current": current,
        "total": total,
        "progress": progress,
        "message": message,
        "timestamp": time.time()
    }