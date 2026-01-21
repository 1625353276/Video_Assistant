#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件
"""

import gradio as gr


def create_video_upload_section():
    """创建视频上传区域"""
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
    
    video_input = gr.File(
        label="上传视频文件",
        file_types=[".mp4", ".avi", ".mov", ".mkv", ".webm"]
    )
    
    upload_btn = gr.Button("上传并处理视频", variant="primary")

    # 处理日志和进度
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
    
    return video_input, cuda_enabled, whisper_model, upload_btn, progress_html, processing_log


def create_video_display_section():
    """创建视频显示区域"""
    video_player = gr.Video(label="视频预览", visible=False)
    video_info = gr.JSON(label="视频信息", visible=False)
    processing_status = gr.Textbox(label="处理状态", visible=False)
    
    return video_player, video_info, processing_status


def create_transcript_section():
    """创建转录文本区域"""
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
    
    return (transcript_display, translate_btn, target_lang, translated_display, 
            translate_progress_html, translate_progress_bar)


def create_qa_section():
    """创建问答区域"""
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
        
        quick_question_btns = []
        for i, question in enumerate(quick_questions):
            btn = gr.Button(question, size="sm")
            quick_question_btns.append(btn)
    
    return chatbot, question_input, send_btn, quick_question_btns


def create_sidebar_section():
    """创建侧边栏区域"""
    # 视频选择
    video_selector = gr.Dropdown(
        label="选择视频",
        choices=[],
        interactive=True
    )
    refresh_btn = gr.Button("刷新视频列表", size="sm")
    
    # 历史对话
    with gr.Accordion("历史对话", open=False):
        conversation_history_df = gr.Dataframe(
            headers=["视频名称", "对话时间", "对话轮数"],
            datatype=["str", "str", "number"],
            label="历史对话列表",
            interactive=True
        )
        load_history_btn = gr.Button("加载选中对话", variant="primary", size="sm")
        refresh_history_btn = gr.Button("刷新历史", size="sm")
        
        # 删除对话功能
        with gr.Row():
            delete_history_btn = gr.Button("删除选中对话", variant="stop", size="sm")
        
        # 历史对话状态
        history_status = gr.Textbox(label="状态", interactive=False, visible=True)
    
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
    
    return (video_selector, refresh_btn, conversation_history_df, load_history_btn, 
            refresh_history_btn, delete_history_btn, history_status, index_status, 
            index_progress_html, search_type, search_query, search_btn, search_results, new_chat_btn)


def create_main_interface():
    """创建主界面"""
    main_interface = gr.Group(visible=False)
    
    with main_interface:
        with gr.Tabs():
            # 视频上传和管理标签页
            with gr.TabItem("视频管理"):
                upload_status = gr.Textbox(label="上传状态", visible=False)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        video_upload_components = create_video_upload_section()
                    with gr.Column(scale=2):
                        video_display_components = create_video_display_section()
                
                transcript_components = create_transcript_section()
            
            # 智能问答标签页
            with gr.TabItem("智能问答"):
                with gr.Row():
                    with gr.Column(scale=1):
                        sidebar_components = create_sidebar_section()
                    with gr.Column(scale=2):
                        qa_components = create_qa_section()
    
    return main_interface, (upload_status, video_upload_components, video_display_components, 
                           transcript_components, sidebar_components, qa_components)