#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频清理功能测试脚本

测试视频清理模块的各项功能：
- 创建测试视频文件
- 测试清理功能
- 验证清理结果
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.utils.video_cleaner import VideoCleaner, get_video_cleanup_info


def create_test_video_files():
    """创建测试视频文件"""
    test_files = []
    
    # 确保测试目录存在
    upload_dirs = [Path("data/uploads"), Path("deploy/data/uploads")]
    for upload_dir in upload_dirs:
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建不同格式的测试视频文件
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov']
        for ext in video_extensions:
            test_file = upload_dir / f"test_video{ext}"
            # 创建一个小的测试文件（模拟视频文件）
            with open(test_file, 'wb') as f:
                f.write(b'fake video content' * 1000)  # 约18KB的测试文件
            test_files.append(test_file)
            print(f"创建测试文件: {test_file}")
    
    return test_files


def test_video_cleaner():
    """测试视频清理器功能"""
    print("=" * 50)
    print("开始测试视频清理功能")
    print("=" * 50)
    
    # 创建测试文件
    test_files = create_test_video_files()
    
    # 初始化清理器
    cleaner = VideoCleaner()
    
    # 1. 测试获取视频文件信息
    print("\n1. 测试获取视频文件信息...")
    video_files = cleaner.get_video_files_info()
    print(f"找到 {len(video_files)} 个视频文件:")
    for file_info in video_files:
        print(f"  - {file_info['name']} ({file_info['size_mb']} MB)")
    
    # 2. 测试获取总大小
    print("\n2. 测试获取总大小...")
    total_size = cleaner.get_total_size()
    print(f"视频文件总大小: {total_size} MB")
    
    # 3. 测试手动清理
    print("\n3. 测试手动清理...")
    cleaned_count = cleaner.cleanup_videos(manual=True)
    print(f"清理了 {cleaned_count} 个文件")
    
    # 4. 验证清理结果
    print("\n4. 验证清理结果...")
    remaining_files = cleaner.get_video_files_info()
    print(f"剩余视频文件数量: {len(remaining_files)}")
    
    if len(remaining_files) == 0:
        print("✅ 清理功能测试通过！所有视频文件已被成功删除。")
    else:
        print("❌ 清理功能测试失败！仍有视频文件未被删除。")
        for file_info in remaining_files:
            print(f"  - {file_info['path']}")
    
    # 5. 测试便捷函数
    print("\n5. 测试便捷函数...")
    
    # 重新创建测试文件
    create_test_video_files()
    
    # 使用便捷函数获取信息
    cleanup_info = get_video_cleanup_info()
    print(f"便捷函数获取的信息:")
    print(f"  - 文件数量: {cleanup_info['file_count']}")
    print(f"  - 总大小: {cleanup_info['total_size_mb']} MB")
    print(f"  - 上传目录: {cleanup_info['upload_dirs']}")
    
    # 使用便捷函数清理
    from modules.utils.video_cleaner import cleanup_videos_now
    cleaned_count = cleanup_videos_now()
    print(f"便捷函数清理了 {cleaned_count} 个文件")
    
    # 最终验证
    final_files = cleaner.get_video_files_info()
    if len(final_files) == 0:
        print("\n✅ 所有测试通过！视频清理功能正常工作。")
        return True
    else:
        print("\n❌ 测试失败！仍有文件未被清理。")
        return False


if __name__ == "__main__":
    try:
        success = test_video_cleaner()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)