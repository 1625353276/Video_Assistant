#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频智能问答助手 - 页面路由版本

使用页面路由实现登录后跳转到主应用
"""

import os
import sys
import gradio as gr
import requests
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置SSL验证
os.environ['SSL_VERIFY'] = 'false'

# 导入重构后的模块
from deploy.auth.auth_handlers import init_auth_bridge
from deploy.ui.ui_handlers import (
    handle_upload, update_progress, handle_question, handle_search, handle_translate,
    update_translation_progress, handle_build_index, get_conversation_list,
    load_conversation_history, start_new_chat, refresh_conversation_history,
    load_selected_conversation, delete_selected_conversation_from_df,
    auto_build_index, refresh_video_list, check_background_tasks
)
from deploy.utils.helpers import exit_if_no_flask_service, log_system_info

# 尝试导入后端模块
try:
    from integration.gradio_bridge import GradioBridge
    print("✓ GradioBridge 导入成功")
except ImportError as e:
    print(f"✗ GradioBridge 导入失败: {e}")
    GradioBridge = None

# 尝试导入视频清理功能
try:
    from modules.utils.video_cleaner import register_video_cleanup
    register_video_cleanup()
    print("✓ 视频清理功能已启用")
except ImportError as e:
    print(f"✗ VideoCleaner 导入失败: {e}")


class PageRouter:
    """页面路由管理器"""
    
    def __init__(self):
        self.current_page = "login"
        self.auth_bridge = init_auth_bridge(GradioBridge)
        
    def show_login_page(self):
        """显示登录页面"""
        self.current_page = "login"
        return (
            gr.update(visible=True),   # login_page
            gr.update(visible=False),  # main_page
            gr.update(visible=False)   # user_info
        )
    
    def show_main_page(self):
        """显示主应用页面"""
        self.current_page = "main"
        return (
            gr.update(visible=False),  # login_page
            gr.update(visible=True),   # main_page
            gr.update(visible=True)    # user_info
        )
    
    def get_current_page(self):
        """获取当前页面"""
        return self.current_page


def create_login_page(router):
    """创建登录页面"""
    with gr.Group(visible=True) as login_page:
        gr.Markdown("# 🔐 用户登录")
        gr.Markdown("请登录以使用视频智能问答助手")
        
        with gr.Row():
            with gr.Column(scale=1):
                pass  # 空白列用于居中
            with gr.Column(scale=2):
                with gr.Tabs() as login_tabs:
                    with gr.Tab("登录"):
                        with gr.Column():
                            login_username = gr.Textbox(
                                label="用户名/邮箱", 
                                placeholder="请输入用户名或邮箱"
                            )
                            login_password = gr.Textbox(
                                label="密码", 
                                type="password",
                                placeholder="请输入密码"
                            )
                            login_btn = gr.Button("登录", variant="primary", size="lg")
                            login_message = gr.Textbox(
                                label="", 
                                visible=False, 
                                interactive=False,
                                elem_classes=["feedback-message"]
                            )
                    
                    with gr.Tab("注册"):
                        with gr.Column():
                            reg_username = gr.Textbox(
                                label="用户名", 
                                placeholder="3-30位字母、数字、下划线"
                            )
                            reg_email = gr.Textbox(
                                label="邮箱", 
                                placeholder="请输入有效邮箱地址"
                            )
                            reg_password = gr.Textbox(
                                label="密码", 
                                type="password",
                                placeholder="至少6位，建议包含大小写字母、数字和特殊字符"
                            )
                            reg_confirm_password = gr.Textbox(
                                label="确认密码", 
                                type="password",
                                placeholder="请再次输入密码"
                            )
                            reg_btn = gr.Button("注册", variant="primary", size="lg")
                            reg_message = gr.Textbox(
                                label="", 
                                visible=False, 
                                interactive=False,
                                elem_classes=["feedback-message"]
                            )
            with gr.Column(scale=1):
                pass  # 空白列用于居中
    
    return login_page, (login_username, login_password, login_btn, login_message, 
                       reg_username, reg_email, reg_password, reg_confirm_password, reg_btn, reg_message, login_tabs)


def create_main_app_page():
    """创建主应用页面"""
    with gr.Group(visible=False) as main_page:
        gr.Markdown("# 🎥 视频智能问答助手")
        gr.Markdown("上传视频，进行智能问答")
        
        with gr.Tabs():
            # 视频上传和管理标签页
            with gr.TabItem("视频管理"):
                upload_status = gr.Textbox(label="上传状态", visible=False)
                
                with gr.Row():
                    with gr.Column(scale=1):
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
                            choices=["请选择语言", "English", "中文"],
                            value="请选择语言",
                            label="",
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
                    
                    translate_progress_bar = gr.HTML(visible=False)
            
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
    
    return main_page, (upload_status, video_input, cuda_enabled, whisper_model, upload_btn, 
                      progress_html, processing_log, video_player, video_info, processing_status,
                      transcript_display, translate_btn, target_lang, translated_display,
                      translate_progress_html, translate_progress_bar, video_selector, refresh_btn,
                      conversation_history_df, load_history_btn, refresh_history_btn,
                      delete_history_btn, history_status, index_status, index_progress_html,
                      search_type, search_query, search_btn, search_results, new_chat_btn,
                      chatbot, question_input, send_btn)


def create_user_info_section():
    """创建用户信息区域"""
    with gr.Group(visible=False) as user_info_section:
        with gr.Row():
            with gr.Column(scale=4):
                user_display = gr.Textbox(
                    label="当前用户", 
                    interactive=False,
                    value="未登录"
                )
            with gr.Column(scale=1):
                logout_btn = gr.Button("登出", variant="secondary")
    
    return user_info_section, user_display, logout_btn


def create_video_qa_interface_routed():
    """创建带页面路由的视频问答界面"""
    
    # 创建路由器
    router = PageRouter()
    
    # 创建界面
    with gr.Blocks(title="视频智能问答助手") as demo:
        # 创建登录页面
        login_page, login_components = create_login_page(router)
        (login_username, login_password, login_btn, login_message, 
         reg_username, reg_email, reg_password, reg_confirm_password, reg_btn, reg_message, login_tabs) = login_components
        
        # 创建主应用页面
        main_page, main_components = create_main_app_page()
        (upload_status, video_input, cuda_enabled, whisper_model, upload_btn, 
         progress_html, processing_log, video_player, video_info, processing_status,
         transcript_display, translate_btn, target_lang, translated_display,
         translate_progress_html, translate_progress_bar, video_selector, refresh_btn,
         conversation_history_df, load_history_btn, refresh_history_btn,
         delete_history_btn, history_status, index_status, index_progress_html,
         search_type, search_query, search_btn, search_results, new_chat_btn,
         chatbot, question_input, send_btn) = main_components
        
        # 创建用户信息区域
        user_info_section, user_display, logout_btn = create_user_info_section()
        
        # 导入认证处理函数
        from deploy.auth.auth_handlers import handle_login, handle_register, handle_logout, update_user_info
        
        # 绑定登录事件
        def login_flow(username, password):
            """登录流程控制"""
            login_result = handle_login(username, password)
            
            # 检查登录是否成功（通过消息内容判断）
            if "登录成功" in str(login_result.get('value', '')):
                # 登录成功，清空表单并继续后续步骤
                user_info_update = update_user_info()
                page_updates = router.show_main_page()
                return (login_result, page_updates[0], user_info_update[0], 
                       user_info_update[1], page_updates[1], page_updates[2],
                       gr.update(value=""), gr.update(value=""))  # 清空登录表单
            else:
                # 登录失败，显示错误消息但不清空表单（方便用户重试）
                return (login_result, gr.update(), gr.update(), 
                       gr.update(), gr.update(), gr.update(),
                       gr.update(), gr.update())  # 保持表单内容
        
        login_btn.click(
            fn=login_flow,
            inputs=[login_username, login_password],
            outputs=[login_message, login_page, user_display, user_info_section, main_page, user_info_section,
                    login_username, login_password]
        )
        
        # 绑定注册事件
        def register_flow(username, email, password, confirm_password):
            """注册流程控制"""
            register_result = handle_register(username, email, password, confirm_password)
            
            # 检查注册是否成功（通过消息内容判断）
            if "注册成功" in str(register_result.get('value', '')):
                # 注册成功，清空表单并切换到登录标签页
                return (
                    register_result,             # 注册成功消息
                    gr.update(selected=0),        # 切换到登录标签页
                    gr.update(value=""),          # 清空用户名
                    gr.update(value=""),          # 清空邮箱
                    gr.update(value=""),          # 清空密码
                    gr.update(value="")           # 清空确认密码
                )
            else:
                # 注册失败，显示错误消息但不清空表单（方便用户修改）
                return (
                    register_result,             # 注册失败消息
                    gr.update(),                 # 保持当前标签页
                    gr.update(),                 # 保持用户名
                    gr.update(),                 # 保持邮箱
                    gr.update(),                 # 保持密码
                    gr.update()                  # 保持确认密码
                )
        
        reg_btn.click(
            fn=register_flow,
            inputs=[reg_username, reg_email, reg_password, reg_confirm_password],
            outputs=[reg_message, login_tabs, reg_username, reg_email, reg_password, reg_confirm_password]
        )
        
        # 绑定登出事件
        logout_btn.click(
            fn=handle_logout,
            outputs=[login_page, main_page, user_info_section, user_display, video_selector, 
                    conversation_history_df, chatbot, question_input, search_results, search_query,
                    transcript_display, translated_display, video_info, processing_status, 
                    processing_log, progress_html, upload_status, index_status, index_progress_html,
                    translate_progress_html, translate_progress_bar, history_status, video_player]
        )
        
        # 绑定主应用事件（与原来相同）
        upload_btn.click(
            handle_upload,
            inputs=[video_input, cuda_enabled, whisper_model],
            outputs=[upload_status, video_player, video_info, processing_status, processing_log, progress_html, transcript_display, translate_btn, target_lang, translated_display]
        )
        
        # 定时更新处理进度
        progress_timer = gr.Timer(2)
        progress_timer.tick(
            update_progress,
            inputs=[video_info],
            outputs=[processing_log, transcript_display, translate_btn, target_lang, translated_display, progress_html, translate_progress_bar, index_status]
        )
        
        # 定时检查翻译和索引构建进度
        background_timer = gr.Timer(3)
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
        
        # 翻译进度更新
        translation_progress_timer = gr.Timer(1)
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
                auto_build_index(x)[0],
                load_conversation_history(x)
            ),
            inputs=[video_selector],
            outputs=[index_status, chatbot]
        )
        
        # 历史对话事件绑定
        refresh_history_btn.click(
            refresh_conversation_history,
            outputs=[conversation_history_df, history_status]
        )
        
        conversation_history_df.select(
            fn=load_selected_conversation,
            inputs=[conversation_history_df],
            outputs=[chatbot]
        )
        
        delete_history_btn.click(
            fn=lambda df: delete_selected_conversation_from_df(df),
            inputs=[conversation_history_df],
            outputs=[history_status]
        ).then(
            refresh_conversation_history,
            outputs=[conversation_history_df, history_status]
        )
        from utils.user_context import user_context

        # 页面加载时检查认证状态并同步用户上下文
        def check_auth_state():
            """检查认证状态并同步用户上下文"""
            try:
                # 获取Flask层面的用户状态
                flask_user = router.auth_bridge.current_user if router.auth_bridge else None
                
                # 获取Gradio层面的用户状态
                gradio_user_id = user_context.get_current_user_id()
                
                # 如果Gradio有用户但Flask没有，同步到Flask
                if gradio_user_id and not flask_user:
                    from deploy.auth.auth_handlers import auth_bridge
                    auth_bridge.current_user = {
                        'user_id': gradio_user_id,
                        'username': user_context.get_current_user_data().get('username', gradio_user_id),
                        'token': None  # 需要重新登录获取token
                    }
                    print(f"同步用户状态：Gradio用户({gradio_user_id}) -> Flask")
                
                # 如果Flask有用户但Gradio没有，同步到Gradio
                elif flask_user and not gradio_user_id:
                    user_context.set_user(flask_user['user_id'], flask_user['username'])
                    print(f"同步用户状态：Flask用户({flask_user['user_id']}) -> Gradio")
                
                # 如果两者都有用户但用户ID不匹配，以Flask为准并清理Gradio状态
                elif flask_user and gradio_user_id and flask_user['user_id'] != gradio_user_id:
                    print(f"检测到用户状态不一致：Flask用户({flask_user['user_id']}) != Gradio用户({gradio_user_id})")
                    # 清理Gradio状态并同步到Flask用户
                    user_context.clear_user()
                    user_context.set_user(flask_user['user_id'], flask_user['username'])
                    
                    # 清理所有缓存
                    try:
                        from deploy.core.conversation_manager_isolated import get_conversation_manager
                        conversation_manager = get_conversation_manager()
                        if hasattr(conversation_manager, 'conversation_chains'):
                            conversation_manager.conversation_chains.clear()
                    except Exception as e:
                        print(f"⚠️ 清理对话管理器缓存失败: {e}")
                    
                    try:
                        from deploy.core.video_processor_isolated import get_isolated_processor
                        processor = get_isolated_processor()
                        if hasattr(processor, 'processing_status'):
                            processor.processing_status.clear()
                    except Exception as e:
                        print(f"⚠️ 清理视频处理器缓存失败: {e}")
                    
                    print(f"✅ 用户状态已同步到Flask用户({flask_user['user_id']})")
                
                # 确定显示哪个页面
                if flask_user or gradio_user_id:
                    return router.show_main_page()
                else:
                    return router.show_login_page()
                    
            except Exception as e:
                print(f"⚠️ 检查认证状态时发生错误: {e}")
                # 出错时默认显示登录页面
                return router.show_login_page()
        
        # 页面加载时检查认证状态
        demo.load(
            fn=check_auth_state,
            outputs=[login_page, main_page, user_info_section]
        ).then(
            fn=lambda: (
                refresh_video_list()[0] if user_context.is_logged_in() else [],
                refresh_conversation_history()[0] if user_context.is_logged_in() else None,
                refresh_conversation_history()[1] if user_context.is_logged_in() else ""
            ),
            outputs=[video_selector, conversation_history_df, history_status]
        )
    
    return demo

if __name__ == "__main__":
    # 记录系统信息
    log_system_info()
    
    # 检查Flask认证服务
    exit_if_no_flask_service()
    
    # 创建并启动界面
    demo = create_video_qa_interface_routed()
    
    # 添加自定义CSS样式
    custom_css = """
    .feedback-message {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 8px 0;
        font-weight: 500;
    }
    
    .feedback-message textarea {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-weight: 500;
    }
    
    .feedback-message.success textarea {
        color: #155724 !important;
    }
    
    .feedback-message.error textarea {
        color: #721c24 !important;
    }
    """
    
    demo.launch(
        server_name="localhost",
        server_port=None,
        share=False,
        debug=True,
        theme=gr.themes.Soft(),
        css=custom_css
    )
