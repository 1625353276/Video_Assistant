#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
界面处理函数
"""

import gradio as gr
import time
import json
import os
from datetime import datetime

# 导入各个模块
from ..core.video_processor import get_processor, get_video_data, default_processor
from ..core.conversation_manager import get_conversation_manager
from ..core.index_builder import get_index_builder
from ..core.translator import get_translator_manager
from ..auth.auth_handlers import get_current_user, get_auth_bridge


def handle_upload(video_file, cuda_enabled, whisper_model):
    """处理视频上传"""
    # 检查用户登录状态
    current_user = get_current_user()
    if not current_user:
        return gr.Warning("请先登录"), gr.Video(visible=False), gr.JSON(visible=False), gr.Textbox(visible=False), gr.Row(visible=False), gr.Textbox(visible=False), gr.Textbox(visible=False), gr.Button(visible=False), gr.Dropdown(visible=False), gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 获取指定配置的处理器
    current_processor = get_processor(cuda_enabled, whisper_model)
    result = current_processor.upload_and_process_video(video_file, user_id=current_user['user_id'])
    
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


def update_progress(video_info):
    """更新处理进度"""
    if not video_info or "video_id" not in video_info:
        return (
            "",  # processing_log内容
            gr.Textbox(visible=False), 
            gr.Button(visible=False), 
            gr.Dropdown(visible=False), 
            gr.Textbox(visible=False),  # 翻译结果区域
            gr.HTML(value="<div style='width:100%; background-color:#f0f0f0; border-radius:5px; padding:5px; text-align:center;'>等待处理...</div>", visible=False),
            gr.HTML(visible=False),  # 翻译进度条
            gr.Textbox(visible=False)  # 索引状态
        )
    
    video_id = video_info["video_id"]
    # 获取当前视频使用的处理器配置
    video_data = get_video_data()
    if video_id in video_data and "assistant_config" in video_data[video_id]:
        config = video_data[video_id]["assistant_config"]
        current_processor = get_processor(config["cuda_enabled"], config["whisper_model"])
    else:
        current_processor = default_processor
    
    progress_info = current_processor.get_processing_progress(video_id)
    
    log_text = "\n".join(progress_info["log_messages"])
    progress_percent = int(progress_info["progress"] * 100)
    
    if progress_info["status"] == "completed":
        # 处理完成，更新转录显示
        video_info_data = current_processor.get_video_info(video_id)
        transcript = video_info_data.get("transcript", {}).get("text", "")
        
        # 自动构建索引
        index_status, _ = auto_build_index(f"{video_id}: {video_info_data.get('filename', 'Unknown')}")
        
        return (
            log_text,
            gr.Textbox(value=transcript, visible=True),
            gr.Button(visible=True),  # 显示翻译按钮
            gr.Dropdown(visible=True),  # 显示语言选择
            gr.Textbox(visible=True),  # 显示翻译结果区域
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
        gr.HTML(value=f"<div style='width:100%; background-color:#e6f3ff; border-radius:5px; padding:5px; text-align:center;'>⏳ {progress_info['current_step']} ({progress_percent}%)</div>", visible=True),
        gr.HTML(visible=False),  # 隐藏翻译进度条
        gr.Textbox(visible=False)  # 索引状态
    )


def handle_question(question, history, video_selector):
    """处理问答"""
    if not question.strip():
        return "", history
    
    if not video_selector:
        # 添加错误消息到历史记录
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": "请先选择一个视频"})
        return "", history
    
    video_id = video_selector.split(":")[0].strip()  # 假设格式为 "video_id: filename"
    
    # 获取当前视频使用的处理器配置
    video_data = get_video_data()
    if video_id in video_data and "assistant_config" in video_data[video_id]:
        config = video_data[video_id]["assistant_config"]
        current_processor = get_processor(config["cuda_enabled"], config["whisper_model"])
    else:
        current_processor = default_processor
    
    # 获取对话管理器
    conversation_manager = get_conversation_manager()
    
    # 调用对话功能
    answer, updated_history = conversation_manager.chat_with_video(video_id, question, history)
    
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


def handle_search(query, video_selector, search_type="hybrid"):
    """处理搜索"""
    if not query.strip() or not video_selector:
        return []
    
    video_id = video_selector.split(":")[0].strip()
    
    # 获取索引构建器
    index_builder = get_index_builder()
    
    results = index_builder.search_in_video(video_id, query, search_type=search_type)
    
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


def handle_translate(video_info, target_lang):
    """处理翻译"""
    if not video_info or "video_id" not in video_info:
        return "请先上传并处理视频", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    video_id = video_info["video_id"]
    
    # 检查视频是否存在
    video_data = get_video_data()
    if video_id not in video_data:
        return "视频不存在", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 获取当前视频使用的处理器配置
    if "assistant_config" in video_data[video_id]:
        config = video_data[video_id]["assistant_config"]
        current_processor = get_processor(config["cuda_enabled"], config["whisper_model"])
    else:
        current_processor = default_processor
    
    # 检查转录是否完成
    if not video_data[video_id].get("transcript"):
        return "视频尚未转录完成，无法翻译", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 设置翻译状态
    video_data[video_id]["translating"] = True
    
    # 获取翻译管理器
    translator_manager = get_translator_manager()
    
    # 实际执行翻译
    try:
        result = translator_manager.translate_transcript(video_id, target_lang)
        
        if "error" in result:
            video_data[video_id]["translating"] = False
            return result["error"], gr.Textbox(visible=False), gr.HTML(visible=False)
        
        # 翻译成功
        translated_text = result.get("translated_text", "")
        video_data[video_id]["translating"] = False
        return (
            "✅ 翻译完成", 
            gr.Textbox(value=translated_text, visible=True),
            gr.HTML(value="<div style='width:100%; background-color:#d4edda; border-radius:5px; padding:5px; text-align:center;'>✅ 翻译完成</div>", visible=True)
        )
        
    except Exception as e:
        video_data[video_id]["translating"] = False
        return f"翻译失败: {str(e)}", gr.Textbox(visible=False), gr.HTML(visible=False)


def update_translation_progress(video_info):
    """更新翻译进度"""
    if not video_info or "video_id" not in video_info:
        return gr.HTML(visible=False)
    
    video_id = video_info["video_id"]
    
    # 检查是否正在翻译
    video_data = get_video_data()
    if video_id not in video_data or not video_data[video_id].get("translating", False):
        return gr.HTML(visible=False)
    
    # 获取翻译管理器
    translator_manager = get_translator_manager()
    
    # 获取翻译进度
    progress_info = translator_manager.get_translation_progress(video_id)
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


def handle_build_index(video_selector):
    """构建向量索引"""
    if not video_selector:
        return "请先选择视频", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    video_id = video_selector.split(":")[0].strip()
    
    # 检查视频是否存在
    video_data = get_video_data()
    if video_id not in video_data:
        return "视频不存在", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 检查转录是否完成
    if not video_data[video_id].get("transcript"):
        return "视频尚未转录完成，无法构建索引", gr.Textbox(visible=False), gr.HTML(visible=False)
    
    # 获取索引构建器
    index_builder = get_index_builder()
    
    # 设置构建状态
    video_data[video_id]["index_building"] = True

    # 实际执行构建索引
    try:
        result = index_builder.build_index_background(video_id)
        if "error" in result:
            video_data[video_id]["index_building"] = False
            return f"构建失败: {result['error']}", gr.Textbox(visible=False), gr.HTML(visible=False)
        else:
            video_data[video_id]["index_building"] = False
            return result.get("message", "索引构建完成"), gr.Textbox(visible=False), gr.HTML(value=f"<div style='width:100%; background-color:#d4edda; border-radius:5px; padding:5px; text-align:center;'>✅ {result.get('message', '索引构建完成')}</div>", visible=True)
    except Exception as e:
        video_data[video_id]["index_building"] = False
        return f"构建失败: {str(e)}", gr.Textbox(visible=False), gr.HTML(visible=False)


def get_conversation_list():
    """获取所有历史对话列表"""
    try:
        memory_dir = "data/memory"
        if not os.path.exists(memory_dir):
            return []
        
        conversations = []
        for filename in os.listdir(memory_dir):
            if filename.endswith("_conversation_history.json"):
                video_id = filename.replace("_conversation_history.json", "")
                file_path = os.path.join(memory_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)
                    
                    # 获取基本信息
                    history = conversation_data.get('history', [])
                    created_at = conversation_data.get('created_at', '')
                    
                    # 计算对话轮数（用户消息数量）
                    user_message_count = sum(1 for turn in history if turn.get('role') == 'user')
                    
                    # 格式化时间
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            created_at = created_at[:10]  # 只取日期部分
                    
                    # 检查索引文件是否存在
                    vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
                    bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
                    has_index = os.path.exists(vector_index_path) and os.path.exists(bm25_index_path)
                    
                    # 获取视频名称（如果有的话）
                    video_name = f"视频 {video_id}"
                    video_data = get_video_data()
                    if video_id in video_data:
                        video_name = video_data[video_id].get('filename', video_name)
                    
                    conversations.append({
                        'video_id': video_id,
                        'video_name': video_name,
                        'created_at': created_at,
                        'message_count': user_message_count,  # 对话轮数
                        'has_index': has_index
                    })
                except Exception as e:
                    print(f"读取对话文件 {filename} 失败: {e}")
                    continue
        
        # 按创建时间排序（最新的在前）
        conversations.sort(key=lambda x: x['created_at'], reverse=True)
        return conversations
    except Exception as e:
        print(f"获取对话列表失败: {e}")
        return []


def load_conversation_history(video_selector):
    """加载选中视频的对话历史"""
    if not video_selector:
        return []
    
    video_id = video_selector.split(":")[0].strip()
    
    try:
        conversation_history_path = f"data/memory/{video_id}_conversation_history.json"
        
        if os.path.exists(conversation_history_path):
            import json
            with open(conversation_history_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            # 返回字典格式，这是Gradio 6.3.0的消息格式
            history = []
            for turn in conversation_data.get('history', []):
                if turn.get('role') and turn.get('content'):
                    history.append({
                        'role': turn['role'],
                        'content': turn['content']
                    })
            
            return history
        else:
            return []
    except Exception as e:
        print(f"加载对话历史失败: {e}")
        return []


def start_new_chat(video_selector):
    """开始新对话"""
    if video_selector:
        video_id = video_selector.split(":")[0].strip()
        
        # 获取对话管理器
        conversation_manager = get_conversation_manager()
        
        conversation_manager.clear_conversation(video_id)
    return [], ""


def refresh_conversation_history():
    """刷新历史对话列表"""
    conversations = get_conversation_list()
    
    if not conversations:
        return gr.Dataframe(value=[], headers=["视频名称", "对话时间", "对话轮数"]), "暂无历史对话"
    
    # 转换为DataFrame格式
    df_data = []
    for conv in conversations:
        df_data.append([
            conv['video_name'],
            conv['created_at'],
            conv['message_count']
        ])
    
    return gr.Dataframe(value=df_data, headers=["视频名称", "对话时间", "对话轮数"]), f"找到 {len(conversations)} 个历史对话"


def load_selected_conversation(history_df, evt: gr.SelectData):
    """加载选中的历史对话"""
    print(f"load_selected_conversation被调用，history_df类型={type(history_df)}")
    if history_df is None or (hasattr(history_df, 'empty') and history_df.empty):
        return []  # 只返回空列表，不返回错误信息
    print(f"history_df长度={len(history_df)}")
    
    try:
        print(f"evt.index={evt.index}")
        # 获取选中的行 - 使用iloc访问行索引
        row_index = evt.index[0] if evt.index else 0
        print(f"row_index={row_index}")
        selected_row = history_df.iloc[row_index]
        video_name = selected_row.iloc[0]  # 使用iloc访问第一列
        print(f"选中的video_name={video_name}")
        
        # 从video_name中提取video_id（如果可能）
        video_id = None
        conversations = get_conversation_list()
        print(f"查找video_id，video_name={video_name}")
        print(f"可用对话列表: {conversations}")
        for conv in conversations:
            print(f"检查conv: {conv}")
            if conv['video_name'] == video_name:
                video_id = conv['video_id']
                print(f"找到匹配的video_id: {video_id}")
                break
        
        if not video_id:
            print(f"未找到video_id，video_name={video_name}")
            return []  # 只返回空列表
        
        # 获取对话管理器
        conversation_manager = get_conversation_manager()
        
        # 使用默认助手加载对话
        result = conversation_manager.load_conversation_without_video(video_id)
        
        if "error" in result:
            print(f"加载对话失败，video_id={video_id}, 错误={result['error']}")
            return []  # 只返回空列表
        
        # 加载对话历史
        history = load_conversation_history(f"{video_id}: {video_name}")
        
        # 确保返回的是列表格式
        if not isinstance(history, list):
            return []
        
        # 确保每个元素都是字典格式
        for item in history:
            if not isinstance(item, dict) or 'role' not in item or 'content' not in item:
                return []  # 格式不正确，返回空列表
        
        # 只返回聊天历史，不更新视频选择器
        return history
    except Exception as e:
        print(f"加载对话失败，异常类型: {type(e)}, 异常值: {e}")
        import traceback
        print(f"完整异常堆栈: {traceback.format_exc()}")
        return []  # 只返回空列表


def delete_selected_conversation_from_df(history_df):
    """从DataFrame删除选中的对话"""
    if history_df is None or len(history_df) == 0:
        return "请先刷新历史对话列表"
    
    try:
        # 删除第一个对话（简化处理）
        if len(history_df) > 0:
            video_name = history_df[0][0]
            
            # 从video_name中提取video_id（如果可能）
            video_id = None
            conversations = get_conversation_list()
            for conv in conversations:
                if conv['video_name'] == video_name:
                    video_id = conv['video_id']
                    break
            
            if not video_id:
                return "无法找到对应的视频ID"
            
            # 删除对话历史文件
            conversation_history_path = f"data/memory/{video_id}_conversation_history.json"
            if os.path.exists(conversation_history_path):
                os.remove(conversation_history_path)
            
            # 清空对话链
            conversation_manager = get_conversation_manager()
            if video_id in conversation_manager.conversation_chains:
                conversation_manager.clear_conversation(video_id)
            
            return f"已删除对话: {video_name}"
        else:
            return "没有可删除的对话"
    except Exception as e:
        return f"删除失败: {str(e)}"


def auto_build_index(video_selector):
    """自动为选中的视频构建索引"""
    if not video_selector:
        return "", gr.HTML(visible=False)
    
    video_id = video_selector.split(":")[0].strip()
    
    # 检查视频是否存在
    video_data = get_video_data()
    if video_id not in video_data:
        return "", gr.HTML(visible=False)
    
    # 检查转录是否完成
    if not video_data[video_id].get("transcript"):
        return "", gr.HTML(visible=False)
    
    # 检查索引是否已经构建
    if video_data[video_id].get("vector_index_built", False):
        return "索引已存在", gr.HTML(visible=False)
    
    # 设置构建状态
    video_data[video_id]["index_building"] = True
    
    # 获取当前视频使用的处理器配置
    if video_id in video_data and "assistant_config" in video_data[video_id]:
        config = video_data[video_id]["assistant_config"]
        current_processor = get_processor(config["cuda_enabled"], config["whisper_model"])
    else:
        current_processor = default_processor
    
    # 获取索引构建器
    index_builder = get_index_builder()
    
    # 实际执行构建索引
    try:
        result = index_builder.build_index_background(video_id)
        if "error" in result:
            video_data[video_id]["index_building"] = False
            return f"构建失败: {result['error']}", gr.HTML(visible=False)
        else:
            video_data[video_id]["index_building"] = False
            return result.get("message", "索引构建完成"), gr.HTML(visible=False)
    except Exception as e:
        video_data[video_id]["index_building"] = False
        return f"构建失败: {str(e)}", gr.HTML(visible=False)


def refresh_video_list():
    """刷新视频列表"""
    videos = default_processor.get_video_list()
    choices = [f"{v['video_id']}: {v['filename']}" for v in videos]
    
    # 如果有视频，自动为第一个视频构建索引
    if choices:
        first_video = choices[0]
        index_status, _ = auto_build_index(first_video)
        return gr.Dropdown(choices=choices, value=choices[0]), gr.Textbox(value=index_status, visible=True)
    return gr.Dropdown(choices=choices, value=None), gr.Textbox(visible=False)


def check_background_tasks(video_info):
    """检查后台任务"""
    if not video_info or "video_id" not in video_info:
        return gr.HTML(visible=False), gr.HTML(visible=False)
    
    video_id = video_info["video_id"]
    video_data = get_video_data()
    
    # 检查翻译进度
    if video_id in video_data and video_data[video_id].get("translating", False):
        # 模拟翻译进度
        return gr.HTML(value="<div style='width:100%; background-color:#fff3cd; border-radius:5px; padding:5px; text-align:center;'>⏳ 正在翻译...</div>", visible=True), gr.HTML(visible=False)
    
    # 检查索引构建进度
    if video_id in video_data and video_data[video_id].get("index_building", False):
        # 模拟索引构建进度
        return gr.HTML(visible=False), gr.HTML(value="<div style='width:100%; background-color:#fff3cd; border-radius:5px; padding:5px; text-align:center;'>⏳ 正在构建索引...</div>", visible=True)
    
    return gr.HTML(visible=False), gr.HTML(visible=False)