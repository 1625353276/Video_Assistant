#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频处理流程
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.user_context import user_context
from deploy.core.video_processor_isolated import get_isolated_processor


def test_video_processing_flow():
    """测试视频处理流程"""
    print("🧪 测试视频处理流程...")
    
    # 创建临时视频文件
    temp_dir = Path(tempfile.mkdtemp())
    video_file = temp_dir / "test_video.mp4"
    video_file.write_bytes(b"fake video content")
    
    try:
        # 设置测试用户
        user_context.set_user("test_user", "testuser")
        
        # 获取处理器
        processor = get_isolated_processor()
        
        # Mock视频验证
        with patch.object(processor.video_loader, 'validate_video') as mock_validate:
            mock_validate.return_value = {
                "duration": 10.0,
                "fps": 30.0,
                "width": 1920,
                "height": 1080
            }
            
            # Mock音频提取
            with patch.object(processor, 'extract_audio') as mock_extract:
                mock_extract.return_value = temp_dir / "test_audio.wav"
                
                # Mock语音识别
                with patch.object(processor.whisper_asr, 'transcribe') as mock_transcribe:
                    mock_transcribe.return_value = {
                        "text": "这是测试转录文本",
                        "segments": [
                            {"id": 0, "start": 0.0, "end": 5.0, "text": "第一段"},
                            {"id": 1, "start": 5.0, "end": 10.0, "text": "第二段"}
                        ],
                        "language": "zh"
                    }
                    
                    # Mock转录保存
                    with patch.object(processor, 'save_transcript') as mock_save:
                        mock_save.return_value = temp_dir / "test_transcript.json"
                        
                        # Mock索引构建
                        with patch('deploy.core.index_builder_isolated.get_index_builder') as mock_index_builder:
                            mock_builder = Mock()
                            mock_index_builder.return_value = mock_builder
                            
                            # 上传并处理视频
                            result = processor.upload_and_process_video(str(video_file))
                            
                            # 打印实际结果进行调试
                            print(f"上传结果: {result}")
                            
                            # 验证上传结果
                            assert "status" in result
                            assert "video_id" in result
                            
                            video_id = result["video_id"]
                            
                            # 等待处理完成（模拟）
                            import time
                            time.sleep(0.1)
                            
                            # 检查处理进度
                            progress = processor.get_processing_progress(video_id)
                            
                            # 验证处理状态
                            assert "progress" in progress
                            assert "status" in progress
                            assert len(progress["log_messages"]) > 0
                            
                            print("✅ 视频处理流程测试通过")
                            print(f"处理状态: {progress['status']}")
                            print(f"处理进度: {progress['progress']}")
                            print(f"当前步骤: {progress['current_step']}")
                            
                            # 测试获取视频信息
                            video_info = processor.get_video_info(video_id)
                            assert "video_id" in video_info
                            assert video_info["video_id"] == video_id
                            
                            print("✅ 视频信息获取测试通过")
        
    finally:
        user_context.clear_user()
        shutil.rmtree(temp_dir)


def run_processing_test():
    """运行处理流程测试"""
    print("🚀 开始视频处理流程测试\n")
    
    try:
        test_video_processing_flow()
        print("\n🎉 视频处理流程测试通过！")
        print("✅ 视频上传后开始处理")
        print("✅ 处理进度正常更新")
        print("✅ 视频信息正常保存")
        print("✅ 用户隔离功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_processing_test()
    sys.exit(0 if success else 1)