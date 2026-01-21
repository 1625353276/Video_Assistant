#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 对话数据结构
Conversation Data Structures for AI Video Assistant

定义对话相关的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class ConversationTurn:
    """对话轮次数据类"""
    turn_id: int
    user_query: str
    retrieved_docs: List[Dict[str, Any]] = field(default_factory=list)
    context: str = ""
    response: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'turn_id': self.turn_id,
            'user_query': self.user_query,
            'retrieved_docs': self.retrieved_docs,
            'context': self.context,
            'response': self.response,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationTurn':
        """从字典创建实例"""
        return cls(
            turn_id=data['turn_id'],
            user_query=data['user_query'],
            retrieved_docs=data.get('retrieved_docs', []),
            context=data.get('context', ''),
            response=data.get('response', ''),
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


@dataclass
class VideoInfo:
    """视频信息数据类"""
    filename: str
    duration: float
    language: str = "zh"
    file_size: Optional[int] = None
    resolution: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'filename': self.filename,
            'duration': self.duration,
            'language': self.language,
            'file_size': self.file_size,
            'resolution': self.resolution,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoInfo':
        """从字典创建实例"""
        return cls(
            filename=data['filename'],
            duration=data['duration'],
            language=data.get('language', 'zh'),
            file_size=data.get('file_size'),
            resolution=data.get('resolution'),
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class SessionData:
    """会话数据类，包含完整的会话信息"""
    session_id: str
    video_info: VideoInfo
    transcript: List[Dict[str, Any]] = field(default_factory=list)
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'session_id': self.session_id,
            'video_info': self.video_info.to_dict(),
            'transcript': self.transcript,
            'conversation_history': [turn.to_dict() for turn in self.conversation_history],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """从字典创建实例"""
        return cls(
            session_id=data['session_id'],
            video_info=VideoInfo.from_dict(data['video_info']),
            transcript=data.get('transcript', []),
            conversation_history=[
                ConversationTurn.from_dict(turn_data) 
                for turn_data in data.get('conversation_history', [])
            ],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            metadata=data.get('metadata', {})
        )
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
    
    def add_conversation_turn(self, turn: ConversationTurn):
        """添加对话轮次"""
        self.conversation_history.append(turn)
        self.update_timestamp()
    
    def get_transcript_text(self) -> str:
        """获取转录文本内容"""
        return "\n".join([segment.get('text', '') for segment in self.transcript])
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        return {
            'session_id': self.session_id,
            'video_filename': self.video_info.filename,
            'video_duration': self.video_info.duration,
            'transcript_segments': len(self.transcript),
            'conversation_turns': len(self.conversation_history),
            'total_text_length': len(self.get_transcript_text()),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }