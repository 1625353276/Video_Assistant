#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理器 - 用户隔离版本

支持用户专属的视频处理和文件管理
"""

import os
import sys
import time
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入用户上下文
from deploy.utils.user_context import get_current_user_id, get_current_user_paths, require_user_login

# 导入原有模块
try:
    from modules.video.video_loader import VideoLoader
    from modules.video.audio_extractor import AudioExtractor
    from modules.speech.whisper_asr import WhisperASR
    from modules.utils.file_manager import FileManager
    from modules.text.translator import TextTranslator
    from modules.retrieval.vector_store import VectorStore
    from modules.retrieval.bm25_retriever import BM25Retriever
    from modules.retrieval.hybrid_retriever import HybridRetriever
    from modules.qa.conversation_chain import ConversationChain
    print("✓ 所有模块导入成功")
except ImportError as e:
    print(f"⚠ 模块导入失败: {e}")


class IsolatedVideoProcessor:
    """用户隔离的视频处理器"""
    
    def __init__(self, cuda_enabled=True, whisper_model="base"):
        """初始化视频处理器
        
        Args:
            cuda_enabled: 是否启用CUDA加速
            whisper_model: Whisper模型大小
        """
        self.cuda_enabled = cuda_enabled
        self.whisper_model = whisper_model
        self.processing_status = {}  # 用户隔离的处理状态
        
        # 初始化核心组件
        self.video_loader = VideoLoader()
        self.audio_extractor = AudioExtractor()
        self.file_manager = FileManager()
        
        # 初始化翻译器和检索器
        self.translator = None
        self.vector_store = None
        self.bm25_retriever = None
        self.hybrid_retriever = None
        
        # 设置设备
        import torch
        device = "cuda" if cuda_enabled and torch.cuda.is_available() else "cpu"
        self.whisper_asr = WhisperASR(model_size=whisper_model, device=device)
        
        # 初始化可选组件
        self._init_optional_components()
    
    def _init_optional_components(self):
        """初始化可选组件"""
        try:
            self.translator = TextTranslator(
                default_method="deep-translator",
                progress_callback=self._on_translation_progress
            )
            print("✓ 翻译器初始化成功")
        except Exception as e:
            print(f"⚠ 翻译器初始化失败: {e}")
        
        try:
            self.vector_store = VectorStore(mirror_site="tuna")
            print("✓ 向量存储初始化成功")
        except Exception as e:
            print(f"⚠ 向量存储初始化失败: {e}")
        
        try:
            self.bm25_retriever = BM25Retriever(language='auto')
            print("✓ BM25检索器初始化成功")
        except Exception as e:
            print(f"⚠ BM25检索器初始化失败: {e}")
        
        if self.vector_store and self.bm25_retriever:
            try:
                self.hybrid_retriever = HybridRetriever(
                    vector_store=self.vector_store,
                    bm25_retriever=self.bm25_retriever,
                    vector_weight=0.6,
                    bm25_weight=0.4,
                    fusion_method="weighted_average"
                )
                print("✓ 混合检索器初始化成功")
            except Exception as e:
                print(f"⚠ 混合检索器初始化失败: {e}")
    
    @require_user_login
    def upload_and_process_video(self, video_file, cuda_enabled=True, whisper_model="base"):
        """
        上传视频并自动开始处理（用户隔离版本）
        """
        if video_file is None:
            return {
                "status": "error",
                "message": "请选择视频文件"
            }
        
        # 获取用户路径
        user_paths = get_current_user_paths()
        if not user_paths:
            return {
                "status": "error",
                "message": "用户未登录或路径获取失败"
            }
        
        try:
            # 生成唯一的视频ID（只使用时间戳+原始文件名）
            user_id = get_current_user_id()
            video_path = Path(video_file)
            video_id = f"{int(time.time())}_{video_path.stem}"
            
            # 使用用户专属的上传路径
            upload_path = user_paths.get_upload_path(video_id, video_path.name)
            
            # 确保目录存在
            upload_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件到用户专属目录
            shutil.copy2(video_file, upload_path)
            
            # 验证视频
            video_info = self.video_loader.validate_video(upload_path)
            
            # 初始化处理状态
            self.processing_status[video_id] = {
                "progress": 0.0,
                "current_step": "开始处理视频",
                "log_messages": [f"[{time.strftime('%H:%M:%S')}] 开始处理: {video_path.name}"],
                "status": "processing"
            }
            
            # 保存视频信息到用户专属位置
            video_data = {
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
                "upload_time": time.time(),
                "user_id": user_id
            }
            
            # 保存视频数据到用户隔离的存储中
            self._save_video_data(video_id, video_data)
            
            # 开始实际处理
            self._continue_processing(video_id, cuda_enabled, whisper_model)
            
            return {
                "video_id": video_id,
                "filename": video_path.name,
                "status": "processing",
                "message": "视频上传成功，开始处理...",
                "user_id": user_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"视频上传失败: {str(e)}"
            }
    
    @require_user_login
    def extract_audio(self, video_id, video_path):
        """提取音频（用户隔离版本）"""
        user_paths = get_current_user_paths()
        if not user_paths:
            raise ValueError("用户路径获取失败")
        
        # 使用用户专属的临时路径
        temp_audio_path = user_paths.get_temp_path(f"{video_id}_extracted.wav")
        
        # 提取音频
        audio_path = self.audio_extractor.extract_audio(Path(video_path))
        
        # 复制到用户专属目录
        shutil.copy2(audio_path, temp_audio_path)
        
        return temp_audio_path
    
    @require_user_login
    def save_transcript(self, video_id, transcript_result):
        """保存转录结果（用户隔离版本）"""
        user_paths = get_current_user_paths()
        if not user_paths:
            raise ValueError("用户路径获取失败")
        
        # 使用用户专属的转录路径
        transcript_path = user_paths.get_transcript_path(video_id)
        
        # 保存转录文件
        self.file_manager.save_transcript_json(transcript_result, transcript_path)
        
        return transcript_path
    
    @require_user_login
    def get_user_video_list(self):
        """获取用户的视频列表"""
        user_id = get_current_user_id()
        if not user_id:
            return []
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return []
        
        videos = []
        
        # 首先从用户数据目录中查找已处理的视频
        data_dir = user_paths.get_user_data_path()
        if data_dir.exists():
            for data_file in data_dir.glob("*_data.json"):
                try:
                    video_data = self._load_video_data(data_file.stem.replace("_data", ""))
                    if video_data and video_data.get("status") == "completed":
                        videos.append({
                            "video_id": video_data["video_id"],
                            "filename": video_data["filename"],
                            "file_path": video_data["file_path"],
                            "upload_time": video_data.get("upload_time", 0),
                            "user_id": user_id,
                            "status": video_data.get("status", "unknown"),
                            "has_transcript": bool(video_data.get("transcript"))
                        })
                except Exception as e:
                    print(f"加载视频数据失败 {data_file}: {e}")
                    continue
        
        # 然后从上传目录查找未处理的视频文件
        upload_dir = user_paths.get_upload_path()
        if upload_dir.exists():
            for video_file in upload_dir.iterdir():
                if video_file.is_file() and video_file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                    video_id = video_file.stem
                    
                    # 检查是否已经在列表中
                    if not any(v["video_id"] == video_id for v in videos):
                        videos.append({
                            "video_id": video_id,
                            "filename": video_file.name,
                            "file_path": str(video_file),
                            "upload_time": video_file.stat().st_mtime,
                            "user_id": user_id,
                            "status": "uploaded",
                            "has_transcript": False
                        })
        
        # 按上传时间排序（最新的在前）
        videos.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return videos
    
    @require_user_login
    def get_processing_progress(self, video_id):
        """
        获取视频处理进度
        """
        if video_id not in self.processing_status:
            return {
                "progress": 0.0,
                "current_step": "未找到处理任务",
                "log_messages": [],
                "status": "error"
            }
        
        # 如果还在处理中，继续处理
        if self.processing_status[video_id]["status"] == "processing":
            self._continue_processing(video_id)
        
        return self.processing_status[video_id]
    
    def _save_video_data(self, video_id, video_data):
        """保存视频数据到用户隔离的存储中"""
        user_paths = get_current_user_paths()
        if not user_paths:
            return
        
        # 保存到用户专属的数据文件
        data_file = user_paths.get_user_data_path() / f"{video_id}_data.json"
        data_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(video_data, f, ensure_ascii=False, indent=2)
    
    def _load_video_data(self, video_id):
        """从用户隔离的存储中加载视频数据"""
        user_paths = get_current_user_paths()
        if not user_paths:
            return None
        
        data_file = user_paths.get_user_data_path() / f"{video_id}_data.json"
        if not data_file.exists():
            return None
        
        import json
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _continue_processing(self, video_id, cuda_enabled=True, whisper_model="base"):
        """
        继续处理视频
        """
        video_data = self._load_video_data(video_id)
        if not video_data:
            return
        
        status = self.processing_status[video_id]
        
        try:
            progress = status["progress"]
            
            if progress < 0.2:
                # 提取音频
                status["current_step"] = "提取音频中..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 开始提取音频")
                status["progress"] = 0.2
                
                video_path = Path(video_data["file_path"])
                audio_path = self.extract_audio(video_id, str(video_path))
                video_data["audio_path"] = str(audio_path)
                self._save_video_data(video_id, video_data)
            
            if progress < 0.4:
                # 语音识别
                status["current_step"] = "语音识别中..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 开始语音识别")
                status["progress"] = 0.4
                
                if "audio_path" in video_data:
                    transcript_result = self.whisper_asr.transcribe(
                        Path(video_data["audio_path"])
                    )
                    video_data["transcript"] = transcript_result
                    self._save_video_data(video_id, video_data)
            
            if progress < 0.6:
                # 保存转录文件
                status["current_step"] = "保存转录文件..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 保存转录文件")
                status["progress"] = 0.6
                
                if "transcript" in video_data:
                    transcript_path = self.save_transcript(video_id, video_data["transcript"])
                    video_data["transcript_path"] = str(transcript_path)
                    self._save_video_data(video_id, video_data)
            
            if progress < 0.8:
                # 构建索引
                status["current_step"] = "构建检索索引..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 构建检索索引")
                status["progress"] = 0.8
                
                if "transcript" in video_data:
                    self._build_index(video_id, video_data)
            
            # 处理完成
            status["current_step"] = "处理完成"
            status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 视频处理完成")
            status["progress"] = 1.0
            status["status"] = "completed"
            video_data["status"] = "completed"
            self._save_video_data(video_id, video_data)
            
        except Exception as e:
            status["status"] = "error"
            status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 处理失败: {str(e)}")
            video_data["status"] = "error"
            video_data["error"] = str(e)
            self._save_video_data(video_id, video_data)
    
    def _build_index(self, video_id, video_data):
        """构建检索索引"""
        try:
            from deploy.core.index_builder_isolated import get_index_builder
            index_builder = get_index_builder()
            
            if "transcript" in video_data and video_data["transcript"]:
                index_builder.build_user_index(video_id, video_data["transcript"])
        except Exception as e:
            print(f"构建索引失败: {e}")
            # 索引构建失败不影响整体处理流程
    
    @require_user_login
    def get_video_info(self, video_id):
        """获取视频信息"""
        # 首先尝试从用户隔离的数据存储中加载
        video_data = self._load_video_data(video_id)
        if video_data:
            return video_data
        
        # 如果没有找到数据，尝试查找视频文件
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户未登录"}
        
        # 查找用户专属的视频文件
        videos_dir = user_paths.get_user_videos_dir()
        if not videos_dir.exists():
            return {"error": "视频目录不存在"}
        
        # 查找对应的视频文件
        for video_file in videos_dir.iterdir():
            if video_file.is_file():
                filename = video_file.stem
                if video_id in filename:  # 匹配包含video_id的文件
                    video_info = self.video_loader.validate_video(video_file)
                    return {
                        "video_id": video_id,
                        "filename": video_file.name,
                        "file_path": str(video_file),
                        "video_info": video_info,
                        "user_id": get_current_user_id()
                    }
        
        return {"error": "视频不存在"}
    
    def _on_translation_progress(self, current: int, total: int, message: str):
        """翻译进度回调函数"""
        # 可以添加用户特定的进度处理
        pass


# 全局处理器实例字典（支持不同配置）
processors = {}


def get_isolated_processor(cuda_enabled=True, whisper_model="base"):
    """获取用户隔离的处理器实例"""
    key = f"{cuda_enabled}_{whisper_model}"
    if key not in processors:
        processors[key] = IsolatedVideoProcessor(cuda_enabled=cuda_enabled, whisper_model=whisper_model)
    return processors[key]