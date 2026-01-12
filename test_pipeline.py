#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端流程测试脚本

用于测试视频处理流水线的各个模块
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.video.video_loader import VideoLoader
from modules.video.audio_extractor import AudioExtractor
from modules.speech.whisper_asr import WhisperASR
from modules.utils.file_manager import FileManager


def test_video_loader():
    """测试视频加载器"""
    print("=" * 50)
    print("测试视频加载器")
    print("=" * 50)
    
    loader = VideoLoader()
    
    # 测试支持的格式
    print(f"支持的视频格式: {loader.SUPPORTED_FORMATS}")
    print(f"最大文件大小: {loader.MAX_FILE_SIZE / (1024*1024*1024)} GB")
    
    return loader


def test_audio_extractor():
    """测试音频提取器"""
    print("=" * 50)
    print("测试音频提取器")
    print("=" * 50)
    
    extractor = AudioExtractor()
    
    print(f"目标采样率: {extractor.target_sample_rate} Hz")
    print(f"目标声道数: {extractor.target_channels}")
    print(f"目标格式: {extractor.target_format}")
    print(f"临时目录: {extractor.temp_dir}")
    
    return extractor


def test_whisper_asr():
    """测试Whisper ASR"""
    print("=" * 50)
    print("测试Whisper ASR")
    print("=" * 50)
    
    try:
        # 使用tiny模型进行快速测试
        asr = WhisperASR(model_size="tiny")
        
        # 获取模型信息
        model_info = asr.get_model_info()
        print("模型信息:")
        for key, value in model_info.items():
            print(f"  {key}: {value}")
        
        return asr
        
    except Exception as e:
        print(f"Whisper ASR初始化失败: {str(e)}")
        print("这可能是因为缺少依赖或模型下载失败")
        return None


def test_file_manager():
    """测试文件管理器"""
    print("=" * 50)
    print("测试文件管理器")
    print("=" * 50)
    
    manager = FileManager()
    
    print(f"支持的输出格式: {manager.supported_formats}")
    
    # 测试创建输出结构
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_paths = manager.create_output_structure(temp_path, "test_video")
        
        print("创建的输出文件路径:")
        for format_name, path in file_paths.items():
            print(f"  {format_name}: {path}")
    
    return manager


def test_integration():
    """测试集成流程（需要实际视频文件）"""
    print("=" * 50)
    print("集成流程测试")
    print("=" * 50)
    
    print("注意：集成测试需要实际的视频文件")
    print("请使用以下命令运行完整测试：")
    print("python main.py --video /path/to/your/video.mp4 --model tiny")
    
    # 创建测试数据
    test_data = {
        "audio_file": "test.wav",
        "language": "zh",
        "text": "这是一个测试文本。",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "这是一个测试文本。",
                "confidence": 0.95
            }
        ]
    }
    
    # 测试文件管理器
    manager = FileManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 测试保存JSON
        json_path = temp_path / "test.json"
        manager.save_transcript_json(test_data, json_path)
        print(f"JSON测试文件已创建: {json_path}")
        
        # 测试保存文本
        txt_path = temp_path / "test.txt"
        manager.save_transcript_text(test_data, txt_path)
        print(f"文本测试文件已创建: {txt_path}")
        
        # 测试保存SRT
        srt_path = temp_path / "test.srt"
        manager.save_transcript_srt(test_data, srt_path)
        print(f"SRT测试文件已创建: {srt_path}")
        
        # 测试保存VTT
        vtt_path = temp_path / "test.vtt"
        manager.save_transcript_vtt(test_data, vtt_path)
        print(f"VTT测试文件已创建: {vtt_path}")


def check_dependencies():
    """检查依赖项"""
    print("=" * 50)
    print("检查依赖项")
    print("=" * 50)
    
    dependencies = {
        "torch": "PyTorch",
        "cv2": "OpenCV",
        "whisper": "OpenAI Whisper",
        "pathlib": "Pathlib",
        "json": "JSON",
        "subprocess": "Subprocess"
    }
    
    missing_deps = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {name} - 已安装")
        except ImportError:
            print(f"✗ {name} - 未安装")
            missing_deps.append(name)
    
    # 检查ffmpeg
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ FFmpeg - 已安装")
        else:
            print("✗ FFmpeg - 未正确安装")
            missing_deps.append("FFmpeg")
    except FileNotFoundError:
        print("✗ FFmpeg - 未安装")
        missing_deps.append("FFmpeg")
    
    if missing_deps:
        print("\n缺少的依赖项:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        if "FFmpeg" in missing_deps:
            print("并安装FFmpeg:")
            print("  macOS: brew install ffmpeg")
            print("  Ubuntu: sudo apt install ffmpeg")
    else:
        print("\n所有依赖项已正确安装！")
    
    return len(missing_deps) == 0


def main():
    """主测试函数"""
    print("AI视频助手 - 后端流程测试")
    print("=" * 50)
    
    # 检查依赖
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n请先安装缺少的依赖项，然后重新运行测试")
        return 1
    
    print("\n")
    
    # 测试各个模块
    try:
        test_video_loader()
        print("\n")
        
        test_audio_extractor()
        print("\n")
        
        test_whisper_asr()
        print("\n")
        
        test_file_manager()
        print("\n")
        
        test_integration()
        print("\n")
        
        print("=" * 50)
        print("所有模块测试完成！")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)