#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户隔离检索系统测试

测试向量存储、BM25检索器和混合检索器的用户隔离功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from deploy.utils.user_context import user_context
from modules.retrieval.isolated_vector_store import get_isolated_vector_store
from modules.retrieval.isolated_bm25_retriever import get_isolated_bm25_retriever
from modules.retrieval.isolated_hybrid_retriever import get_isolated_hybrid_retriever


def test_isolated_vector_store():
    """测试用户隔离的向量存储"""
    print("🔧 测试用户隔离的向量存储...")
    
    # 设置测试用户1
    user_context.set_user('test_user_1')
    
    try:
        # 创建用户隔离的向量存储
        vector_store_1 = get_isolated_vector_store()
        print(f"   ✅ 用户1向量存储创建成功: {vector_store_1.user_id}")
        
        # 测试文档添加
        documents_1 = [
            {"text": "人工智能是计算机科学的一个分支", "start": 0.0, "end": 5.0},
            {"text": "机器学习是人工智能的子领域", "start": 5.0, "end": 10.0}
        ]
        vector_store_1.add_documents(documents_1)
        print(f"   ✅ 用户1添加文档成功")
        
        # 测试索引保存
        video_id = "test_video_1"
        vector_store_1.save_user_index(video_id)
        print(f"   ✅ 用户1索引保存成功")
        
        # 测试索引存在性检查
        exists = vector_store_1.user_index_exists(video_id)
        print(f"   ✅ 用户1索引存在性检查: {exists}")
        
    except Exception as e:
        print(f"   ❌ 用户1测试失败: {e}")
        return False
    
    # 设置测试用户2
    user_context.set_user('test_user_2')
    
    try:
        # 创建用户隔离的向量存储
        vector_store_2 = get_isolated_vector_store()
        print(f"   ✅ 用户2向量存储创建成功: {vector_store_2.user_id}")
        
        # 测试文档添加
        documents_2 = [
            {"text": "深度学习是机器学习的一个分支", "start": 0.0, "end": 5.0},
            {"text": "神经网络是深度学习的基础", "start": 5.0, "end": 10.0}
        ]
        vector_store_2.add_documents(documents_2)
        print(f"   ✅ 用户2添加文档成功")
        
        # 测试索引保存
        video_id = "test_video_1"  # 相同的视频ID，但不同用户
        vector_store_2.save_user_index(video_id)
        print(f"   ✅ 用户2索引保存成功")
        
    except Exception as e:
        print(f"   ❌ 用户2测试失败: {e}")
        return False
    
    # 验证路径隔离
    try:
        user1_path = vector_store_1.get_user_vector_index_path(video_id)
        user2_path = vector_store_2.get_user_vector_index_path(video_id)
        
        print(f"   ✅ 用户1索引路径: {user1_path}")
        print(f"   ✅ 用户2索引路径: {user2_path}")
        
        # 验证路径不同
        if user1_path != user2_path:
            print(f"   ✅ 用户索引路径隔离验证成功")
        else:
            print(f"   ❌ 用户索引路径隔离验证失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 路径隔离验证失败: {e}")
        return False
    
    return True


def test_isolated_bm25_retriever():
    """测试用户隔离的BM25检索器"""
    print("\n🔧 测试用户隔离的BM25检索器...")
    
    # 设置测试用户1
    user_context.set_user('test_user_1')
    
    try:
        # 创建用户隔离的BM25检索器
        bm25_1 = get_isolated_bm25_retriever()
        print(f"   ✅ 用户1 BM25检索器创建成功: {bm25_1.user_id}")
        
        # 测试文档添加
        documents_1 = [
            {"text": "人工智能是计算机科学的一个分支", "start": 0.0, "end": 5.0},
            {"text": "机器学习是人工智能的子领域", "start": 5.0, "end": 10.0}
        ]
        bm25_1.add_documents(documents_1)
        print(f"   ✅ 用户1添加文档成功")
        
        # 测试索引保存
        video_id = "test_video_2"
        bm25_1.save_user_index(video_id)
        print(f"   ✅ 用户1索引保存成功")
        
        # 测试检索
        results = bm25_1.search("人工智能", top_k=2)
        print(f"   ✅ 用户1检索成功，返回{len(results)}个结果")
        
    except Exception as e:
        print(f"   ❌ 用户1测试失败: {e}")
        return False
    
    return True


