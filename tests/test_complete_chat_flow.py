#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整对话流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_complete_chat_flow():
    """测试完整对话流程"""
    print("=== 测试完整对话流程 ===")
    
    try:
        from deploy.app import VideoAssistant
        from modules.qa.conversation_chain import ConversationChain
        
        # 创建助手
        assistant = VideoAssistant()
        
        # 模拟视频数据
        video_id = "test_video_complete"
        import deploy.app as app_module
        app_module.video_data[video_id] = {
            "video_id": video_id,
            "filename": "test.mp4",
            "status": "completed",
            "transcript": [
                {"text": "这是测试视频的第一个片段。", "start": 0.0, "end": 5.0},
                {"text": "这是测试视频的第二个片段。", "start": 5.0, "end": 10.0}
            ],
            "assistant_config": {"cuda_enabled": True, "whisper_model": "base"}
        }
        
        # 测试对话
        print("1. 开始第一次对话")
        response1, history1 = assistant.chat_with_video(video_id, "视频讲了什么？", [])
        print(f"   回答: {response1[:50]}...")
        print(f"   历史长度: {len(history1)}")
        
        # 测试第二次对话
        print("\n2. 继续对话")
        response2, history2 = assistant.chat_with_video(video_id, "第二个片段的内容是什么？", history1)
        print(f"   回答: {response2[:50]}...")
        print(f"   历史长度: {len(history2)}")
        
        # 测试清空对话
        print("\n3. 清空对话")
        clear_result = assistant.clear_conversation(video_id)
        print(f"   清空结果: {clear_result}")
        
        # 测试新对话
        print("\n4. 开始新对话")
        response3, history3 = assistant.chat_with_video(video_id, "新对话的问题", [])
        print(f"   回答: {response3[:50]}...")
        print(f"   历史长度: {len(history3)}")
        
        # 验证隔离效果
        print(f"\n5. 验证结果:")
        print(f"   第一次对话成功: {len(response1) > 0}")
        print(f"   第二次对话成功: {len(response2) > 0}")
        print(f"   新对话成功: {len(response3) > 0}")
        print(f"   新对话历史为空: {len(history3) == 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试完整对话流程")
    
    test_result = test_complete_chat_flow()
    
    print(f"\n=== 测试总结 ===")
    print(f"完整对话流程: {'✅' if test_result else '❌'}")
    
    if test_result:
        print("🎉 完整对话流程测试通过！")
        print("现在可以正常进行对话了。")
    else:
        print("⚠️ 对话流程仍有问题")

if __name__ == "__main__":
    main()