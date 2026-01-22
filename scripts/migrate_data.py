#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移执行脚本

用于将现有的共享数据迁移到用户隔离的目录结构中
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from deploy.utils.data_migrator import DataMigrator


def main():
    """主函数"""
    print("🚀 视频助手数据迁移工具")
    print("=" * 50)
    
    # 检查当前目录结构
    data_dir = project_root / "data"
    if not data_dir.exists():
        print("❌ 错误: 未找到 data 目录")
        print("请确保在项目根目录中运行此脚本")
        return False
    
    print(f"📁 数据目录: {data_dir}")
    
    # 检查是否有共享数据需要迁移
    shared_dirs = ["raw_videos", "transcripts", "memory", "vectors"]
    has_shared_data = False
    
    for dir_name in shared_dirs:
        dir_path = data_dir / dir_name
        if dir_path.exists() and any(dir_path.iterdir()):
            has_shared_data = True
            file_count = len([f for f in dir_path.iterdir() if f.is_file()])
            print(f"📂 发现共享数据: {dir_name} ({file_count} 个文件)")
    
    if not has_shared_data:
        print("✅ 未发现需要迁移的共享数据")
        print("数据可能已经是用户隔离的，或者目录为空")
        return True
    
    print("\n⚠️  重要提示:")
    print("1. 此操作将把共享数据移动到用户专属目录")
    print("2. 原始数据将被备份到 data/backup_YYYYMMDD_HHMMSS 目录")
    print("3. 迁移完成后，每个用户的数据将独立存储在 data/users/{user_id}/ 目录下")
    print("4. 此操作是安全的，可以随时回滚")
    
    # 询问用户确认
    response = input("\n是否继续数据迁移? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ 用户取消操作")
        return False
    
    try:
        # 创建迁移器并执行迁移
        migrator = DataMigrator(base_data_dir=str(data_dir))
        
        print("\n🔄 开始数据迁移...")
        success = migrator.run_full_migration(cleanup_shared=True, backup=True)
        
        if success:
            print("\n✅ 数据迁移成功完成！")
            print(f"📊 迁移报告: {migrator.save_migration_report()}")
            
            # 显示迁移结果
            users_dir = data_dir / "users"
            if users_dir.exists():
                print("\n👥 用户数据概览:")
                for user_dir in users_dir.iterdir():
                    if user_dir.is_dir():
                        user_id = user_dir.name
                        video_count = len(list((user_dir / "videos").glob("*"))) if (user_dir / "videos").exists() else 0
                        transcript_count = len(list((user_dir / "transcripts").glob("*"))) if (user_dir / "transcripts").exists() else 0
                        conversation_count = len(list((user_dir / "conversations").glob("*"))) if (user_dir / "conversations").exists() else 0
                        
                        print(f"  👤 {user_id}:")
                        print(f"    📹 视频: {video_count} 个")
                        print(f"    📝 转录: {transcript_count} 个")
                        print(f"    💬 对话: {conversation_count} 个")
            
            # 显示备份信息
            backup_dirs = list(data_dir.glob("backup_*"))
            if backup_dirs:
                latest_backup = max(backup_dirs, key=lambda x: x.stat().st_mtime)
                print(f"\n💾 数据备份: {latest_backup}")
                print("如需回滚，可以从备份目录恢复数据")
            
            print("\n🎉 迁移完成！系统现在已支持用户数据隔离")
            return True
        else:
            print("\n❌ 数据迁移失败")
            print("请检查日志并重试")
            return False
            
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)