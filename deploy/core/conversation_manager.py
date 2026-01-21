#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话链管理
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 尝试导入对话链相关模块
try:
    from modules.qa.conversation_chain import ConversationChain
    print("✓ ConversationChain 导入成功")
except ImportError as e:
    print(f"✗ ConversationChain 导入失败: {e}")
    ConversationChain = None


class ConversationManager:
    """对话链管理器"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.conversation_chains = {}
        self._init_retrievers()
    
    def _init_retrievers(self):
        """初始化检索器"""
        try:
            from modules.retrieval.vector_store import VectorStore
            from modules.retrieval.bm25_retriever import BM25Retriever
            from modules.retrieval.hybrid_retriever import HybridRetriever
            from modules.text.translator import TextTranslator
            
            self.vector_store = VectorStore(mirror_site="tuna")
            self.bm25_retriever = BM25Retriever(language='auto')
            self.hybrid_retriever = HybridRetriever(
                vector_store=self.vector_store,
                bm25_retriever=self.bm25_retriever,
                vector_weight=0.6,
                bm25_weight=0.4,
                fusion_method="weighted_average"
            )
            self.translator = TextTranslator(
                default_method="deep-translator",
                progress_callback=self._on_translation_progress
            )
            self.mock_mode = False
            print("✓ 检索器和翻译器初始化成功")
            
        except ImportError as e:
            print(f"⚠ 检索器或翻译器导入失败，使用模拟模式: {e}")
            self.mock_mode = True
            self.vector_store = None
            self.bm25_retriever = None
            self.hybrid_retriever = None
            self.translator = None
    
    def _on_translation_progress(self, current: int, total: int, message: str):
        """翻译进度回调函数"""
        # 这里需要获取当前正在翻译的视频ID
        if hasattr(self, '_current_translating_video_id'):
            video_id = self._current_translating_video_id
            update_translation_progress(video_id, current, total, message)
    
    def create_conversation_chain(self, video_id, load_history=True):
        """为视频创建对话链
        
        Args:
            video_id: 视频ID
            load_history: 是否加载历史对话，False表示创建全新对话
        """
        if not self.mock_mode and ConversationChain:
            try:
                # 检查索引文件是否存在
                vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
                bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
                
                if not os.path.exists(vector_index_path) or not os.path.exists(bm25_index_path):
                    print(f"索引文件不存在，创建无检索器的对话链")
                    # 创建无检索器的对话链，仍然可以进行基本对话
                    conversation_chain = ConversationChain()
                    
                    # 根据参数决定是否加载对话历史
                    if load_history:
                        self._load_conversation_history(conversation_chain, video_id)
                    
                    return conversation_chain
                
                # 创建检索器
                vector_store = VectorStore()
                vector_store.load_index(vector_index_path)
                
                bm25_retriever = BM25Retriever()
                bm25_retriever.load_index(bm25_index_path)
                
                hybrid_retriever = HybridRetriever(
                    vector_store=vector_store,
                    bm25_retriever=bm25_retriever
                )
                
                # 创建带检索器的对话链
                conversation_chain = ConversationChain(retriever=hybrid_retriever)
                
                # 根据参数决定是否加载对话历史
                if load_history:
                    self._load_conversation_history(conversation_chain, video_id)
                
                # 设置转录内容
                transcript_file = f"data/transcripts/{video_id}_transcript.json"
                if os.path.exists(transcript_file):
                    import json
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                        if 'segments' in transcript_data:
                            conversation_chain.set_full_transcript(transcript_data['segments'])
                            print(f"已为视频 {video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
                
                return conversation_chain
            except Exception as e:
                print(f"创建对话链失败，使用基本对话链: {e}")
                conversation_chain = ConversationChain()
                
                # 根据参数决定是否加载对话历史
                if load_history:
                    self._load_conversation_history(conversation_chain, video_id)
                
                return conversation_chain
        else:
            # Mock模式或ConversationChain不可用
            if ConversationChain:
                return ConversationChain()
            else:
                return None
    
    def create_new_conversation_chain(self, video_id):
        """创建全新的对话链（不加载历史）
        
        Args:
            video_id: 视频ID
            
        Returns:
            全新的对话链实例
        """
        if not self.mock_mode and ConversationChain:
            try:
                # 生成新的会话ID
                new_session_id = self._generate_session_id()
                
                # 检查索引文件是否存在
                vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
                bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
                
                if not os.path.exists(vector_index_path) or not os.path.exists(bm25_index_path):
                    print(f"索引文件不存在，创建无检索器的对话链")
                    # 创建无检索器的对话链，传入新的会话ID
                    conversation_chain = ConversationChain(session_id=new_session_id)
                    
                    # 设置转录内容
                    transcript_file = f"data/transcripts/{video_id}_transcript.json"
                    if os.path.exists(transcript_file):
                        import json
                        with open(transcript_file, 'r', encoding='utf-8') as f:
                            transcript_data = json.load(f)
                            if 'segments' in transcript_data:
                                conversation_chain.set_full_transcript(transcript_data['segments'])
                                print(f"已为视频 {video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
                    
                    print(f"已创建全新对话链，会话ID: {new_session_id}")
                    return conversation_chain
                
                # 创建检索器
                vector_store = VectorStore()
                vector_store.load_index(vector_index_path)
                
                bm25_retriever = BM25Retriever()
                bm25_retriever.load_index(bm25_index_path)
                
                hybrid_retriever = HybridRetriever(
                    vector_store=vector_store,
                    bm25_retriever=bm25_retriever
                )
                
                # 创建带检索器的对话链，传入新的会话ID
                conversation_chain = ConversationChain(retriever=hybrid_retriever, session_id=new_session_id)
                
                # 设置转录内容
                transcript_file = f"data/transcripts/{video_id}_transcript.json"
                if os.path.exists(transcript_file):
                    import json
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                        if 'segments' in transcript_data:
                            conversation_chain.set_full_transcript(transcript_data['segments'])
                            print(f"已为视频 {video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
                
                print(f"已创建全新对话链，会话ID: {new_session_id}")
                return conversation_chain
                
            except Exception as e:
                print(f"创建对话链失败，使用基本对话链: {e}")
                new_session_id = self._generate_session_id()
                return ConversationChain(session_id=new_session_id)
        
        # Mock模式下的处理
        if ConversationChain:
            new_session_id = self._generate_session_id()
            return ConversationChain(session_id=new_session_id)
        else:
            return None
    
    def _generate_session_id(self):
        """生成会话ID"""
        import random
        now = time.time()
        timestamp = int(now * 1000)  # 毫秒时间戳
        random_suffix = random.randint(1000, 9999)
        return f"session_{timestamp}_{random_suffix}"
    
    def _load_conversation_history(self, conversation_chain, video_id):
        """加载对话历史"""
        try:
            conversation_history_path = f"data/memory/{video_id}_conversation_history.json"
            
            if os.path.exists(conversation_history_path):
                conversation_chain.load_conversation(conversation_history_path)
                print(f"已加载视频 {video_id} 的对话历史")
            else:
                print(f"视频 {video_id} 暂无对话历史")
        except Exception as e:
            print(f"加载对话历史失败: {e}")
    
    def _save_conversation_history(self, conversation_chain, video_id):
        """保存对话历史"""
        try:
            # 确保目录存在
            os.makedirs("data/memory", exist_ok=True)
            
            conversation_history_path = f"data/memory/{video_id}_conversation_history.json"
            conversation_chain.save_conversation(conversation_history_path)
            print(f"已保存视频 {video_id} 的对话历史")
        except Exception as e:
            print(f"保存对话历史失败: {e}")
    
    def _save_gradio_conversation_history(self, new_messages, video_id):
        """直接保存Gradio界面的对话历史到文件"""
        try:
            # 确保目录存在
            os.makedirs("data/memory", exist_ok=True)
            
            conversation_history_path = f"data/memory/{video_id}_conversation_history.json"
            
            # 检查文件是否已存在
            if os.path.exists(conversation_history_path):
                # 如果文件存在，读取现有内容并合并
                try:
                    with open(conversation_history_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = {
                        'session_id': video_id,
                        'created_at': datetime.now().isoformat(),
                        'history': [],
                        'config': {}
                    }
            else:
                # 如果文件不存在，创建新的数据结构
                existing_data = {
                    'session_id': video_id,
                    'created_at': datetime.now().isoformat(),
                    'history': [],
                    'config': {}
                }
            
            # 合并新的对话历史
            existing_data['history'].extend(new_messages)
            
            # 保存到文件
            with open(conversation_history_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print(f"已保存视频 {video_id} 的Gradio对话历史")
        except Exception as e:
            print(f"保存Gradio对话历史失败: {e}")
    
    def clear_conversation(self, video_id):
        """清空指定视频的对话历史，创建全新的对话链实例"""
        try:
            if video_id in self.conversation_chains:
                # 完全移除旧的对话链实例
                del self.conversation_chains[video_id]
                
                # 删除保存的对话历史文件
                conversation_history_path = f"data/memory/{video_id}_conversation_history.json"
                if os.path.exists(conversation_history_path):
                    os.remove(conversation_history_path)
                    print(f"已删除视频 {video_id} 的对话历史文件")
                
                print(f"已清除视频 {video_id} 的对话链实例，下次使用将创建新实例")
                return True
        except Exception as e:
            print(f"清空对话历史失败: {e}")
        return False
    
    def load_conversation_without_video(self, video_id):
        """无需视频文件加载对话历史和索引"""
        print(f"开始加载对话，video_id={video_id}")
        try:
            # 检查对话历史是否存在
            conversation_history_path = f"data/memory/{video_id}_conversation_history.json"
            print(f"检查对话历史文件: {conversation_history_path}")
            if not os.path.exists(conversation_history_path):
                print("对话历史文件不存在")
                return {"error": "对话历史不存在"}
            
            # 检查索引文件是否存在
            vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
            bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
            
            if not os.path.exists(vector_index_path) or not os.path.exists(bm25_index_path):
                print(f"索引文件检查: vector_index={os.path.exists(vector_index_path)}, bm25_index={os.path.exists(bm25_index_path)}")
                print("索引文件不存在，创建基本对话链")
                
                # 获取视频信息
                video_name = f"视频 {video_id}"
                from .video_processor import get_video_data
                video_data = get_video_data()
                if video_id in video_data:
                    video_name = video_data[video_id].get('filename', video_name)
                
                try:
                    # 检查ConversationChain是否可用
                    if ConversationChain is None:
                        return {"error": "ConversationChain模块未导入，无法创建对话链"}
                    
                    # 创建基本对话链（无检索功能）
                    conversation_chain = ConversationChain()
                    self._load_conversation_history(conversation_chain, video_id)
                    self.conversation_chains[video_id] = conversation_chain
                    
                    print(f"成功创建基本对话链: {video_id}")
                    return {
                        "success": True,
                        "message": f"成功加载对话历史（无索引）",
                        "video_name": video_name
                    }
                except Exception as e2:
                    print(f"创建基本对话链失败: {e2}")
                    import traceback
                    print(traceback.format_exc())
                    return {"error": f"创建基本对话链失败: {str(e2)}"}
            
            # 创建对话链
            conversation_chain = self._create_conversation_chain_from_index(video_id)
            if conversation_chain:
                self.conversation_chains[video_id] = conversation_chain
                
                # 获取视频名称
                video_name = f"视频 {video_id}"
                from .video_processor import get_video_data
                video_data = get_video_data()
                if video_id in video_data:
                    video_name = video_data[video_id].get('filename', video_name)
                
                return {
                    "success": True,
                    "message": f"成功加载对话历史和索引",
                    "video_name": video_name
                }
            else:
                return {"error": "创建对话链失败"}
        except Exception as e:
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return {"error": f"加载对话失败: {str(e)}"}
    
    def _create_conversation_chain_from_index(self, video_id):
        """从索引文件创建对话链（无需原始视频）"""
        try:
            # 检查索引文件是否存在
            vector_index_path = f"data/vectors/{video_id}_vector_index.pkl"
            bm25_index_path = f"data/vectors/{video_id}_bm25_index.pkl"
            
            print(f"检查索引文件: {vector_index_path}, {bm25_index_path}")
            print(f"索引文件存在: vector={os.path.exists(vector_index_path)}, bm25={os.path.exists(bm25_index_path)}")
            
            if not os.path.exists(vector_index_path) or not os.path.exists(bm25_index_path):
                print(f"索引文件不存在，创建基本对话链")
                try:
                    conversation_chain = ConversationChain()
                    self._load_conversation_history(conversation_chain, video_id)
                    print(f"成功创建基本对话链: {video_id}")
                    return conversation_chain
                except Exception as e2:
                    print(f"创建基本对话链失败: {e2}")
                    import traceback
                    print(traceback.format_exc())
                    return None
            
            # 创建检索器
            print("创建向量存储...")
            from modules.retrieval.vector_store import VectorStore
            vector_store = VectorStore()
            vector_store.load_index(vector_index_path)
            
            print("创建BM25检索器...")
            from modules.retrieval.bm25_retriever import BM25Retriever
            bm25_retriever = BM25Retriever()
            bm25_retriever.load_index(bm25_index_path)
            
            print("创建混合检索器...")
            from modules.retrieval.hybrid_retriever import HybridRetriever
            hybrid_retriever = HybridRetriever(
                vector_store=vector_store,
                bm25_retriever=bm25_retriever
            )
            
            # 创建对话链
            print("创建对话链...")
            conversation_chain = ConversationChain(retriever=hybrid_retriever)
            
            # 加载对话历史
            print("加载对话历史...")
            self._load_conversation_history(conversation_chain, video_id)
            
            # 尝试加载转录内容（如果存在）
            transcript_file = f"data/transcripts/{video_id}_transcript.json"
            if os.path.exists(transcript_file):
                import json
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)
                    if 'segments' in transcript_data:
                        conversation_chain.set_full_transcript(transcript_data['segments'])
                        print(f"已为视频 {video_id} 设置转录内容，共 {len(transcript_data['segments'])} 个片段")
            
            print(f"成功从索引创建对话链: {video_id}")
            return conversation_chain
        except Exception as e:
            print(f"从索引创建对话链失败: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def chat_with_video(self, video_id, question, chat_history, temperature=0.7):
        """
        基于视频内容进行问答
        """
        from .video_processor import get_video_data
        video_data = get_video_data()
        
        if video_id not in video_data:
            return "视频不存在", chat_history
        
        video_info = video_data[video_id]
        
        if not video_info.get("transcript"):
            return "视频尚未处理完成，无法进行问答", chat_history
        
        # 获取或创建对话链
        if video_id not in self.conversation_chains:
            self.conversation_chains[video_id] = self.create_conversation_chain(video_id)
        
        conversation_chain = self.conversation_chains[video_id]
        
        if conversation_chain is None:
            return "对话链初始化失败，请重启应用或联系管理员", chat_history
        
        try:
            # 调用对话链
            result = conversation_chain.chat(question)
            
            # 检查是否有检索结果
            retrieved_docs = result.get('retrieved_docs', [])
            retrieved_count = len(retrieved_docs)
            
            # 确保检索文档格式一致（提取字段到顶层）
            for doc in retrieved_docs:
                if 'document' in doc and 'text' not in doc:
                    # 如果有document对象但没有顶层字段，提取常用字段
                    document = doc['document']
                    for key in ['text', 'start', 'end', 'confidence']:
                        if key in document:
                            doc[key] = document[key]
            
            if retrieved_count == 0:
                # 如果没有检索结果，可能是索引未构建
                response = result['response']
                if "未找到相关内容" not in response:
                    # 添加提示信息
                    response = f"{response}\n\n💡 提示：如需基于视频内容的精准回答，请先在'内容搜索'中点击'构建检索索引'按钮。"
            else:
                response = result['response']
            
            # 确保历史记录格式正确
            if not isinstance(chat_history, list):
                chat_history = []
            
            # 检查chat_history的格式，如果是元组格式则转换为字典格式
            if chat_history and isinstance(chat_history[0], tuple):
                # 转换为字典格式
                formatted_history = []
                for user_msg, assistant_msg in chat_history:
                    formatted_history.append({"role": "user", "content": user_msg})
                    formatted_history.append({"role": "assistant", "content": assistant_msg})
                chat_history = formatted_history
            
            # 添加新消息到历史记录
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": response})
            
            # 保存对话历史
            new_messages = [
                {"role": "user", "content": question},
                {"role": "assistant", "content": response}
            ]
            self._save_gradio_conversation_history(new_messages, video_id)
            
            return response, chat_history
        except Exception as e:
            return f"问答失败: {str(e)}", chat_history
    
    def get_conversation_history(self, video_id):
        """获取对话历史"""
        if video_id in self.conversation_chains:
            return self.conversation_chains[video_id].get_conversation_history()
        return []
    
    def get_conversation_stats(self, video_id):
        """获取对话统计信息"""
        if video_id in self.conversation_chains:
            return self.conversation_chains[video_id].get_stats()
        return {}


# 全局对话管理器实例
conversation_manager = ConversationManager()


def get_conversation_manager():
    """获取对话管理器实例"""
    return conversation_manager


# 翻译进度回调函数
def update_translation_progress(video_id, current, total, message):
    """更新翻译进度"""
    from .video_processor import get_video_data
    video_data = get_video_data()
    
    if video_id not in video_data:
        return
    
    # 计算进度百分比
    if total > 0:
        progress = min(current / total, 1.0)
    else:
        progress = 0.0
    
    # 更新视频数据中的翻译进度
    video_data[video_id]["translation_progress"] = {
        "current": current,
        "total": total,
        "progress": progress,
        "message": message,
        "timestamp": time.time()
    }