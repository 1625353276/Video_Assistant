#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动视频智能问答助手
"""

import os
import sys
from pathlib import Path

# 设置环境变量以避免NumPy兼容性问题
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入gradio
import gradio as gr

if __name__ == "__main__":
    print("正在启动视频智能问答助手...")
    print("项目根目录:", project_root)
    
    # 检查是否在模拟模式下运行
    try:
        from modules.video.video_loader import VideoLoader
        print("✓ 后端模块加载成功，将使用完整功能")
    except ImportError as e:
        print(f"⚠ 后端模块加载失败 ({e})，将在模拟模式下运行")
        print("  模拟模式下，视频处理和语音识别功能将返回模拟数据")
    
# 启动应用
    from deploy.app import create_video_qa_interface
    
    # 设置环境变量抑制警告
    os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
    
    demo = create_video_qa_interface()
    demo.launch(
        server_name="localhost",
        server_port=None,  # 自动寻找可用端口
        share=False,
        debug=True,
        theme=gr.themes.Soft(),
        show_error=True,
        quiet=False  # 显示重要信息
    )