#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第五阶段测试：数据迁移和清理

测试数据从共享目录迁移到用户隔离目录的功能
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deploy.utils.data_migrator import DataMigrator


def create_test_data_structure(base_dir: Path):
    """创建测试数据结构"""
    # 创建共享数据目录
    shared_dirs = {
        "videos": base_dir / "data" / "raw_videos",
        "transcripts": base_dir / "data" / "transcripts",
        "conversations": base_dir / "data" / "memory",
        "vectors": base_dir / "data" / "vectors"
    }
    
    for dir_path in shared_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 创建测试视频文件
    test_video = shared_dirs["videos"] / "test_video.mp4"
    test_video.write_bytes(b"fake video content")
    
    # 创建测试转录文件
    test_transcript = shared_dirs["transcripts"] / "test_video_transcript.json"
    transcript_data = {
        "text": "这是测试转录文本",
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "第一段测试内容"},
            {"id": 1, "start": 5.0, "end": 10.0, "text": "第二段测试内容"}
        ]
    }
    test_transcript.write_text(json.dumps(transcript_data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    # 创建测试对话文件
    test_conversation = shared_dirs["conversations"] / "test_video_conversation.json"
    conversation_data = {
        "user_id": "test_user_123",
        "session_id": "test_session",
        "created_at": datetime.now().isoformat(),
        "history": [
            {"role": "user", "content": "什么是人工智能？"},
            {"role": "assistant", "content": "人工智能是计算机科学的一个分支..."}
        ]
    }
    test_conversation.write_text(json.dumps(conversation_data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    # 创建测试向量文件
    test_vector = shared_dirs["vectors"] / "test_vector_index.pkl"
    test_vector.write_bytes(b"fake vector data")
    
    return shared_dirs


def test_data_migrator_init():
    """测试数据迁移器初始化"""
    print("🧪 测试数据迁移器初始化...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        migrator = DataMigrator(base_data_dir=os.path.join(temp_dir, "data"))
        
        assert migrator.base_data_dir == Path(os.path.join(temp_dir, "data"))
        assert isinstance(migrator.shared_dirs, dict)
        assert isinstance(migrator.users_dir, Path)
        assert isinstance(migrator.migration_log, list)
        
        print("✅ 数据迁移器初始化测试通过")


def test_scan_shared_data():
    """测试扫描共享数据"""
    print("🧪 测试扫描共享数据...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试数据
        shared_dirs = create_test_data_structure(temp_path)
        
        # 创建迁移器并扫描
        migrator = DataMigrator(base_data_dir=str(temp_path / "data"))
        shared_data = migrator.scan_shared_data()
        
        # 验证扫描结果
        assert len(shared_data["videos"]) == 1
        assert len(shared_data["transcripts"]) == 1
        assert len(shared_data["conversations"]) == 1
        assert len(shared_data["vectors"]) == 1
        
        # 验证视频数据
        video = shared_data["videos"][0]
        assert video["filename"] == "test_video.mp4"
        assert "md5" in video
        assert "size" in video
        
        # 验证转录数据
        transcript = shared_data["transcripts"][0]
        assert transcript["filename"] == "test_video_transcript.json"
        assert transcript["type"] == ".json"
        
        # 验证对话数据
        conversation = shared_data["conversations"][0]
        assert conversation["filename"] == "test_video_conversation.json"
        assert conversation["user_id"] == "test_user_123"
        assert "data" in conversation
        
        print("✅ 扫描共享数据测试通过")


def test_identify_user_ownership():
    """测试识别用户归属"""
    print("🧪 测试识别用户归属...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试数据
        shared_dirs = create_test_data_structure(temp_path)
        
        # 创建迁移器并扫描
        migrator = DataMigrator(base_data_dir=str(temp_path / "data"))
        shared_data = migrator.scan_shared_data()
        
        # 识别用户归属
        user_data_map = migrator.identify_user_ownership(shared_data)
        
        # 验证用户数据映射
        assert "test_user_123" in user_data_map
        assert "default_user" in user_data_map  # 未分配数据的默认用户
        
        # 验证用户数据
        user_data = user_data_map["test_user_123"]
        assert user_data["user_id"] == "test_user_123"
        assert len(user_data["conversations"]) == 1
        assert isinstance(user_data["videos"], list)
        assert isinstance(user_data["transcripts"], list)
        assert isinstance(user_data["vectors"], list)
        
        print("✅ 识别用户归属测试通过")


def test_migrate_user_data():
    """测试迁移用户数据"""
    print("🧪 测试迁移用户数据...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试数据
        shared_dirs = create_test_data_structure(temp_path)
        
        # 创建迁移器并扫描
        migrator = DataMigrator(base_data_dir=str(temp_path / "data"))
        shared_data = migrator.scan_shared_data()
        user_data_map = migrator.identify_user_ownership(shared_data)
        
        # 执行迁移
        migration_success = migrator.migrate_user_data(user_data_map)
        
        # 验证迁移结果
        assert migration_success is True
        assert len(migrator.migration_log) > 0
        
        # 验证用户目录结构
        users_dir = temp_path / "data" / "users"
        assert users_dir.exists()
        
        # 验证test_user_123的目录
        test_user_dir = users_dir / "test_user_123"
        assert test_user_dir.exists()
        
        # 验证子目录
        for subdir in ["videos", "transcripts", "conversations", "vectors"]:
            assert (test_user_dir / subdir).exists()
        
        # 验证文件迁移
        assert (test_user_dir / "conversations" / "test_video_conversation.json").exists()
        
        print("✅ 迁移用户数据测试通过")


def test_validate_migration():
    """测试验证迁移结果"""
    print("🧪 测试验证迁移结果...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试数据并迁移
        shared_dirs = create_test_data_structure(temp_path)
        migrator = DataMigrator(base_data_dir=str(temp_path / "data"))
        shared_data = migrator.scan_shared_data()
        user_data_map = migrator.identify_user_ownership(shared_data)
        migrator.migrate_user_data(user_data_map)
        
        # 验证迁移结果
        validation_results = migrator.validate_migration()
        
        # 验证结果
        assert isinstance(validation_results, dict)
        assert len(validation_results) > 0
        
        # 检查关键验证项
        assert "test_user_123_videos" in validation_results
        assert "test_user_123_transcripts" in validation_results
        assert "test_user_123_conversations" in validation_results
        assert "test_user_123_vectors" in validation_results
        
        # 所有验证项应该都为True
        assert all(validation_results.values())
        
        print("✅ 验证迁移结果测试通过")


def test_save_migration_report():
    """测试保存迁移报告"""
    print("🧪 测试保存迁移报告...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建迁移器并执行迁移
        shared_dirs = create_test_data_structure(temp_path)
        migrator = DataMigrator(base_data_dir=str(temp_path / "data"))
        shared_data = migrator.scan_shared_data()
        user_data_map = migrator.identify_user_ownership(shared_data)
        migrator.migrate_user_data(user_data_map)
        
        # 保存迁移报告
        report_path = migrator.save_migration_report()
        
        # 验证报告文件
        assert Path(report_path).exists()
        
        # 验证报告内容
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        assert "migration_time" in report_data
        assert "total_operations" in report_data
        assert "successful_operations" in report_data
        assert "failed_operations" in report_data
        assert "log" in report_data
        
        # 验证日志内容
        assert len(report_data["log"]) > 0
        assert report_data["log"][0]["action"] == "copy"
        assert report_data["log"][0]["status"] == "success"
        
        print("✅ 保存迁移报告测试通过")


def test_cleanup_shared_data():
    """测试清理共享数据"""
    print("🧪 测试清理共享数据...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试数据
        shared_dirs = create_test_data_structure(temp_path)
        
        # 验证数据存在
        for dir_path in shared_dirs.values():
            assert dir_path.exists()
        
        # 创建迁移器并清理
        migrator = DataMigrator(base_data_dir=str(temp_path / "data"))
        cleanup_success = migrator.cleanup_shared_data(backup=True)
        
        # 验证清理结果
        assert cleanup_success is True
        
        # 验证共享目录已清理
        for dir_path in shared_dirs.values():
            assert not dir_path.exists()
        
        # 验证备份目录已创建
        backup_dirs = list((temp_path / "data").glob("backup_*"))
        assert len(backup_dirs) == 1
        
        # 验证备份数据
        backup_dir = backup_dirs[0]
        # 检查备份目录中是否有内容
        backup_subdirs = [d for d in backup_dir.iterdir() if d.is_dir()]
        assert len(backup_subdirs) >= 1  # 至少有一个备份目录
        
        # 验证备份目录包含预期的数据
        backup_has_data = False
        for subdir in backup_subdirs:
            if subdir.name in ["raw_videos", "transcripts", "memory", "vectors"]:
                backup_has_data = True
                break
        assert backup_has_data
        
        print("✅ 清理共享数据测试通过")


def test_full_migration():
    """测试完整迁移流程"""
    print("🧪 测试完整迁移流程...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试数据
        shared_dirs = create_test_data_structure(temp_path)
        
        # 创建迁移器并执行完整流程
        migrator = DataMigrator(base_data_dir=str(temp_path / "data"))
        migration_success = migrator.run_full_migration(cleanup_shared=False, backup=True)
        
        # 验证迁移成功
        assert migration_success is True
        
        # 验证用户数据已迁移
        users_dir = temp_path / "data" / "users"
        assert users_dir.exists()
        
        # 验证迁移报告已生成
        report_files = list((temp_path / "data").glob("migration_report_*.json"))
        assert len(report_files) == 1
        
        # 验证共享数据仍然存在（因为cleanup_shared=False）
        for dir_path in shared_dirs.values():
            assert dir_path.exists()
        
        print("✅ 完整迁移流程测试通过")


def test_md5_calculation():
    """测试MD5计算"""
    print("🧪 测试MD5计算...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试文件
        test_file = temp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content, encoding='utf-8')
        
        # 创建迁移器并计算MD5
        migrator = DataMigrator()
        md5_hash = migrator._calculate_md5(test_file)
        
        # 验证MD5结果
        assert isinstance(md5_hash, str)
        assert len(md5_hash) == 32  # MD5哈希长度
        
        # 验证相同内容产生相同哈希
        test_file2 = temp_path / "test2.txt"
        test_file2.write_text(test_content, encoding='utf-8')
        md5_hash2 = migrator._calculate_md5(test_file2)
        assert md5_hash == md5_hash2
        
        # 验证不同内容产生不同哈希
        test_file3 = temp_path / "test3.txt"
        test_file3.write_text("Different content", encoding='utf-8')
        md5_hash3 = migrator._calculate_md5(test_file3)
        assert md5_hash != md5_hash3
        
        print("✅ MD5计算测试通过")


def run_stage5_tests():
    """运行第五阶段所有测试"""
    print("🚀 开始第五阶段测试：数据迁移和清理\n")
    
    try:
        test_data_migrator_init()
        print()
        test_scan_shared_data()
        print()
        test_identify_user_ownership()
        print()
        test_migrate_user_data()
        print()
        test_validate_migration()
        print()
        test_save_migration_report()
        print()
        test_cleanup_shared_data()
        print()
        test_full_migration()
        print()
        test_md5_calculation()
        print()
        
        print("🎉 第五阶段所有测试通过！")
        print("✅ 数据迁移器实现完成")
        print("✅ 共享数据扫描功能实现完成")
        print("✅ 用户归属识别功能实现完成")
        print("✅ 用户数据迁移功能实现完成")
        print("✅ 迁移结果验证功能实现完成")
        print("✅ 迁移报告生成功能实现完成")
        print("✅ 共享数据清理功能实现完成")
        print("✅ 完整迁移流程实现完成")
        print("✅ MD5文件校验功能实现完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_stage5_tests()
    sys.exit(0 if success else 1)