def test_isolated_hybrid_retriever():
    """测试用户隔离的混合检索器"""
    print("\n🔧 测试用户隔离的混合检索器...")
    
    # 设置测试用户1
    user_context.set_user('test_user_1')
    
    try:
        # 创建用户隔离的混合检索器
        hybrid_1 = get_isolated_hybrid_retriever()
        print(f"   ✅ 用户1混合检索器创建成功: {hybrid_1.user_id}")
        
        # 测试索引构建
        documents_1 = [
            {"text": "人工智能是计算机科学的一个分支", "start": 0.0, "end": 5.0},
            {"text": "机器学习是人工智能的子领域", "start": 5.0, "end": 10.0},
            {"text": "深度学习使用神经网络", "start": 10.0, "end": 15.0}
        ]
        video_id = "test_video_3"
        hybrid_1.build_user_index(video_id, documents_1)
        print(f"   ✅ 用户1混合索引构建成功")
        
        # 测试检索
        results = hybrid_1.search("人工智能", top_k=3)
        print(f"   ✅ 用户1混合检索成功，返回{len(results)}个结果")
        
        # 测试索引存在性
        exists = hybrid_1.user_indexes_exist(video_id)
        print(f"   ✅ 用户1混合索引存在性检查: {exists}")
        
    except Exception as e:
        print(f"   ❌ 用户1测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_cross_user_isolation():
    """测试跨用户隔离"""
    print("\n🔧 测试跨用户隔离...")
    
    # 设置用户1并构建索引
    user_context.set_user('test_user_1')
    try:
        hybrid_1 = get_isolated_hybrid_retriever()
        documents_1 = [
            {"text": "用户1的私有文档", "start": 0.0, "end": 5.0},
            {"text": "包含敏感信息", "start": 5.0, "end": 10.0}
        ]
        video_id = "private_video"
        hybrid_1.build_user_index(video_id, documents_1)
        print(f"   ✅ 用户1私有索引构建成功")
    except Exception as e:
        print(f"   ❌ 用户1索引构建失败: {e}")
        return False
    
    # 设置用户2并尝试访问用户1的索引
    user_context.set_user('test_user_2')
    try:
        hybrid_2 = get_isolated_hybrid_retriever()
        
        # 检查用户2是否能访问用户1的索引（在用户2构建自己的索引之前）
        exists = hybrid_2.user_indexes_exist(video_id)
        if not exists:
            print(f"   ✅ 用户2无法访问用户1的索引（隔离成功）")
        else:
            print(f"   ❌ 用户2能够访问用户1的索引（隔离失败）")
            return False
        
        # 用户2构建自己的索引
        documents_2 = [
            {"text": "用户2的私有文档", "start": 0.0, "end": 5.0},
            {"text": "包含其他信息", "start": 5.0, "end": 10.0}
        ]
        hybrid_2.build_user_index(video_id, documents_2)
        print(f"   ✅ 用户2私有索引构建成功")
        
        # 验证用户2现在能访问自己的索引
        exists_after_build = hybrid_2.user_indexes_exist(video_id)
        if not exists_after_build:
            print(f"   ❌ 用户2无法访问自己构建的索引")
            return False
        
        # 验证两个用户的索引路径不同
        user1_path = hybrid_1.get_user_hybrid_index_path(video_id)
        user2_path = hybrid_2.get_user_hybrid_index_path(video_id)
        
        if user1_path != user2_path:
            print(f"   ✅ 跨用户索引路径隔离验证成功")
        else:
            print(f"   ❌ 跨用户索引路径隔离验证失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 用户2测试失败: {e}")
        return False
    
    return True


def test_index_builder_integration():
    """测试索引构建器集成"""
    print("\n🔧 测试索引构建器集成...")
    
    # 设置测试用户
    user_context.set_user('test_user_integration')
    
    try:
        from deploy.core.index_builder_isolated import get_index_builder
        
        # 获取索引构建器
        index_builder = get_index_builder()
        print(f"   ✅ 索引构建器获取成功")
        
        # 准备转录数据
        transcript_data = {
            "segments": [
                {"text": "这是第一个片段", "start": 0.0, "end": 5.0},
                {"text": "这是第二个片段", "start": 5.0, "end": 10.0},
                {"text": "这是第三个片段", "start": 10.0, "end": 15.0}
            ]
        }
        
        # 构建索引
        video_id = "integration_test_video"
        result = index_builder.build_user_index(video_id, transcript_data)
        
        if "error" in result:
            print(f"   ❌ 索引构建失败: {result['error']}")
            return False
        else:
            print(f"   ✅ 索引构建成功")
        
        # 测试检索
        search_results = index_builder.search_in_video(video_id, "片段", search_type="hybrid")
        print(f"   ✅ 检索测试成功，返回{len(search_results)}个结果")
        
    except Exception as e:
        print(f"   ❌ 索引构建器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """主测试函数"""
    print("🚀 开始用户隔离检索系统测试...")
    
    tests = [
        ("用户隔离向量存储", test_isolated_vector_store),
        ("用户隔离BM25检索器", test_isolated_bm25_retriever),
        ("用户隔离混合检索器", test_isolated_hybrid_retriever),
        ("跨用户隔离", test_cross_user_isolation),
        ("索引构建器集成", test_index_builder_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} 测试通过")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！用户隔离检索系统重构成功！")
        return True
    else:
        print("⚠ 部分测试失败，需要检查和修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
