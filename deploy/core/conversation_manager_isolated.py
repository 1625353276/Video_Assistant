#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话管理器 - 用户隔离版本

支持用户专属的对话链管理和历史记录
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入用户上下文
from deploy.utils.user_context import get_current_user_id, get_current_user_paths, require_user_login

# 导入原有模块
try:
    from modules.qa.conversation_chain import ConversationChain
    from modules.retrieval.vector_store import VectorStore
    from modules.retrieval.bm25_retriever import BM25Retriever
    from modules.retrieval.hybrid_retriever import HybridRetriever
    print("✓ 对话相关模块导入成功")
except ImportError as e:
    print(f"⚠ 对话模块导入失败: {e}")


class IsolatedConversationManager:
    """用户隔离的对话管理器"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.conversation_chains = {}  # {user_id: {video_id: ConversationChain}}
        self._current_user_id = None
    
    def _clear_user_data(self, user_id: str):
        """清除指定用户的所有数据"""
        if user_id in self.conversation_chains:
            del self.conversation_chains[user_id]
            print(f"✅ 已清除用户 {user_id} 的对话管理器数据")
    
    def _ensure_user_context(self):
        """确保用户上下文一致性"""
        current_user_id = get_current_user_id()
        if current_user_id != self._current_user_id:
            # 用户已切换，清理旧用户数据
            if self._current_user_id and self._current_user_id in self.conversation_chains:
                self._clear_user_data(self._current_user_id)
            self._current_user_id = current_user_id
            print(f"✅ 用户上下文已切换到: {current_user_id}")
    
    @require_user_login
    
    @require_user_login
    def create_conversation_chain(self, video_id: str, load_history: bool = True):
        """为用户创建对话链
        
        Args:
            video_id: 视频ID
            load_history: 是否加载历史对话
        """
        # 确保用户上下文一致性
        self._ensure_user_context()
        
        user_id = get_current_user_id()
        if not user_id:
            raise ValueError("用户未登录")
        
        # 确保用户字典存在
        if user_id not in self.conversation_chains:
            self.conversation_chains[user_id] = {}
        
        # 检查是否已存在对话链
        if video_id in self.conversation_chains[user_id]:
            return self.conversation_chains[user_id][video_id]
        
        # 创建新的对话链
        conversation_chain = self._create_conversation_chain_internal(video_id, load_history)
        self.conversation_chains[user_id][video_id] = conversation_chain
        
        return conversation_chain
    
    def _create_conversation_chain_internal(self, video_id: str, load_history: bool = True):
        """内部创建对话链的方法"""
        user_paths = get_current_user_paths()
        if not user_paths:
            raise ValueError("用户路径获取失败")
        
        # 检查索引文件是否存在
        vector_index_path = user_paths.get_vector_index_path(video_id)
        bm25_index_path = user_paths.get_bm25_index_path(video_id)
        
        if not vector_index_path.exists() or not bm25_index_path.exists():
            print(f"索引文件不存在，创建无检索器的对话链")
            # 创建无检索器的对话链
            conversation_chain = ConversationChain()
            
            # 加载对话历史
            if load_history:
                self._load_conversation_history(conversation_chain, video_id)
            
            return conversation_chain
        
        try:
            # 创建用户隔离的检索器
            try:
                from modules.retrieval.isolated_vector_store import get_isolated_vector_store
                from modules.retrieval.isolated_bm25_retriever import get_isolated_bm25_retriever
                from modules.retrieval.isolated_hybrid_retriever import get_isolated_hybrid_retriever
                
                vector_store = get_isolated_vector_store()
                vector_store.load_index(vector_index_path)
                
                bm25_retriever = get_isolated_bm25_retriever()
                bm25_retriever.load_index(bm25_index_path)
                
                hybrid_retriever = get_isolated_hybrid_retriever(
                    vector_store=vector_store,
                    bm25_retriever=bm25_retriever
                )
                print("✓ 使用用户隔离的检索器")
            except ImportError:
                # 回退到原有检索器
                vector_store = VectorStore()
                vector_store.load_index(vector_index_path)
                
                bm25_retriever = BM25Retriever()
                bm25_retriever.load_index(bm25_index_path)
                
                hybrid_retriever = HybridRetriever(
                    vector_store=vector_store,
                    bm25_retriever=bm25_retriever
                )
                print("⚠ 回退到原有检索器")
            
            # 创建带检索器的对话链
            conversation_chain = ConversationChain(retriever=hybrid_retriever)
            
            # 加载对话历史
            if load_history:
                self._load_conversation_history(conversation_chain, video_id)
            
            # 设置转录内容
            transcript_file = user_paths.get_transcript_path(video_id)
            if transcript_file.exists():
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)
                    if 'segments' in transcript_data:
                        conversation_chain.set_full_transcript(transcript_data['segments'])
                        print(f"已为视频 {video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
            
            return conversation_chain
            
        except Exception as e:
            print(f"创建对话链失败，使用基本对话链: {e}")
            conversation_chain = ConversationChain()
            
            # 尝试加载对话历史
            if load_history:
                self._load_conversation_history(conversation_chain, video_id)
            
            return conversation_chain
    
    def _load_conversation_history(self, conversation_chain, video_id: str):
        """加载对话历史"""
        user_paths = get_current_user_paths()
        if not user_paths:
            return
        
        conversation_history_path = user_paths.get_conversation_path(video_id)
        
        if conversation_history_path.exists():
            conversation_chain.load_conversation(str(conversation_history_path))
            user_id = get_current_user_id()
            print(f"已加载用户 {user_id} 视频 {video_id} 的对话历史")
    
    @require_user_login
    def save_conversation_history(self, video_id: str):
        """保存对话历史"""
        user_id = get_current_user_id()
        if not user_id:
            return
        
        if user_id not in self.conversation_chains or video_id not in self.conversation_chains[user_id]:
            return
        
        conversation_chain = self.conversation_chains[user_id][video_id]
        user_paths = get_current_user_paths()
        if not user_paths:
            return
        
        conversation_history_path = user_paths.get_conversation_path(video_id)
        conversation_chain.save_conversation(str(conversation_history_path))
        print(f"已保存用户 {user_id} 视频 {video_id} 的对话历史")
    
    @require_user_login
    def get_conversation_chain(self, video_id: str):
        """获取对话链"""
        user_id = get_current_user_id()
        if not user_id:
            return None
        
        if user_id not in self.conversation_chains:
            return None
        
        return self.conversation_chains[user_id].get(video_id)
    
    @require_user_login
    def clear_conversation(self, video_id: str):
        """清除指定视频的对话历史"""
        user_id = get_current_user_id()
        if not user_id:
            return False
        
        if user_id in self.conversation_chains and video_id in self.conversation_chains[user_id]:
            # 移除对话链实例
            del self.conversation_chains[user_id][video_id]
            
            # 删除保存的对话历史文件
            user_paths = get_current_user_paths()
            if user_paths:
                conversation_history_path = user_paths.get_conversation_path(video_id)
                if conversation_history_path.exists():
                    conversation_history_path.unlink()
                    print(f"已删除用户 {user_id} 视频 {video_id} 的对话历史文件")
            
            print(f"已清除用户 {user_id} 视频 {video_id} 的对话链实例")
            return True
        
        return False
    
    @require_user_login
    def get_user_conversation_list(self):
        """获取用户的对话列表"""
        # 确保用户上下文一致性
        self._ensure_user_context()
        
        user_id = get_current_user_id()
        if not user_id:
            return []
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return []
        
        conversations_dir = user_paths.get_user_conversations_dir()
        if not conversations_dir.exists():
            return []
        
        conversations = []
        for conversation_file in conversations_dir.iterdir():
            if conversation_file.is_file() and conversation_file.suffix == '.json':
                try:
                    with open(conversation_file, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)
                    
                    # 提取video_id
                    filename = conversation_file.stem
                    video_id = filename.replace('_conversation_history', '')
                    
                    # 获取基本信息
                    history = conversation_data.get('history', [])
                    created_at = conversation_data.get('created_at', '')
                    
                    # 计算对话轮数
                    user_message_count = sum(1 for turn in history if turn.get('role') == 'user')
                    
                    # 格式化时间
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            created_at = created_at[:10]
                    
                    conversations.append({
                        'video_id': video_id,
                        'user_id': user_id,
                        'created_at': created_at,
                        'message_count': user_message_count,
                        'has_index': self._check_user_index_exists(video_id)
                    })
                except Exception as e:
                    print(f"读取对话文件 {conversation_file.name} 失败: {e}")
                    continue
        
        # 按创建时间排序（最新的在前）
        conversations.sort(key=lambda x: x['created_at'], reverse=True)
        return conversations
    
    def _check_user_index_exists(self, video_id: str):
        """检查用户索引文件是否存在"""
        user_paths = get_current_user_paths()
        if not user_paths:
            return False
        
        vector_index_path = user_paths.get_vector_index_path(video_id)
        bm25_index_path = user_paths.get_bm25_index_path(video_id)
        
        return vector_index_path.exists() and bm25_index_path.exists()
    
    @require_user_login
    def chat_with_video(self, video_id: str, question: str, chat_history: List[Dict], temperature: float = 0.7):
        """基于视频内容进行问答"""
        # 确保用户上下文一致性
        self._ensure_user_context()
        
        user_id = get_current_user_id()
        if not user_id:
            return "用户未登录", chat_history
        
        # 获取或创建对话链
        conversation_chain = self.get_conversation_chain(video_id)
        if not conversation_chain:
            conversation_chain = self.create_conversation_chain(video_id)
        
        if conversation_chain is None:
            return "对话链初始化失败，请重启应用或联系管理员", chat_history
        
        try:
            # 调用对话链
            result = conversation_chain.chat(question)
            
            # 检查是否有检索结果
            retrieved_docs = result.get('retrieved_docs', [])
            
            # 确保检索文档格式一致
            for doc in retrieved_docs:
                if 'document' in doc and 'text' not in doc:
                    document = doc['document']
                    for key in ['text', 'start', 'end', 'confidence']:
                        if key in document:
                            doc[key] = document[key]
            
            response = result['response']
            
            # 确保历史记录格式正确
            if not isinstance(chat_history, list):
                chat_history = []
            
            # 添加新消息到历史记录
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": response})
            
            # 保存对话历史
            self.save_conversation_history(video_id)
            
            return response, chat_history
        except Exception as e:
            return f"问答失败: {str(e)}", chat_history
    
    @require_user_login
    def load_conversation_without_video(self, video_id: str):
        """无需视频文件加载对话历史和索引"""
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "用户未登录"}
        
        user_paths = get_current_user_paths()
        if not user_paths:
            return {"error": "用户路径获取失败"}
        
        # 检查对话历史是否存在
        conversation_history_path = user_paths.get_conversation_path(video_id)
        if not conversation_history_path.exists():
            return {"error": "对话历史不存在"}
        
        # 检查索引文件是否存在
        vector_index_path = user_paths.get_vector_index_path(video_id)
        bm25_index_path = user_paths.get_bm25_index_path(video_id)
        
        if not vector_index_path.exists() or not bm25_index_path.exists():
            # 创建基本对话链
            conversation_chain = ConversationChain()
            self._load_conversation_history(conversation_chain, video_id)
            
            # 添加到管理器
            if user_id not in self.conversation_chains:
                self.conversation_chains[user_id] = {}
            self.conversation_chains[user_id][video_id] = conversation_chain
            
            return {
                "success": True,
                "message": f"成功加载对话历史（无索引）",
                "user_id": user_id
            }
        
        # 创建完整的对话链
        try:
            conversation_chain = self._create_conversation_chain_internal(video_id, load_history=True)
            
            # 添加到管理器
            if user_id not in self.conversation_chains:
                self.conversation_chains[user_id] = {}
            self.conversation_chains[user_id][video_id] = conversation_chain
            
            return {
                "success": True,
                "message": f"成功加载对话历史和索引",
                "user_id": user_id
            }
        except Exception as e:
            return {"error": f"加载对话失败: {str(e)}"}
    
    @require_user_login
    def delete_conversation_history(self, video_id: str):
        """删除对话历史"""
        user_id = get_current_user_id()
        if not user_id:
            return "用户未登录"
        
        # 清除对话链
        if self.clear_conversation(video_id):
            return f"已删除对话: {video_id}"
        else:
            return f"对话不存在: {video_id}"


# 全局对话管理器实例
conversation_manager = IsolatedConversationManager()


def get_conversation_manager():
    """获取对话管理器实例"""
    return conversation_manager