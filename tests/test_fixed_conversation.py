#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的新建对话和删除功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.qa.conversation_chain import ConversationChain
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.hybrid_retriever import HybridRetriever


def create_test_transcript():
    """创建测试转录数据"""
    transcript = [
        {"text": "这是测试视频的第一个片段。", "start": 0.0, "end": 5.0, "confidence": 0.95},
        {"text": "这是测试视频的第二个片段。", "start": 5.0, "end": 10.0, "confidence": 0.92},
        {"text": "这是测试视频的第三个片段。", "start": 10.0, "end": 15.0, "confidence": 0.94}
    ]
    return transcript


def test_session_id_uniqueness():
    """测试会话ID唯一性"""
    print("=== 测试会话ID唯一性 ===")
    
    # 创建对话链
    conversation_chain = ConversationChain()
    
    # 快速生成多个会话ID
    session_ids = []
    for i in range(5):
        session_id = conversation_chain._generate_session_id()
        session_ids.append(session_id)
        print(f"生成的会话ID {i+1}: {session_id}")
        time.sleep(0.01)  # 很短的间隔
    
    # 检查唯一性
    unique_ids = set(session_ids)
    if len(unique_ids) == len(session_ids):
        print("✅ 会话ID唯一性测试通过")
        return True
    else:
        print("❌ 会话ID存在重复")
        return False


def test_new_conversation():
    """测试新建对话功能"""
    print("\n=== 测试新建对话功能 ===")
    
    # 创建检索器
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    # 创建对话链
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 创建第一个对话
    transcript1 = create_test_transcript()
    session_id1 = conversation_chain.new_conversation(
        video_filename="video1.mp4",
        duration=15.0,
        transcript=transcript1,
        language="zh"
    )
    
    print(f"第一个对话会话ID: {session_id1}")
    
    # 添加一些对话
    conversation_chain.chat("第一个视频的问题")
    conversation_chain.chat("第一个视频的另一个问题")
    
    print(f"第一个对话轮数: {len(conversation_chain.conversation_history)}")
    
    # 创建第二个对话（应该完全独立）
    transcript2 = [
        {"text": "这是第二个视频的第一个片段。", "start": 0.0, "end": 5.0, "confidence": 0.95},
        {"text": "这是第二个视频的第二个片段。", "start": 5.0, "end": 10.0, "confidence": 0.92}
    ]
    
    session_id2 = conversation_chain.new_conversation(
        video_filename="video2.mp4",
        duration=10.0,
        transcript=transcript2,
        language="zh"
    )
    
    print(f"第二个对话会话ID: {session_id2}")
    
    # 检查状态是否完全重置
    print(f"第二个对话初始轮数: {len(conversation_chain.conversation_history)}")
    print(f"第二个对话转录片段数: {len(conversation_chain.full_transcript) if conversation_chain.full_transcript else 0}")
    print(f"第二个对话视频文件: {conversation_chain.video_info.filename if conversation_chain.video_info else None}")
    
    # 添加对话到第二个视频
    conversation_chain.chat("第二个视频的问题")
    
    print(f"第二个对话当前轮数: {len(conversation_chain.conversation_history)}")
    
    # 验证会话ID不同
    if session_id1 != session_id2:
        print("✅ 新建对话功能测试通过")
        return True
    else:
        print("❌ 会话ID重复")
        return False


