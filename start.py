#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 一键启动脚本

同时启动Flask认证服务和Gradio Web界面
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# 设置环境变量
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
os.environ['SSL_VERIFY'] = 'false'

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.flask_process = None
        self.gradio_process = None
        self.running = True
    
    def start_flask_service(self):
        """启动Flask认证服务"""
        print("🚀 启动Flask认证服务...")
        try:
            # 启动Flask服务
            flask_app_path = project_root / "deploy" / "flask_app.py"
            self.flask_process = subprocess.Popen(
                [sys.executable, str(flask_app_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待Flask服务启动
            time.sleep(3)
            
            if self.flask_process.poll() is None:
                print("✅ Flask认证服务启动成功 (http://localhost:5001)")
                return True
            else:
                print("❌ Flask认证服务启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动Flask服务时发生错误: {e}")
            return False
    
    def start_gradio_service(self):
        """启动Gradio Web界面"""
        print("🚀 启动Gradio Web界面...")
        try:
            # 启动Gradio应用
            gradio_app_path = project_root / "deploy" / "app.py"
            self.gradio_process = subprocess.Popen(
                [sys.executable, str(gradio_app_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待Gradio服务启动
            time.sleep(5)
            
            if self.gradio_process.poll() is None:
                print("✅ Gradio Web界面启动成功")
                print("🌐 请在浏览器中访问: http://localhost:7860")
                return True
            else:
                print("❌ Gradio Web界面启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动Gradio服务时发生错误: {e}")
            return False
    
    def monitor_services(self):
        """监控服务状态"""
        while self.running:
            time.sleep(2)
            
            # 检查Flask服务状态
            if self.flask_process and self.flask_process.poll() is not None:
                print("⚠️ Flask服务已停止")
                self.running = False
            
            # 检查Gradio服务状态
            if self.gradio_process and self.gradio_process.poll() is not None:
                print("⚠️ Gradio服务已停止")
                self.running = False
    
    def stop_services(self):
        """停止所有服务"""
        print("\n🛑 正在停止服务...")
        self.running = False
        
        if self.flask_process:
            self.flask_process.terminate()
            self.flask_process.wait()
            print("✅ Flask服务已停止")
        
        if self.gradio_process:
            self.gradio_process.terminate()
            self.gradio_process.wait()
            print("✅ Gradio服务已停止")
        
        print("👋 所有服务已停止，再见！")
    
    def run(self):
        """运行所有服务"""
        print("=" * 60)
        print("🎬 AI视频助手 - 一键启动")
        print("=" * 60)
        
        # 注册信号处理器
        def signal_handler(signum, frame):
            self.stop_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动Flask服务
        if not self.start_flask_service():
            return
        
        # 启动Gradio服务
        if not self.start_gradio_service():
            self.stop_services()
            return
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
        monitor_thread.start()
        
        print("\n" + "=" * 60)
        print("🎉 所有服务启动成功！")
        print("📝 使用说明:")
        print("   1. 打开浏览器访问: http://localhost:7860")
        print("   2. 注册新用户或登录现有用户")
        print("   3. 上传视频文件开始使用")
        print("   4. 按 Ctrl+C 停止所有服务")
        print("=" * 60)
        
        try:
            # 保持主线程运行
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_services()


def main():
    """主函数"""
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return
    
    # 检查依赖
    try:
        import flask
        import gradio as gr
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("💡 请运行: pip install -r requirements.txt")
        return
    
    # 创建服务管理器并运行
    manager = ServiceManager()
    manager.run()


if __name__ == "__main__":
    main()