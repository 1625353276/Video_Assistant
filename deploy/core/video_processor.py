#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理核心类
"""

import os
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

# 全局变量
processing_status = {}
video_data = {}


class VideoProcessor:
    """视频处理核心类"""
    
    def __init__(self, cuda_enabled=True, whisper_model="base"):
        """初始化视频处理器
        
        Args:
            cuda_enabled: 是否启用CUDA加速
            whisper_model: Whisper模型大小
        """
        # 尝试导入后端模块
        self._init_modules(cuda_enabled, whisper_model)
        
        # 创建必要的目录
        os.makedirs("data/uploads", exist_ok=True)
        os.makedirs("data/transcripts", exist_ok=True)
        os.makedirs("data/temp", exist_ok=True)
        os.makedirs("data/vectors", exist_ok=True)
    
    def _init_modules(self, cuda_enabled, whisper_model):
        """初始化模块"""
        try:
            from modules.video.video_loader import VideoLoader
            from modules.video.audio_extractor import AudioExtractor
            from modules.speech.whisper_asr import WhisperASR
            from modules.utils.file_manager import FileManager
            import torch
            
            self.video_loader = VideoLoader()
            self.audio_extractor = AudioExtractor()
            
            # 设置设备
            device = "cuda" if cuda_enabled and torch.cuda.is_available() else "cpu"
            self.whisper_asr = WhisperASR(model_size=whisper_model, device=device)
            self.file_manager = FileManager()
            
            self.mock_mode = False
            print("✓ 视频处理模块初始化成功")
            
        except ImportError as e:
            print(f"⚠ 视频处理模块导入失败，使用模拟模式: {e}")
            self._init_mock_modules()
    
    def _init_mock_modules(self):
        """初始化模拟模块"""
        self.mock_mode = True
        
        # 模拟类
        class VideoLoader:
            def validate_video(self, video_path):
                import os
                file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
                return {
                    "file_path": str(video_path),
                    "file_name": os.path.basename(video_path),
                    "file_size": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "format": os.path.splitext(video_path)[1],
                    "resolution": "1920x1080",
                    "width": 1920,
                    "height": 1080,
                    "fps": 30.0,
                    "frame_count": 9000,
                    "duration": 300.0,
                    "duration_formatted": "05:00",
                    "aspect_ratio": 1.78,
                    "validation_status": "passed"
                }
        
        class AudioExtractor:
            def extract_audio(self, video_path):
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "ai_video_assistant"
                temp_dir.mkdir(parents=True, exist_ok=True)
                audio_path = temp_dir / f"{Path(video_path).stem}_extracted.wav"
                audio_path.touch()
                return audio_path
        
        class WhisperASR:
            def __init__(self, model_size="base"):
                self.model_size = model_size
            
            def transcribe(self, audio_path):
                return {
                    "audio_file": str(audio_path),
                    "audio_file_name": Path(audio_path).name,
                    "language": "zh",
                    "language_probability": 0.9,
                    "text": "这是模拟的转录文本。在实际应用中，这里会是Whisper模型生成的真实转录结果。",
                    "segments": [
                        {
                            "id": 0,
                            "start": 0.0,
                            "end": 5.0,
                            "text": "这是第一段模拟转录文本。",
                            "confidence": 0.95,
                            "no_speech_prob": 0.01,
                            "words": []
                        },
                        {
                            "id": 1,
                            "start": 5.0,
                            "end": 10.0,
                            "text": "这是第二段模拟转录文本。",
                            "confidence": 0.93,
                            "no_speech_prob": 0.02,
                            "words": []
                        }
                    ],
                    "words": [],
                    "model_used": self.model_size,
                    "device_used": "cpu",
                    "total_duration": 10.0,
                    "avg_confidence": 0.94,
                    "speech_duration": 10.0,
                    "speech_ratio": 1.0
                }
        
        class FileManager:
            def save_transcript_json(self, transcript_data, output_path):
                import json
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            def save_transcript_text(self, transcript_data, output_path):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_data["text"])
        
        self.video_loader = VideoLoader()
        self.audio_extractor = AudioExtractor()
        self.whisper_asr = WhisperASR()
        self.file_manager = FileManager()
    
    def upload_and_process_video(self, video_file, user_id=None, cuda_enabled=True, whisper_model="base"):
        """
        上传视频并自动开始处理
        """
        if video_file is None:
            return {
                "status": "error",
                "message": "请选择视频文件"
            }
        
        try:
            # 生成唯一的视频ID
            video_path = Path(video_file)
            video_id = f"video_{int(time.time())}_{video_path.stem}"
            
            # 复制文件到上传目录
            upload_path = Path(f"data/uploads/{video_id}{video_path.suffix}")
            shutil.copy2(video_file, upload_path)
            
            # 验证视频
            video_info = self.video_loader.validate_video(upload_path)
            
            # 保存视频信息
            video_data[video_id] = {
                "video_id": video_id,
                "filename": video_path.name,
                "file_path": str(upload_path),
                "video_info": video_info,
                "status": "uploaded",
                "transcript": None,
                "assistant_config": {
                    "cuda_enabled": cuda_enabled,
                    "whisper_model": whisper_model
                },
                "upload_time": time.time()
            }
            
            # 开始处理
            processing_status[video_id] = {
                "progress": 0.0,
                "current_step": "开始处理...",
                "log_messages": [f"[{time.strftime('%H:%M:%S')}] 视频上传成功: {video_path.name}"],
                "status": "processing"
            }
            
            return {
                "video_id": video_id,
                "filename": video_path.name,
                "status": "processing",
                "message": "视频上传成功，开始处理..."
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"视频上传失败: {str(e)}"
            }
    
    def get_processing_progress(self, video_id):
        """
        获取视频处理进度
        """
        if video_id not in processing_status:
            return {
                "progress": 0.0,
                "current_step": "未找到处理任务",
                "log_messages": [],
                "status": "error"
            }
        
        # 如果还在处理中，继续处理
        if processing_status[video_id]["status"] == "processing":
            self._continue_processing(video_id)
        
        return processing_status[video_id]
    
    def _continue_processing(self, video_id, cuda_enabled=True, whisper_model="base"):
        """
        继续处理视频
        """
        if video_id not in video_data:
            return
        
        status = processing_status[video_id]
        video_info = video_data[video_id]
        
        try:
            progress = status["progress"]
            
            if progress < 0.2:
                # 提取音频
                status["current_step"] = "提取音频中..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 开始提取音频")
                status["progress"] = 0.2
                
                video_path = Path(video_info["file_path"])
                audio_path = self.audio_extractor.extract_audio(video_path)
                video_info["audio_path"] = str(audio_path)
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 音频提取完成")
                
            elif progress < 0.7:
                # 语音转文本
                status["current_step"] = "语音转文本中..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 开始语音转文本")
                status["progress"] = 0.7
                
                if "audio_path" in video_info:
                    audio_path = Path(video_info["audio_path"])
                    transcript_result = self.whisper_asr.transcribe(audio_path)
                    video_info["transcript"] = transcript_result
                    
                    # 保存转录结果
                    transcript_path = Path(f"data/transcripts/{video_id}_transcript.json")
                    self.file_manager.save_transcript_json(transcript_result, transcript_path)
                    
                    status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 语音转文本完成")
                    
                    # 清理临时音频文件
                    if audio_path.exists():
                        audio_path.unlink()
                        
            elif progress < 0.9:
                # 处理流程中的其他步骤
                status["current_step"] = "准备完成..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 处理即将完成")
                status["progress"] = 0.9
                    
            else:
                # 处理完成
                status["progress"] = 1.0
                status["current_step"] = "处理完成"
                status["status"] = "completed"
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 所有处理任务完成")
                video_info["status"] = "completed"
                
        except Exception as e:
            status["status"] = "error"
            status["current_step"] = f"处理失败: {str(e)}"
            status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 错误: {str(e)}")
    
    def get_video_info(self, video_id):
        """
        获取视频信息
        """
        if video_id not in video_data:
            return {"error": "视频不存在"}
        
        return video_data[video_id]
    
    def get_video_list(self, user_id=None):
        """
        获取视频列表
        """
        videos = []
        for video_id, info in video_data.items():
            if info["status"] == "completed":
                # 处理upload_time字段，如果不存在则使用当前时间
                upload_time = info.get("upload_time", time.time())
                videos.append({
                    "video_id": video_id,
                    "filename": info["filename"],
                    "thumbnail": "",  # 可以添加缩略图生成
                    "upload_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(upload_time)),
                    "config": info.get("assistant_config", {"cuda_enabled": True, "whisper_model": "base"})
                })
        
        return videos


# 全局处理器实例字典，支持不同配置
processors = {}
default_processor = VideoProcessor(cuda_enabled=True, whisper_model="base")


def get_processor(cuda_enabled=True, whisper_model="base"):
    """获取或创建指定配置的处理器实例"""
    key = f"{cuda_enabled}_{whisper_model}"
    if key not in processors:
        processors[key] = VideoProcessor(cuda_enabled=cuda_enabled, whisper_model=whisper_model)
    return processors[key]


def get_video_data():
    """获取全局视频数据"""
    return video_data


def get_processing_status():
    """获取全局处理状态"""
    return processing_status