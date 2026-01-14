#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 对话数据结构
Conversation Data Structures for AI Video Assistant

定义对话相关的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any


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