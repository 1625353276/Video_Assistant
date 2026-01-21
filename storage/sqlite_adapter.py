#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite存储适配器

基于SQLite的存储适配器实现，适用于本地部署
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base import StorageAdapter, User, Session, Video, Conversation

logger = logging.getLogger(__name__)


class SQLiteAdapter(StorageAdapter):
    """SQLite存储适配器"""
    
    def __init__(self, db_path: str = "data/app.db"):
        """
        初始化SQLite适配器
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        logger.info(f"SQLite适配器初始化，数据库路径: {self.db_path}")
    
    def connect(self) -> bool:
        """连接到数据库"""
        try:
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row
            logger.info("SQLite数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"SQLite数据库连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开数据库连接"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info("SQLite数据库连接已断开")
            return True
        except Exception as e:
            logger.error(f"断开SQLite数据库连接失败: {e}")
            return False
    
    def initialize_schema(self) -> bool:
        """初始化数据库表结构"""
        try:
            cursor = self.connection.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT
                )
            ''')
            
            # 会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            ''')
            
            # 视频表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    language TEXT NOT NULL,
                    resolution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            ''')
            
            # 对话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    conversation_data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions (expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_video_id ON conversations (video_id)')
            
            self.connection.commit()
            logger.info("SQLite数据库表结构初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化数据库表结构失败: {e}")
            return False
    
    # 用户管理方法
    def create_user(self, user: User) -> bool:
        """创建新用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO users (
                    user_id, username, email, password_hash,
                    created_at, updated_at, is_active, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id,
                user.username,
                user.email,
                user.password_hash,
                user.created_at,
                user.updated_at,
                user.is_active,
                json.dumps(user.metadata) if user.metadata else None
            ))
            self.connection.commit()
            logger.info(f"用户创建成功: {user.username}")
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"用户创建失败，用户名或邮箱已存在: {e}")
            return False
        except Exception as e:
            logger.error(f"用户创建失败: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    is_active=bool(row['is_active']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    is_active=bool(row['is_active']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
            return None
        except Exception as e:
            logger.error(f"根据用户名获取用户失败: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    is_active=bool(row['is_active']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
            return None
        except Exception as e:
            logger.error(f"根据邮箱获取用户失败: {e}")
            return None
    
    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE users SET
                    username = ?,
                    email = ?,
                    password_hash = ?,
                    updated_at = ?,
                    is_active = ?,
                    metadata = ?
                WHERE user_id = ?
            ''', (
                user.username,
                user.email,
                user.password_hash,
                user.updated_at,
                user.is_active,
                json.dumps(user.metadata) if user.metadata else None,
                user.user_id
            ))
            self.connection.commit()
            logger.info(f"用户更新成功: {user.username}")
            return True
        except Exception as e:
            logger.error(f"用户更新失败: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            self.connection.commit()
            logger.info(f"用户删除成功: {user_id}")
            return True
        except Exception as e:
            logger.error(f"用户删除失败: {e}")
            return False
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """列出用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?', 
                          (limit, offset))
            rows = cursor.fetchall()
            
            users = []
            for row in rows:
                users.append(User(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    is_active=bool(row['is_active']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                ))
            return users
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return []
    
    # 会话管理方法
    def create_session(self, session: Session) -> bool:
        """创建新会话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO sessions (
                    session_id, user_id, session_data,
                    created_at, updated_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.user_id,
                json.dumps(session.session_data),
                session.created_at,
                session.updated_at,
                session.expires_at
            ))
            self.connection.commit()
            logger.info(f"会话创建成功: {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"会话创建失败: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
            row = cursor.fetchone()
            
            if row:
                return Session(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    session_data=json.loads(row['session_data']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None
                )
            return None
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    def update_session(self, session: Session) -> bool:
        """更新会话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE sessions SET
                    user_id = ?,
                    session_data = ?,
                    updated_at = ?,
                    expires_at = ?
                WHERE session_id = ?
            ''', (
                session.user_id,
                json.dumps(session.session_data),
                session.updated_at,
                session.expires_at,
                session.session_id
            ))
            self.connection.commit()
            logger.info(f"会话更新成功: {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"会话更新失败: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            self.connection.commit()
            logger.info(f"会话删除成功: {session_id}")
            return True
        except Exception as e:
            logger.error(f"会话删除失败: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """获取用户的所有会话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC', 
                          (user_id,))
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                sessions.append(Session(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    session_data=json.loads(row['session_data']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None
                ))
            return sessions
        except Exception as e:
            logger.error(f"获取用户会话失败: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话，返回清理数量"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM sessions WHERE expires_at < ?', 
                          (datetime.now(),))
            deleted_count = cursor.rowcount
            self.connection.commit()
            logger.info(f"清理过期会话数量: {deleted_count}")
            return deleted_count
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
    
    # 视频管理方法
    def create_video(self, video: Video) -> bool:
        """创建视频记录"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO videos (
                    video_id, user_id, filename, file_path,
                    file_size, duration, language, resolution,
                    created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video.video_id,
                video.user_id,
                video.filename,
                video.file_path,
                video.file_size,
                video.duration,
                video.language,
                video.resolution,
                video.created_at or datetime.now(),
                json.dumps(video.metadata) if video.metadata else None
            ))
            self.connection.commit()
            logger.info(f"视频记录创建成功: {video.video_id}")
            return True
        except Exception as e:
            logger.error(f"视频记录创建失败: {e}")
            return False
    
    def get_video(self, video_id: str) -> Optional[Video]:
        """获取视频"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
            row = cursor.fetchone()
            
            if row:
                return Video(
                    video_id=row['video_id'],
                    user_id=row['user_id'],
                    filename=row['filename'],
                    file_path=row['file_path'],
                    file_size=row['file_size'],
                    duration=row['duration'],
                    language=row['language'],
                    resolution=row['resolution'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
            return None
        except Exception as e:
            logger.error(f"获取视频失败: {e}")
            return None
    
    def update_video(self, video: Video) -> bool:
        """更新视频信息"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE videos SET
                    filename = ?,
                    file_path = ?,
                    file_size = ?,
                    duration = ?,
                    language = ?,
                    resolution = ?,
                    metadata = ?
                WHERE video_id = ?
            ''', (
                video.filename,
                video.file_path,
                video.file_size,
                video.duration,
                video.language,
                video.resolution,
                json.dumps(video.metadata) if video.metadata else None,
                video.video_id
            ))
            self.connection.commit()
            logger.info(f"视频更新成功: {video.video_id}")
            return True
        except Exception as e:
            logger.error(f"视频更新失败: {e}")
            return False
    
    def delete_video(self, video_id: str) -> bool:
        """删除视频"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM videos WHERE video_id = ?', (video_id,))
            self.connection.commit()
            logger.info(f"视频删除成功: {video_id}")
            return True
        except Exception as e:
            logger.error(f"视频删除失败: {e}")
            return False
    
    def get_user_videos(self, user_id: str) -> List[Video]:
        """获取用户的所有视频"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM videos WHERE user_id = ? ORDER BY created_at DESC', 
                          (user_id,))
            rows = cursor.fetchall()
            
            videos = []
            for row in rows:
                videos.append(Video(
                    video_id=row['video_id'],
                    user_id=row['user_id'],
                    filename=row['filename'],
                    file_path=row['file_path'],
                    file_size=row['file_size'],
                    duration=row['duration'],
                    language=row['language'],
                    resolution=row['resolution'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                ))
            return videos
        except Exception as e:
            logger.error(f"获取用户视频失败: {e}")
            return []
    
    # 对话管理方法
    def create_conversation(self, conversation: Conversation) -> bool:
        """创建对话记录"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO conversations (
                    conversation_id, user_id, video_id, session_id,
                    conversation_data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                conversation.conversation_id,
                conversation.user_id,
                conversation.video_id,
                conversation.session_id,
                json.dumps(conversation.conversation_data),
                conversation.created_at,
                conversation.updated_at
            ))
            self.connection.commit()
            logger.info(f"对话记录创建成功: {conversation.conversation_id}")
            return True
        except Exception as e:
            logger.error(f"对话记录创建失败: {e}")
            return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM conversations WHERE conversation_id = ?', 
                          (conversation_id,))
            row = cursor.fetchone()
            
            if row:
                return Conversation(
                    conversation_id=row['conversation_id'],
                    user_id=row['user_id'],
                    video_id=row['video_id'],
                    session_id=row['session_id'],
                    conversation_data=json.loads(row['conversation_data']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
            return None
        except Exception as e:
            logger.error(f"获取对话失败: {e}")
            return None
    
    def update_conversation(self, conversation: Conversation) -> bool:
        """更新对话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE conversations SET
                    user_id = ?,
                    video_id = ?,
                    session_id = ?,
                    conversation_data = ?,
                    updated_at = ?
                WHERE conversation_id = ?
            ''', (
                conversation.user_id,
                conversation.video_id,
                conversation.session_id,
                json.dumps(conversation.conversation_data),
                conversation.updated_at,
                conversation.conversation_id
            ))
            self.connection.commit()
            logger.info(f"对话更新成功: {conversation.conversation_id}")
            return True
        except Exception as e:
            logger.error(f"对话更新失败: {e}")
            return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM conversations WHERE conversation_id = ?', 
                          (conversation_id,))
            self.connection.commit()
            logger.info(f"对话删除成功: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"对话删除失败: {e}")
            return False
    
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """获取用户的所有对话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC', 
                          (user_id,))
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversations.append(Conversation(
                    conversation_id=row['conversation_id'],
                    user_id=row['user_id'],
                    video_id=row['video_id'],
                    session_id=row['session_id'],
                    conversation_data=json.loads(row['conversation_data']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                ))
            return conversations
        except Exception as e:
            logger.error(f"获取用户对话失败: {e}")
            return []
    
    def get_video_conversations(self, video_id: str) -> List[Conversation]:
        """获取视频的所有对话"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM conversations WHERE video_id = ? ORDER BY updated_at DESC', 
                          (video_id,))
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversations.append(Conversation(
                    conversation_id=row['conversation_id'],
                    user_id=row['user_id'],
                    video_id=row['video_id'],
                    session_id=row['session_id'],
                    conversation_data=json.loads(row['conversation_data']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                ))
            return conversations
        except Exception as e:
            logger.error(f"获取视频对话失败: {e}")
            return []
    
    # 统计方法
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            cursor = self.connection.cursor()
            
            # 获取用户基本信息
            cursor.execute('SELECT created_at FROM users WHERE user_id = ?', (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return {}
            
            # 获取视频数量
            cursor.execute('SELECT COUNT(*) as count FROM videos WHERE user_id = ?', (user_id,))
            video_count = cursor.fetchone()['count']
            
            # 获取会话数量
            cursor.execute('SELECT COUNT(*) as count FROM sessions WHERE user_id = ?', (user_id,))
            session_count = cursor.fetchone()['count']
            
            # 获取对话数量
            cursor.execute('SELECT COUNT(*) as count FROM conversations WHERE user_id = ?', (user_id,))
            conversation_count = cursor.fetchone()['count']
            
            return {
                'user_id': user_id,
                'created_at': user_row['created_at'],
                'video_count': video_count,
                'session_count': session_count,
                'conversation_count': conversation_count
            }
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            cursor = self.connection.cursor()
            
            # 获取用户数量
            cursor.execute('SELECT COUNT(*) as count FROM users')
            user_count = cursor.fetchone()['count']
            
            # 获取视频数量
            cursor.execute('SELECT COUNT(*) as count FROM videos')
            video_count = cursor.fetchone()['count']
            
            # 获取会话数量
            cursor.execute('SELECT COUNT(*) as count FROM sessions')
            session_count = cursor.fetchone()['count']
            
            # 获取对话数量
            cursor.execute('SELECT COUNT(*) as count FROM conversations')
            conversation_count = cursor.fetchone()['count']
            
            # 获取数据库大小
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                'user_count': user_count,
                'video_count': video_count,
                'session_count': session_count,
                'conversation_count': conversation_count,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {}
    
    # 数据清理方法
    def cleanup_user_data(self, user_id: str) -> bool:
        """清理用户的所有数据"""
        try:
            cursor = self.connection.cursor()
            
            # 删除对话
            cursor.execute('DELETE FROM conversations WHERE user_id = ?', (user_id,))
            
            # 删除会话
            cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
            
            # 删除视频
            cursor.execute('DELETE FROM videos WHERE user_id = ?', (user_id,))
            
            # 删除用户
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            
            self.connection.commit()
            logger.info(f"用户数据清理成功: {user_id}")
            return True
        except Exception as e:
            logger.error(f"用户数据清理失败: {e}")
            return False
    
    def backup_data(self, backup_path: str) -> bool:
        """备份数据"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"数据备份成功: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据备份失败: {e}")
            return False
    
    def restore_data(self, backup_path: str) -> bool:
        """恢复数据"""
        try:
            import shutil
            self.disconnect()  # 先断开连接
            shutil.copy2(backup_path, self.db_path)
            self.connect()  # 重新连接
            logger.info(f"数据恢复成功: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据恢复失败: {e}")
            return False