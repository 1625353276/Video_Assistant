#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试跨用户隔离问题
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from deploy.utils.user_context import user_context
from modules.retrieval.isolated_hybrid_retriever import get_isolated_hybrid_retriever


def debug_isolation():
    """调试用户隔离问题"""
    print("🔧 调试跨用户隔离问题...")
    
    video_id = "debug_video"
    
    # 设置用户1并构建索引
    print("\n1. 设置用户1并构建索引...")
    user_context.set_user('debug_user_1')
    
    hybrid_1 = get_isolated_hybrid_retriever()
    print(f"   用户1 hybrid_retriever: {hybrid_1.user_id}")
    
    documents_1 = [
        {"text": "用户1的私有文档", "start": 0.0, "end": 5.0}
    ]
    
    hybrid_1.build_user_index(video_id, documents_1)
    
    # 检查用户1的索引路径
    user1_vector_path = hybrid_1.vector_store.get_user_vector_index_path(video_id)
    user1_bm25_path = hybrid_1.bm25_retriever.get_user_bm25_index_path(video_id)
    user1_hybrid_path = hybrid_1.get_user_hybrid_index_path(video_id)
    
    print(f"   用户1向量索引路径: {user1_vector_path}")
    print(f"   用户1BM25索引路径: {user1_bm25_path}")
    print(f"   用户1混合索引路径: {user1_hybrid_path}")
    print(f"   用户1索引存在: {user1_vector_path.exists() and user1_bm25_path.exists() and user1_hybrid_path.exists()}")
    
    # 设置用户2并检查索引
    print("\n2. 设置用户2并检查索引...")
    user_context.set_user('debug_user_2')
    
    hybrid_2 = get_isolated_hybrid_retriever()
    print(f"   用户2 hybrid_retriever: {hybrid_2.user_id}")
    
    # 检查用户2的索引路径
    user2_vector_path = hybrid_2.vector_store.get_user_vector_index_path(video_id)
    user2_bm25_path = hybrid_2.bm25_retriever.get_user_bm25_index_path(video_id)
    user2_hybrid_path = hybrid_2.get_user_hybrid_index_path(video_id)
    
    print(f"   用户2向量索引路径: {user2_vector_path}")
    print(f"   用户2BM25索引路径: {user2_bm25_path}")
    print(f"   用户2混合索引路径: {user2_hybrid_path}")
    print(f"   用户2索引存在: {user2_vector_path.exists() and user2_bm25_path.exists() and user2_hybrid_path.exists()}")
    
    # 检查路径是否不同
    print(f"\n3. 路径隔离检查:")
    print(f"   向量索引路径不同: {user1_vector_path != user2_vector_path}")
    print(f"   BM25索引路径不同: {user1_bm25_path != user2_bm25_path}")
    print(f"   混合索引路径不同: {user1_hybrid_path != user2_hybrid_path}")
    
    # 检查用户2是否能访问用户1的索引
    print(f"\n4. 访问隔离检查:")
    user2_can_access_user1_vector = user2_vector_path.exists()
    user2_can_access_user1_bm25 = user2_bm25_path.exists()
    user2_can_access_user1_hybrid = user2_hybrid_path.exists()
    
    print(f"   用户2能访问用户1的向量索引: {user2_can_access_user1_vector}")
    print(f"   用户2能访问用户1的BM25索引: {user2_can_access_user1_bm25}")
    print(f"   用户2能访问用户1的混合索引: {user2_can_access_user1_hybrid}")
    
    # 使用 user_indexes_exist 方法检查
    user2_thinks_exists = hybrid_2.user_indexes_exist(video_id)
    print(f"   用户2的user_indexes_exist返回: {user2_thinks_exists}")
    
    # 分析问题
    print(f"\n5. 问题分析:")
    if user2_can_access_user1_vector or user2_can_access_user1_bm25 or user2_can_access_user1_hybrid:
        print("   ❌ 用户2能够访问用户1的索引文件！")
        print("   这表明路径隔离存在问题。")
    else:
        print("   ✅ 用户2无法访问用户1的索引文件！")
        print("   路径隔离正常。")
        
        if user2_thinks_exists:
            print("   ❌ 但user_indexes_exist方法返回True，可能是逻辑错误。")
        else:
            print("   ✅ user_indexes_exist方法也正确返回False。")


if __name__ == "__main__":
    debug_isolation()