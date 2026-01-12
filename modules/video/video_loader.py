#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理服务模块

职责：
- 校验视频格式（mp4 / avi / mkv）
- 管理视频文件存储路径
- 提取视频基本信息
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List
import cv2


class VideoLoader:
    """视频加载和验证服务"""
    
    # 支持的视频格式
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
    
    # 最大文件大小 (2GB)
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024
    
    def __init__(self):
        """初始化视频加载器"""
        self.supported_codecs = ['H264', 'H265', 'AVC', 'HEVC', 'VP9', 'AV1']
    
    def validate_video(self, video_path: Path) -> Dict:
        """
        验证视频文件的合法性和完整性
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict: 包含视频信息的字典
            
        Raises:
            ValueError: 视频文件不合法时抛出异常
        """
        # 检查文件是否存在
        if not video_path.exists():
            raise ValueError(f"视频文件不存在: {video_path}")
        
        # 检查文件格式
        if video_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的视频格式: {video_path.suffix}. 支持的格式: {self.SUPPORTED_FORMATS}")
        
        # 检查文件大小
        file_size = video_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"视频文件过大: {file_size / (1024*1024*1024):.2f}GB. 最大支持: {self.MAX_FILE_SIZE / (1024*1024*1024)}GB")
        
        if file_size == 0:
            raise ValueError("视频文件为空")
        
        # 使用OpenCV验证视频完整性
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                raise ValueError("无法打开视频文件，可能文件已损坏")
            
            # 获取视频基本信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            # 检查视频内容
            ret, frame = cap.read()
            if not ret or frame is None:
                raise ValueError("视频文件无有效帧内容")
            
            cap.release()
            
            # 检查基本参数合理性
            if fps <= 0 or fps > 120:
                raise ValueError(f"视频帧率异常: {fps}")
            
            if width <= 0 or height <= 0:
                raise ValueError(f"视频分辨率异常: {width}x{height}")
            
            if duration <= 0:
                raise ValueError(f"视频时长异常: {duration}")
            
            # 返回视频信息
            video_info = {
                "file_path": str(video_path),
                "file_name": video_path.name,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "format": video_path.suffix.lower(),
                "resolution": f"{width}x{height}",
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "frame_count": frame_count,
                "duration": round(duration, 2),
                "duration_formatted": self._format_duration(duration),
                "aspect_ratio": round(width / height, 2),
                "validation_status": "passed"
            }
            
            return video_info
            
        except Exception as e:
            if "cap" in locals():
                cap.release()
            raise ValueError(f"视频验证失败: {str(e)}")
    
    def _format_duration(self, duration_seconds: float) -> str:
        """
        格式化时长显示
        
        Args:
            duration_seconds: 时长（秒）
            
        Returns:
            str: 格式化的时长字符串 (HH:MM:SS)
        """
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_video_metadata(self, video_path: Path) -> Dict:
        """
        获取视频详细元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict: 视频元数据信息
        """
        # 先进行基础验证
        basic_info = self.validate_video(video_path)
        
        try:
            # 尝试获取更多详细信息
            cap = cv2.VideoCapture(str(video_path))
            
            # 获取编码信息
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            # 获取比特率（估算）
            bitrate = (basic_info["file_size"] * 8) / basic_info["duration"] if basic_info["duration"] > 0 else 0
            
            cap.release()
            
            # 添加详细信息
            detailed_info = {
                **basic_info,
                "codec": codec,
                "bitrate": round(bitrate, 2),
                "bitrate_kbps": round(bitrate / 1000, 2),
                "estimated_quality": self._estimate_quality(basic_info, bitrate)
            }
            
            return detailed_info
            
        except Exception as e:
            # 如果获取详细信息失败，返回基础信息
            return basic_info
    
    def _estimate_quality(self, video_info: Dict, bitrate: float) -> str:
        """
        估算视频质量
        
        Args:
            video_info: 视频基本信息
            bitrate: 比特率
            
        Returns:
            str: 质量评级
        """
        resolution = video_info["width"] * video_info["height"]
        fps = video_info["fps"]
        
        # 简单的质量评估算法
        if resolution >= 1920 * 1080 and fps >= 30 and bitrate > 5000000:
            return "高质量"
        elif resolution >= 1280 * 720 and fps >= 25 and bitrate > 2000000:
            return "中等质量"
        elif resolution >= 640 * 480 and fps >= 15:
            return "基础质量"
        else:
            return "低质量"
    
    def check_video_integrity(self, video_path: Path) -> bool:
        """
        检查视频文件完整性
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            bool: 文件是否完整
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                return False
            
            # 尝试读取首尾帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_first, _ = cap.read()
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 1))
            ret_last, _ = cap.read()
            
            cap.release()
            
            return ret_first and ret_last
            
        except Exception:
            return False