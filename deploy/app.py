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


class VideoAssistant:
    """视频助手主类"""
    
    def __init__(self):
        """初始化视频助手"""
        self.video_loader = VideoLoader()
        self.audio_extractor = AudioExtractor()
        self.whisper_asr = WhisperASR(model_size="base")
        self.file_manager = FileManager()
        
        # 初始化翻译器和检索器
        if not MOCK_MODE:
            try:
                self.translator = TextTranslator(default_method="googletrans")
                print("✓ 翻译器初始化成功")
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
    
    def upload_and_process_video(self, video_file, user_id=None):
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
                "summary": None,
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
    
    def _continue_processing(self, video_id):
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
                    transcript_path = Path(f"data/transcripts/{video_id}.json")
                    self.file_manager.save_transcript_json(transcript_result, transcript_path)
                    
                    status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 语音转文本完成")
                    
                    # 清理临时音频文件
                    if audio_path.exists():
                        audio_path.unlink()
                        
            elif progress < 0.9:
                # 摘要生成功能未实现
                status["current_step"] = "摘要生成功能未实现..."
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 摘要生成功能在modules/text/中未实现")
                status["progress"] = 0.9
                
                # 跳过摘要生成
                video_info["summary"] = "摘要生成功能尚未实现"
                status["log_messages"].append(f"[{time.strftime('%H:%M:%S')}] 跳过摘要生成")
                    
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
    
    # 注意：摘要生成功能在modules中未实现
    # 需要实现 modules/text/ 中的相关模块
    
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
                    "upload_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info["upload_time"]))
                })
        
        return videos
    
    def chat_with_video(self, video_id, question, chat_history, temperature=0.7):
        """
        基于视频内容进行问答
        注意：问答功能在modules/qa/中未实现
        """
        if video_id not in video_data:
            return "视频不存在", chat_history
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return "视频尚未处理完成，无法进行问答", chat_history
        
        # 问答功能未实现，需要实现 modules/qa/ 中的相关模块
        return f"问答功能尚未实现。问题：{question}\n注意：需要在modules/qa/中实现conversation_chain等模块", chat_history + [(question, f"问答功能尚未实现。问题：{question}")]
    
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
            transcript = video_info["transcript"]
            translated_transcript = self.translator.translate_transcript(transcript, target_lang)
            
            # 保存翻译结果
            video_info[f"translated_transcript_{target_lang}"] = translated_transcript
            
            return {
                "success": True,
                "translated_text": translated_transcript.get("text", ""),
                "segments": translated_transcript.get("segments", []),
                "metadata": translated_transcript.get("translation_metadata", {})
            }
        except Exception as e:
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


# 创建全局助手实例
assistant = VideoAssistant()


