#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件绑定
"""

import gradio as gr

# 导入处理函数
from .ui_handlers import (
    handle_upload, update_progress, handle_question, handle_search, handle_translate,
    update_translation_progress, handle_build_index, get_conversation_list,
    load_conversation_history, start_new_chat, refresh_conversation_history,
    load_selected_conversation, delete_selected_conversation_from_df,
    auto_build_index, refresh_video_list, check_background_tasks
)

# 导入认证处理函数
from ..auth.auth_handlers import (
    handle_login, handle_register, handle_logout, update_user_info,
    check_auth_status, update_video_selector_for_user
)


def bind_events(demo, main_interface, auth_interface, user_info_group, 
               upload_status, video_upload_components, video_display_components,
               transcript_components, sidebar_components, qa_components):
    """绑定所有事件"""
    
    # 解包组件
    (video_input, cuda_enabled, whisper_model, upload_btn, progress_html, processing_log) = video_upload_components
    (video_player, video_info, processing_status) = video_display_components
    (transcript_display, translate_btn, target_lang, translated_display, 
     translate_progress_html, translate_progress_bar) = transcript_components
    (video_selector, refresh_btn, conversation_history_df, load_history_btn,
     refresh_history_btn, delete_history_btn, history_status, index_status,
     index_progress_html, search_type, search_query, search_btn, search_results, new_chat_btn) = sidebar_components
    (chatbot, question_input, send_btn, quick_question_btns) = qa_components
    
    # 解包认证组件
    (auth_interface_group, login_username, login_password, login_btn, login_message,
     reg_username, reg_email, reg_password, reg_confirm_password, reg_btn, reg_message) = auth_interface
    (user_info_group_inner, user_display, logout_btn_inner) = user_info_group
    
    # 事件绑定
    upload_btn.click(
        handle_upload,
        inputs=[video_input, cuda_enabled, whisper_model],
        outputs=[upload_status, video_player, video_info, processing_status, processing_log, progress_html, transcript_display, translate_btn, target_lang, translated_display]
    )
    
    # 定时更新处理进度 - 使用Timer组件替代
    progress_timer = gr.Timer(2)  # 每2秒触发一次
    progress_timer.tick(
        update_progress,
        inputs=[video_info],
        outputs=[processing_log, transcript_display, translate_btn, target_lang, translated_display, progress_html, translate_progress_bar, index_status]
    )
    
    # 定时检查翻译和索引构建进度
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
    
    # 新对话事件
    new_chat_btn.click(
        start_new_chat,
        inputs=[video_selector],
        outputs=[chatbot, question_input]
    )
    
    # 刷新视频列表
    refresh_btn.click(
        refresh_video_list,
        outputs=[video_selector, index_status]
    )
    
    # 视频选择时自动构建索引并加载对话历史
    video_selector.change(
        fn=lambda x: (
            auto_build_index(x)[0],  # 索引状态
            load_conversation_history(x)  # 加载对话历史
        ),
        inputs=[video_selector],
        outputs=[index_status, chatbot]
    )
    
    # 历史对话事件绑定
    refresh_history_btn.click(
        refresh_conversation_history,
        outputs=[conversation_history_df, history_status]
    )
    
    # 加载选中的历史对话 - 直接使用DataFrame的select事件
    conversation_history_df.select(
        fn=load_selected_conversation,
        inputs=[conversation_history_df],
        outputs=[chatbot]
    )
    
    # 删除选中的历史对话 - 使用单独的按钮
    delete_history_btn.click(
        fn=lambda df: delete_selected_conversation_from_df(df),
        inputs=[conversation_history_df],
        outputs=[history_status]
    ).then(
        refresh_conversation_history,
        outputs=[conversation_history_df, history_status]
    )
    
    # 绑定认证事件
    login_btn.click(
        fn=handle_login,
        inputs=[login_username, login_password],
        outputs=[login_message, auth_interface_group]
    ).then(
        fn=update_user_info,
        outputs=[user_display, user_info_group_inner]
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[main_interface]
    )
    
    reg_btn.click(
        fn=handle_register,
        inputs=[reg_username, reg_email, reg_password, reg_confirm_password],
        outputs=[reg_message]
    )
    
    logout_btn_inner.click(
        fn=handle_logout,
        outputs=[auth_interface_group, user_info_group_inner]
    ).then(
        fn=lambda: gr.update(visible=False),
        outputs=[main_interface]
    )
    
    # 页面加载时检查认证状态
    demo.load(
        fn=check_auth_status,
        outputs=[auth_interface_group, user_info_group_inner, main_interface, user_display]
    ).then(
        fn=lambda: (
            update_video_selector_for_user(),
            refresh_conversation_history()[0],  # 取DataFrame
            refresh_conversation_history()[1]   # 取状态消息
        ),
        outputs=[video_selector, conversation_history_df, history_status]
    )
    
    # 绑定快捷问题按钮
    for i, btn in enumerate(quick_question_btns):
        quick_questions = [
            "这个视频的主要内容是什么？",
            "视频中提到了哪些关键点？",
            "能总结一下视频的核心观点吗？",
            "视频中的结论是什么？"
        ]
        btn.click(
            lambda q=quick_questions[i]: q,
            outputs=question_input
        )