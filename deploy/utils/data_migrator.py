#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移工具

将共享数据目录中的现有数据迁移到用户隔离的目录结构中
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self, base_data_dir: str = "data"):
        """
        初始化数据迁移器
        
        Args:
            base_data_dir: 基础数据目录
        """
        self.base_data_dir = Path(base_data_dir)
        self.shared_dirs = {
            "videos": self.base_data_dir / "raw_videos",
            "transcripts": self.base_data_dir / "transcripts", 
            "conversations": self.base_data_dir / "memory",
            "vectors": self.base_data_dir / "vectors",
            "cache": self.base_data_dir / "cache"
        }
        self.users_dir = self.base_data_dir / "users"
        self.migration_log = []
        
    def scan_shared_data(self) -> Dict[str, List[Dict]]:
        """
        扫描共享数据目录中的所有数据
        
        Returns:
            Dict[str, List[Dict]]: 各个类型的数据列表
        """
        logger.info("开始扫描共享数据目录...")
        
        shared_data = {
            "videos": [],
            "transcripts": [],
            "conversations": [],
            "vectors": []
        }
        
        # 扫描视频文件
        if self.shared_dirs["videos"].exists():
            for video_file in self.shared_dirs["videos"].glob("*"):
                if video_file.is_file() and video_file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                    stat = video_file.stat()
                    shared_data["videos"].append({
                        "path": str(video_file),
                        "filename": video_file.name,
                        "size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "md5": self._calculate_md5(video_file)
                    })
        
        # 扫描转录文件
        if self.shared_dirs["transcripts"].exists():
            for transcript_file in self.shared_dirs["transcripts"].glob("*"):
                if transcript_file.is_file() and transcript_file.suffix.lower() in ['.json', '.txt', '.srt']:
                    stat = transcript_file.stat()
                    shared_data["transcripts"].append({
                        "path": str(transcript_file),
                        "filename": transcript_file.name,
                        "size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": transcript_file.suffix.lower()
                    })
        
        # 扫描对话历史
        if self.shared_dirs["conversations"].exists():
            for conv_file in self.shared_dirs["conversations"].glob("*"):
                if conv_file.is_file() and conv_file.suffix.lower() == '.json':
                    try:
                        with open(conv_file, 'r', encoding='utf-8') as f:
                            conv_data = json.load(f)
                        
                        # 尝试识别对话所属用户（如果有）
                        user_id = conv_data.get('user_id', 'unknown')
                        
                        shared_data["conversations"].append({
                            "path": str(conv_file),
                            "filename": conv_file.name,
                            "size": conv_file.stat().st_size,
                            "modified_time": datetime.fromtimestamp(conv_file.stat().st_mtime).isoformat(),
                            "user_id": user_id,
                            "data": conv_data
                        })
                    except Exception as e:
                        logger.warning(f"无法读取对话文件 {conv_file}: {e}")
        
        # 扫描向量索引
        if self.shared_dirs["vectors"].exists():
            for vector_file in self.shared_dirs["vectors"].glob("*"):
                if vector_file.is_file():
                    stat = vector_file.stat()
                    shared_data["vectors"].append({
                        "path": str(vector_file),
                        "filename": vector_file.name,
                        "size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": "vector_index"
                    })
        
        logger.info(f"扫描完成，发现: {len(shared_data['videos'])} 个视频, "
                   f"{len(shared_data['transcripts'])} 个转录文件, "
                   f"{len(shared_data['conversations'])} 个对话, "
                   f"{len(shared_data['vectors'])} 个向量文件")
        
        return shared_data
    
    def identify_user_ownership(self, shared_data: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """
        识别数据归属用户
        
        Args:
            shared_data: 共享数据
            
        Returns:
            Dict[str, Dict]: 用户数据映射
        """
        logger.info("开始识别数据归属...")
        
        user_data_map = {}
        
        # 分析对话文件中的用户信息
        for conv in shared_data["conversations"]:
            user_id = conv["user_id"]
            if user_id not in user_data_map:
                user_data_map[user_id] = {
                    "user_id": user_id,
                    "videos": [],
                    "transcripts": [],
                    "conversations": [],
                    "vectors": []
                }
            
            user_data_map[user_id]["conversations"].append(conv)
        
        # 通过文件名关联视频和转录文件
        video_transcript_map = {}
        for video in shared_data["videos"]:
            video_name = Path(video["filename"]).stem
            video_transcript_map[video_name] = {"video": video, "transcripts": []}
        
        for transcript in shared_data["transcripts"]:
            transcript_name = Path(transcript["filename"]).stem
            if transcript_name in video_transcript_map:
                video_transcript_map[transcript_name]["transcripts"].append(transcript)
        
        # 将视频和转录文件分配给用户（这里简化处理，实际可能需要更复杂的逻辑）
        # 如果有对话数据，尝试通过对话内容关联视频
        for user_id, user_data in user_data_map.items():
            for conv in user_data["conversations"]:
                # 简单的文件名匹配逻辑
                conv_filename = Path(conv["filename"]).stem
                for video_name, vt_data in video_transcript_map.items():
                    if conv_filename in video_name or video_name in conv_filename:
                        if vt_data["video"] not in user_data["videos"]:
                            user_data["videos"].append(vt_data["video"])
                        user_data["transcripts"].extend(vt_data["transcripts"])
        
        # 对于无法关联的数据，创建默认用户
        unassigned_videos = [v for v in shared_data["videos"] 
                           if not any(v in ud["videos"] for ud in user_data_map.values())]
        unassigned_transcripts = [t for t in shared_data["transcripts"] 
                                if not any(t in ud["transcripts"] for ud in user_data_map.values())]
        
        if unassigned_videos or unassigned_transcripts:
            default_user_id = "default_user"
            if default_user_id not in user_data_map:
                user_data_map[default_user_id] = {
                    "user_id": default_user_id,
                    "videos": [],
                    "transcripts": [],
                    "conversations": [],
                    "vectors": []
                }
            
            user_data_map[default_user_id]["videos"].extend(unassigned_videos)
            user_data_map[default_user_id]["transcripts"].extend(unassigned_transcripts)
            user_data_map[default_user_id]["vectors"] = shared_data["vectors"]
        
        logger.info(f"识别出 {len(user_data_map)} 个用户的数据")
        return user_data_map
    
    def migrate_user_data(self, user_data_map: Dict[str, Dict]) -> bool:
        """
        迁移用户数据
        
        Args:
            user_data_map: 用户数据映射
            
        Returns:
            bool: 迁移是否成功
        """
        logger.info("开始迁移用户数据...")
        
        try:
            # 确保用户目录存在
            self.users_dir.mkdir(exist_ok=True)
            
            migration_success = True
            
            for user_id, user_data in user_data_map.items():
                logger.info(f"迁移用户 {user_id} 的数据...")
                
                # 创建用户目录结构
                user_dir = self.users_dir / user_id
                user_videos_dir = user_dir / "videos"
                user_transcripts_dir = user_dir / "transcripts"
                user_conversations_dir = user_dir / "conversations"
                user_vectors_dir = user_dir / "vectors"
                
                for dir_path in [user_dir, user_videos_dir, user_transcripts_dir, 
                               user_conversations_dir, user_vectors_dir]:
                    dir_path.mkdir(exist_ok=True)
                
                # 迁移视频文件
                for video in user_data["videos"]:
                    try:
                        src_path = Path(video["path"])
                        dst_path = user_videos_dir / video["filename"]
                        
                        if not dst_path.exists():
                            shutil.copy2(src_path, dst_path)
                            self.migration_log.append({
                                "timestamp": datetime.now().isoformat(),
                                "user_id": user_id,
                                "action": "copy",
                                "source": str(src_path),
                                "destination": str(dst_path),
                                "status": "success"
                            })
                            logger.info(f"复制视频文件: {video['filename']}")
                        else:
                            logger.warning(f"视频文件已存在: {video['filename']}")
                    except Exception as e:
                        logger.error(f"复制视频文件失败 {video['filename']}: {e}")
                        migration_success = False
                
                # 迁移转录文件
                for transcript in user_data["transcripts"]:
                    try:
                        src_path = Path(transcript["path"])
                        dst_path = user_transcripts_dir / transcript["filename"]
                        
                        if not dst_path.exists():
                            shutil.copy2(src_path, dst_path)
                            self.migration_log.append({
                                "timestamp": datetime.now().isoformat(),
                                "user_id": user_id,
                                "action": "copy",
                                "source": str(src_path),
                                "destination": str(dst_path),
                                "status": "success"
                            })
                            logger.info(f"复制转录文件: {transcript['filename']}")
                        else:
                            logger.warning(f"转录文件已存在: {transcript['filename']}")
                    except Exception as e:
                        logger.error(f"复制转录文件失败 {transcript['filename']}: {e}")
                        migration_success = False
                
                # 迁移对话文件
                for conv in user_data["conversations"]:
                    try:
                        src_path = Path(conv["path"])
                        dst_path = user_conversations_dir / conv["filename"]
                        
                        if not dst_path.exists():
                            shutil.copy2(src_path, dst_path)
                            self.migration_log.append({
                                "timestamp": datetime.now().isoformat(),
                                "user_id": user_id,
                                "action": "copy",
                                "source": str(src_path),
                                "destination": str(dst_path),
                                "status": "success"
                            })
                            logger.info(f"复制对话文件: {conv['filename']}")
                        else:
                            logger.warning(f"对话文件已存在: {conv['filename']}")
                    except Exception as e:
                        logger.error(f"复制对话文件失败 {conv['filename']}: {e}")
                        migration_success = False
                
                # 迁移向量文件
                for vector in user_data["vectors"]:
                    try:
                        src_path = Path(vector["path"])
                        dst_path = user_vectors_dir / vector["filename"]
                        
                        if not dst_path.exists():
                            shutil.copy2(src_path, dst_path)
                            self.migration_log.append({
                                "timestamp": datetime.now().isoformat(),
                                "user_id": user_id,
                                "action": "copy",
                                "source": str(src_path),
                                "destination": str(dst_path),
                                "status": "success"
                            })
                            logger.info(f"复制向量文件: {vector['filename']}")
                        else:
                            logger.warning(f"向量文件已存在: {vector['filename']}")
                    except Exception as e:
                        logger.error(f"复制向量文件失败 {vector['filename']}: {e}")
                        migration_success = False
            
            logger.info("用户数据迁移完成")
            return migration_success
            
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            return False
    
    def cleanup_shared_data(self, backup: bool = True) -> bool:
        """
        清理共享数据目录
        
        Args:
            backup: 是否创建备份
            
        Returns:
            bool: 清理是否成功
        """
        logger.info("开始清理共享数据目录...")
        
        try:
            if backup:
                # 创建备份目录
                backup_dir = self.base_data_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_dir.mkdir(exist_ok=True)
                
                # 备份共享数据
                for dir_name, dir_path in self.shared_dirs.items():
                    if dir_path.exists():
                        backup_target = backup_dir / dir_name
                        shutil.copytree(dir_path, backup_target)
                        logger.info(f"备份 {dir_name} 到 {backup_target}")
            
            # 清理共享数据目录
            for dir_path in self.shared_dirs.values():
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    logger.info(f"清理目录: {dir_path}")
            
            logger.info("共享数据目录清理完成")
            return True
            
        except Exception as e:
            logger.error(f"清理共享数据失败: {e}")
            return False
    
    def save_migration_report(self, output_path: str = None) -> str:
        """
        保存迁移报告
        
        Args:
            output_path: 输出路径
            
        Returns:
            str: 报告文件路径
        """
        if output_path is None:
            output_path = self.base_data_dir / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "migration_time": datetime.now().isoformat(),
            "total_operations": len(self.migration_log),
            "successful_operations": len([log for log in self.migration_log if log["status"] == "success"]),
            "failed_operations": len([log for log in self.migration_log if log["status"] != "success"]),
            "log": self.migration_log
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"迁移报告已保存到: {output_path}")
        return str(output_path)
    
    def validate_migration(self) -> Dict[str, bool]:
        """
        验证迁移结果
        
        Returns:
            Dict[str, bool]: 验证结果
        """
        logger.info("开始验证迁移结果...")
        
        validation_results = {}
        
        # 检查用户目录结构
        if self.users_dir.exists():
            for user_dir in self.users_dir.iterdir():
                if user_dir.is_dir():
                    user_id = user_dir.name
                    required_dirs = ["videos", "transcripts", "conversations", "vectors"]
                    
                    for required_dir in required_dirs:
                        dir_path = user_dir / required_dir
                        validation_results[f"{user_id}_{required_dir}"] = dir_path.exists()
        
        logger.info("迁移结果验证完成")
        return validation_results
    
    def _calculate_md5(self, file_path: Path) -> str:
        """
        计算文件MD5哈希
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: MD5哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def run_full_migration(self, cleanup_shared: bool = True, backup: bool = True) -> bool:
        """
        运行完整的数据迁移流程
        
        Args:
            cleanup_shared: 是否清理共享数据
            backup: 是否创建备份
            
        Returns:
            bool: 迁移是否成功
        """
        logger.info("开始完整数据迁移流程...")
        
        try:
            # 1. 扫描共享数据
            shared_data = self.scan_shared_data()
            
            # 2. 识别用户归属
            user_data_map = self.identify_user_ownership(shared_data)
            
            # 3. 迁移用户数据
            migration_success = self.migrate_user_data(user_data_map)
            
            if not migration_success:
                logger.error("数据迁移失败，停止流程")
                return False
            
            # 4. 验证迁移结果
            validation_results = self.validate_migration()
            if not all(validation_results.values()):
                logger.warning("迁移验证发现问题，请检查日志")
            
            # 5. 保存迁移报告
            report_path = self.save_migration_report()
            
            # 6. 清理共享数据（可选）
            if cleanup_shared:
                cleanup_success = self.cleanup_shared_data(backup=backup)
                if not cleanup_success:
                    logger.warning("共享数据清理失败")
            
            logger.info("完整数据迁移流程完成")
            return True
            
        except Exception as e:
            logger.error(f"完整迁移流程失败: {e}")
            return False


def main():
    """主函数"""
    migrator = DataMigrator()
    
    print("🚀 开始数据迁移...")
    success = migrator.run_full_migration(cleanup_shared=False, backup=True)
    
    if success:
        print("✅ 数据迁移成功完成！")
        print(f"📊 迁移报告: {migrator.save_migration_report()}")
    else:
        print("❌ 数据迁移失败，请检查日志")
    
    return success


if __name__ == "__main__":
    main()