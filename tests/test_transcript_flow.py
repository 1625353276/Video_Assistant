#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试转录内容设置和对话流程
"""

import sys
import os
import json
import shutil
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.qa.conversation_chain import ConversationChain

def test_transcript_loading():
    """测试转录内容加载和对话"""
    print("=== 测试转录内容加载和对话 ===\n")
    
    # 1. 创建测试转录文件（使用正确的格式）
    transcript_dir = "data/transcripts"
    os.makedirs(transcript_dir, exist_ok=True)
    
    test_video_id = "test_video_123"
    transcript_file = os.path.join(transcript_dir, f"{test_video_id}_transcript.json")
    
    # 创建测试转录数据
    test_transcript_data = {
        "audio_file": "test.wav",
        "language": "en",
        "segments": [
            {"id": 0, "start": 0.0, "end": 3.0, "text": "人工智能是计算机科学的一个分支", "confidence": 0.95},
            {"id": 1, "start": 3.0, "end": 6.0, "text": "机器学习是人工智能的子领域", "confidence": 0.94},
            {"id": 2, "start": 6.0, "end": 9.0, "text": "深度学习使用神经网络模拟人脑", "confidence": 0.96},
            {"id": 3, "start": 9.0, "end": 12.0, "text": "自然语言处理是AI的应用领域", "confidence": 0.93}
        ],
        "text": "人工智能是计算机科学的一个分支。机器学习是人工智能的子领域。深度学习使用神经网络模拟人脑。自然语言处理是AI的应用领域。"
    }
    
    # 保存转录文件
    with open(transcript_file, 'w', encoding='utf-8') as f:
        json.dump(test_transcript_data, f, ensure_ascii=False, indent=2)
    
    print(f"创建测试转录文件: {transcript_file}")
    print(f"转录内容包含 {len(test_transcript_data['segments'])} 个片段")
    
    # 2. 模拟 _create_conversation_chain 方法
    print("\n=== 模拟创建对话链 ===")
    
    # 创建对话链
    conversation_chain = ConversationChain()
    
    # 设置转录内容
    if os.path.exists(transcript_file):
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
            if 'segments' in transcript_data:
                conversation_chain.set_full_transcript(transcript_data['segments'])
                print(f"已为视频 {test_video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
                
                # 验证设置
                if hasattr(conversation_chain, 'full_transcript') and conversation_chain.full_transcript:
                    print(f"转录内容设置成功，第一段: {conversation_chain.full_transcript[0].get('text', '')}")
                else:
                    print("警告：转录内容设置失败！")
    
    # 3. 测试对话
    print("\n=== 测试对话 ===")
    
    questions = [
        "什么是人工智能？",
        "机器学习与人工智能的关系是什么？",
        "深度学习有什么特点？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n第 {i} 个问题: {question}")
        
        # 构建消息
        messages = conversation_chain._build_messages(question, "检索到的相关片段")
        print(f"构建了 {len(messages)} 条消息")
        
        # 检查是否包含完整视频内容
        has_full_content = False
        for msg in messages:
            if msg['role'] == 'system' and '完整转录内容' in msg['content']:
                has_full_content = True
                print(f"✅ 消息中包含完整视频内容（长度: {len(msg['content'])} 字符）")
                break
        
        if not has_full_content:
            print("❌ 消息中没有包含完整视频内容")
    
    # 4. 清理测试文件
    print(f"\n=== 清理测试文件 ===")
    os.remove(transcript_file)
    print(f"已删除测试文件: {transcript_file}")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_transcript_loading()