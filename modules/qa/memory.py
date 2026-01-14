#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 记忆管理模块
Memory Management Module for AI Video Assistant

实现短期对话记忆和长期知识存储，支持上下文压缩和摘要
"""

import json
import pickle
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# 导入配置
from config.settings import settings

# 导入对话轮次数据类
from modules.qa.conversation_data import ConversationTurn


@dataclass
class MemoryItem:
    """记忆项数据类"""
    item_id: str
    content: str
    item_type: str  # 'conversation', 'knowledge', 'summary'
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 1.0  # 重要性评分 0-1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'item_id': self.item_id,
            'content': self.content,
            'item_type': self.item_type,
            'timestamp': self.timestamp.isoformat(),
            'importance': self.importance,
            'tags': self.tags,
            'metadata': self.metadata,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """从字典创建实例"""
        return cls(
            item_id=data['item_id'],
            content=data['content'],
            item_type=data['item_type'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            importance=data.get('importance', 1.0),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            access_count=data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(data.get('last_accessed', datetime.now().isoformat()))
        )
    
    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class Memory:
    """记忆管理类"""
    
    def __init__(self, memory_type: str = "buffer"):
        """
        初始化记忆管理
        
        Args:
            memory_type: 记忆类型 ('buffer', 'summary', 'knowledge_graph')
        """
        self.logger = logging.getLogger(__name__)
        
        # 记忆配置
        self.memory_type = memory_type
        self.buffer_size = settings.get_model_config('qa_system', 'buffer_size', 1000)
        self.enable_persistence = settings.get_model_config('qa_system', 'enable_persistence', True)
        self.storage_path = settings.MEMORY_DIR
        
        # 记忆存储
        self.memory_items: List[MemoryItem] = []
        self.conversation_buffer: List[ConversationTurn] = []
        
        # 索引
        self.item_index: Dict[str, MemoryItem] = {}
        self.tag_index: Dict[str, List[str]] = {}
        
        # 统计信息
        self.total_items = 0
        self.total_conversations = 0
        
        # 初始化存储
        self._init_storage()
        
        self.logger.info(f"记忆管理初始化完成，类型: {memory_type}")
    
    def _init_storage(self):
        """初始化存储"""
        if self.enable_persistence:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # 尝试加载已有记忆
            self._load_memory()
    
    def _generate_item_id(self, content: str) -> str:
        """生成记忆项ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.memory_type}_{timestamp}_{content_hash}"
    
    def _calculate_importance(self, item: MemoryItem) -> float:
        """计算记忆项重要性"""
        # 基础重要性
        base_importance = 0.5
        
        # 根据类型调整
        if item.item_type == 'conversation':
            base_importance += 0.2
        elif item.item_type == 'knowledge':
            base_importance += 0.3
        elif item.item_type == 'summary':
            base_importance += 0.4
        
        # 根据访问频率调整
        access_bonus = min(item.access_count * 0.1, 0.3)
        
        # 根据时间衰减
        days_old = (datetime.now() - item.timestamp).days
        time_decay = max(0, 1 - days_old * 0.05)
        
        # 计算最终重要性
        final_importance = base_importance + access_bonus
        final_importance *= time_decay
        
        return min(max(final_importance, 0.0), 1.0)
    
    def _update_indexes(self, item: MemoryItem):
        """更新索引"""
        self.item_index[item.item_id] = item
        
        # 更新标签索引
        for tag in item.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            if item.item_id not in self.tag_index[tag]:
                self.tag_index[tag].append(item.item_id)
    
    def _remove_from_indexes(self, item: MemoryItem):
        """从索引中移除"""
        if item.item_id in self.item_index:
            del self.item_index[item.item_id]
        
        # 从标签索引中移除
        for tag in item.tags:
            if tag in self.tag_index and item.item_id in self.tag_index[tag]:
                self.tag_index[tag].remove(item.item_id)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
    
    def _cleanup_memory(self):
        """清理记忆，保持缓冲区大小"""
        if len(self.memory_items) <= self.buffer_size:
            return
        
        # 按重要性排序，移除重要性最低的项目
        sorted_items = sorted(self.memory_items, key=lambda x: x.importance)
        items_to_remove = sorted_items[:len(self.memory_items) - self.buffer_size]
        
        for item in items_to_remove:
            self._remove_from_indexes(item)
            self.memory_items.remove(item)
        
        self.logger.info(f"清理了 {len(items_to_remove)} 个记忆项")
    
    def _save_memory(self):
        """保存记忆到文件"""
        if not self.enable_persistence:
            return
        
        try:
            memory_data = {
                'memory_type': self.memory_type,
                'memory_items': [item.to_dict() for item in self.memory_items],
                'conversation_buffer': [turn.to_dict() for turn in self.conversation_buffer],
                'total_items': self.total_items,
                'total_conversations': self.total_conversations,
                'last_updated': datetime.now().isoformat()
            }
            
            file_path = self.storage_path / f"memory_{self.memory_type}.pkl"
            with open(file_path, 'wb') as f:
                pickle.dump(memory_data, f)
            
            self.logger.debug(f"记忆已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存记忆失败: {e}")
    
    def _load_memory(self):
        """从文件加载记忆"""
        if not self.enable_persistence:
            return
        
        try:
            file_path = self.storage_path / f"memory_{self.memory_type}.pkl"
            if not file_path.exists():
                return
            
            with open(file_path, 'rb') as f:
                memory_data = pickle.load(f)
            
            # 恢复记忆项
            self.memory_items = [
                MemoryItem.from_dict(item_data) 
                for item_data in memory_data.get('memory_items', [])
            ]
            
            # 恢复对话缓冲区
            self.conversation_buffer = [
                ConversationTurn.from_dict(turn_data)
                for turn_data in memory_data.get('conversation_buffer', [])
            ]
            
            # 恢复统计信息
            self.total_items = memory_data.get('total_items', 0)
            self.total_conversations = memory_data.get('total_conversations', 0)
            
            # 重建索引
            for item in self.memory_items:
                self._update_indexes(item)
            
            self.logger.info(f"从 {file_path} 加载了 {len(self.memory_items)} 个记忆项")
            
        except Exception as e:
            self.logger.error(f"加载记忆失败: {e}")
    
    def add_conversation_turn(self, turn: ConversationTurn):
        """添加对话轮次"""
        self.conversation_buffer.append(turn)
        self.total_conversations += 1
        
        # 限制缓冲区大小
        if len(self.conversation_buffer) > self.buffer_size:
            self.conversation_buffer = self.conversation_buffer[-self.buffer_size:]
        
        # 自动保存
        if self.enable_persistence:
            self._save_memory()
    
    def add_turn(self, turn: ConversationTurn):
        """添加对话轮次（兼容性方法）"""
        self.add_conversation_turn(turn)
    
    def add_memory_item(self, 
                       content: str, 
                       item_type: str = 'knowledge',
                       tags: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, Any]] = None,
                       importance: Optional[float] = None) -> str:
        """
        添加记忆项
        
        Args:
            content: 记忆内容
            item_type: 记忆类型
            tags: 标签列表
            metadata: 元数据
            importance: 重要性评分
            
        Returns:
            记忆项ID
        """
        item_id = self._generate_item_id(content)
        
        item = MemoryItem(
            item_id=item_id,
            content=content,
            item_type=item_type,
            tags=tags or [],
            metadata=metadata or {},
            importance=importance or 0.5
        )
        
        # 计算重要性
        item.importance = self._calculate_importance(item)
        
        # 添加到记忆
        self.memory_items.append(item)
        self._update_indexes(item)
        self.total_items += 1
        
        # 清理记忆
        self._cleanup_memory()
        
        # 自动保存
        if self.enable_persistence:
            self._save_memory()
        
        self.logger.debug(f"添加记忆项: {item_id}")
        return item_id
    
    def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """获取记忆项"""
        item = self.item_index.get(item_id)
        if item:
            item.update_access()
        return item
    
    def search_memory(self, 
                     query: str, 
                     item_type: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     limit: int = 10) -> List[MemoryItem]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            item_type: 记忆类型过滤
            tags: 标签过滤
            limit: 返回数量限制
            
        Returns:
            匹配的记忆项列表
        """
        results = []
        
        for item in self.memory_items:
            # 类型过滤
            if item_type and item.item_type != item_type:
                continue
            
            # 标签过滤
            if tags and not any(tag in item.tags for tag in tags):
                continue
            
            # 内容匹配
            if query.lower() in item.content.lower():
                results.append(item)
        
        # 按重要性排序
        results.sort(key=lambda x: x.importance, reverse=True)
        
        return results[:limit]
    
    def get_recent_conversations(self, limit: int = 5) -> List[ConversationTurn]:
        """获取最近的对话"""
        return self.conversation_buffer[-limit:]
    
    def get_memory_by_tags(self, tags: List[str]) -> List[MemoryItem]:
        """根据标签获取记忆"""
        item_ids = set()
        for tag in tags:
            if tag in self.tag_index:
                item_ids.update(self.tag_index[tag])
        
        return [self.item_index[item_id] for item_id in item_ids if item_id in self.item_index]
    
    def update_memory_item(self, item_id: str, **kwargs) -> bool:
        """
        更新记忆项
        
        Args:
            item_id: 记忆项ID
            **kwargs: 更新的属性
            
        Returns:
            是否更新成功
        """
        item = self.item_index.get(item_id)
        if not item:
            return False
        
        # 更新属性
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        # 重新计算重要性
        item.importance = self._calculate_importance(item)
        
        # 更新索引（如果标签发生变化）
        if 'tags' in kwargs:
            self._remove_from_indexes(item)
            self._update_indexes(item)
        
        # 自动保存
        if self.enable_persistence:
            self._save_memory()
        
        self.logger.debug(f"更新记忆项: {item_id}")
        return True
    
    def delete_memory_item(self, item_id: str) -> bool:
        """
        删除记忆项
        
        Args:
            item_id: 记忆项ID
            
        Returns:
            是否删除成功
        """
        item = self.item_index.get(item_id)
        if not item:
            return False
        
        self._remove_from_indexes(item)
        self.memory_items.remove(item)
        self.total_items -= 1
        
        # 自动保存
        if self.enable_persistence:
            self._save_memory()
        
        self.logger.debug(f"删除记忆项: {item_id}")
        return True
    
    def clear(self):
        """清空所有记忆"""
        self.memory_items.clear()
        self.conversation_buffer.clear()
        self.item_index.clear()
        self.tag_index.clear()
        self.total_items = 0
        self.total_conversations = 0
        
        # 自动保存
        if self.enable_persistence:
            self._save_memory()
        
        self.logger.info("所有记忆已清空")
    
    def get_summary(self, max_length: int = 500) -> str:
        """
        获取记忆摘要
        
        Args:
            max_length: 摘要最大长度
            
        Returns:
            记忆摘要文本
        """
        if not self.memory_items:
            return "暂无记忆内容。"
        
        # 按重要性排序
        sorted_items = sorted(self.memory_items, key=lambda x: x.importance, reverse=True)
        
        # 构建摘要
        summary_parts = []
        current_length = 0
        
        for item in sorted_items:
            item_text = f"[{item.item_type}] {item.content}"
            if current_length + len(item_text) <= max_length:
                summary_parts.append(item_text)
                current_length += len(item_text)
            else:
                break
        
        return "\n".join(summary_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        # 按类型统计
        type_stats = {}
        for item in self.memory_items:
            item_type = item.item_type
            if item_type not in type_stats:
                type_stats[item_type] = 0
            type_stats[item_type] += 1
        
        # 标签统计
        tag_stats = {}
        for tag, item_ids in self.tag_index.items():
            tag_stats[tag] = len(item_ids)
        
        return {
            'memory_type': self.memory_type,
            'total_items': len(self.memory_items),
            'total_conversations': len(self.conversation_buffer),
            'buffer_size': self.buffer_size,
            'type_distribution': type_stats,
            'tag_distribution': tag_stats,
            'oldest_item': min([item.timestamp for item in self.memory_items]).isoformat() if self.memory_items else None,
            'newest_item': max([item.timestamp for item in self.memory_items]).isoformat() if self.memory_items else None,
            'average_importance': sum([item.importance for item in self.memory_items]) / len(self.memory_items) if self.memory_items else 0,
            'persistence_enabled': self.enable_persistence,
            'storage_path': str(self.storage_path) if self.enable_persistence else None
        }
    
    def export_memory(self, file_path: str, format: str = 'json'):
        """
        导出记忆
        
        Args:
            file_path: 导出文件路径
            format: 导出格式 ('json', 'pickle')
        """
        try:
            export_data = {
                'memory_type': self.memory_type,
                'export_time': datetime.now().isoformat(),
                'memory_items': [item.to_dict() for item in self.memory_items],
                'conversation_buffer': [turn.to_dict() for turn in self.conversation_buffer],
                'stats': self.get_stats()
            }
            
            if format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif format == 'pickle':
                with open(file_path, 'wb') as f:
                    pickle.dump(export_data, f)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            self.logger.info(f"记忆已导出到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"导出记忆失败: {e}")
    
    def import_memory(self, file_path: str, format: str = 'json'):
        """
        导入记忆
        
        Args:
            file_path: 导入文件路径
            format: 导入格式 ('json', 'pickle')
        """
        try:
            if format == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
            elif format == 'pickle':
                with open(file_path, 'rb') as f:
                    import_data = pickle.load(f)
            else:
                raise ValueError(f"不支持的导入格式: {format}")
            
            # 导入记忆项
            for item_data in import_data.get('memory_items', []):
                item = MemoryItem.from_dict(item_data)
                self.memory_items.append(item)
                self._update_indexes(item)
            
            # 导入对话缓冲区
            for turn_data in import_data.get('conversation_buffer', []):
                turn = ConversationTurn.from_dict(turn_data)
                self.conversation_buffer.append(turn)
            
            # 更新统计
            self.total_items = len(self.memory_items)
            self.total_conversations = len(self.conversation_buffer)
            
            # 清理和保存
            self._cleanup_memory()
            if self.enable_persistence:
                self._save_memory()
            
            self.logger.info(f"记忆已从 {file_path} 导入")
            
        except Exception as e:
            self.logger.error(f"导入记忆失败: {e}")