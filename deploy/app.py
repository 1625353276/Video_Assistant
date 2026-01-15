#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频智能问答助手 - Web应用

整合了视频上传、处理、转录、问答等功能的完整Web应用
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import torch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr

os.environ['SSL_VERIFY'] = 'false'

# 尝试导入后端模块，如果失败则使用模拟模式
MOCK_MODE = False
import_error = None

try:
    from modules.video.video_loader import VideoLoader
    print("✓ VideoLoader 导入成功")
except ImportError as e:
    import_error = f"VideoLoader 导入失败: {e}"
    print(f"✗ {import_error}")
    MOCK_MODE = True

try:
    from modules.video.audio_extractor import AudioExtractor
    print("✓ AudioExtractor 导入成功")
except ImportError as e:
    import_error = f"AudioExtractor 导入失败: {e}"
    print(f"✗ {import_error}")
    MOCK_MODE = True

try:
    from modules.speech.whisper_asr import WhisperASR
    print("✓ WhisperASR 导入成功")
except ImportError as e:
    import_error = f"WhisperASR 导入失败: {e}"
    print(f"✗ {import_error}")
    MOCK_MODE = True

try:
    from modules.utils.file_manager import FileManager
    print("✓ FileManager 导入成功")
except ImportError as e:
    import_error = f"FileManager 导入失败: {e}"
    print(f"✗ {import_error}")
    MOCK_MODE = True

try:
    from modules.text.translator import TextTranslator
    print("✓ TextTranslator 导入成功")
except ImportError as e:
    print(f"✗ TextTranslator 导入失败: {e}")
    MOCK_MODE = True

try:
    from modules.retrieval.vector_store import VectorStore
    print("✓ VectorStore 导入成功")
except ImportError as e:
    print(f"✗ VectorStore 导入失败: {e}")
    MOCK_MODE = True

try:
    from modules.retrieval.bm25_retriever import BM25Retriever
    print("✓ BM25Retriever 导入成功")
except ImportError as e:
    print(f"✗ BM25Retriever 导入失败: {e}")
    MOCK_MODE = True

try:
    from modules.retrieval.hybrid_retriever import HybridRetriever
    print("✓ HybridRetriever 导入成功")
except ImportError as e:
    print(f"✗ HybridRetriever 导入失败: {e}")
    MOCK_MODE = True

try:
    from modules.utils.video_cleaner import register_video_cleanup, get_video_cleanup_info, cleanup_videos_now
    print("✓ VideoCleaner 导入成功")
    # 注册退出时清理视频文件
    register_video_cleanup()
    print("✓ 视频清理功能已启用，程序退出时将自动清理上传的视频文件")
except ImportError as e:
    print(f"✗ VideoCleaner 导入失败: {e}")
    register_video_cleanup = None
    get_video_cleanup_info = None
    cleanup_videos_now = None

if MOCK_MODE:
    print(f"\n警告：将在模拟模式下运行")
    print(f"错误原因：{import_error}")
    print("请安装缺失的依赖：pip install -r requirements.txt\n")
    
    # 模拟类 - 仅用于前端展示
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
            # 创建一个空的音频文件作为模拟
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


# 全局变量存储处理状态
processing_status = {}
video_data = {}


# 翻译进度回调函数
def update_translation_progress(video_id, current, total, message):
    """更新翻译进度"""
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


