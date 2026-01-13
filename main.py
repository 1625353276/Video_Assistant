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
from modules.text.text_cleaner import TextCleaner
from modules.text.segmenter import TextSegmenter
from modules.text.translator import TextTranslator


def main():
    """主处理函数 - 视频到文本的完整流水线"""
    parser = argparse.ArgumentParser(description="AI视频助手 - 视频内容转文本处理")
    parser.add_argument("--video", type=str, required=True, help="输入视频文件路径")
    parser.add_argument("--output", type=str, default="data/transcripts", help="输出目录路径")
    parser.add_argument("--model", type=str, default="base", help="Whisper模型大小 (tiny/base/small/medium/large)")
    parser.add_argument("--no-clean", action="store_true", help="跳过文本清洗")
    parser.add_argument("--no-segment", action="store_true", help="跳过文本分段")
    parser.add_argument("--no-translate", action="store_true", help="跳过文本翻译")
    parser.add_argument("--target-lang", type=str, default="en", help="翻译目标语言 (zh/en)")
    parser.add_argument("--max-tokens", type=int, default=400, help="分段最大token数")
    
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
    
    # 初始化文本处理模块
    text_cleaner = TextCleaner()
    text_segmenter = TextSegmenter()
    text_translator = TextTranslator()
    
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
        
        # 4. 文本后处理流程
        current_transcript = transcript_result
        
        # 文本清洗
        if not args.no_clean:
            print("正在进行文本清洗...")
            cleaned_transcript = text_cleaner.clean_transcript(current_transcript)
            current_transcript = cleaned_transcript
            print("文本清洗完成")
        else:
            print("跳过文本清洗")
            cleaned_transcript = current_transcript
        
        # 文本分段
        if not args.no_segment:
            print("正在进行文本分段...")
            text_segmenter.max_tokens = args.max_tokens
            segments = text_segmenter.hybrid_segment(cleaned_transcript.get("text", ""), cleaned_transcript)
            segment_stats = text_segmenter.get_segment_statistics(segments)
            print(f"文本分段完成: 共{segment_stats.get('total_segments', 0)}段, 平均{segment_stats.get('avg_tokens_per_segment', 0):.1f} tokens/段")
        else:
            print("跳过文本分段")
            segments = []
            segment_stats = {}
        
        # 文本翻译
        if not args.no_translate:
            print("正在进行文本翻译...")
            # 检测语言并翻译为目标语言
            source_lang = text_translator.detect_language(cleaned_transcript.get("text", ""))
            if source_lang != args.target_lang:
                translated_transcript = text_translator.translate_transcript(cleaned_transcript, args.target_lang)
                print(f"文本翻译完成: {source_lang} -> {args.target_lang}")
            else:
                translated_transcript = cleaned_transcript
                print(f"文本已是{args.target_lang}，无需翻译")
        else:
            print("跳过文本翻译")
            translated_transcript = cleaned_transcript
        
        # 5. 保存结构化结果
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        video_name = video_path.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存原始转录结果
        original_json_path = output_dir / f"{video_name}_{timestamp}_original.json"
        file_manager.save_transcript_json(transcript_result, original_json_path)
        
        # 保存清洗后的结果
        cleaned_json_path = output_dir / f"{video_name}_{timestamp}_cleaned.json"
        file_manager.save_transcript_json(cleaned_transcript, cleaned_json_path)
        
        # 保存翻译后的结果
        translated_json_path = output_dir / f"{video_name}_{timestamp}_translated.json"
        file_manager.save_transcript_json(translated_transcript, translated_json_path)
        
        # 保存分段结果
        segments_json_path = output_dir / f"{video_name}_{timestamp}_segments.json"
        with open(segments_json_path, 'w', encoding='utf-8') as f:
            segments_data = {
                "segments": [
                    {
                        "segment_id": seg.segment_id,
                        "text": seg.text,
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "token_count": seg.token_count
                    } for seg in segments
                ],
                "statistics": segment_stats
            }
            json.dump(segments_data, f, ensure_ascii=False, indent=2)
        
        # 保存纯文本格式结果（清洗后）
        cleaned_txt_path = output_dir / f"{video_name}_{timestamp}_cleaned.txt"
        file_manager.save_transcript_text(cleaned_transcript, cleaned_txt_path)
        
        print(f"处理结果已保存:")
        print(f"  原始转录: {original_json_path}")
        print(f"  清洗后: {cleaned_json_path}")
        print(f"  翻译后: {translated_json_path}")
        print(f"  分段结果: {segments_json_path}")
        print(f"  清洗文本: {cleaned_txt_path}")
        
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