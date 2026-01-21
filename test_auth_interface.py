#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试认证界面

简化的认证界面测试，验证登录注册功能
"""

import gradio as gr
import sys
import requests
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

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
        return "请输入用户名和密码", gr.update(visible=True)
    
    if not auth_bridge:
        return "认证服务不可用", gr.update(visible=True)
    
    # 调用后端登录接口
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
        
        return "登录成功！", gr.update(visible=False)
    else:
        return f"登录失败: {result['message']}", gr.update(visible=True)

def handle_register(username, email, password, confirm_password):
    """处理用户注册"""
    if not username or not email or not password:
        return "请填写所有字段"
    
    if password != confirm_password:
        return "两次输入的密码不一致"
    
    # 基本验证
    if len(username) < 3 or len(username) > 30:
        return "用户名长度应为3-30位"
    
    if '@' not in email:
        return "请输入有效的邮箱地址"
    
    if len(password) < 6:
        return "密码长度至少6位"
    
    if not auth_bridge:
        return "认证服务不可用"
    
    # 调用后端注册接口
    result = auth_bridge.register_user(username, email, password)
    
    if result['success']:
        return "注册成功！请登录"
    else:
        error_msg = result.get('message', '注册失败')
        if 'errors' in result:
            error_msg += f": {', '.join(result['errors'])}"
        return f"注册失败: {error_msg}"

def handle_logout():
    """处理用户登出"""
    global current_user, auth_token
    
    if auth_token and auth_bridge:
        result = auth_bridge.logout_user()
        current_user = None
        auth_token = None
        return "登出成功", gr.update(visible=True), gr.update(value="未登录")
    else:
        return "登出失败", gr.update(visible=True), gr.update(value="未登录")

def update_user_info():
    """更新用户信息显示"""
    global current_user
    
    if current_user:
        return f"用户: {current_user['username']}", gr.update(visible=True)
    else:
        return "未登录", gr.update(visible=False)

def check_auth_status():
    """检查认证状态"""
    global current_user
    
    if current_user:
        return (
            gr.update(visible=False),  # 隐藏认证界面
            gr.update(visible=True),   # 显示用户信息
            gr.update(value=f"用户: {current_user['username']}")
        )
    else:
        return (
            gr.update(visible=True),   # 显示认证界面
            gr.update(visible=False),  # 隐藏用户信息
            gr.update(value="未登录")
        )

def create_test_interface():
    """创建测试界面"""
    
    with gr.Blocks(title="认证系统测试", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🔐 用户认证系统测试")
        
        # 认证界面
        with gr.Group(visible=True) as auth_group:
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
                            label="状态", 
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
                            label="状态", 
                            interactive=False
                        )
        
        # 用户信息显示
        with gr.Group(visible=False) as user_info_group:
            with gr.Row():
                user_display = gr.Textbox(
                    label="当前用户", 
                    interactive=False,
                    value="未登录"
                )
                logout_btn = gr.Button("登出", size="sm")
            
            logout_message = gr.Textbox(
                label="状态", 
                interactive=False
            )
        
        # 测试区域
        with gr.Group(visible=False) as test_group:
            gr.Markdown("## 🧪 认证功能测试")
            
            test_info = gr.JSON(label="当前用户信息")
            
            with gr.Row():
                test_profile_btn = gr.Button("获取用户资料")
                test_videos_btn = gr.Button("获取用户视频")
            
            test_result = gr.Textbox(
                label="测试结果", 
                lines=5,
                interactive=False
            )
        
        # 绑定事件
        login_btn.click(
            fn=handle_login,
            inputs=[login_username, login_password],
            outputs=[login_message, auth_group]
        ).then(
            fn=update_user_info,
            outputs=[user_display, user_info_group]
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=[test_group]
        )
        
        reg_btn.click(
            fn=handle_register,
            inputs=[reg_username, reg_email, reg_password, reg_confirm_password],
            outputs=[reg_message]
        )
        
        logout_btn.click(
            fn=handle_logout,
            outputs=[logout_message, auth_group, user_display]
        ).then(
            fn=lambda: gr.update(visible=False),
            outputs=[test_group]
        )
        
        # 测试功能
        def get_test_info():
            global current_user
            return current_user if current_user else {"status": "未登录"}
        
        def test_user_profile():
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
        
        test_profile_btn.click(
            fn=test_user_profile,
            outputs=[test_result]
        )
        
        test_videos_btn.click(
            fn=test_user_videos,
            outputs=[test_result]
        )
        
        # 定时更新用户信息
        demo.load(
            fn=get_test_info,
            outputs=[test_info]
        )
        
        # 页面加载时检查认证状态
        demo.load(
            fn=check_auth_status,
            outputs=[auth_group, user_info_group, user_display]
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
    
    # 创建并启动测试界面
    demo = create_test_interface()
    demo.launch(
        server_name="localhost",
        server_port=None,
        share=False,
        debug=True
    )