def test_delete_and_list():
    """测试删除和列表功能"""
    print("\n=== 测试删除和列表功能 ===")
    
    # 创建检索器
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    # 创建对话链
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 创建多个会话
    session_ids = []
    for i in range(3):
        transcript = [
            {"text": f"视频{i+1}的片段1", "start": 0.0, "end": 5.0, "confidence": 0.95},
            {"text": f"视频{i+1}的片段2", "start": 5.0, "end": 10.0, "confidence": 0.92}
        ]
        
        session_id = conversation_chain.new_conversation(
            video_filename=f"video{i+1}.mp4",
            duration=10.0,
            transcript=transcript,
            language="zh"
        )
        session_ids.append(session_id)
        print(f"创建会话 {i+1}: {session_id}")
    
    # 列出所有会话
    sessions = conversation_chain.list_sessions()
    print(f"删除前会话数量: {len(sessions)}")
    
    # 删除中间的会话
    delete_success = conversation_chain.delete_session(session_ids[1])
    print(f"删除会话 {session_ids[1]}: {'成功' if delete_success else '失败'}")
    
    # 再次列出会话
    sessions_after = conversation_chain.list_sessions()
    print(f"删除后会话数量: {len(sessions_after)}")
    
    # 验证删除结果
    remaining_ids = [s['session_id'] for s in sessions_after]
    deleted_session_exists = session_ids[1] in remaining_ids
    
    if not deleted_session_exists and len(sessions_after) == len(sessions) - 1:
        print("✅ 删除功能测试通过")
        return True
    else:
        print("❌ 删除功能测试失败")
        return False


def test_clear_functions():
    """测试清空功能"""
    print("\n=== 测试清空功能 ===")
    
    # 创建检索器
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    # 创建对话链
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 创建会话并添加对话
    transcript = create_test_transcript()
    session_id = conversation_chain.new_conversation(
        video_filename="test_clear.mp4",
        duration=15.0,
        transcript=transcript,
        language="zh"
    )
    
    # 添加对话
    conversation_chain.chat("测试问题1")
    conversation_chain.chat("测试问题2")
    
    print(f"清空前状态:")
    print(f"  会话ID: {conversation_chain.session_id}")
    print(f"  对话轮数: {len(conversation_chain.conversation_history)}")
    print(f"  转录片段: {len(conversation_chain.full_transcript) if conversation_chain.full_transcript else 0}")
    
    # 测试清空历史（保留会话数据）
    conversation_chain.clear_history()
    
    print(f"\n清空历史后状态:")
    print(f"  会话ID: {conversation_chain.session_id}")
    print(f"  对话轮数: {len(conversation_chain.conversation_history)}")
    print(f"  转录片段: {len(conversation_chain.full_transcript) if conversation_chain.full_transcript else 0}")
    print(f"  会话数据存在: {conversation_chain.session_data is not None}")
    
    # 重新添加对话
    conversation_chain.chat("清空后的问题")
    
    # 测试完全清空当前会话
    original_session_id = conversation_chain.session_id
    conversation_chain.clear_current_session()
    
    print(f"\n完全清空后状态:")
    print(f"  会话ID: {conversation_chain.session_id}")
    print(f"  会话ID改变: {conversation_chain.session_id != original_session_id}")
    print(f"  对话轮数: {len(conversation_chain.conversation_history)}")
    print(f"  转录片段: {len(conversation_chain.full_transcript) if conversation_chain.full_transcript else 0}")
    print(f"  会话数据存在: {conversation_chain.session_data is not None}")
    
    print("✅ 清空功能测试完成")
    return True


def main():
    """主测试函数"""
    print("开始测试修复后的功能")
    
    try:
        # 测试会话ID唯一性
        test1 = test_session_id_uniqueness()
        
        # 测试新建对话功能
        test2 = test_new_conversation()
        
        # 测试删除和列表功能
        test3 = test_delete_and_list()
        
        # 测试清空功能
        test4 = test_clear_functions()
        
        print("\n=== 测试总结 ===")
        print(f"会话ID唯一性: {'✅' if test1 else '❌'}")
        print(f"新建对话功能: {'✅' if test2 else '❌'}")
        print(f"删除和列表功能: {'✅' if test3 else '❌'}")
        print(f"清空功能: {'✅' if test4 else '❌'}")
        
        if all([test1, test2, test3, test4]):
            print("🎉 所有测试通过！")
        else:
            print("⚠️ 部分测试失败")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise


if __name__ == "__main__":
    main()