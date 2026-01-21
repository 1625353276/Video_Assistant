#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证处理函数
"""

import gradio as gr

# 全局变量
auth_bridge = None
current_user = None
auth_token = None


def init_auth_bridge(GradioBridge):
    """初始化认证桥接器"""
    global auth_bridge
    
    if GradioBridge:
        try:
            auth_bridge = GradioBridge("http://localhost:5001")
            print("✓ 认证桥接器初始化成功")
            return auth_bridge
        except Exception as e:
            print(f"✗ 认证桥接器初始化失败: {e}")
            auth_bridge = None
            return None
    return None


def handle_login(username, password):
    """处理用户登录"""
    global current_user, auth_token
    
    if not username or not password:
        return gr.update(visible=True, value="❌ 请输入用户名和密码", elem_classes=["feedback-message", "error"]), gr.update()
    
    if not auth_bridge:
        return gr.update(visible=True, value="❌ 认证服务不可用", elem_classes=["feedback-message", "error"]), gr.update()
    
    # 先清理任何现有的用户状态（防止用户切换时的状态污染）
    try:
        # 清理Gradio层面的用户上下文
        from deploy.utils.user_context import user_context
        if user_context.get_current_user_id():
            print(f"清理前一个用户状态: {user_context.get_current_user_id()}")
            user_context.clear_user()
        
        # 清理对话管理器缓存
        try:
            from deploy.core.conversation_manager_isolated import get_conversation_manager
            conversation_manager = get_conversation_manager()
            if hasattr(conversation_manager, 'conversation_chains'):
                conversation_manager.conversation_chains.clear()
        except Exception as e:
            print(f"⚠️ 清理对话管理器缓存失败: {e}")
        
        # 清理视频处理器缓存
        try:
            from deploy.core.video_processor_isolated import get_isolated_processor
            processor = get_isolated_processor()
            if hasattr(processor, 'processing_status'):
                processor.processing_status.clear()
        except Exception as e:
            print(f"⚠️ 清理视频处理器缓存失败: {e}")
        
        print("✅ 前一个用户状态已清理")
    except Exception as e:
        print(f"⚠️ 清理用户状态时发生错误: {e}")
    
    # 调用后端登录接口
    result = auth_bridge.login_user(username, password)
    
    if result['success']:
        current_user = {
            'user_id': result['user_id'],
            'username': result['username'],
            'token': result['token']
        }
        auth_token = result['token']
        
        # 更新认证桥接器的当前用户
        auth_bridge.current_user = current_user
        
        # 设置用户上下文
        from deploy.utils.user_context import user_context
        user_context.set_user(result['user_id'], result['username'])
        
        # 创建用户数据目录
        try:
            user_data_dir = auth_bridge.create_user_data_dir(result['user_id'])
            print(f"用户数据目录创建成功: {user_data_dir}")
        except Exception as e:
            print(f"用户数据目录创建失败: {e}")
        
        print(f"✅ 用户登录成功: {result['username']} (ID: {result['user_id']})")
        return gr.update(visible=True, value="✅ 登录成功！", elem_classes=["feedback-message", "success"])
    else:
        return gr.update(visible=True, value=f"❌ 登录失败: {result['message']}", elem_classes=["feedback-message", "error"])


def handle_register(username, email, password, confirm_password):
    """处理用户注册"""
    if not username or not email or not password:
        return gr.update(visible=True, value="❌ 请填写所有字段", elem_classes=["feedback-message", "error"])
    
    if password != confirm_password:
        return gr.update(visible=True, value="❌ 两次输入的密码不一致", elem_classes=["feedback-message", "error"])
    
    # 基本验证
    if len(username) < 3 or len(username) > 30:
        return gr.update(visible=True, value="❌ 用户名长度应为3-30位", elem_classes=["feedback-message", "error"])
    
    if '@' not in email:
        return gr.update(visible=True, value="❌ 请输入有效的邮箱地址", elem_classes=["feedback-message", "error"])
    
    if len(password) < 6:
        return gr.update(visible=True, value="❌ 密码长度至少6位", elem_classes=["feedback-message", "error"])
    
    if not auth_bridge:
        return gr.update(visible=True, value="❌ 认证服务不可用", elem_classes=["feedback-message", "error"])
    
    # 调用后端注册接口
    result = auth_bridge.register_user(username, email, password)
    
    if result['success']:
        return gr.update(visible=True, value="✅ 注册成功！请登录", elem_classes=["feedback-message", "success"])
    else:
        error_msg = result.get('message', '注册失败')
        if 'errors' in result:
            error_msg += f": {', '.join(result['errors'])}"
        return gr.update(visible=True, value=f"❌ 注册失败: {error_msg}", elem_classes=["feedback-message", "error"])


def handle_logout():
    """处理用户登出"""
    global current_user, auth_token
    
    try:
        # 先清除Flask层面的认证状态
        if auth_token and auth_bridge:
            result = auth_bridge.logout_user()
            current_user = None
            auth_token = None
            auth_bridge.current_user = None
            print("✅ Flask认证状态已清除")
        
        # 然后清除Gradio层面的用户上下文
        from deploy.utils.user_context import user_context
        user_context.clear_user()
        print("✅ Gradio用户上下文已清除")
        
        # 清理对话管理器缓存
        try:
            from deploy.core.conversation_manager_isolated import get_conversation_manager
            conversation_manager = get_conversation_manager()
            if hasattr(conversation_manager, 'conversation_chains'):
                conversation_manager.conversation_chains.clear()
            print("✅ 对话管理器缓存已清除")
        except Exception as e:
            print(f"⚠️ 清理对话管理器缓存失败: {e}")
        
        # 清理视频处理器缓存
        try:
            from deploy.core.video_processor_isolated import get_isolated_processor
            processor = get_isolated_processor()
            if hasattr(processor, 'processing_status'):
                processor.processing_status.clear()
            print("✅ 视频处理器缓存已清除")
        except Exception as e:
            print(f"⚠️ 清理视频处理器缓存失败: {e}")
        
        # 清理索引构建器缓存
        try:
            from deploy.core.index_builder_isolated import get_index_builder
            index_builder = get_index_builder()
            # 清理检索器缓存
            if index_builder.vector_store and hasattr(index_builder.vector_store, 'clear'):
                index_builder.vector_store.clear()
            if index_builder.bm25_retriever and hasattr(index_builder.bm25_retriever, 'clear'):
                index_builder.bm25_retriever.clear()
            if index_builder.hybrid_retriever and hasattr(index_builder.hybrid_retriever, 'clear'):
                index_builder.hybrid_retriever.clear()
            print("✓ 索引构建器缓存已清除")
        except Exception as e:
            print(f"⚠️ 清理索引构建器缓存失败: {e}")
        
        # 清理翻译管理器缓存
        try:
            from deploy.core.translator_isolated import get_translator_manager
            translator_manager = get_translator_manager()
            if hasattr(translator_manager, 'translation_progress'):
                translator_manager.translation_progress.clear()
            print("✅ 翻译管理器缓存已清除")
        except Exception as e:
            print(f"⚠️ 清理翻译管理器缓存失败: {e}")
        
        # 清理全局变量
        current_user = None
        auth_token = None
        
        # 强制垃圾回收
        import gc
        gc.collect()
        print("✅ 垃圾回收完成")
        
        # 返回完整的界面清理更新
        return (
            gr.update(visible=True),   # login_page
            gr.update(visible=False),  # main_page  
            gr.update(visible=False),  # user_info_section
            gr.update(value="未登录"), # user_display
            gr.update(choices=[], value=None),  # video_selector
            gr.update(value=[]),       # conversation_history_df
            gr.update(value=[]),       # chatbot
            gr.update(value=""),       # question_input
            gr.update(value=[]),       # search_results
            gr.update(value=""),       # search_query
            gr.update(value="", visible=False),  # transcript_display
            gr.update(value="", visible=False),  # translated_display
            gr.update(value=None, visible=False),  # video_info
            gr.update(value="", visible=False),  # processing_status
            gr.update(value="", visible=False),  # processing_log
            gr.update(value="", visible=False),  # progress_html
            gr.update(value="", visible=False),  # upload_status
            gr.update(value="", visible=False),  # index_status
            gr.update(value="", visible=False),  # index_progress_html
            gr.update(value="", visible=False),  # translate_progress_html
            gr.update(value="", visible=False),  # translate_progress_bar
            gr.update(value="", visible=False),  # history_status
            gr.update(visible=False)   # video_player
        )
        
    except Exception as e:
        print(f"⚠️ 登出过程中发生错误: {e}")
        # 即使出错也要返回基本清理
        return (
            gr.update(visible=True),   # login_page
            gr.update(visible=False),  # main_page
            gr.update(visible=False),  # user_info_section
            gr.update(value="未登录"), # user_display
            gr.update(choices=[], value=None),  # video_selector
            gr.update(value=[]),       # conversation_history_df
            gr.update(value=[]),       # chatbot
            gr.update(value=""),       # question_input
            gr.update(value=[]),       # search_results
            gr.update(value=""),       # search_query
            gr.update(value="", visible=False),  # transcript_display
            gr.update(value="", visible=False),  # translated_display
            gr.update(value=None, visible=False),  # video_info
            gr.update(value="", visible=False),  # processing_status
            gr.update(value="", visible=False),  # processing_log
            gr.update(value="", visible=False),  # progress_html
            gr.update(value="", visible=False),  # upload_status
            gr.update(value="", visible=False),  # index_status
            gr.update(value="", visible=False),  # index_progress_html
            gr.update(value="", visible=False),  # translate_progress_html
            gr.update(value="", visible=False),  # translate_progress_bar
            gr.update(value="", visible=False),  # history_status
            gr.update(visible=False)   # video_player
        )


def update_user_info():
    """更新用户信息显示"""
    global current_user
    
    if current_user:
        return (
            gr.update(value=f"用户: {current_user['username']}"), 
            gr.update(visible=True)
        )
    else:
        return (
            gr.update(value="未登录"), 
            gr.update(visible=False)
        )


def check_auth_status():
    """检查认证状态"""
    global current_user
    
    if current_user:
        return gr.update(value=f"用户: {current_user['username']}")
    else:
        return gr.update(value="未登录")


def get_current_user():
    """获取当前用户信息"""
    return current_user


def get_auth_bridge():
    """获取认证桥接器"""
    return auth_bridge


def update_video_selector_for_user():
    """更新视频选择器（基于用户）"""
    global current_user
    
    if not current_user or not auth_bridge:
        return gr.Dropdown(choices=[], value=None)
    
    # 获取用户专属视频列表
    result = auth_bridge.get_user_videos(current_user['user_id'])
    if result['success']:
        videos = result['videos']
        choices = [f"{v['filename']}" for v in videos]
        return gr.Dropdown(choices=choices, value=choices[0] if choices else None)
    else:
        return gr.Dropdown(choices=[], value=None)