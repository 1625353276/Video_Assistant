#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转文本功能测试

测试完整的视频处理流程：
- 视频文件验证
- 音频提取
- Whisper语音识别
- 结果保存
"""

import os
import sys
import unittest
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 检查依赖
missing_dependencies = []

try:
    from modules.video.video_loader import VideoLoader
except ImportError as e:
    missing_dependencies.append(f"VideoLoader: {e}")

try:
    from modules.video.audio_extractor import AudioExtractor
except ImportError as e:
    missing_dependencies.append(f"AudioExtractor: {e}")

try:
    from modules.speech.whisper_asr import WhisperASR
except ImportError as e:
    missing_dependencies.append(f"WhisperASR: {e}")

try:
    from modules.utils.file_manager import FileManager
except ImportError as e:
    missing_dependencies.append(f"FileManager: {e}")

if missing_dependencies:
    print("缺少以下依赖，无法运行视频转文本测试:")
    for dep in missing_dependencies:
        print(f"  - {dep}")
    print("\n请安装所需依赖或使用虚拟环境。")
    sys.exit(0)


class TestVideoToText(unittest.TestCase):
    """视频转文本功能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.test_data_dir = Path(__file__).parent.parent / "data"
        cls.test_video_dir = cls.test_data_dir / "raw_videos"
        cls.test_audio_dir = cls.test_data_dir / "audio"
        cls.test_output_dir = cls.test_data_dir / "test_outputs"
        
        # 创建测试目录
        cls.test_audio_dir.mkdir(exist_ok=True)
        cls.test_output_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        cls.video_loader = VideoLoader()
        cls.audio_extractor = AudioExtractor()
        cls.whisper_asr = WhisperASR(model_size="base")  # 使用base模型加快测试
        cls.file_manager = FileManager()
        
        # 测试视频文件路径
        cls.test_video_path = cls.test_video_dir / "Test.mp4"
    
    def setUp(self):
        """每个测试方法前的初始化"""
        self.temp_files = []  # 记录临时文件，测试后清理
    
    def tearDown(self):
        """每个测试方法后的清理"""
        # 清理临时文件
        for file_path in self.temp_files:
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"清理文件失败: {file_path}, 错误: {e}")
    
    def test_video_validation(self):
        """测试视频文件验证功能"""
        print("\n=== 测试视频文件验证 ===")
        
        if not self.test_video_path.exists():
            self.skipTest(f"测试视频文件不存在: {self.test_video_path}")
        
        # 测试视频验证
        video_info = self.video_loader.validate_video(self.test_video_path)
        
        self.assertIsNotNone(video_info)
        self.assertIn("duration", video_info)
        self.assertIn("fps", video_info)
        self.assertIn("width", video_info)
        self.assertIn("height", video_info)
        
        print(f"视频信息: {video_info}")
        print("✅ 视频验证测试通过")
    
    def test_audio_extraction(self):
        """测试音频提取功能"""
        print("\n=== 测试音频提取 ===")
        
        if not self.test_video_path.exists():
            self.skipTest(f"测试视频文件不存在: {self.test_video_path}")
        
        # 提取音频
        audio_path = self.audio_extractor.extract_audio(self.test_video_path)
        self.temp_files.append(audio_path)  # 记录临时文件
        
        self.assertTrue(audio_path.exists())
        self.assertGreater(audio_path.stat().st_size, 0)
        
        print(f"音频文件: {audio_path}")
        print(f"音频大小: {audio_path.stat().st_size} bytes")
        print("✅ 音频提取测试通过")
    
    def test_whisper_transcription(self):
        """测试Whisper语音识别功能"""
        print("\n=== 测试Whisper语音识别 ===")
        
        if not self.test_video_path.exists():
            self.skipTest(f"测试视频文件不存在: {self.test_video_path}")
        
        # 先提取音频
        audio_path = self.audio_extractor.extract_audio(self.test_video_path)
        self.temp_files.append(audio_path)
        
        # 进行语音识别
        print("正在进行语音识别（使用base模型）...")
        transcript_result = self.whisper_asr.transcribe(audio_path)
        
        self.assertIsNotNone(transcript_result)
        self.assertIn("text", transcript_result)
        self.assertIn("segments", transcript_result)
        
        # 验证转录结果结构
        self.assertIsInstance(transcript_result["text"], str)
        self.assertGreater(len(transcript_result["text"].strip()), 0)
        self.assertIsInstance(transcript_result["segments"], list)
        
        # 验证段落结构
        if transcript_result["segments"]:
            segment = transcript_result["segments"][0]
            self.assertIn("text", segment)
            self.assertIn("start", segment)
            self.assertIn("end", segment)
        
        print(f"识别文本长度: {len(transcript_result['text'])} 字符")
        print(f"段落数量: {len(transcript_result['segments'])}")
        print(f"识别文本预览: {transcript_result['text'][:100]}...")
        print("✅ Whisper语音识别测试通过")
    
    def test_file_saving(self):
        """测试结果保存功能"""
        print("\n=== 测试结果保存 ===")
        
        if not self.test_video_path.exists():
            self.skipTest(f"测试视频文件不存在: {self.test_video_path}")
        
        # 完整处理流程
        audio_path = self.audio_extractor.extract_audio(self.test_video_path)
        self.temp_files.append(audio_path)
        
        transcript_result = self.whisper_asr.transcribe(audio_path)
        
        # 保存JSON格式
        json_output = self.test_output_dir / "test_transcript.json"
        self.file_manager.save_transcript_json(transcript_result, json_output)
        self.temp_files.append(json_output)
        
        self.assertTrue(json_output.exists())
        
        # 验证JSON文件内容
        with open(json_output, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["text"], transcript_result["text"])
        self.assertEqual(len(saved_data["segments"]), len(transcript_result["segments"]))
        
        # 保存文本格式
        txt_output = self.test_output_dir / "test_transcript.txt"
        self.file_manager.save_transcript_text(transcript_result, txt_output)
        self.temp_files.append(txt_output)
        
        self.assertTrue(txt_output.exists())
        
        # 验证文本文件内容
        with open(txt_output, 'r', encoding='utf-8') as f:
            txt_content = f.read()
        
        self.assertIn(transcript_result["text"], txt_content)
        
        print(f"JSON文件: {json_output}")
        print(f"TXT文件: {txt_output}")
        print("✅ 文件保存测试通过")
    
    def test_complete_pipeline(self):
        """测试完整的视频处理流水线"""
        print("\n=== 测试完整处理流水线 ===")
        
        if not self.test_video_path.exists():
            self.skipTest(f"测试视频文件不存在: {self.test_video_path}")
        
        print(f"处理视频: {self.test_video_path}")
        
        # 1. 视频验证
        video_info = self.video_loader.validate_video(self.test_video_path)
        print(f"视频时长: {video_info.get('duration', 'unknown')} 秒")
        
        # 2. 音频提取
        audio_path = self.audio_extractor.extract_audio(self.test_video_path)
        self.temp_files.append(audio_path)
        print(f"音频提取完成: {audio_path}")
        
        # 3. 语音识别
        transcript_result = self.whisper_asr.transcribe(audio_path)
        print(f"语音识别完成，识别文本长度: {len(transcript_result['text'])} 字符")
        
        # 4. 保存结果
        output_prefix = f"pipeline_test_{self.test_video_path.stem}"
        json_output = self.test_output_dir / f"{output_prefix}.json"
        txt_output = self.test_output_dir / f"{output_prefix}.txt"
        
        self.file_manager.save_transcript_json(transcript_result, json_output)
        self.file_manager.save_transcript_text(transcript_result, txt_output)
        
        self.temp_files.extend([json_output, txt_output])
        
        # 验证输出
        self.assertTrue(json_output.exists())
        self.assertTrue(txt_output.exists())
        
        print(f"结果保存完成:")
        print(f"  JSON: {json_output}")
        print(f"  TXT: {txt_output}")
        print("✅ 完整流水线测试通过")


def run_video_to_text_tests():
    """运行视频转文本测试"""
    print("=" * 60)
    print("视频转文本功能测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVideoToText)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n测试结果: {'通过' if success else '失败'}")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    run_video_to_text_tests()