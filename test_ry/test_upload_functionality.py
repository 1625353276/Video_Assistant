#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证上传功能完整性

测试完整的视频上传和处理流程，确保所有修复都正常工作
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from deploy.utils.user_context import user_context


def test_upload_functionality():
    """测试上传功能完整性"""
    print("🔧 验证上传功能完整性...")
    
    # 设置测试用户
    user_context.set_user('upload_test_user')
    
    try:
        # 1. 测试路径管理器
        print("\n1. 测试路径管理器...")
        from deploy.utils.user_context import get_current_user_paths
        user_paths = get_current_user_paths()
        
        if not user_paths:
            print("   ❌ 无法获取用户路径管理器")
            return False
        
        print(f"   ✅ 用户路径管理器获取成功: {user_paths}")
        
        # 测试所有路径方法
        temp_path = user_paths.get_temp_path('test.wav')
        upload_path = user_paths.get_upload_path('video123', 'test.mp4')
        user_data_path = user_paths.get_user_data_path()
        
        print(f"   ✅ 临时路径: {temp_path}")
        print(f"   ✅ 上传路径: {upload_path}")
        print(f"   ✅ 用户数据路径: {user_data_path}")
        
        # 2. 测试视频处理器
        print("\n2. 测试视频处理器...")
        from deploy.core.video_processor_isolated import get_isolated_processor
        
        processor = get_isolated_processor()
        print(f"   ✅ 视频处理器获取成功")
        
        # 测试获取用户视频列表
        video_list = processor.get_user_video_list()
        print(f"   ✅ 用户视频列表: {len(video_list)} 个视频")
        
        # 3. 测试索引构建器
        print("\n3. 测试索引构建器...")
        from deploy.core.index_builder_isolated import get_index_builder
        
        index_builder = get_index_builder()
        print(f"   ✅ 索引构建器获取成功")
        
        # 测试获取用户索引列表
        indexes_result = index_builder.get_user_indexes()
        if indexes_result.get("success"):
            print(f"   ✅ 用户索引列表: {indexes_result['total_count']} 个索引")
        else:
            print(f"   ❌ 获取用户索引列表失败: {indexes_result.get('error')}")
            return False
        
        # 4. 测试对话管理器
        print("\n4. 测试对话管理器...")
        from deploy.core.conversation_manager_isolated import get_conversation_manager
        
        conversation_manager = get_conversation_manager()
        print(f"   ✅ 对话管理器获取成功")
        
        # 5. 测试完整的模拟上传流程
        print("\n5. 测试模拟上传流程...")
        
        # 创建临时视频文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'fake video content')
            temp_video_path = temp_file.name
        
        try:
            # 模拟上传处理
            video_id = "test_video_123"
            filename = Path(temp_video_path).name
            
            # 测试上传路径生成
            upload_dest = user_paths.get_upload_path(video_id, filename)
            print(f"   ✅ 上传目标路径: {upload_dest}")
            
            # 确保目录存在
            upload_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件到用户目录
            import shutil
            shutil.copy2(temp_video_path, upload_dest)
            print(f"   ✅ 文件复制到用户目录成功")
            
            # 验证文件存在
            if upload_dest.exists():
                print(f"   ✅ 上传文件验证成功")
            else:
                print(f"   ❌ 上传文件验证失败")
                return False
            
            # 测试视频信息获取
            video_info = processor.get_video_info(video_id)
            if video_info:
                print(f"   ✅ 视频信息获取成功: {video_info.get('filename', 'Unknown')}")
            else:
                print(f"   ⚠ 视频信息不存在（正常，因为未实际处理）")
            
            # 测试转录数据保存（模拟）
            transcript_data = {
                "text": "这是测试转录内容",
                "segments": [
                    {"text": "这是第一个片段", "start": 0.0, "end": 5.0},
                    {"text": "这是第二个片段", "start": 5.0, "end": 10.0}
                ]
            }
            
            # 保存转录数据
            transcript_path = user_paths.get_transcript_path(video_id)
            import json
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 转录数据保存成功: {transcript_path}")
            
            # 测试索引构建
            index_result = index_builder.build_user_index(video_id, transcript_data)
            if index_result.get("success"):
                print(f"   ✅ 索引构建成功: {index_result.get('message')}")
            else:
                print(f"   ❌ 索引构建失败: {index_result.get('error')}")
                return False
            
            # 测试检索功能
            search_result = index_builder.search_in_video(video_id, "片段", search_type="hybrid")
            if search_result.get("success"):
                print(f"   ✅ 检索功能正常: 返回 {search_result.get('total_results', 0)} 个结果")
            else:
                print(f"   ❌ 检索功能失败: {search_result.get('error')}")
                return False
            
        finally:
            # 清理临时文件
            os.unlink(temp_video_path)
            print(f"   ✅ 临时文件清理完成")
        
        print(f"\n🎉 所有功能验证通过！上传功能完整性测试成功！")
        return True
        
    except Exception as e:
        print(f"   ❌ 功能验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_upload_functionality()
    sys.exit(0 if success else 1)