#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的认证应用

用于测试认证功能的简化版本
"""

import os
import sys
import requests
import gradio as gr

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from integration.gradio_bridge import GradioBridge
    print("✓ GradioBridge 导入成功")
except ImportError as e:
    print(f"✗ GradioBridge 导入失败: {e}")
    GradioBridge = None

# 全局变量
auth_bridge = None
current_user = None
auth_token = None

# 初始化认证桥接器
if GradioBridge:
    try:
        auth_bridge = GradioBridge("http://localhost:5001")
        print("✓ 认证桥接器初始化成功")
    except Exception as e:
        print(f"✗ 认证桥接器初始化失败: {e}")
        auth_bridge = None

def check_flask_service():
    """检查Flask服务是否运行"""
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def handle_login(username, password):
    """处理用户登录"""
    global current_user, auth_token
    
    if not username or not password:
        return "请输入用户名和密码", False
    
    if not auth_bridge:
        return "认证服务不可用", False
    
    try:
        result = auth_bridge.login_user(username, password)
        
        if result['success']:
            current_user = {
                'user_id': result['user_id'],
                'username': result['username'],
                'token': result['token']
            }
            auth_token = result['token']
            
            # 创建用户数据目录
            try:
                user_data_dir = auth_bridge.create_user_data_dir(result['user_id'])
                print(f"用户数据目录创建成功: {user_data_dir}")
            except Exception as e:
                print(f"用户数据目录创建失败: {e}")
            
            return "登录成功！", True
        else:
            return f"登录失败: {result['message']}", False
    except Exception as e:
        return f"登录异常: {e}", False

def handle_register(username, email, password, confirm_password):
    """处理用户注册"""
    if not username or not email or not password:
        return "请填写所有字段", False
    
    if password != confirm_password:
        return "两次输入的密码不一致", False
    
    # 基本验证
    if len(username) < 3 or len(username) > 30:
        return "用户名长度应为3-30位", False
    
    if '@' not in email:
        return "请输入有效的邮箱地址", False
    
    if len(password) < 6:
        return "密码长度至少6位", False
    
    if not auth_bridge:
        return "认证服务不可用", False
    
    try:
        result = auth_bridge.register_user(username, email, password)
        
        if result['success']:
            return "注册成功！请登录", True
        else:
            error_msg = result.get('message', '注册失败')
            if 'errors' in result:
                error_msg += f": {', '.join(result['errors'])}"
            return f"注册失败: {error_msg}", False
    except Exception as e:
        return f"注册异常: {e}", False

def handle_logout():
    """处理用户登出"""
    global current_user, auth_token
    
    if auth_token and auth_bridge:
        try:
            result = auth_bridge.logout_user()
            current_user = None
            auth_token = None
            return "登出成功", True
        except Exception as e:
            return f"登出异常: {e}", False
    else:
        return "登出失败", False

def get_user_info():
    """获取用户信息"""
    global current_user
    if current_user:
        return f"""
用户ID: {current_user['user_id']}
用户名: {current_user['username']}
登录状态: 已登录
"""
    else:
        return "未登录"

def test_user_profile():
    """测试获取用户资料"""
    global current_user, auth_bridge
    if not current_user or not auth_bridge:
        return "用户未登录或认证服务不可用"
    
    try:
        result = auth_bridge.get_user_profile()
        if result['success']:
            return f"用户资料获取成功:\n{result}"
        else:
            return f"用户资料获取失败: {result['message']}"
    except Exception as e:
        return f"用户资料获取异常: {e}"

def test_user_videos():
    """测试获取用户视频"""
    global current_user, auth_bridge
    if not current_user or not auth_bridge:
        return "用户未登录或认证服务不可用"
    
    try:
        result = auth_bridge.get_user_videos(current_user['user_id'])
        if result['success']:
            return f"用户视频获取成功:\n找到 {result['count']} 个视频"
        else:
            return f"用户视频获取失败: {result['message']}"
    except Exception as e:
        return f"用户视频获取异常: {e}"

def create_simple_auth_app():
    """创建简化的认证应用"""
    
    with gr.Blocks(title="认证系统测试") as demo:
        gr.Markdown("# 🔐 用户认证系统测试")
        
        # 状态显示
        status_display = gr.Textbox(
            label="当前状态",
            value="等待操作...",
            interactive=False
        )
        
        # 认证界面
        with gr.Group() as auth_group:
            gr.Markdown("## 认证操作")
            
            with gr.Tabs():
                with gr.TabItem("登录"):
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
                
                with gr.TabItem("注册"):
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
                        placeholder="至少6位"
                    )
                    reg_confirm_password = gr.Textbox(
                        label="确认密码", 
                        type="password",
                        placeholder="请再次输入密码"
                    )
                    reg_btn = gr.Button("注册", variant="primary")
        
        # 用户操作界面
        with gr.Group(visible=False) as user_group:
            gr.Markdown("## 用户操作")
            
            logout_btn = gr.Button("登出", variant="secondary")
            
            with gr.Tabs():
                with gr.TabItem("用户信息"):
                    user_info = gr.Markdown(get_user_info())
                    refresh_info_btn = gr.Button("刷新信息")
                
                with gr.TabItem("功能测试"):
                    with gr.Row():
                        test_profile_btn = gr.Button("获取用户资料")
                        test_videos_btn = gr.Button("获取用户视频")
                    
                    test_result = gr.Textbox(
                        label="测试结果",
                        lines=5,
                        interactive=False
                    )
        
        # 事件绑定
        def login_handler(username, password):
            message, success = handle_login(username, password)
            if success:
                # 登录成功：隐藏认证界面，显示用户界面
                return message, gr.update(visible=False), gr.update(visible=True)
            else:
                # 登录失败：保持认证界面显示
                return message, gr.update(visible=True), gr.update(visible=False)
        
        def register_handler(username, email, password, confirm_password):
            message, success = handle_register(username, email, password, confirm_password)
            return message
        
        def logout_handler():
            message, success = handle_logout()
            if success:
                # 登出成功：显示认证界面，隐藏用户界面
                return message, gr.update(visible=True), gr.update(visible=False)
            else:
                # 登出失败：保持当前状态
                return message, gr.update(visible=False), gr.update(visible=True)
        
        login_btn.click(
            fn=login_handler,
            inputs=[login_username, login_password],
            outputs=[status_display, auth_group, user_group]
        )
        
        reg_btn.click(
            fn=register_handler,
            inputs=[reg_username, reg_email, reg_password, reg_confirm_password],
            outputs=[status_display]
        )
        
        logout_btn.click(
            fn=logout_handler,
            outputs=[status_display, auth_group, user_group]
        )
        
        refresh_info_btn.click(
            fn=get_user_info,
            outputs=[user_info]
        )
        
        test_profile_btn.click(
            fn=test_user_profile,
            outputs=[test_result]
        )
        
        test_videos_btn.click(
            fn=test_user_videos,
            outputs=[test_result]
        )
    
    return demo

if __name__ == "__main__":
    # 检查Flask认证服务
    if not check_flask_service():
        print("❌ Flask认证服务未启动，请先运行：")
        print("   python deploy/flask_app.py")
        print("或者使用集成启动脚本：")
        print("   python start_with_auth.py")
        print("\nFlask认证服务需要在端口5001上运行")
        sys.exit(1)
    
    print("✅ Flask认证服务正常运行")
    
    # 创建并启动界面
    demo = create_simple_auth_app()
    demo.launch(
        server_name="localhost",
        server_port=None,
        share=False,
        debug=True
    )