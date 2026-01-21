#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频智能问答助手 - Web应用 (重构版)

整合了视频上传、处理、转录、问答等功能的完整Web应用
重构后采用模块化架构，提高代码可维护性
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr

# 导入重构后的模块
from deploy.auth.auth_handlers import init_auth_bridge
from deploy.ui.events import bind_events
from deploy.utils.helpers import exit_if_no_flask_service, log_system_info

# 尝试导入后端模块，如果失败则使用模拟模式
MOCK_MODE = False
import_error = None

try:
    from integration.gradio_bridge import GradioBridge
    print("✓ GradioBridge 导入成功")
except ImportError as e:
    import_error = f"GradioBridge 导入失败: {e}"
    print(f"✗ {import_error}")
    MOCK_MODE = True

# 设置SSL验证
os.environ['SSL_VERIFY'] = 'false'

# 尝试导入视频清理功能
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


def create_auth_interface():
    """创建登录注册界面"""
    with gr.Group(visible=True) as auth_interface:
        with gr.Tabs():
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
                    login_btn = gr.Button("登录", variant="primary")
                    login_message = gr.Textbox(
                        label="", 
                        visible=False, 
                        interactive=False
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
                    reg_btn = gr.Button("注册", variant="primary")
                    reg_message = gr.Textbox(
                        label="", 
                        visible=False, 
                        interactive=False
                    )
    
    return (auth_interface, login_username, login_password, login_btn, login_message, 
            reg_username, reg_email, reg_password, reg_confirm_password, reg_btn, reg_message)


def create_user_info():
    """创建用户信息显示"""
    with gr.Group(visible=False) as user_info_group:
        with gr.Row():
            user_display = gr.Textbox(
                label="当前用户", 
                interactive=False,
                value="未登录"
            )
            logout_btn = gr.Button("登出", size="sm")
    
    return user_info_group, user_display, logout_btn


def create_video_qa_interface():
    """创建视频问答界面（集成认证）"""
    
    # 初始化认证桥接器
    GradioBridgeClass = None if MOCK_MODE else GradioBridge
    auth_bridge = init_auth_bridge(GradioBridgeClass)
    
    # 创建界面
    with gr.Blocks(title="视频智能问答助手") as demo:
        gr.Markdown("# 🎥 视频智能问答助手")
        gr.Markdown("上传视频，进行智能问答")
        
        # 创建认证界面
        with gr.Group(visible=True) as auth_interface:
            with gr.Tabs():
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
                        login_btn = gr.Button("登录", variant="primary")
                        login_message = gr.Textbox(
                            label="", 
                            visible=False, 
                            interactive=False
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
                        reg_btn = gr.Button("注册", variant="primary")
                        reg_message = gr.Textbox(
                            label="", 
                            visible=False, 
                            interactive=False
                        )
        
        # 创建用户信息显示
        with gr.Group(visible=False) as user_info_group:
            with gr.Row():
                user_display = gr.Textbox(
                    label="当前用户", 
                    interactive=False,
                    value="未登录"
                )
                logout_btn = gr.Button("登出", size="sm")
        
        # 主应用界面（默认隐藏）
        with gr.Group(visible=False) as main_interface:
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
        
        # 绑定事件
        from deploy.ui.ui_handlers import (
            handle_upload, update_progress, handle_question, handle_search, handle_translate,
            update_translation_progress, handle_build_index, get_conversation_list,
            load_conversation_history, start_new_chat, refresh_conversation_history,
            load_selected_conversation, delete_selected_conversation_from_df,
            auto_build_index, refresh_video_list, check_background_tasks
        )
        
        from deploy.auth.auth_handlers import (
            handle_login, handle_register, handle_logout, update_user_info,
            check_auth_status, update_video_selector_for_user
        )
        
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
            outputs=[login_message, auth_interface]
        ).then(
            fn=update_user_info,
            outputs=[user_display, user_info_group]
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=[main_interface]
        )
        
        reg_btn.click(
            fn=handle_register,
            inputs=[reg_username, reg_email, reg_password, reg_confirm_password],
            outputs=[reg_message]
        )
        
        logout_btn.click(
            fn=handle_logout,
            outputs=[auth_interface, user_info_group]
        ).then(
            fn=lambda: gr.update(visible=False),
            outputs=[main_interface]
        )
        
        # 页面加载时检查认证状态
        demo.load(
            fn=check_auth_status,
            outputs=[auth_interface, user_info_group, main_interface, user_display]
        ).then(
            fn=lambda: (
                update_video_selector_for_user(),
                refresh_conversation_history()[0],  # 取DataFrame
                refresh_conversation_history()[1]   # 取状态消息
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
    demo = create_video_qa_interface()
    demo.launch(
        server_name="localhost",
        server_port=None,
        share=False,
        debug=True,
        theme=gr.themes.Soft(),
        css="""
        .scrollable-textbox textarea {
            overflow-y: scroll !important;
            max-height: 300px !important;
        }
        """
    )