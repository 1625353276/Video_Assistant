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
        return gr.update(visible=True, value="请输入用户名和密码"), gr.update()
    
    if not auth_bridge:
        return gr.update(visible=True, value="认证服务不可用"), gr.update()
    
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
        
        # 创建用户数据目录
        try:
            user_data_dir = auth_bridge.create_user_data_dir(result['user_id'])
            print(f"用户数据目录创建成功: {user_data_dir}")
        except Exception as e:
            print(f"用户数据目录创建失败: {e}")
        
        return gr.update(visible=True, value="登录成功！"), gr.update()
    else:
        return gr.update(visible=True, value=f"登录失败: {result['message']}"), gr.update()


def handle_register(username, email, password, confirm_password):
    """处理用户注册"""
    if not username or not email or not password:
        return gr.update(visible=True, value="请填写所有字段")
    
    if password != confirm_password:
        return gr.update(visible=True, value="两次输入的密码不一致")
    
    # 基本验证
    if len(username) < 3 or len(username) > 30:
        return gr.update(visible=True, value="用户名长度应为3-30位")
    
    if '@' not in email:
        return gr.update(visible=True, value="请输入有效的邮箱地址")
    
    if len(password) < 6:
        return gr.update(visible=True, value="密码长度至少6位")
    
    if not auth_bridge:
        return gr.update(visible=True, value="认证服务不可用")
    
    # 调用后端注册接口
    result = auth_bridge.register_user(username, email, password)
    
    if result['success']:
        return (
            gr.update(visible=True, value="注册成功！请登录"), 
            gr.update()  # 保持界面显示
        )
    else:
        error_msg = result.get('message', '注册失败')
        if 'errors' in result:
            error_msg += f": {', '.join(result['errors'])}"
        return (
            gr.update(visible=True, value=f"注册失败: {error_msg}"), 
            gr.update()
        )


def handle_logout():
    """处理用户登出"""
    global current_user, auth_token
    
    if auth_token and auth_bridge:
        result = auth_bridge.logout_user()
        current_user = None
        auth_token = None
        auth_bridge.current_user = None
        
        return gr.update(), gr.update(value="")  # 返回login_page和user_info_section的更新
    else:
        return gr.update(), gr.update(value="")


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