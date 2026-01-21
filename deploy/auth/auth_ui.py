#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证界面组件
"""

import gradio as gr


def create_auth_interface():
    """创建登录注册界面"""
    # 创建主容器
    auth_interface = gr.Group(visible=True)
    
    # 创建选项卡
    with gr.Tabs():
        with gr.Tab("登录"):
            # 登录组件
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
            # 注册组件
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
    # 创建主容器
    user_info_group = gr.Group(visible=False)
    
    # 创建行容器
    with user_info_group:
        user_display = gr.Textbox(
            label="当前用户", 
            interactive=False,
            value="未登录"
        )
        logout_btn = gr.Button("登出", size="sm")
    
    return user_info_group, user_display, logout_btn