# Gradio界面函数
def create_video_qa_interface():
    """创建视频问答界面"""
    
    # 处理视频上传
    def handle_upload(video_file):
        result = assistant.upload_and_process_video(video_file)
        
        if result["status"] == "error":
            return (
                gr.Warning(result["message"]),
                gr.Video(visible=False),
                gr.JSON(visible=False),
                gr.Textbox(visible=False),
                gr.Row(visible=False),
                gr.Textbox(visible=False)
            )
        
        return (
            gr.Textbox(value=result["message"], visible=True),
            gr.Video(value=video_file, visible=True),
            gr.JSON(value={"video_id": result["video_id"], "filename": result["filename"]}, visible=True),
            gr.Textbox(value="正在处理视频...", visible=True),
            gr.Row(visible=True),  # 显示处理日志区域
            gr.Textbox(value=f"[{time.strftime('%H:%M:%S')}] 开始处理: {result['filename']}", visible=True)
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
                gr.Textbox(value="等待上传视频...", visible=True)
            )
        
        video_id = video_info["video_id"]
        progress_info = assistant.get_processing_progress(video_id)
        
        log_text = "\n".join(progress_info["log_messages"])
        
        if progress_info["status"] == "completed":
            # 处理完成，更新转录和摘要显示
            video_data = assistant.get_video_info(video_id)
            transcript = video_data.get("transcript", {}).get("text", "")
            summary = video_data.get("summary", "")
            
            return (
                log_text,
                gr.Textbox(value=transcript, visible=True),
                gr.Button(visible=True),  # 显示翻译按钮
                gr.Dropdown(visible=True),  # 显示语言选择
                gr.Textbox(visible=True),  # 显示翻译结果区域
                gr.Textbox(value=summary, visible=True),
                gr.Textbox(value="处理完成！", visible=True)
            )
        
        return (
            log_text,
            gr.Textbox(visible=False),
            gr.Button(visible=False),
            gr.Dropdown(visible=False),
            gr.Textbox(visible=False),  # 翻译结果区域
            gr.Textbox(visible=False),
            gr.Textbox(value=progress_info["current_step"], visible=True)
        )
    
    # 处理问答
    def handle_question(question, history, video_selector):
        if not question.strip():
            return "", history
        
        if not video_selector:
            return "", history + [(question, "请先选择一个视频")]
        
        video_id = video_selector.split(":")[0].strip()  # 假设格式为 "video_id: filename"
        
        answer, updated_history = assistant.chat_with_video(video_id, question, history)
        
        return "", updated_history
    
    # 处理搜索
    def handle_search(query, video_selector, search_type="hybrid"):
        if not query.strip() or not video_selector:
            return []
        
        video_id = video_selector.split(":")[0].strip()
        results = assistant.search_in_video(video_id, query, search_type=search_type)
        
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
            return "请先上传并处理视频", gr.Textbox(visible=False)
        
        video_id = video_info["video_id"]
        result = assistant.translate_transcript(video_id, target_lang)
        
        if "error" in result:
            return result["error"], gr.Textbox(visible=False)
        
        return "翻译成功", gr.Textbox(value=result["translated_text"], visible=True)
    
    # 构建向量索引
    def handle_build_index(video_selector):
        if not video_selector:
            return "请先选择视频"
        
        video_id = video_selector.split(":")[0].strip()
        result = assistant.build_vector_index(video_id)
        
        if "error" in result:
            return result["error"]
        
        return result["message"]
    
    # 开始新对话
    def start_new_chat():
        return [], ""
    
    # 更新视频选择器
    def update_video_selector():
        videos = assistant.get_video_list()
        choices = [f"{v['video_id']}: {v['filename']}" for v in videos]
        return gr.Dropdown(choices=choices, value=choices[0] if choices else None)
    
    # 创建界面
    with gr.Blocks(title="视频智能问答助手") as demo:
        gr.Markdown("# 🎥 视频智能问答助手")
        gr.Markdown("上传视频，获取智能摘要，进行多轮问答")
        
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
                        upload_btn = gr.Button("上传并处理视频", variant="primary")
                        
                    with gr.Column(scale=2):
                        video_player = gr.Video(label="视频预览", visible=False)
                        video_info = gr.JSON(label="视频信息", visible=False)
                        processing_status = gr.Textbox(label="处理状态", visible=False)
                
                # 处理日志和进度
                with gr.Row(visible=False) as processing_row:
                    with gr.Column():
                        processing_log = gr.Textbox(
                            label="处理日志",
                            lines=10,
                            interactive=False,
                            max_lines=15,
                            show_label=True
                        )
                
                # 视频内容展示
                with gr.Accordion("视频内容分析", open=False):
                    transcript_display = gr.Textbox(
                        label="转录文本",
                        lines=10,
                        interactive=False,
                        visible=False
                    )
                    
                    # 翻译功能
                    with gr.Row():
                        translate_btn = gr.Button("翻译文本", variant="secondary", visible=False)
                        target_lang = gr.Dropdown(
                            choices=["en", "zh"],
                            value="en",
                            label="目标语言",
                            visible=False
                        )
                    
                    translated_display = gr.Textbox(
                        label="翻译结果",
                        lines=10,
                        interactive=False,
                        visible=False
                    )
                    
                    summary_display = gr.Textbox(
                        label="视频摘要",
                        lines=5,
                        interactive=False,
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
                            # 索引构建
                            build_index_btn = gr.Button("构建检索索引", variant="secondary", size="sm")
                            index_status = gr.Textbox(label="索引状态", interactive=False, lines=2)
                            
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
            inputs=[video_input],
            outputs=[upload_status, video_player, video_info, processing_status, processing_row, processing_log]
        )
        
        # 定时更新处理进度 - 使用Timer组件替代
        progress_timer = gr.Timer(2)  # 每2秒触发一次
        progress_timer.tick(
            update_progress,
            inputs=[video_info],
            outputs=[processing_log, transcript_display, translate_btn, target_lang, translated_display, summary_display, processing_status]
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
            outputs=[processing_status, translated_display]
        )
        
        # 构建向量索引事件
        build_index_btn.click(
            handle_build_index,
            inputs=[video_selector],
            outputs=[index_status]
        )
        
        # 新对话事件
        new_chat_btn.click(
            start_new_chat,
            outputs=[chatbot, question_input]
        )
        
        # 刷新视频列表
        refresh_btn.click(
            update_video_selector,
            outputs=[video_selector]
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
        server_port=7860,
        share=False,
        debug=True,
        theme=gr.themes.Soft()
    )