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
            Path("data/uploads")
        ]
        self.transcript_dirs = [
            Path("data/transcripts")
        ]
        self.vector_dirs = [
            Path("data/vectors")
        ]
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        self._registered = False
    
    def cleanup_videos(self, manual: bool = False, in_signal_handler: bool = False) -> int:
        """
        清理所有上传目录中的视频文件以及相关的转录和向量文件
        
        Args:
            manual: 是否为手动清理（影响日志输出）
            in_signal_handler: 是否在信号处理器中调用（避免使用logger）
            
        Returns:
            int: 清理的文件数量
        """
        cleaned_count = 0
        
        # 清理视频文件
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
                            
                            if not in_signal_handler:
                                action = "手动清理" if manual else "自动清理"
                                logger.info(f"{action}视频文件: {file_path.name} ({file_size / (1024*1024):.2f} MB)")
                            
                        except Exception as e:
                            if not in_signal_handler:
                                logger.error(f"清理文件失败 {file_path}: {str(e)}")
                
                # 如果目录为空，尝试删除目录
                try:
                    if not any(upload_dir.iterdir()):
                        upload_dir.rmdir()
                        if not in_signal_handler:
                            logger.info(f"删除空目录: {upload_dir}")
                except Exception:
                    # 忽略删除目录失败
                    pass
                    
            except Exception as e:
                if not in_signal_handler:
                    logger.error(f"清理目录失败 {upload_dir}: {str(e)}")
        
        # 清理转录文件
        for transcript_dir in self.transcript_dirs:
            if not transcript_dir.exists():
                continue
                
            try:
                # 遍历目录中的所有文件
                for file_path in transcript_dir.glob("*"):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_count += 1
                            
                            if not in_signal_handler:
                                action = "手动清理" if manual else "自动清理"
                                logger.info(f"{action}转录文件: {file_path.name} ({file_size / (1024*1024):.2f} MB)")
                            
                        except Exception as e:
                            if not in_signal_handler:
                                logger.error(f"清理转录文件失败 {file_path}: {str(e)}")
                
                # 如果目录为空，尝试删除目录
                try:
                    if not any(transcript_dir.iterdir()):
                        transcript_dir.rmdir()
                        if not in_signal_handler:
                            logger.info(f"删除空转录目录: {transcript_dir}")
                except Exception:
                    # 忽略删除目录失败
                    pass
                    
            except Exception as e:
                if not in_signal_handler:
                    logger.error(f"清理转录目录失败 {transcript_dir}: {str(e)}")
        
        # 清理向量文件
        for vector_dir in self.vector_dirs:
            if not vector_dir.exists():
                continue
                
            try:
                # 遍历目录中的所有文件
                for file_path in vector_dir.glob("*"):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_count += 1
                            
                            if not in_signal_handler:
                                action = "手动清理" if manual else "自动清理"
                                logger.info(f"{action}向量文件: {file_path.name} ({file_size / (1024*1024):.2f} MB)")
                            
                        except Exception as e:
                            if not in_signal_handler:
                                logger.error(f"清理向量文件失败 {file_path}: {str(e)}")
                
                # 如果目录为空，尝试删除目录
                try:
                    if not any(vector_dir.iterdir()):
                        vector_dir.rmdir()
                        if not in_signal_handler:
                            logger.info(f"删除空向量目录: {vector_dir}")
                except Exception:
                    # 忽略删除目录失败
                    pass
                    
            except Exception as e:
                if not in_signal_handler:
                    logger.error(f"清理向量目录失败 {vector_dir}: {str(e)}")
        
        if cleaned_count > 0:
            if not in_signal_handler:
                action = "手动清理" if manual else "自动清理"
                logger.info(f"{action}完成，共清理 {cleaned_count} 个文件")
        elif manual and not in_signal_handler:
            logger.info("没有找到需要清理的文件")
            
        return cleaned_count
    
    def get_video_files_info(self) -> List[dict]:
        """
        获取所有视频文件、转录文件和向量文件的信息
        
        Returns:
            List[dict]: 文件信息列表
        """
        files = []
        
        # 获取视频文件信息
        for upload_dir in self.upload_dirs:
            if not upload_dir.exists():
                continue
                
            for file_path in upload_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.video_extensions:
                    try:
                        stat = file_path.stat()
                        files.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "size": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified_time": stat.st_mtime,
                            "directory": str(upload_dir),
                            "type": "video"
                        })
                    except Exception as e:
                        logger.error(f"获取视频文件信息失败 {file_path}: {str(e)}")
        
        # 获取转录文件信息
        for transcript_dir in self.transcript_dirs:
            if not transcript_dir.exists():
                continue
                
            for file_path in transcript_dir.glob("*"):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        files.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "size": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified_time": stat.st_mtime,
                            "directory": str(transcript_dir),
                            "type": "transcript"
                        })
                    except Exception as e:
                        logger.error(f"获取转录文件信息失败 {file_path}: {str(e)}")
        
        # 获取向量文件信息
        for vector_dir in self.vector_dirs:
            if not vector_dir.exists():
                continue
                
            for file_path in vector_dir.glob("*"):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        files.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "size": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified_time": stat.st_mtime,
                            "directory": str(vector_dir),
                            "type": "vector"
                        })
                    except Exception as e:
                        logger.error(f"获取向量文件信息失败 {file_path}: {str(e)}")
        
        return files
    
    def get_total_size(self) -> float:
        """
        获取所有文件的总大小（MB），包括视频、转录和向量文件
        
        Returns:
            float: 总大小（MB）
        """
        total_size = 0
        
        # 视频文件大小
        for upload_dir in self.upload_dirs:
            if not upload_dir.exists():
                continue
                
            for file_path in upload_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.video_extensions:
                    try:
                        total_size += file_path.stat().st_size
                    except Exception:
                        pass
        
        # 转录文件大小
        for transcript_dir in self.transcript_dirs:
            if not transcript_dir.exists():
                continue
                
            for file_path in transcript_dir.glob("*"):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except Exception:
                        pass
        
        # 向量文件大小
        for vector_dir in self.vector_dirs:
            if not vector_dir.exists():
                continue
                
            for file_path in vector_dir.glob("*"):
                if file_path.is_file():
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
            # 使用print而不是logger，避免递归错误
            print("程序退出，开始清理上传的视频文件...")
            self.cleanup_videos(manual=False, in_signal_handler=True)
        except Exception as e:
            print(f"退出清理失败: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        # 防止重复处理信号
        if hasattr(self, '_signal_handled'):
            return
        self._signal_handled = True
        
        # 避免在信号处理器中使用logger，防止递归错误
        print(f"接收到信号 {signum}，开始清理...")
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
    """获取文件清理信息（便捷函数）"""
    files = video_cleaner.get_video_files_info()
    total_size = video_cleaner.get_total_size()
    
    # 按类型统计文件数量
    video_count = len([f for f in files if f.get("type") == "video"])
    transcript_count = len([f for f in files if f.get("type") == "transcript"])
    vector_count = len([f for f in files if f.get("type") == "vector"])
    
    return {
        "file_count": len(files),
        "total_size_mb": total_size,
        "files": files,
        "upload_dirs": [str(d) for d in video_cleaner.upload_dirs],
        "transcript_dirs": [str(d) for d in video_cleaner.transcript_dirs],
        "vector_dirs": [str(d) for d in video_cleaner.vector_dirs],
        "video_count": video_count,
        "transcript_count": transcript_count,
        "vector_count": vector_count
    }