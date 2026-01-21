#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译功能模块 - 用户隔离版本

支持用户专属的翻译功能和进度管理
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入用户上下文
from deploy.utils.user_context import get_current_user_id, get_current_user_paths, require_user_login


class IsolatedTranslatorManager:
    """用户隔离的翻译管理器"""
    
    def __init__(self):
        """初始化翻译管理器"""
        self._init_translator()
        self.translation_progress = {}  # 用户隔离的翻译进度
    
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
            self.update_translation_progress(video_id, current, total, message)
    
    @require_user_login
    def translate_transcript(self, video_id: str, target_lang: str):
        """
        翻译转录文本（用户隔离版本）
        """
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        # 检查转录文件是否存在
        transcript_path = user_paths.get_transcript_path(video_id)
        if not transcript_path.exists():
            return {"error": "转录文件不存在"}
        
        if not self.translator:
            return {"error": "翻译器未初始化"}
        
        try:
            # 读取转录文件
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            # 设置当前正在翻译的视频ID，用于进度回调
            self._current_translating_video_id = video_id
            
            # 初始化翻译进度
            progress_key = f"{user_id}_{video_id}"
            self.translation_progress[progress_key] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": "准备翻译...",
                "timestamp": time.time()
            }
            
            # 执行翻译
            translated_transcript = self.translator.translate_transcript(transcript_data, target_lang)
            
            # 保存翻译结果到用户专属目录
            translated_path = user_paths.get_transcript_path(f"{video_id}_translated_{target_lang}")
            with open(translated_path, 'w', encoding='utf-8') as f:
                json.dump(translated_transcript, f, ensure_ascii=False, indent=2)
            
            # 更新翻译完成状态
            self.translation_progress[progress_key] = {
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
            progress_key = f"{user_id}_{video_id}"
            self.translation_progress[progress_key] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": f"翻译失败: {str(e)}",
                "timestamp": time.time()
            }
            return {"error": f"翻译失败: {str(e)}"}
    
    @require_user_login
    def translate_background(self, video_id: str, target_lang: str):
        """后台翻译处理（用户隔离版本）"""
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        # 检查转录文件是否存在
        transcript_path = user_paths.get_transcript_path(video_id)
        if not transcript_path.exists():
            return {"error": "转录文件不存在"}
        
        if not self.translator:
            return {"error": "翻译器未初始化"}
        
        try:
            # 读取转录文件
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            # 设置当前正在翻译的视频ID，用于进度回调
            self._current_translating_video_id = video_id
            
            # 初始化翻译进度
            progress_key = f"{user_id}_{video_id}"
            self.translation_progress[progress_key] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": "准备翻译...",
                "timestamp": time.time()
            }
            
            # 执行翻译
            translated_transcript = self.translator.translate_transcript(transcript_data, target_lang)
            
            # 保存翻译结果到用户专属目录
            translated_path = user_paths.get_transcript_path(f"{video_id}_translated_{target_lang}")
            with open(translated_path, 'w', encoding='utf-8') as f:
                json.dump(translated_transcript, f, ensure_ascii=False, indent=2)
            
            # 更新翻译完成状态
            self.translation_progress[progress_key] = {
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
            # 更新错误状态
            progress_key = f"{user_id}_{video_id}"
            self.translation_progress[progress_key] = {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": f"翻译失败: {str(e)}",
                "timestamp": time.time()
            }
            return {"error": f"翻译失败: {str(e)}"}
    
    @require_user_login
    def get_translation_progress(self, video_id: str):
        """获取翻译进度（用户隔离版本）"""
        user_id = get_current_user_id()
        if not user_id:
            return {
                "current": 0,
                "total": 0,
                "progress": 0.0,
                "message": "用户未登录",
                "timestamp": time.time()
            }
        
        progress_key = f"{user_id}_{video_id}"
        return self.translation_progress.get(progress_key, {
            "current": 0,
            "total": 0,
            "progress": 0.0,
            "message": "尚未开始翻译",
            "timestamp": time.time()
        })
    
    @require_user_login
    def get_translated_text(self, video_id: str, target_lang: str):
        """获取已翻译的文本（用户隔离版本）"""
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        # 检查翻译文件是否存在
        translated_path = user_paths.get_transcript_path(f"{video_id}_translated_{target_lang}")
        if not translated_path.exists():
            return {"error": "翻译文件不存在"}
        
        try:
            with open(translated_path, 'r', encoding='utf-8') as f:
                translated_data = json.load(f)
            
            return {
                "success": True,
                "translated_text": translated_data.get("text", ""),
                "segments": translated_data.get("segments", []),
                "metadata": translated_data.get("translation_metadata", {})
            }
        except Exception as e:
            return {"error": f"读取翻译文件失败: {str(e)}"}
    
    def _clear_user_data(self, user_id: str):
        """清除指定用户的翻译进度数据"""
        keys_to_remove = [key for key in self.translation_progress.keys() if key.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del self.translation_progress[key]
        print(f"✅ 已清除用户 {user_id} 的翻译进度数据")


# 全局翻译管理器实例
translator_manager = IsolatedTranslatorManager()


def get_translator_manager():
    """获取翻译管理器实例"""
    return translator_manager