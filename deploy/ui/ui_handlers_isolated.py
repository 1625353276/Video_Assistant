#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI处理函数 - 用户隔离版本

支持用户隔离的界面处理逻辑
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import gradio as gr

# 导入用户隔离的处理器
from deploy.core.video_processor_isolated import get_isolated_processor
from deploy.utils.user_context import get_current_user_id, get_current_user_paths

# 导入原有的处理函数（需要修改的）
from deploy.ui.ui_handlers import (
    update_progress, handle_question, handle_search, handle_translate,
    update_translation_progress, handle_build_index, get_conversation_list,
    load_conversation_history, start_new_chat, refresh_conversation_history,
    load_selected_conversation, delete_selected_conversation_from_df,
    auto_build_index, check_background_tasks
)


@get_current_user_id
def handle_upload_isolated(video_file, cuda_enabled, whisper_model):
    """处理视频上传（用户隔离版本）"""
    # 检查用户登录状态
    current_user_id = get_current_user_id()
    if not current_user_id:
        return gr.Warning("请先登录"), gr.Video(visible=False), gr.JSON(visible=False), gr.Textbox(visible=False), gr.Row(visible=False), gr.Textbox(visible=False), gr.Textbox(visible=False), gr.Button(visible=False), gr.Dropdown(visible=False), gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 获取用户隔离的处理器
    processor = get_isolated_processor(cuda_enabled, whisper_model)
    result = processor.upload_and_process_video(video_file, cuda_enabled, whisper_model)
    
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
        gr.JSON(value={"video_id": result["video_id"], "filename": result["filename"], "user_id": result["user_id"]}, visible=True),
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


def refresh_video_list_isolated():
    """刷新视频列表（用户隔离版本）"""
    current_user_id = get_current_user_id()
    if not current_user_id:
        return gr.Dropdown(choices=[], value=None)
    
    # 获取用户隔离的处理器
    processor = get_isolated_processor()
    videos = processor.get_user_video_list()
    
    if videos:
        choices = [f"{v['video_id']}: {v['filename']}" for v in videos]
        return gr.Dropdown(choices=choices, value=choices[0] if choices else None)
    else:
        return gr.Dropdown(choices=[], value=None)


def get_user_video_info_isolated(video_selector):
    """获取用户视频信息（用户隔离版本）"""
    if not video_selector:
        return None
    
    current_user_id = get_current_user_id()
    if not current_user_id:
        return None
    
    video_id = video_selector.split(":")[0].strip()
    
    # 获取用户隔离的处理器
    processor = get_isolated_processor()
    video_info = processor.get_video_info(video_id)
    
    return video_info


def build_user_index_isolated(video_selector):
    """为用户构建向量索引（用户隔离版本）"""
    if not video_selector:
        return "请先选择视频", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    current_user_id = get_current_user_id()
    if not current_user_id:
        return "用户未登录", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    video_id = video_selector.split(":")[0].strip()
    
    # 获取用户路径
    user_paths = get_current_user_paths()
    if not user_paths:
        return "用户路径获取失败", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 检查转录文件是否存在
    transcript_path = user_paths.get_transcript_path(video_id)
    if not transcript_path.exists():
        return "视频尚未转录完成，无法构建索引", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    try:
        # 读取转录文件
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        if "segments" not in transcript_data:
            return "转录文件格式错误", gr.Textbox(visible=False), gr.HTML(visible=False)
        
        # 准备文档数据
        documents = []
        for segment in transcript_data.get("segments", []):
            doc = {
                "text": segment["text"],
                "start": segment["start"],
                "end": segment["end"],
                "video_id": video_id,
                "user_id": current_user_id
            }
            documents.append(doc)
        
        if not documents:
            return "没有可用的文档片段", gr.Textbox(visible=False), gr.HTML(visible=False)
        
        # 获取用户隔离的处理器并构建索引
        processor = get_isolated_processor()
        
        # 构建向量索引（用户专属）
        if processor.vector_store:
            processor.vector_store.clear()
            processor.vector_store.add_documents(documents, text_field="text")
            vector_index_path = user_paths.get_vector_index_path(video_id)
            processor.vector_store.save_index(vector_index_path)
        
        # 构建BM25索引（用户专属）
        if processor.bm25_retriever:
            processor.bm25_retriever.clear()
            processor.bm25_retriever.add_documents(documents, text_field="text")
            bm25_index_path = user_paths.get_bm25_index_path(video_id)
            processor.bm25_retriever.save_index(bm25_index_path)
        
        return (
            f"成功构建索引，包含 {len(documents)} 个文档片段", 
            gr.Textbox(value=f"索引构建完成，文档数量: {len(documents)}", visible=True),
            gr.HTML(value=f"<div style='width:100%; background-color:#d4edda; border-radius:5px; padding:5px; text-align:center;'>✅ 索引构建完成</div>", visible=True)
        )
        
    except Exception as e:
        return f"构建索引失败: {str(e)}", gr.Textbox(visible=False), gr.HTML(visible=False)


def search_user_content_isolated(query, video_selector, search_type="hybrid"):
    """搜索用户内容（用户隔离版本）"""
    if not query.strip() or not video_selector:
        return []
    
    current_user_id = get_current_user_id()
    if not current_user_id:
        return [{"text": "用户未登录", "timestamp": 0.0, "score": 0.0, "type": "error"}]
    
    video_id = video_selector.split(":")[0].strip()
    
    # 获取用户路径
    user_paths = get_current_user_paths()
    if not user_paths:
        return [{"text": "用户路径获取失败", "timestamp": 0.0, "score": 0.0, "type": "error"}]
    
    # 检查索引文件是否存在
    vector_index_path = user_paths.get_vector_index_path(video_id)
    bm25_index_path = user_paths.get_bm25_index_path(video_id)
    
    if not vector_index_path.exists() or not bm25_index_path.exists():
        return [{"text": "索引文件不存在，请先构建索引", "timestamp": 0.0, "score": 0.0, "type": "error"}]
    
    try:
        # 获取用户隔离的处理器
        processor = get_isolated_processor()
        
        results = []
        
        # 根据搜索类型执行不同的搜索
        if search_type == "vector" and processor.vector_store:
            # 加载用户专属的向量索引
            processor.vector_store.clear()
            processor.vector_store.load_index(vector_index_path)
            
            vector_results = processor.vector_store.search(query, top_k=5, threshold=0.3)
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
        
        elif search_type == "bm25" and processor.bm25_retriever:
            # 加载用户专属的BM25索引
            processor.bm25_retriever.clear()
            processor.bm25_retriever.load_index(bm25_index_path)
            
            bm25_results = processor.bm25_retriever.search(query, top_k=5, threshold=0.3)
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
        
        elif search_type == "hybrid" and processor.hybrid_retriever:
            # 加载用户专属的混合索引
            processor.vector_store.clear()
            processor.vector_store.load_index(vector_index_path)
            processor.bm25_retriever.clear()
            processor.bm25_retriever.load_index(bm25_index_path)
            
            hybrid_results = processor.hybrid_retriever.search(query, top_k=5, threshold=0.3)
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