#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带认证系统的启动脚本

同时启动Flask API服务和Gradio Web界面
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthSystemLauncher:
    """认证系统启动器"""
    
    def __init__(self):
        self.flask_process = None
        self.gradio_process = None
        self.running = True
        
        # 确保必要的目录存在
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            'data',
            'data/users',
            'data/uploads',
            'data/transcripts',
            'data/memory',
            'data/sessions',
            'data/vectors',
            'models',
            'logs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        logger.info("必要的目录已创建")
    
    def start_flask_app(self):
        """启动Flask应用"""
        try:
            logger.info("启动Flask API服务...")
            
            # 启动Flask应用
            flask_cmd = [
                sys.executable, 
                str(project_root / 'deploy' / 'flask_app.py')
            ]
            
            self.flask_process = subprocess.Popen(
                flask_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 监控Flask输出
            def monitor_flask():
                while self.running and self.flask_process and self.flask_process.poll() is None:
                    line = self.flask_process.stdout.readline()
                    if line:
                        logger.info(f"[Flask] {line.strip()}")
                    time.sleep(0.1)
            
            flask_monitor = threading.Thread(target=monitor_flask)
            flask_monitor.daemon = True
            flask_monitor.start()
            
            # 等待Flask启动
            time.sleep(3)
            
            # 检查Flask是否启动成功
            if self.flask_process.poll() is None:
                logger.info("Flask API服务启动成功 (http://localhost:5001)")
                return True
            else:
                logger.error("Flask API服务启动失败")
                return False
                
        except Exception as e:
            logger.error(f"启动Flask应用失败: {e}")
            return False
    
    def start_gradio_app(self):
        """启动Gradio应用"""
        try:
            logger.info("启动Gradio Web界面...")
            
            # 启动Gradio应用
            gradio_cmd = [
                sys.executable,
                str(project_root / 'deploy' / 'app.py')
            ]
            
            self.gradio_process = subprocess.Popen(
                gradio_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 监控Gradio输出
            def monitor_gradio():
                while self.running and self.gradio_process and self.gradio_process.poll() is None:
                    line = self.gradio_process.stdout.readline()
                    if line:
                        logger.info(f"[Gradio] {line.strip()}")
                    time.sleep(0.1)
            
            gradio_monitor = threading.Thread(target=monitor_gradio)
            gradio_monitor.daemon = True
            gradio_monitor.start()
            
            # 等待Gradio启动
            time.sleep(5)
            
            # 检查Gradio是否启动成功
            if self.gradio_process.poll() is None:
                logger.info("Gradio Web界面启动成功 (http://localhost:7860)")
                return True
            else:
                logger.error("Gradio Web界面启动失败")
                return False
                
        except Exception as e:
            logger.error(f"启动Gradio应用失败: {e}")
            return False
    
    def stop_all(self):
        """停止所有服务"""
        logger.info("正在停止所有服务...")
        self.running = False
        
        if self.flask_process:
            self.flask_process.terminate()
            self.flask_process.wait()
            logger.info("Flask API服务已停止")
        
        if self.gradio_process:
            self.gradio_process.terminate()
            self.gradio_process.wait()
            logger.info("Gradio Web界面已停止")
    
    def run(self):
        """运行认证系统"""
        logger.info("=== AI视频助手认证系统启动 ===")
        
        # 注册信号处理器
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在停止服务...")
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # 启动Flask应用
            if not self.start_flask_app():
                logger.error("Flask应用启动失败，退出")
                return
            
            # 启动Gradio应用
            if not self.start_gradio_app():
                logger.error("Gradio应用启动失败，退出")
                self.stop_all()
                return
            
            logger.info("=== 所有服务启动完成 ===")
            logger.info("Flask API: http://localhost:5001")
            logger.info("Gradio Web: http://localhost:7860")
            logger.info("按 Ctrl+C 停止服务")
            
            # 保持运行
            while self.running:
                time.sleep(1)
                
                # 检查进程状态
                if self.flask_process and self.flask_process.poll() is not None:
                    logger.error("Flask进程意外退出")
                    break
                
                if self.gradio_process and self.gradio_process.poll() is not None:
                    logger.error("Gradio进程意外退出")
                    break
        
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止服务...")
        
        except Exception as e:
            logger.error(f"运行过程中发生错误: {e}")
        
        finally:
            self.stop_all()
            logger.info("=== 所有服务已停止 ===")


def main():
    """主函数"""
    launcher = AuthSystemLauncher()
    launcher.run()


if __name__ == '__main__':
    main()