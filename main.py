#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 主处理入口

负责接收视频路径，串联整个后端处理流程：
视频文件 -> 视频合法性校验 -> 音频提取 -> Whisper语音转文本 -> 文本结果保存
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.video.video_loader import VideoLoader
from modules.video.audio_extractor import AudioExtractor
from modules.speech.whisper_asr import WhisperASR
from modules.utils.file_manager import FileManager


def main():
    """主处理函数 - 视频到文本的完整流水线"""
    parser = argparse.ArgumentParser(description="AI视频助手 - 视频内容转文本处理")
    parser.add_argument("--video", type=str, required=True, help="输入视频文件路径")
    parser.add_argument("--output", type=str, default="data/transcripts", help="输出目录路径")
    parser.add_argument("--model", type=str, default="base", help="Whisper模型大小 (tiny/base/small/medium/large)")
    
    args = parser.parse_args()
    
    # 验证输入文件
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"错误：视频文件不存在 - {video_path}")
        return 1
    
    # 初始化各个服务模块
    video_loader = VideoLoader()
    audio_extractor = AudioExtractor()
    whisper_asr = WhisperASR(model_size=args.model)
    file_manager = FileManager()
    
    try:
        # 1. 视频合法性校验
        print(f"正在处理视频文件: {video_path}")
        video_info = video_loader.validate_video(video_path)
        print(f"视频信息: {video_info}")
        
        # 2. 音频提取
        print("正在提取音频...")
        audio_path = audio_extractor.extract_audio(video_path)
        print(f"音频已保存至: {audio_path}")
        
        # 3. Whisper语音识别
        print("正在进行语音转文本...")
        transcript_result = whisper_asr.transcribe(audio_path)
        print("语音转文本完成")
        
        # 4. 保存结构化结果
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        video_name = video_path.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON格式结果
        json_output_path = output_dir / f"{video_name}_{timestamp}.json"
        file_manager.save_transcript_json(transcript_result, json_output_path)
        
        # 保存纯文本格式结果
        txt_output_path = output_dir / f"{video_name}_{timestamp}.txt"
        file_manager.save_transcript_text(transcript_result, txt_output_path)
        
        print(f"转写结果已保存:")
        print(f"  JSON格式: {json_output_path}")
        print(f"  纯文本格式: {txt_output_path}")
        
        # 清理临时音频文件
        if audio_path.exists():
            audio_path.unlink()
            print("临时音频文件已清理")
        
        return 0
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)