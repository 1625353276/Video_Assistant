#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频提取模块

职责：
- 从视频中提取音频流
- 转换为Whisper需要的.wav格式
- 统一音频参数（单声道，16kHz采样率）
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioExtractor:
    """音频提取服务"""
    
    def __init__(self):
        """初始化音频提取器"""
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_video_assistant"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Whisper推荐的音频参数
        self.target_sample_rate = 16000  # 16kHz
        self.target_channels = 1  # 单声道
        self.target_format = "wav"  # WAV格式
    
    def extract_audio(self, video_path: Path) -> Path:
        """
        从视频文件中提取音频并转换为Whisper需要的格式
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Path: 提取的音频文件路径
            
        Raises:
            RuntimeError: 音频提取失败时抛出异常
        """
        try:
            logger.info(f"开始从视频提取音频: {video_path}")
            
            # 生成输出音频文件路径
            audio_filename = f"{video_path.stem}_extracted.wav"
            audio_path = self.temp_dir / audio_filename
            
            # 使用ffmpeg提取音频
            self._extract_with_ffmpeg(video_path, audio_path)
            
            # 验证提取的音频文件
            if not audio_path.exists():
                raise RuntimeError("音频提取失败：输出文件不存在")
            
            # 检查音频文件大小
            file_size = audio_path.stat().st_size
            if file_size == 0:
                raise RuntimeError("音频提取失败：输出文件为空")
            
            logger.info(f"音频提取成功: {audio_path}")
            logger.info(f"音频文件大小: {file_size / (1024*1024):.2f} MB")
            
            return audio_path
            
        except Exception as e:
            logger.error(f"音频提取失败: {str(e)}")
            raise RuntimeError(f"音频提取失败: {str(e)}")
    
    def _extract_with_ffmpeg(self, video_path: Path, audio_path: Path) -> None:
        """
        使用ffmpeg提取音频
        
        Args:
            video_path: 输入视频文件路径
            audio_path: 输出音频文件路径
        """
        # 构建ffmpeg命令
        # -vn: 不包含视频流
        # -acodec pcm_s16le: 使用PCM 16位编码
        # -ar 16000: 设置采样率为16kHz
        # -ac 1: 设置为单声道
        # -y: 覆盖输出文件
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # 不包含视频
            "-acodec", "pcm_s16le",  # 音频编码器
            "-ar", str(self.target_sample_rate),  # 采样率
            "-ac", str(self.target_channels),  # 声道数
            "-y",  # 覆盖输出文件
            str(audio_path)
        ]
        
        try:
            # 执行ffmpeg命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                raise RuntimeError(f"ffmpeg执行失败: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("音频提取超时")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg未找到，请确保已安装ffmpeg")
    
    def extract_audio_with_progress(self, video_path: Path, progress_callback=None) -> Path:
        """
        带进度回调的音频提取
        
        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数
            
        Returns:
            Path: 提取的音频文件路径
        """
        try:
            logger.info(f"开始提取音频（带进度）: {video_path}")
            
            # 生成输出音频文件路径
            audio_filename = f"{video_path.stem}_extracted.wav"
            audio_path = self.temp_dir / audio_filename
            
            # 构建ffmpeg命令（包含进度信息）
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", str(self.target_sample_rate),
                "-ac", str(self.target_channels),
                "-progress", "pipe:1",  # 输出进度到stdout
                "-y",
                str(audio_path)
            ]
            
            # 启动ffmpeg进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # 读取进度信息
            total_duration = None
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output and progress_callback:
                    # 解析ffmpeg进度输出
                    if "out_time_ms=" in output:
                        try:
                            time_ms = int(output.split("out_time_ms=")[1].strip())
                            current_time = time_ms / 1000000  # 转换为秒
                            
                            if total_duration:
                                progress = min(100, (current_time / total_duration) * 100)
                                progress_callback(progress)
                        except (ValueError, IndexError):
                            pass
                    
                    # 获取总时长
                    if "Duration:" in output and total_duration is None:
                        try:
                            duration_str = output.split("Duration:")[1].split(",")[0].strip()
                            total_duration = self._parse_duration(duration_str)
                        except (IndexError, ValueError):
                            pass
            
            # 检查执行结果
            if process.returncode != 0:
                error_msg = process.stderr.read()
                raise RuntimeError(f"ffmpeg执行失败: {error_msg}")
            
            logger.info(f"音频提取完成: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"音频提取失败: {str(e)}")
            raise RuntimeError(f"音频提取失败: {str(e)}")
    
    def _parse_duration(self, duration_str: str) -> float:
        """
        解析时长字符串（格式：HH:MM:SS.ms）
        
        Args:
            duration_str: 时长字符串
            
        Returns:
            float: 时长（秒）
        """
        try:
            parts = duration_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except (IndexError, ValueError):
            return 0.0
    
    def get_audio_info(self, audio_path: Path) -> Dict:
        """
        获取音频文件信息
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Dict: 音频信息字典
        """
        try:
            # 使用ffprobe获取音频信息
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_format",
                "-show_streams",
                "-select_streams", "a",  # 只选择音频流
                str(audio_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"ffprobe执行失败: {result.stderr}")
            
            # 解析输出
            info = {
                "file_path": str(audio_path),
                "file_size": audio_path.stat().st_size,
                "file_size_mb": round(audio_path.stat().st_size / (1024 * 1024), 2)
            }
            
            # 简单解析关键信息
            output = result.stdout
            if "sample_rate=" in output:
                sample_rate = output.split("sample_rate=")[1].split("\n")[0]
                info["sample_rate"] = int(sample_rate)
            
            if "channels=" in output:
                channels = output.split("channels=")[1].split("\n")[0]
                info["channels"] = int(channels)
            
            if "duration=" in output:
                duration = output.split("duration=")[1].split("\n")[0]
                info["duration"] = float(duration)
            
            return info
            
        except Exception as e:
            logger.error(f"获取音频信息失败: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_temp_files(self) -> None:
        """清理临时音频文件"""
        try:
            for file_path in self.temp_dir.glob("*.wav"):
                file_path.unlink()
                logger.info(f"已清理临时文件: {file_path}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
    
    def __del__(self):
        """析构函数，清理临时文件"""
        self.cleanup_temp_files()