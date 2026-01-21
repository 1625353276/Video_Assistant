#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理测试脚本
测试会话保存、加载和索引重建功能
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入模块
from modules.qa.conversation_chain import ConversationChain
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.hybrid_retriever import HybridRetriever
from config.settings import settings

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_transcript():
    """创建测试转录数据"""
    transcript = [
        {"text": "人工智能是计算机科学的一个分支，它试图理解和构建智能体。", "start": 0.0, "end": 5.0, "confidence": 0.95},
        {"text": "机器学习是人工智能的子领域，专注于算法和统计模型。", "start": 5.0, "end": 10.0, "confidence": 0.92},
        {"text": "深度学习是机器学习的一个分支，使用神经网络进行学习。", "start": 10.0, "end": 15.0, "confidence": 0.94},
        {"text": "自然语言处理是AI的一个重要应用领域。", "start": 15.0, "end": 20.0, "confidence": 0.96},
        {"text": "计算机视觉让机器能够理解和解释视觉信息。", "start": 20.0, "end": 25.0, "confidence": 0.93},
        {"text": "强化学习通过试错来学习最优策略。", "start": 25.0, "end": 30.0, "confidence": 0.91},
        {"text": "大语言模型如GPT在自然语言处理方面表现出色。", "start": 30.0, "end": 35.0, "confidence": 0.95},
        {"text": "AI在医疗、金融、交通等领域有广泛应用。", "start": 35.0, "end": 40.0, "confidence": 0.94}
    ]
    return transcript


def test_session_creation():
    """测试会话创建"""
    logger.info("=== 测试会话创建 ===")
    
    # 创建检索器
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    # 创建对话链
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 设置视频信息
    conversation_chain.set_video_info(
        filename="test_video.mp4",
        duration=40.0,
        language="zh",
        file_size=1024000,
        resolution="1920x1080"
    )
    
    # 创建测试转录
    transcript = create_test_transcript()
    
    # 创建会话
    session_id = conversation_chain.create_session(transcript)
    
    logger.info(f"会话创建成功: {session_id}")
    logger.info(f"会话状态: {conversation_chain.get_session_status()}")
    
    return conversation_chain, session_id


def test_conversation_and_save(conversation_chain):
    """测试对话和保存"""
    logger.info("=== 测试对话和保存 ===")
    
    # 等待索引重建完成
    max_wait = 10  # 最多等待10秒
    wait_time = 0
    while not conversation_chain.index_ready and wait_time < max_wait:
        time.sleep(0.5)
        wait_time += 0.5
        logger.info(f"等待索引重建... {wait_time}s")
    
    # 测试对话
    test_questions = [
        "什么是人工智能？",
        "机器学习和深度学习有什么关系？",
        "AI有哪些应用领域？"
    ]
    
    for question in test_questions:
        logger.info(f"问题: {question}")
        result = conversation_chain.chat(question)
        logger.info(f"回答: {result['response'][:100]}...")
        logger.info(f"检索方法: {result['metadata']['retrieval_method']}")
        logger.info(f"检索到 {len(result['retrieved_docs'])} 个文档")
    
    # 保存会话
    success = conversation_chain.save_session()
    logger.info(f"会话保存: {'成功' if success else '失败'}")
    
    return conversation_chain.session_id


def test_session_loading(session_id):
    """测试会话加载"""
    logger.info("=== 测试会话加载 ===")
    
    # 创建新的对话链实例
    vector_store = VectorStore()
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(vector_store, bm25_retriever)
    
    conversation_chain = ConversationChain(retriever=hybrid_retriever)
    
    # 加载会话
    success = conversation_chain.load_session(session_id)
    logger.info(f"会话加载: {'成功' if success else '失败'}")
    
    if success:
        # 检查加载状态
        status = conversation_chain.get_session_status()
        logger.info(f"会话状态: {status}")
        
        # 测试对话历史
        logger.info(f"对话历史轮数: {len(conversation_chain.conversation_history)}")
        
        # 测试即时对话（索引可能还在重建）
        logger.info("测试即时对话...")
        result = conversation_chain.chat("计算机视觉是什么？")
        logger.info(f"即时回答: {result['response'][:100]}...")
        logger.info(f"检索方法: {result['metadata']['retrieval_method']}")
        
        # 等待索引重建完成
        wait_time = 0
        while not conversation_chain.index_ready and wait_time < 10:
            time.sleep(0.5)
            wait_time += 0.5
        
        # 测试完整检索对话
        if conversation_chain.index_ready:
            logger.info("测试完整检索对话...")
            result = conversation_chain.chat("强化学习的原理是什么？")
            logger.info(f"完整检索回答: {result['response'][:100]}...")
            logger.info(f"检索方法: {result['metadata']['retrieval_method']}")
        
        return conversation_chain
    
    return None


def test_session_management():
    """测试会话管理功能"""
    logger.info("=== 测试会话管理 ===")
    
    # 创建对话链
    conversation_chain = ConversationChain()
    
    # 列出所有会话
    sessions = conversation_chain.list_sessions()
    logger.info(f"找到 {len(sessions)} 个会话")
    
    for session in sessions[:3]:  # 只显示前3个
        logger.info(f"会话ID: {session['session_id']}")
        logger.info(f"视频文件: {session['video_filename']}")
        logger.info(f"对话轮数: {session['conversation_turns']}")
        logger.info(f"更新时间: {session['updated_at']}")
    
    return len(sessions)


def main():
    """主测试函数"""
    logger.info("开始会话管理测试")
    
    try:
        # 测试会话创建
        chain1, session_id = test_session_creation()
        
        # 测试对话和保存
        saved_session_id = test_conversation_and_save(chain1)
        
        # 测试会话加载
        chain2 = test_session_loading(saved_session_id)
        
        # 测试会话管理
        session_count = test_session_management()
        
        logger.info("=== 测试总结 ===")
        logger.info(f"创建会话ID: {session_id}")
        logger.info(f"保存会话ID: {saved_session_id}")
        logger.info(f"加载成功: {chain2 is not None}")
        logger.info(f"总会话数: {session_count}")
        
        if chain2:
            logger.info(f"最终会话状态: {chain2.get_session_status()}")
        
        logger.info("所有测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise


if __name__ == "__main__":
    main()