#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试删除历史对话功能
"""

import sys
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
        {"text": "这是第一个测试片段。", "start": 0.0, "end": 5.0, "confidence": 0.95},
        {"text": "这是第二个测试片段。", "start": 5.0, "end": 10.0, "confidence": 0.92},
        {"text": "这是第三个测试片段。", "start": 10.0, "end": 15.0, "confidence": 0.94}
    ]
    return transcript


def test_clear_history():
    """测试清空对话历史功能"""
    print("=== 测试清空对话历史 ===")
    
    # 创建检索器
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    # 创建对话链
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 设置视频信息
    conversation_chain.set_video_info(
        filename="test_clear_history.mp4",
        duration=15.0,
        language="zh"
    )
    
    # 创建会话
    transcript = create_test_transcript()
    session_id = conversation_chain.create_session(transcript)
    
    print(f"创建会话: {session_id}")
    
    # 等待索引重建
    import time
    time.sleep(2)
    
    # 添加一些对话
    conversation_chain.chat("第一个问题")
    conversation_chain.chat("第二个问题")
    conversation_chain.chat("第三个问题")
    
    print(f"对话历史轮数: {len(conversation_chain.conversation_history)}")
    print(f"会话数据对话轮数: {len(conversation_chain.session_data.conversation_history)}")
    
    # 清空对话历史
    conversation_chain.clear_history()
    
    print(f"清空后对话历史轮数: {len(conversation_chain.conversation_history)}")
    print(f"清空后会话数据对话轮数: {len(conversation_chain.session_data.conversation_history)}")
    
    # 重新加载会话验证
    new_chain = ConversationChain(retriever=hybrid_retriever)
    success = new_chain.load_session(session_id)
    
    if success:
        print(f"重新加载后对话历史轮数: {len(new_chain.conversation_history)}")
        print("✅ 清空历史对话功能正常")
    else:
        print("❌ 重新加载失败")
    
    return session_id


def test_clear_current_session():
    """测试完全清空当前会话功能"""
    print("\n=== 测试完全清空当前会话 ===")
    
    # 创建检索器
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    # 创建对话链
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 设置视频信息
    conversation_chain.set_video_info(
        filename="test_clear_session.mp4",
        duration=15.0,
        language="zh"
    )
    
    # 创建会话
    transcript = create_test_transcript()
    original_session_id = conversation_chain.create_session(transcript)
    
    print(f"原始会话ID: {original_session_id}")
    
    # 添加对话
    conversation_chain.chat("测试问题")
    
    print(f"清空前会话状态:")
    print(f"  会话ID: {conversation_chain.session_id}")
    print(f"  对话历史: {len(conversation_chain.conversation_history)}")
    print(f"  转录片段: {len(conversation_chain.full_transcript) if conversation_chain.full_transcript else 0}")
    print(f"  索引状态: {conversation_chain.index_ready}")
    
    # 完全清空当前会话
    conversation_chain.clear_current_session()
    
    print(f"\n清空后会话状态:")
    print(f"  会话ID: {conversation_chain.session_id}")
    print(f"  对话历史: {len(conversation_chain.conversation_history)}")
    print(f"  转录片段: {len(conversation_chain.full_transcript) if conversation_chain.full_transcript else 0}")
    print(f"  索引状态: {conversation_chain.index_ready}")
    print(f"  会话数据: {conversation_chain.session_data is not None}")
    
    # 验证会话ID是否改变
    if conversation_chain.session_id != original_session_id:
        print("✅ 完全清空当前会话功能正常")
    else:
        print("❌ 会话ID未改变")
    
    return original_session_id


def test_delete_session():
    """测试删除会话功能"""
    print("\n=== 测试删除会话功能 ===")
    
    # 创建检索器
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    # 创建对话链
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 设置视频信息
    conversation_chain.set_video_info(
        filename="test_delete.mp4",
        duration=15.0,
        language="zh"
    )
    
    # 创建会话
    transcript = create_test_transcript()
    session_id = conversation_chain.create_session(transcript)
    
    print(f"创建会话: {session_id}")
    
    # 列出所有会话
    sessions_before = conversation_chain.list_sessions()
    print(f"删除前会话数量: {len(sessions_before)}")
    
    # 删除会话
    success = conversation_chain.delete_session(session_id)
    print(f"删除结果: {'成功' if success else '失败'}")
    
    # 列出所有会话
    sessions_after = conversation_chain.list_sessions()
    print(f"删除后会话数量: {len(sessions_after)}")
    
    # 验证删除
    deleted_session = any(s['session_id'] == session_id for s in sessions_after)
    if not deleted_session and len(sessions_after) == len(sessions_before) - 1:
        print("✅ 删除会话功能正常")
    else:
        print("❌ 删除会话功能异常")
    
    return success


def main():
    """主测试函数"""
    print("开始测试删除历史对话功能")
    
    try:
        # 测试清空对话历史
        session1 = test_clear_history()
        
        # 测试完全清空当前会话
        session2 = test_clear_current_session()
        
        # 测试删除会话
        result = test_delete_session()
        
        print("\n=== 测试总结 ===")
        print(f"清空历史对话: ✅")
        print(f"完全清空会话: ✅") 
        print(f"删除会话: {'✅' if result else '❌'}")
        print("所有测试完成！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise


if __name__ == "__main__":
    main()