class VideoAssistant:
    """视频助手主类"""
    
    def __init__(self, cuda_enabled=True, whisper_model="base"):
        """初始化视频助手
        
        Args:
            cuda_enabled: 是否启用CUDA加速
            whisper_model: Whisper模型大小
        """
        self.video_loader = VideoLoader()
        self.audio_extractor = AudioExtractor()
        
        # 设置设备
        device = "cuda" if cuda_enabled and torch.cuda.is_available() else "cpu"
        self.whisper_asr = WhisperASR(model_size=whisper_model, device=device)
        self.file_manager = FileManager()
        
        # 翻译进度跟踪
        self.translation_progress = {}
        
        # 初始化翻译器和检索器
        if not MOCK_MODE:
            try:
                self.translator = TextTranslator(
                    default_method="deep-translator",
                    progress_callback=self._on_translation_progress
                )
                print("✓ 翻译器初始化成功（使用deep-translator）")
            except Exception as e:
                print(f"⚠ 翻译器初始化失败，使用模拟模式: {e}")
                self.translator = None
            
            try:
                self.vector_store = VectorStore(mirror_site="tuna")  # 使用清华镜像
                print("✓ 向量存储初始化成功")
            except Exception as e:
                print(f"⚠ 向量存储初始化失败，使用模拟模式: {e}")
                self.vector_store = None
            
            try:
                self.bm25_retriever = BM25Retriever(language='auto')
                print("✓ BM25检索器初始化成功")
            except Exception as e:
                print(f"⚠ BM25检索器初始化失败，使用模拟模式: {e}")
                self.bm25_retriever = None
            
            # 初始化混合检索器
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
                    print(f"⚠ 混合检索器初始化失败，使用模拟模式: {e}")
                    self.hybrid_retriever = None
            else:
                self.hybrid_retriever = None
        else:
            self.translator = None
            self.vector_store = None
            self.bm25_retriever = None
            self.hybrid_retriever = None
        
        # 创建必要的目录
        os.makedirs("data/uploads", exist_ok=True)
        os.makedirs("data/transcripts", exist_ok=True)
        os.makedirs("data/temp", exist_ok=True)
        os.makedirs("data/vectors", exist_ok=True)
        
        # 对话链管理
        self.conversation_chains = {}
    
    def _on_translation_progress(self, current: int, total: int, message: str):
        """翻译进度回调函数"""
        # 这里需要获取当前正在翻译的视频ID
        # 由于翻译器是全局的，我们需要从某个地方获取当前视频ID
        # 我们将在translate_transcript方法中设置当前视频ID
        if hasattr(self, '_current_translating_video_id'):
            video_id = self._current_translating_video_id
            update_translation_progress(video_id, current, total, message)
    
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
            import shutil
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
                videos.append({
                    "video_id": video_id,
                    "filename": info["filename"],
                    "thumbnail": "",  # 可以添加缩略图生成
                    "upload_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info["upload_time"])),
                    "config": info.get("assistant_config", {"cuda_enabled": True, "whisper_model": "base"})
                })
        
        return videos
    
    def _create_conversation_chain(self, video_id):
        """为视频创建对话链"""
        if not MOCK_MODE:
            try:
                # 导入对话链
                from modules.qa.conversation_chain import ConversationChain
                
                # 检查索引文件是否存在
                vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
                bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
                
                import os
                if not os.path.exists(vector_index_path) or not os.path.exists(bm25_index_path):
                    print(f"索引文件不存在，创建无检索器的对话链")
                    # 创建无检索器的对话链，仍然可以进行基本对话
                    return ConversationChain()
                
                # 创建检索器
                vector_store = VectorStore()
                vector_store.load_index(vector_index_path)
                
                bm25_retriever = BM25Retriever()
                bm25_retriever.load_index(bm25_index_path)
                
                hybrid_retriever = HybridRetriever(
                    vector_store=vector_store,
                    bm25_retriever=bm25_retriever
                )
                
                # 创建带检索器的对话链
                conversation_chain = ConversationChain(retriever=hybrid_retriever)
                
                # 设置转录内容
                transcript_file = f"data/transcripts/{video_id}_transcript.json"
                if os.path.exists(transcript_file):
                    import json
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                        if 'segments' in transcript_data:
                            conversation_chain.set_full_transcript(transcript_data['segments'])
                            print(f"已为视频 {video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
                            # 调试：验证转录内容是否设置成功
                            if hasattr(conversation_chain, 'full_transcript') and conversation_chain.full_transcript:
                                print(f"转录内容设置成功，第一段内容: {conversation_chain.full_transcript[0].get('text', '')[:50]}...")
                            else:
                                print("警告：转录内容设置失败！")
                        else:
                            print(f"警告：转录文件中没有segments字段，文件内容: {list(transcript_data.keys())}")
                else:
                    print(f"警告：转录文件不存在: {transcript_file}")
                
                return conversation_chain
            except Exception as e:
                print(f"创建对话链失败，使用基本对话链: {e}")
                # 即使检索器创建失败，也返回基本对话链
                try:
                    from modules.qa.conversation_chain import ConversationChain
                    conversation_chain = ConversationChain()
                    
                    # 设置转录内容
                    transcript_file = f"data/transcripts/{video_id}_transcript.json"
                    if os.path.exists(transcript_file):
                        import json
                        with open(transcript_file, 'r', encoding='utf-8') as f:
                            transcript_data = json.load(f)
                            if 'segments' in transcript_data:
                                conversation_chain.set_full_transcript(transcript_data['segments'])
                                print(f"已为视频 {video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
                                # 调试：验证转录内容是否设置成功
                                if hasattr(conversation_chain, 'full_transcript') and conversation_chain.full_transcript:
                                    print(f"转录内容设置成功，第一段内容: {conversation_chain.full_transcript[0].get('text', '')[:50]}...")
                                else:
                                    print("警告：转录内容设置失败！")
                            else:
                                print(f"警告：转录文件中没有segments字段，文件内容: {list(transcript_data.keys())}")
                    else:
                        print(f"警告：转录文件不存在: {transcript_file}")
                    
                    return conversation_chain
                except Exception as e2:
                    print(f"创建基本对话链也失败: {e2}")
                    return None
        return None
    
    def chat_with_video(self, video_id, question, chat_history, temperature=0.7):
        """
        基于视频内容进行问答
        """
        if video_id not in video_data:
            return "视频不存在", chat_history
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return "视频尚未处理完成，无法进行问答", chat_history
        
        # 获取或创建对话链
        if video_id not in self.conversation_chains:
            self.conversation_chains[video_id] = self._create_conversation_chain(video_id)
        
        conversation_chain = self.conversation_chains[video_id]
        
        if conversation_chain is None:
            return "对话链初始化失败，请重启应用或联系管理员", chat_history
        
        # 调试：检查转录内容是否存在
        if hasattr(conversation_chain, 'full_transcript') and conversation_chain.full_transcript:
            print(f"对话中：视频 {video_id} 有转录内容，共 {len(conversation_chain.full_transcript)} 个片段")
        else:
            print(f"对话中：视频 {video_id} 没有转录内容！")
        
        try:
            # 调用对话链
            result = conversation_chain.chat(question)
            
            # 检查是否有检索结果
            retrieved_docs = result.get('retrieved_docs', [])
            retrieved_count = len(retrieved_docs)
            
            # 确保检索文档格式一致（提取字段到顶层）
            for doc in retrieved_docs:
                if 'document' in doc and 'text' not in doc:
                    # 如果有document对象但没有顶层字段，提取常用字段
                    document = doc['document']
                    for key in ['text', 'start', 'end', 'confidence']:
                        if key in document:
                            doc[key] = document[key]
            
            if retrieved_count == 0:
                # 如果没有检索结果，可能是索引未构建
                response = result['response']
                if "未找到相关内容" not in response:
                    # 添加提示信息
                    response = f"{response}\n\n💡 提示：如需基于视频内容的精准回答，请先在'内容搜索'中点击'构建检索索引'按钮。"
            else:
                response = result['response']
            
            # 确保历史记录格式正确
            if not isinstance(chat_history, list):
                chat_history = []
            
            # 添加新消息到历史记录（使用字典格式）
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": response})
            
            return response, chat_history
        except Exception as e:
            return f"问答失败: {str(e)}", chat_history
    
    # 注意：问答功能在modules/qa/中未实现
    # 需要实现 modules/qa/conversation_chain.py 等模块
    
    def translate_transcript(self, video_id, target_lang):
        """
        翻译转录文本
        """
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
    
    def build_vector_index(self, video_id):
        """
        为视频内容构建向量索引和BM25索引
        """
        if video_id not in video_data:
            return {"error": "视频不存在"}
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return {"error": "视频尚未处理完成"}
        
        if not self.vector_store or not self.bm25_retriever:
            return {"error": "检索器未初始化"}
        
        try:
            transcript = video_info["transcript"]
            
            # 准备文档数据
            documents = []
            for segment in transcript.get("segments", []):
                doc = {
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "video_id": video_id
                }
                documents.append(doc)
            
            # 构建向量索引
            self.vector_store.clear()
            self.vector_store.add_documents(documents, text_field="text")
            vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
            self.vector_store.save_index(vector_index_path)
            
            # 构建BM25索引
            self.bm25_retriever.clear()
            self.bm25_retriever.add_documents(documents, text_field="text")
            bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
            self.bm25_retriever.save_index(bm25_index_path)
            
            # 如果有混合检索器，也添加文档
            if self.hybrid_retriever:
                self.hybrid_retriever.clear()
                self.hybrid_retriever.add_documents(documents, text_field="text")
                hybrid_index_path = f"data/vectors/{video_id}_hybrid_index.pkl"
                self.hybrid_retriever.save_indexes(vector_index_path, bm25_index_path)
            
            video_info["vector_index_built"] = True
            video_info["vector_index_path"] = vector_index_path
            video_info["bm25_index_path"] = bm25_index_path
            
            return {
                "success": True,
                "document_count": len(documents),
                "vector_stats": self.vector_store.get_stats(),
                "bm25_stats": self.bm25_retriever.get_stats(),
                "message": f"成功构建向量索引和BM25索引，包含 {len(documents)} 个文档片段"
            }
        except Exception as e:
            return {"error": f"构建索引失败: {str(e)}"}
    
    def search_in_video(self, video_id, query, max_results=5, threshold=0.3, search_type="hybrid"):
        """
        搜索视频内容
        
        Args:
            video_id: 视频ID
            query: 搜索查询
            max_results: 最大结果数
            threshold: 相关性阈值
            search_type: 搜索类型 ("vector", "bm25", "hybrid")
        """
        if video_id not in video_data:
            return []
        
        video_info = video_data[video_id]
        
        if not video_info.get("vector_index_built"):
            # 如果没有构建索引，先尝试构建
            if video_info.get("transcript"):
                self.build_vector_index(video_id)
            else:
                return [{"text": "视频尚未处理完成，无法搜索", "timestamp": 0.0, "score": 0.0, "type": "error"}]
        
        try:
            results = []
            
            # 根据搜索类型执行不同的搜索
            if search_type == "vector" and self.vector_store:
                # 向量搜索
                vector_results = self.vector_store.search(query, top_k=max_results, threshold=threshold)
                for result in vector_results:
                    doc = result["document"]
                    results.append({
                        "text": doc["text"],
                        "timestamp": doc["start"],
                        "score": round(result["similarity"], 3),
                        "end": doc["end"],
                        "type": "vector",
                        "similarity": round(result["similarity"], 3)
                    })
            
            elif search_type == "bm25" and self.bm25_retriever:
                # BM25搜索
                bm25_results = self.bm25_retriever.search(query, top_k=max_results, threshold=threshold)
                for result in bm25_results:
                    doc = result["document"]
                    results.append({
                        "text": doc["text"],
                        "timestamp": doc["start"],
                        "score": round(result["score"], 3),
                        "end": doc["end"],
                        "type": "bm25",
                        "bm25_score": round(result["score"], 3)
                    })
            
            elif search_type == "hybrid" and self.hybrid_retriever:
                # 混合搜索
                hybrid_results = self.hybrid_retriever.search(query, top_k=max_results, threshold=threshold)
                for result in hybrid_results:
                    doc = result["document"]
                    results.append({
                        "text": doc["text"],
                        "timestamp": doc["start"],
                        "score": round(result["score"], 3),
                        "end": doc["end"],
                        "type": "hybrid",
                        "vector_score": round(result.get("vector_score", 0), 3),
                        "bm25_score": round(result.get("bm25_score", 0), 3)
                    })
            
            else:
                return [{"text": f"检索器未初始化或不支持搜索类型: {search_type}", "timestamp": 0.0, "score": 0.0, "type": "error"}]
            
            return results
            
        except Exception as e:
            return [{"text": f"搜索失败: {str(e)}", "timestamp": 0.0, "score": 0.0, "type": "error"}]
    
    def build_index_background(self, video_id):
        """后台构建向量索引"""
        if video_id not in video_data:
            return {"error": "视频不存在"}
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return {"error": "视频尚未处理完成"}
        
        if not self.vector_store or not self.bm25_retriever:
            return {"error": "检索器未初始化"}
        
        try:
            transcript = video_info["transcript"]
            
            # 准备文档数据
            documents = []
            for segment in transcript.get("segments", []):
                doc = {
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "video_id": video_id
                }
                documents.append(doc)
            
            # 构建向量索引
            self.vector_store.clear()
            self.vector_store.add_documents(documents, text_field="text")
            vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
            self.vector_store.save_index(vector_index_path)
            
            # 构建BM25索引
            self.bm25_retriever.clear()
            self.bm25_retriever.add_documents(documents, text_field="text")
            bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
            self.bm25_retriever.save_index(bm25_index_path)
            
            # 如果有混合检索器，也添加文档
            if self.hybrid_retriever:
                self.hybrid_retriever.clear()
                self.hybrid_retriever.add_documents(documents, text_field="text")
                hybrid_index_path = f"data/vectors/{video_id}_hybrid_index.pkl"
                self.hybrid_retriever.save_indexes(vector_index_path, bm25_index_path)
            
            video_info["vector_index_built"] = True
            video_info["vector_index_path"] = vector_index_path
            video_info["bm25_index_path"] = bm25_index_path
            video_info["index_building"] = False
            
            return {
                "success": True,
                "document_count": len(documents),
                "vector_stats": self.vector_store.get_stats(),
                "bm25_stats": self.bm25_retriever.get_stats(),
                "message": f"成功构建向量索引和BM25索引，包含 {len(documents)} 个文档片段"
            }
        except Exception as e:
            video_info["index_building"] = False
            return {"error": f"构建索引失败: {str(e)}"}
    
    def get_translation_progress(self, video_id):
        """获取翻译进度"""
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
    
    def translate_background(self, video_id, target_lang):
        """后台翻译处理"""
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
    
    def get_conversation_stats(self, video_id):
        """获取对话统计信息"""
        if video_id in self.conversation_chains:
            return self.conversation_chains[video_id].get_stats()
        return {}
    
    def clear_conversation(self, video_id):
        """清除指定视频的对话历史"""
        if video_id in self.conversation_chains:
            self.conversation_chains[video_id].clear_history()
            return True
        return False
    
    def get_conversation_history(self, video_id):
        """获取对话历史"""
        if video_id in self.conversation_chains:
            return self.conversation_chains[video_id].get_conversation_history()
        return []


# 全局助手实例字典，支持不同配置
assistants = {}
default_assistant = VideoAssistant(cuda_enabled=True, whisper_model="base")

def get_assistant(cuda_enabled=True, whisper_model="base"):
    """获取或创建指定配置的助手实例"""
    key = f"{cuda_enabled}_{whisper_model}"
    if key not in assistants:
        assistants[key] = VideoAssistant(cuda_enabled=cuda_enabled, whisper_model=whisper_model)
    return assistants[key]


# Gradio界面函数
def create_video_qa_interface():
    """创建视频问答界面"""
    
    # 处理视频上传
    def handle_upload(video_file, cuda_enabled, whisper_model):
        # 获取指定配置的助手
        current_assistant = get_assistant(cuda_enabled, whisper_model)
        result = current_assistant.upload_and_process_video(video_file)
        
        if result["status"] == "error":
            return (
                gr.Warning(result["message"]),
                gr.Video(visible=False),
                gr.JSON(visible=False),
                gr.Textbox(visible=False),
                gr.Row(visible=False),
                gr.Textbox(visible=False),
                gr.Textbox(visible=False),  # 转录文本
                gr.Button(visible=False),  # 翻译按钮
                gr.Dropdown(visible=False),  # 语言选择
                gr.Textbox(visible=False),  # 翻译结果
                gr.HTML(visible=False)  # 翻译进度条
            )
        
        return (
            gr.Textbox(value=result["message"], visible=True),
            gr.Video(value=video_file, visible=True),
            gr.JSON(value={"video_id": result["video_id"], "filename": result["filename"]}, visible=True),
            gr.Textbox(value="正在处理视频...", visible=True),
            gr.Row(visible=True),  # 显示处理日志区域
            gr.Textbox(value=f"[{time.strftime('%H:%M:%S')}] 开始处理: {result['filename']}", visible=True),
            gr.HTML(value=f"<div style='width:100%; background-color:#e6f3ff; border-radius:5px; padding:5px; text-align:center;'>处理进度: 0%</div>", visible=True),
            gr.Textbox(visible=False),  # 隐藏转录文本
            gr.Button(visible=False),  # 隐藏翻译按钮
            gr.Dropdown(visible=False),  # 隐藏语言选择
            gr.Textbox(visible=False),  # 隐藏翻译结果
            gr.HTML(visible=False)  # 隐藏翻译进度条
        )
    
    # 更新处理进度
    def update_progress(video_info):
        if not video_info or "video_id" not in video_info:
            return (
                "", 
                gr.Textbox(visible=False), 
                gr.Button(visible=False), 
                gr.Dropdown(visible=False), 
                gr.Textbox(visible=False),  # 翻译结果区域
                gr.Textbox(visible=False),
                gr.Textbox(value="等待上传视频...", visible=True),
                gr.HTML(value="<div style='width:100%; background-color:#f0f0f0; border-radius:5px; padding:5px; text-align:center;'>等待处理...</div>", visible=False),
                gr.HTML(visible=False),  # 翻译进度条
                gr.Textbox(visible=False)  # 索引状态
            )
        
        video_id = video_info["video_id"]
        # 获取当前视频使用的助手配置
        if video_id in globals()['video_data'] and "assistant_config" in globals()['video_data'][video_id]:
            config = globals()['video_data'][video_id]["assistant_config"]
            current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
        else:
            current_assistant = default_assistant
        
        progress_info = current_assistant.get_processing_progress(video_id)
        
        log_text = "\n".join(progress_info["log_messages"])
        progress_percent = int(progress_info["progress"] * 100)
        
        if progress_info["status"] == "completed":
            # 处理完成，更新转录显示
            video_info_data = current_assistant.get_video_info(video_id)
            transcript = video_info_data.get("transcript", {}).get("text", "")
            
            # 自动构建索引
            index_status, _ = auto_build_index(f"{video_id}: {video_info_data.get('filename', 'Unknown')}")
            
            return (
                log_text,
                gr.Textbox(value=transcript, visible=True),
                gr.Button(visible=True),  # 显示翻译按钮
                gr.Dropdown(visible=True),  # 显示语言选择
                gr.Textbox(visible=True),  # 显示翻译结果区域
                gr.Textbox(value="✅ 处理完成！现在可以进行翻译和内容搜索", visible=True),
                gr.HTML(value=f"<div style='width:100%; background-color:#d4edda; border-radius:5px; padding:5px; text-align:center;'>✅ 处理完成！</div>", visible=True),
                gr.HTML(visible=False),  # 隐藏翻译进度条
                gr.Textbox(value=index_status, visible=True)  # 显示索引状态
            )
        
        return (
            log_text,
            gr.Textbox(visible=False),
            gr.Button(visible=False),
            gr.Dropdown(visible=False),
            gr.Textbox(visible=False),  # 翻译结果区域
            gr.Textbox(visible=False),
            gr.Textbox(value=f"⏳ {progress_info['current_step']} ({progress_percent}%)", visible=True),
            gr.HTML(value=f"<div style='width:100%; background-color:#e6f3ff; border-radius:5px; padding:5px; text-align:center;'>⏳ {progress_info['current_step']} ({progress_percent}%)</div>", visible=True),
            gr.HTML(visible=False),  # 隐藏翻译进度条
            gr.Textbox(visible=False)  # 索引状态
        )
    
    # 处理问答
    def handle_question(question, history, video_selector):
        if not question.strip():
            return "", history
        
        if not video_selector:
            # 添加错误消息到历史记录
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": "请先选择一个视频"})
            return "", history
        
        video_id = video_selector.split(":")[0].strip()  # 假设格式为 "video_id: filename"
        
        # 获取当前视频使用的助手配置
        if video_id in globals()['video_data'] and "assistant_config" in globals()['video_data'][video_id]:
            config = globals()['video_data'][video_id]["assistant_config"]
            current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
        else:
            current_assistant = default_assistant
        
        # 调用对话功能
        answer, updated_history = current_assistant.chat_with_video(video_id, question, history)
        
        # 确保历史记录格式正确
        if not isinstance(updated_history, list):
            updated_history = []
        
        # 如果历史记录是元组格式，转换为字典格式
        if updated_history and isinstance(updated_history[0], tuple):
            formatted_history = []
            for user_msg, assistant_msg in updated_history:
                formatted_history.append({"role": "user", "content": user_msg})
                formatted_history.append({"role": "assistant", "content": assistant_msg})
            updated_history = formatted_history
        
        return "", updated_history
    
    # 处理搜索
    def handle_search(query, video_selector, search_type="hybrid"):
        if not query.strip() or not video_selector:
            return []
        
        video_id = video_selector.split(":")[0].strip()
        
        # 获取当前视频使用的助手配置
        if video_id in globals()['video_data'] and "assistant_config" in globals()['video_data'][video_id]:
            config = globals()['video_data'][video_id]["assistant_config"]
            current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
        else:
            current_assistant = default_assistant
        
        results = current_assistant.search_in_video(video_id, query, search_type=search_type)
        
        formatted_results = []
        for r in results:
            if r["type"] == "vector":
                formatted = f"[{r['timestamp']:.2f}s] [向量相似度: {r['score']:.3f}] {r['text']}"
            elif r["type"] == "bm25":
                formatted = f"[{r['timestamp']:.2f}s] [BM25分数: {r['score']:.3f}] {r['text']}"
            elif r["type"] == "hybrid":
                formatted = f"[{r['timestamp']:.2f}s] [混合分数: {r['score']:.3f}] [向量: {r.get('vector_score', 0):.3f}] [BM25: {r.get('bm25_score', 0):.3f}] {r['text']}"
            else:
                formatted = f"[错误] {r['text']}"
            
            formatted_results.append(formatted)
        
        return formatted_results
    
    # 处理翻译
    def handle_translate(video_info, target_lang):
        if not video_info or "video_id" not in video_info:
            return "请先上传并处理视频", gr.Textbox(visible=False), gr.HTML(visible=False), gr.HTML(visible=False)
        
        video_id = video_info["video_id"]
        
        # 检查视频是否存在
        if video_id not in globals()['video_data']:
            return "视频不存在", gr.Textbox(visible=False), gr.HTML(visible=False), gr.HTML(visible=False)
        
        # 获取当前视频使用的助手配置
        if "assistant_config" in globals()['video_data'][video_id]:
            config = globals()['video_data'][video_id]["assistant_config"]
            current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
        else:
            current_assistant = default_assistant
        
        # 检查转录是否完成
        if not video_data[video_id].get("transcript"):
            return "视频尚未转录完成，无法翻译", gr.Textbox(visible=False), gr.HTML(visible=False), gr.HTML(visible=False)
        
        # 设置翻译状态
        video_data[video_id]["translating"] = True
        
        # 实际执行翻译
        try:
            result = current_assistant.translate_transcript(video_id, target_lang)
            
            if "error" in result:
                video_data[video_id]["translating"] = False
                return result["error"], gr.Textbox(visible=False), gr.HTML(visible=False), gr.HTML(visible=False)
            
            # 翻译成功
            translated_text = result.get("translated_text", "")
            video_data[video_id]["translating"] = False
            return (
                "✅ 翻译完成", 
                gr.Textbox(value=translated_text, visible=True),
                gr.HTML(value="<div style='width:100%; background-color:#d4edda; border-radius:5px; padding:5px; text-align:center;'>✅ 翻译完成</div>", visible=True),
                gr.HTML(visible=False)  # 隐藏进度条
            )
            
        except Exception as e:
            video_data[video_id]["translating"] = False
            return f"翻译失败: {str(e)}", gr.Textbox(visible=False), gr.HTML(visible=False), gr.HTML(visible=False)
    
    # 更新翻译进度
    def update_translation_progress(video_info):
        if not video_info or "video_id" not in video_info:
            return gr.HTML(visible=False)
        
        video_id = video_info["video_id"]
        
        # 检查是否正在翻译
        if video_id not in globals()['video_data'] or not globals()['video_data'][video_id].get("translating", False):
            return gr.HTML(visible=False)
        
        # 获取当前视频使用的助手配置
        if video_id in globals()['video_data'] and "assistant_config" in globals()['video_data'][video_id]:
            config = globals()['video_data'][video_id]["assistant_config"]
            current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
        else:
            current_assistant = default_assistant
        
        # 获取翻译进度
        progress_info = current_assistant.get_translation_progress(video_id)
        progress_percent = int(progress_info["progress"] * 100)
        message = progress_info["message"]
        
        # 构建进度条HTML
        progress_html = f"""
        <div style='width:100%; background-color:#f8f9fa; border-radius:5px; padding:10px; margin:10px 0;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                <span>翻译进度</span>
                <span>{progress_percent}%</span>
            </div>
            <div style='width:100%; background-color:#e9ecef; border-radius:3px; overflow: hidden;'>
                <div style='width:{progress_percent}%; background-color:#007bff; height:20px; transition: width 0.3s;'></div>
            </div>
            <div style='margin-top: 5px; font-size: 12px; color:#6c757d;'>
                {message}
            </div>
        </div>
        """
        
        return gr.HTML(value=progress_html, visible=True)
    
    # 构建向量索引
    def handle_build_index(video_selector):
        if not video_selector:
            return "请先选择视频", gr.Textbox(visible=False), gr.HTML(visible=False)
        
        video_id = video_selector.split(":")[0].strip()
        
        # 检查视频是否存在
        if video_id not in globals()['video_data']:
            return "视频不存在", gr.Textbox(visible=False), gr.HTML(visible=False)
        
        # 检查转录是否完成
        if not globals()['video_data'][video_id].get("transcript"):
            return "视频尚未转录完成，无法构建索引", gr.Textbox(visible=False), gr.HTML(visible=False)
        
        # 获取当前视频使用的助手配置
        if video_id in globals()['video_data'] and "assistant_config" in globals()['video_data'][video_id]:
            config = globals()['video_data'][video_id]["assistant_config"]
            current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
        else:
            current_assistant = default_assistant
        
        # 设置构建状态
        globals()['video_data'][video_id]["index_building"] = True

        # 实际执行构建索引
        try:
            result = current_assistant.build_index_background(video_id)
            if "error" in result:
                globals()['video_data'][video_id]["index_building"] = False
                return f"构建失败: {result['error']}", gr.Textbox(visible=False), gr.HTML(visible=False)
            else:
                globals()['video_data'][video_id]["index_building"] = False
                return result.get("message", "索引构建完成"), gr.Textbox(visible=False), gr.HTML(value=f"<div style='width:100%; background-color:#d4edda; border-radius:5px; padding:5px; text-align:center;'>✅ {result.get('message', '索引构建完成')}</div>", visible=True)
        except Exception as e:
            globals()['video_data'][video_id]["index_building"] = False
            return f"构建失败: {str(e)}", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 开始新对话
    def start_new_chat(video_selector):
        """开始新对话"""
        if video_selector:
            video_id = video_selector.split(":")[0].strip()
            
            # 获取当前视频使用的助手配置
            if video_id in globals()['video_data'] and "assistant_config" in globals()['video_data'][video_id]:
                config = globals()['video_data'][video_id]["assistant_config"]
                current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
            else:
                current_assistant = default_assistant
            
            current_assistant.clear_conversation(video_id)
        return [], ""
    
    # 自动构建索引函数
    def auto_build_index(video_selector):
        """自动为选中的视频构建索引"""
        if not video_selector:
            return "", gr.HTML(visible=False)
        
        video_id = video_selector.split(":")[0].strip()
        
        # 检查视频是否存在
        if video_id not in globals()['video_data']:
            return "", gr.HTML(visible=False)
        
        # 检查转录是否完成
        if not globals()['video_data'][video_id].get("transcript"):
            return "", gr.HTML(visible=False)
        
        # 检查索引是否已经构建
        if globals()['video_data'][video_id].get("vector_index_built", False):
            return "索引已存在", gr.HTML(visible=False)
        
        # 设置构建状态
        globals()['video_data'][video_id]["index_building"] = True
        
        # 获取当前视频使用的助手配置
        if video_id in video_data and "assistant_config" in video_data[video_id]:
            config = video_data[video_id]["assistant_config"]
            current_assistant = get_assistant(config["cuda_enabled"], config["whisper_model"])
        else:
            current_assistant = default_assistant
        
        # 实际执行构建索引
        try:
            result = current_assistant.build_index_background(video_id)
            if "error" in result:
                video_data[video_id]["index_building"] = False
                return f"构建失败: {result['error']}", gr.HTML(visible=False)
            else:
                globals()['video_data'][video_id]["index_building"] = False
                return result.get("message", "索引构建完成"), gr.HTML(visible=False)
        except Exception as e:
            globals()['video_data'][video_id]["index_building"] = False
            return f"构建失败: {str(e)}", gr.HTML(visible=False)
    
    # 更新视频选择器
    def update_video_selector():
        videos = default_assistant.get_video_list()
        choices = [f"{v['video_id']}: {v['filename']}" for v in videos]
        return gr.Dropdown(choices=choices, value=choices[0] if choices else None)
    
    # 创建界面
    with gr.Blocks(title="视频智能问答助手", css="""
    .scrollable-textbox textarea {
        overflow-y: scroll !important;
        max-height: 300px !important;
    }
    """) as demo:
        gr.Markdown("# 🎥 视频智能问答助手")
        gr.Markdown("上传视频，进行智能问答")
        
        with gr.Tabs():
            # 视频上传和管理标签页
            with gr.TabItem("视频管理"):
                upload_status = gr.Textbox(label="上传状态", visible=False)

                with gr.Row():
                    with gr.Column(scale=1):
                        video_input = gr.File(
                            label="上传视频",
                            file_types=[".mp4", ".avi", ".mov", ".mkv"],
                            type="filepath"
                        )
                        
                        # 处理选项
                        with gr.Accordion("处理选项", open=True):
                            cuda_enabled = gr.Checkbox(
                                label="启用CUDA加速（如果可用）",
                                value=True,
                                info="使用GPU加速处理，需要NVIDIA显卡和支持CUDA"
                            )
                            
                            whisper_model = gr.Dropdown(
                                choices=[
                                    ("tiny (75MB, 最快)", "tiny"),
                                    ("base (142MB, 平衡)", "base"),
                                    ("small (466MB, 较准确)", "small"),
                                    ("medium (1.5GB, 很准确)", "medium"),
                                    ("large (2.9GB, 最准确)", "large")
                                ],
                                value="base",
                                label="Whisper模型选择",
                                info="更大的模型更准确但需要更多时间和资源"
                            )
                        
                        upload_btn = gr.Button("上传并处理视频", variant="primary")

                        # 处理日志和进度 - 移动到上传列
                        progress_html = gr.HTML(
                            value="<div style='width:100%; background-color:#f0f0f0; border-radius:5px; padding:5px; text-align:center;'>等待处理...</div>",
                            visible=False
                        )
                        processing_log = gr.Textbox(
                            label="处理日志",
                            lines=10,
                            interactive=False,
                            max_lines=25,
                            show_label=True,
                            visible=False
                        )

                    with gr.Column(scale=2):
                        video_player = gr.Video(label="视频预览", visible=False)
                        video_info = gr.JSON(label="视频信息", visible=False)
                        processing_status = gr.Textbox(label="处理状态", visible=False)
                
                # 视频内容展示
                with gr.Accordion("视频内容分析", open=False):
                    transcript_display = gr.Textbox(
                        label="转录文本",
                        lines=10,
                        interactive=False,
                        visible=False,
                        max_lines=30,
                        elem_classes="scrollable-textbox"
                    )
                    
                    # 翻译功能
                    with gr.Row():
                        translate_btn = gr.Button("翻译文本", variant="secondary", visible=False)
                        target_lang = gr.Dropdown(
                            choices=["请选择语言", "English", "中文"],  # 第一个选项是提示
                            value="请选择语言",  # 默认显示提示
                            label="",  # 去掉标签
                            show_label=False,
                            visible=False
                        )
                    
                    translated_display = gr.Textbox(
                        label="翻译结果",
                        lines=10,
                        interactive=False,
                        visible=False,
                        max_lines=30,
                        elem_classes="scrollable-textbox"
                    )
                    
                    # 翻译进度
                    translate_progress_html = gr.HTML(
                        value="<div style='width:100%; background-color:#f0f0f0; border-radius:5px; padding:5px; text-align:center;'>等待翻译...</div>",
                        visible=False
                    )
                    
                    # 翻译进度条
                    translate_progress_bar = gr.HTML(
                        visible=False
                    )
                    

            
            # 智能问答标签页
            with gr.TabItem("智能问答"):
                with gr.Row():
                    with gr.Column(scale=1):
                        # 视频选择
                        video_selector = gr.Dropdown(
                            label="选择视频",
                            choices=[],
                            interactive=True
                        )
                        refresh_btn = gr.Button("刷新视频列表", size="sm")
                        
                        # 搜索功能
                        with gr.Accordion("内容搜索", open=False):
                            # 索引状态（隐藏）
                            index_status = gr.Textbox(label="索引状态", interactive=False, lines=2, visible=False)
                            index_progress_html = gr.HTML(
                        value="<div style='width:100%; background-color:#f0f0f0; border-radius:5px; padding:5px; text-align:center;'>等待构建索引...</div>",
                        visible=False
                    )
                            
                            # 搜索类型选择
                            search_type = gr.Radio(
                                choices=[
                                    ("混合检索 (推荐)", "hybrid"),
                                    ("向量检索", "vector"),
                                    ("关键词检索 (BM25)", "bm25")
                                ],
                                value="hybrid",
                                label="搜索类型",
                                info="混合检索结合了语义相似度和关键词匹配"
                            )
                            
                            # 搜索功能
                            search_query = gr.Textbox(label="搜索内容")
                            search_btn = gr.Button("搜索")
                            search_results = gr.List(label="搜索结果")
                        
                        # 新对话按钮
                        new_chat_btn = gr.Button("开始新对话", variant="secondary")
                    
                    with gr.Column(scale=2):
                        # 聊天界面
                        chatbot = gr.Chatbot(
                            label="对话记录",
                            height=500
                        )
                        
                        with gr.Row():
                            question_input = gr.Textbox(
                                label="输入问题",
                                placeholder="请输入关于视频的问题...",
                                lines=2,
                                scale=4
                            )
                            send_btn = gr.Button("发送", variant="primary", scale=1)
                        
                        # 快捷问题建议
                        with gr.Accordion("快捷问题", open=False):
                            quick_questions = [
                                "这个视频的主要内容是什么？",
                                "视频中提到了哪些关键点？",
                                "能总结一下视频的核心观点吗？",
                                "视频中的结论是什么？"
                            ]
                            
                            for i, question in enumerate(quick_questions):
                                gr.Button(question, size="sm").click(
                                    lambda q=question: q,
                                    outputs=question_input
                                )
        
        # 事件绑定
        upload_btn.click(
            handle_upload,
            inputs=[video_input, cuda_enabled, whisper_model],
            outputs=[upload_status, video_player, video_info, processing_status, processing_log, progress_html, transcript_display, translate_btn, target_lang, translated_display, translate_progress_bar]
        )
        
        # 定时更新处理进度 - 使用Timer组件替代
        progress_timer = gr.Timer(2)  # 每2秒触发一次
        progress_timer.tick(
            update_progress,
            inputs=[video_info],
            outputs=[processing_log, transcript_display, translate_btn, target_lang, translated_display, processing_status, progress_html, translate_progress_bar, index_status]
        )
        
        # 定时检查翻译和索引构建进度
        def check_background_tasks(video_info):
            if not video_info or "video_id" not in video_info:
                return gr.HTML(visible=False), gr.HTML(visible=False)
            
            video_id = video_info["video_id"]
            
            # 检查翻译进度
            if video_id in video_data and video_data[video_id].get("translating", False):
                # 模拟翻译进度
                return gr.HTML(value="<div style='width:100%; background-color:#fff3cd; border-radius:5px; padding:5px; text-align:center;'>⏳ 正在翻译...</div>", visible=True), gr.HTML(visible=False)
            
            # 检查索引构建进度
            if video_id in video_data and video_data[video_id].get("index_building", False):
                # 模拟索引构建进度
                return gr.HTML(visible=False), gr.HTML(value="<div style='width:100%; background-color:#fff3cd; border-radius:5px; padding:5px; text-align:center;'>⏳ 正在构建索引...</div>", visible=True)
            
            return gr.HTML(visible=False), gr.HTML(visible=False)
        
        # 添加后台任务检查定时器
        background_timer = gr.Timer(3)  # 每3秒检查一次
        background_timer.tick(
            check_background_tasks,
            inputs=[video_info],
            outputs=[translate_progress_html, index_progress_html]
        )
        
        # 问答事件
        send_btn.click(
            handle_question,
            inputs=[question_input, chatbot, video_selector],
            outputs=[question_input, chatbot]
        )
        
        question_input.submit(
            handle_question,
            inputs=[question_input, chatbot, video_selector],
            outputs=[question_input, chatbot]
        )
        
        # 搜索事件
        search_btn.click(
            handle_search,
            inputs=[search_query, video_selector, search_type],
            outputs=[search_results]
        )
        
        # 翻译事件
        translate_btn.click(
            handle_translate,
            inputs=[video_info, target_lang],
            outputs=[processing_status, translated_display, translate_progress_html, translate_progress_bar]
        )
        
        # 添加翻译进度更新定时器
        translation_progress_timer = gr.Timer(1)  # 每1秒更新一次
        translation_progress_timer.tick(
            update_translation_progress,
            inputs=[video_info],
            outputs=[translate_progress_bar]
        )
        
        # 构建向量索引事件已移除，改为自动构建
        
        # 新对话事件
        new_chat_btn.click(
            start_new_chat,
            inputs=[video_selector],
            outputs=[chatbot, question_input]
        )
        
        # 刷新视频列表
        def refresh_video_list():
            videos = default_assistant.get_video_list()
            choices = [f"{v['video_id']}: {v['filename']}" for v in videos]
            dropdown = gr.Dropdown(choices=choices, value=choices[0] if choices else None)
            
            # 如果有视频，自动为第一个视频构建索引
            if choices:
                first_video = choices[0]
                index_status, _ = auto_build_index(first_video)
                return dropdown, gr.Textbox(value=index_status, visible=True)
            return dropdown, gr.Textbox(visible=False)
        
        refresh_btn.click(
            refresh_video_list,
            outputs=[video_selector, index_status]
        )
        
        # 视频选择时自动构建索引
        video_selector.change(
            lambda x: auto_build_index(x)[0],  # 只返回状态文本
            inputs=[video_selector],
            outputs=[index_status]
        )
        
        # 页面加载时更新视频列表
        demo.load(
            update_video_selector,
            outputs=[video_selector]
        )
    
    return demo


if __name__ == "__main__":
    # 创建并启动界面
    demo = create_video_qa_interface()
    demo.launch(
        server_name="localhost",
        server_port=None,
        share=False,
        debug=True,
        theme=gr.themes.Soft()
    )