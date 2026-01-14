#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试向量存储本地模型加载
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.retrieval.vector_store import VectorStore

def test_local_model():
    """测试本地模型加载"""
    print("=" * 60)
    print("测试向量存储本地模型加载")
    print("=" * 60)
    
    try:
        # 设置模型缓存目录为项目本地目录
        models_dir = project_root / "models"
        
        print(f"模型缓存目录: {models_dir}")
        print()
        
        # 创建向量存储实例
        print("1. 创建VectorStore实例...")
        vector_store = VectorStore(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(models_dir),
            mirror_site="tuna"  # 使用国内镜像
        )
        print("✅ VectorStore实例创建成功")
        print()
        
        # 测试模型加载
        print("2. 测试模型加载...")
        vector_store.load_model()
        print("✅ 模型加载成功")
        print()
        
        # 测试文本编码
        print("3. 测试文本编码...")
        test_texts = [
            "人工智能是计算机科学的一个分支",
            "机器学习是人工智能的子领域"
        ]
        
        embeddings = vector_store.encode_texts(test_texts)
        print(f"✅ 文本编码成功，向量形状: {embeddings.shape}")
        print()
        
        # 测试文档添加和检索
        print("4. 测试文档添加和检索...")
        test_documents = [
            {
                'text': '人工智能是计算机科学的一个分支，它试图理解和构建智能体。',
                'start': 0.0,
                'end': 5.0,
                'confidence': 0.95
            },
            {
                'text': '机器学习是人工智能的一个子领域，专注于算法和统计模型。',
                'start': 5.0,
                'end': 10.0,
                'confidence': 0.92
            }
        ]
        
        vector_store.add_documents(test_documents)
        
        # 测试检索
        results = vector_store.search("什么是人工智能？", top_k=2)
        print(f"✅ 检索成功，返回 {len(results)} 个结果")
        
        for i, result in enumerate(results, 1):
            print(f"   结果 {i}: {result['document']['text'][:50]}...")
            print(f"   相似度: {result['similarity']:.3f}")
        
        print()
        print("🎉 所有测试通过！本地模型加载正常工作。")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_local_model()