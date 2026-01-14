#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频清理模块

职责：
- 在程序退出时清理上传的视频文件
- 管理临时文件的清理策略
- 提供手动清理功能
"""

import os
import shutil
import atexit
import signal
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class VideoCleaner:
    """视频文件清理器"""
    
    def __init__(self):
        """初始化清理器"""
        self.upload_dirs = [
            Path("data/uploads"),
            Path("deploy/data/uploads")
        ]
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        self._registered = False
    
    def cleanup_videos(self, manual: bool = False) -> int:
        """
        清理所有上传目录中的视频文件
        
        Args:
            manual: 是否为手动清理（影响日志输出）
            
        Returns:
            int: 清理的文件数量
        """
        cleaned_count = 0
        
        for upload_dir in self.upload_dirs:
            if not upload_dir.exists():
                continue
                
            try:
                # 遍历目录中的所有文件
                for file_path in upload_dir.glob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in self.video_extensions:
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_count += 1
                            
                            action = "手动清理" if manual else "自动清理"
                            logger.info(f"{action}视频文件: {file_path.name} ({file_size / (1024*1024):.2f} MB)")
                            
                        except Exception as e:
                            logger.error(f"清理文件失败 {file_path}: {str(e)}")
                
                # 如果目录为空，尝试删除目录
                try:
                    if not any(upload_dir.iterdir()):
                        upload_dir.rmdir()
                        logger.info(f"删除空目录: {upload_dir}")
                except Exception:
                    # 忽略删除目录失败
                    pass
                    
            except Exception as e:
                logger.error(f"清理目录失败 {upload_dir}: {str(e)}")
        
        if cleaned_count > 0:
            action = "手动清理" if manual else "自动清理"
            logger.info(f"{action}完成，共清理 {cleaned_count} 个视频文件")
        elif manual:
            logger.info("没有找到需要清理的视频文件")
            
        return cleaned_count
    
    def get_video_files_info(self) -> List[dict]:
        """
        获取所有视频文件的信息
        
        Returns:
            List[dict]: 视频文件信息列表
        """
        video_files = []
        
        for upload_dir in self.upload_dirs:
            if not upload_dir.exists():
                continue
                
            for file_path in upload_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.video_extensions:
                    try:
                        stat = file_path.stat()
                        video_files.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "size": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified_time": stat.st_mtime,
                            "directory": str(upload_dir)
                        })
                    except Exception as e:
                        logger.error(f"获取文件信息失败 {file_path}: {str(e)}")
        
        return video_files
    
    def get_total_size(self) -> float:
        """
        获取所有视频文件的总大小（MB）
        
        Returns:
            float: 总大小（MB）
        """
        total_size = 0
        
        for upload_dir in self.upload_dirs:
            if not upload_dir.exists():
                continue
                
            for file_path in upload_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.video_extensions:
                    try:
                        total_size += file_path.stat().st_size
                    except Exception:
                        pass
        
        return round(total_size / (1024 * 1024), 2)
    
    def register_exit_handler(self):
        """注册程序退出时的清理函数"""
        if self._registered:
            return
            
        # 注册atexit处理函数
        atexit.register(self._cleanup_on_exit)
        
        # 注册信号处理函数
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, self._signal_handler)
        
        self._registered = True
        logger.info("视频清理器已注册，程序退出时将自动清理上传的视频文件")
    
    def _cleanup_on_exit(self):
        """程序退出时的清理函数"""
        try:
            logger.info("程序退出，开始清理上传的视频文件...")
            self.cleanup_videos(manual=False)
        except Exception as e:
            logger.error(f"退出清理失败: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        logger.info(f"接收到信号 {signum}，开始清理...")
        self._cleanup_on_exit()
        # 重新发送信号，确保程序正常退出
        os.kill(os.getpid(), signum)


# 创建全局清理器实例
video_cleaner = VideoCleaner()


def register_video_cleanup():
    """注册视频清理功能（便捷函数）"""
    video_cleaner.register_exit_handler()


def cleanup_videos_now():
    """立即清理视频文件（便捷函数）"""
    return video_cleaner.cleanup_videos(manual=True)


def get_video_cleanup_info():
    """获取视频清理信息（便捷函数）"""
    files = video_cleaner.get_video_files_info()
    total_size = video_cleaner.get_total_size()
    
    return {
        "file_count": len(files),
        "total_size_mb": total_size,
        "files": files,
        "upload_dirs": [str(d) for d in video_cleaner.upload_dirs]
    }