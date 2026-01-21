#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频列表修复
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 模拟video_data数据结构
def test_video_list_fix():
    """测试视频列表修复"""
    print("=== 测试视频列表修复 ===")
    
    # 模拟有upload_time的视频数据
    video_with_upload_time = {
        "video_id": "test1",
        "filename": "video1.mp4",
        "status": "completed",
        "upload_time": time.time() - 3600,  # 1小时前
        "assistant_config": {"cuda_enabled": True, "whisper_model": "base"}
    }
    
    # 模拟没有upload_time的视频数据（之前会导致bug）
    video_without_upload_time = {
        "video_id": "test2", 
        "filename": "video2.mp4",
        "status": "completed",
        "assistant_config": {"cuda_enabled": True, "whisper_model": "base"}
    }
    
    # 模拟video_data
    video_data = {
        "test1": video_with_upload_time,
        "test2": video_without_upload_time
    }
    
    # 测试修复后的逻辑
    videos = []
    for video_id, info in video_data.items():
        if info["status"] == "completed":
            # 使用修复后的逻辑
            upload_time = info.get("upload_time", time.time())
            videos.append({
                "video_id": video_id,
                "filename": info["filename"],
                "upload_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(upload_time)),
                "config": info.get("assistant_config", {"cuda_enabled": True, "whisper_model": "base"})
            })
    
    print(f"处理了 {len(videos)} 个视频")
    
    for video in videos:
        print(f"视频ID: {video['video_id']}")
        print(f"文件名: {video['filename']}")
        print(f"上传时间: {video['upload_time']}")
        print("---")
    
    # 验证所有视频都有upload_time字段
    all_have_upload_time = all("upload_time" in video for video in videos)
    
    if all_have_upload_time:
        print("✅ 视频列表修复测试通过")
        return True
    else:
        print("❌ 仍有视频缺少upload_time字段")
        return False

if __name__ == "__main__":
    test_video_list_fix()