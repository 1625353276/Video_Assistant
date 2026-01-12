#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理模块

职责：
- 保存转写结果为JSON和文本格式
- 管理输出文件组织结构
- 提供文件操作工具函数
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """文件管理服务"""
    
    def __init__(self):
        """初始化文件管理器"""
        self.supported_formats = ['json', 'txt', 'srt', 'vtt']
    
    def save_transcript_json(self, transcript_data: Dict, output_path: Path) -> None:
        """
        保存转写结果为JSON格式
        
        Args:
            transcript_data: 转写数据
            output_path: 输出文件路径
        """
        try:
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 添加元数据
            enriched_data = {
                **transcript_data,
                "export_info": {
                    "export_time": datetime.now().isoformat(),
                    "export_format": "json",
                    "export_version": "1.0"
                }
            }
            
            # 写入JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON转写结果已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
            raise RuntimeError(f"保存JSON文件失败: {str(e)}")
    
    def save_transcript_text(self, transcript_data: Dict, output_path: Path) -> None:
        """
        保存转写结果为纯文本格式
        
        Args:
            transcript_data: 转写数据
            output_path: 输出文件路径
        """
        try:
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建文本内容
            text_content = self._build_text_content(transcript_data)
            
            # 写入文本文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"文本转写结果已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"保存文本文件失败: {str(e)}")
            raise RuntimeError(f"保存文本文件失败: {str(e)}")
    
    def save_transcript_srt(self, transcript_data: Dict, output_path: Path) -> None:
        """
        保存转写结果为SRT字幕格式
        
        Args:
            transcript_data: 转写数据
            output_path: 输出文件路径
        """
        try:
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建SRT内容
            srt_content = self._build_srt_content(transcript_data)
            
            # 写入SRT文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"SRT字幕文件已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"保存SRT文件失败: {str(e)}")
            raise RuntimeError(f"保存SRT文件失败: {str(e)}")
    
    def save_transcript_vtt(self, transcript_data: Dict, output_path: Path) -> None:
        """
        保存转写结果为VTT字幕格式
        
        Args:
            transcript_data: 转写数据
            output_path: 输出文件路径
        """
        try:
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建VTT内容
            vtt_content = self._build_vtt_content(transcript_data)
            
            # 写入VTT文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(vtt_content)
            
            logger.info(f"VTT字幕文件已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"保存VTT文件失败: {str(e)}")
            raise RuntimeError(f"保存VTT文件失败: {str(e)}")
    
    def _build_text_content(self, transcript_data: Dict) -> str:
        """
        构建纯文本格式内容
        
        Args:
            transcript_data: 转写数据
            
        Returns:
            str: 文本内容
        """
        lines = []
        
        # 添加头部信息
        lines.append("=" * 50)
        lines.append("AI视频助手 - 转写结果")
        lines.append("=" * 50)
        lines.append(f"文件: {transcript_data.get('audio_file_name', 'Unknown')}")
        lines.append(f"语言: {transcript_data.get('language', 'Unknown')}")
        lines.append(f"模型: {transcript_data.get('model_used', 'Unknown')}")
        lines.append(f"总时长: {transcript_data.get('total_duration', 0)} 秒")
        lines.append(f"平均置信度: {transcript_data.get('avg_confidence', 0)}")
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")
        
        # 添加完整文本
        lines.append("【完整转写文本】")
        lines.append(transcript_data.get('text', ''))
        lines.append("")
        
        # 添加分段文本
        lines.append("【分段转写文本】")
        lines.append("-" * 30)
        
        for i, segment in enumerate(transcript_data.get('segments', []), 1):
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            
            lines.append(f"段落 {i} [{start_time} - {end_time}]")
            lines.append(segment['text'])
            lines.append(f"置信度: {segment['confidence']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_srt_content(self, transcript_data: Dict) -> str:
        """
        构建SRT格式内容
        
        Args:
            transcript_data: 转写数据
            
        Returns:
            str: SRT内容
        """
        lines = []
        
        for i, segment in enumerate(transcript_data.get('segments', []), 1):
            start_time = self._format_srt_timestamp(segment['start'])
            end_time = self._format_srt_timestamp(segment['end'])
            
            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(segment['text'])
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_vtt_content(self, transcript_data: Dict) -> str:
        """
        构建VTT格式内容
        
        Args:
            transcript_data: 转写数据
            
        Returns:
            str: VTT内容
        """
        lines = []
        
        # VTT文件头
        lines.append("WEBVTT")
        lines.append("")
        
        for segment in transcript_data.get('segments', []):
            start_time = self._format_vtt_timestamp(segment['start'])
            end_time = self._format_vtt_timestamp(segment['end'])
            
            lines.append(f"{start_time} --> {end_time}")
            lines.append(segment['text'])
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        格式化时间戳为 HH:MM:SS
        
        Args:
            seconds: 秒数
            
        Returns:
            str: 格式化的时间戳
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _format_srt_timestamp(self, seconds: float) -> str:
        """
        格式化SRT时间戳为 HH:MM:SS,mmm
        
        Args:
            seconds: 秒数
            
        Returns:
            str: SRT格式时间戳
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """
        格式化VTT时间戳为 HH:MM:SS.mmm
        
        Args:
            seconds: 秒数
            
        Returns:
            str: VTT格式时间戳
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    def create_output_structure(self, base_dir: Path, video_name: str) -> Dict[str, Path]:
        """
        创建输出目录结构
        
        Args:
            base_dir: 基础输出目录
            video_name: 视频名称
            
        Returns:
            Dict[str, Path]: 各类输出文件的路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建输出目录
        output_dir = base_dir / f"{video_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成各类文件路径
        file_paths = {
            "output_dir": output_dir,
            "json": output_dir / f"{video_name}_{timestamp}.json",
            "txt": output_dir / f"{video_name}_{timestamp}.txt",
            "srt": output_dir / f"{video_name}_{timestamp}.srt",
            "vtt": output_dir / f"{video_name}_{timestamp}.vtt"
        }
        
        return file_paths
    
    def cleanup_old_files(self, directory: Path, days: int = 7) -> None:
        """
        清理旧的输出文件
        
        Args:
            directory: 要清理的目录
            days: 保留天数
        """
        try:
            if not directory.exists():
                return
            
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            
            for file_path in directory.glob("**/*"):
                if file_path.is_file():
                    file_time = file_path.stat().st_mtime
                    if file_time < cutoff_time:
                        file_path.unlink()
                        logger.info(f"已清理旧文件: {file_path}")
                        
        except Exception as e:
            logger.error(f"清理旧文件失败: {str(e)}")
    
    def get_output_summary(self, output_dir: Path) -> Dict:
        """
        获取输出文件摘要
        
        Args:
            output_dir: 输出目录
            
        Returns:
            Dict: 输出摘要信息
        """
        summary = {
            "output_dir": str(output_dir),
            "files": [],
            "total_size": 0,
            "file_count": 0
        }
        
        if not output_dir.exists():
            return summary
        
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                file_info = {
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                    "format": file_path.suffix.lower()
                }
                summary["files"].append(file_info)
                summary["total_size"] += file_info["size"]
                summary["file_count"] += 1
        
        summary["total_size_mb"] = round(summary["total_size"] / (1024 * 1024), 2)
        
        return summary