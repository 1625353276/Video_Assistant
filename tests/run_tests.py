#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器
Run all tests in the tests directory
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test_file(test_file):
    """运行单个测试文件"""
    print(f"\n{'='*60}")
    print(f"运行测试: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_file} 测试通过 (耗时: {duration:.2f}秒)")
            if result.stdout:
                print("输出:", result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            print(f"❌ {test_file} 测试失败 (耗时: {duration:.2f}秒)")
            if result.stderr:
                print("错误:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 运行 {test_file} 时出现异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始运行所有测试...")
    
    tests_dir = Path(__file__).parent
    test_files = [
        "test_vector_store.py",
        "test_bm25_retriever.py", 
        "test_hybrid_retriever.py",
        "test_multi_query.py",
        "test_local_model.py",
        "test_pipeline.py",
        "test_qa_integration.py",
        "test_complete_qa_flow.py",
        "test_qa_system.py",
        "test_retrieval_integration.py",
        "test_llm_api.py"
    ]
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            if run_test_file(test_file):
                passed += 1
            else:
                failed += 1
        else:
            print(f"⚠️  测试文件不存在: {test_file}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"测试结果汇总")
    print(f"{'='*60}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试都通过了！")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())