#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 对话链模块
Conversation Chain Module for AI Video Assistant

实现对话链管理，集成检索系统和LLM，处理多轮对话逻辑
"""

import json
import logging
import threading
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# 导入配置
from config.settings import settings

# 导入检索模块
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.hybrid_retriever import HybridRetriever
from modules.retrieval.multi_query import MultiQueryGenerator

# 导入对话数据结构
from modules.qa.conversation_data import ConversationTurn, SessionData, VideoInfo

# 导入记忆和提示模块
from modules.qa.memory import Memory
from modules.qa.prompt import PromptTemplate


class ConversationChain:
    """对话链管理类"""
    
    def __init__(self, 
                 retriever: Optional[Union[VectorStore, BM25Retriever, HybridRetriever]] = None,
                 memory: Optional[Memory] = None,
                 prompt_template: Optional[PromptTemplate] = None,
                 llm_config: Optional[Dict[str, Any]] = None,
                 session_id: Optional[str] = None,
                 user_id: Optional[str] = None):
        """
        初始化对话链
        
        Args:
            retriever: 检索器实例
            memory: 记忆管理实例
            prompt_template: 提示模板实例
            llm_config: LLM配置
        """
        self.logger = logging.getLogger(__name__)
        
        # 用户隔离
        self.user_id = user_id
        
        # 初始化组件
        self.retriever = retriever
        self.memory = memory or Memory()
        self.prompt_template = prompt_template or PromptTemplate()
        self.llm_config = llm_config or settings.get_model_config('llm')
        self.openai_config = self.llm_config.get('openai', {})
        
        # 对话状态
        self.conversation_history: List[ConversationTurn] = []
        self.current_turn_id = 0
        self.session_id = session_id or self._generate_session_id()
        
        # 完整转录内容存储
        self.full_transcript = None  # 存储完整转录数据
        self.full_context_sent = False  # 标记完整内容是否已发送
        self._full_context_cache = None  # 缓存完整上下文
        
        # 会话数据
        self.session_data: Optional[SessionData] = None
        self.video_info: Optional[VideoInfo] = None
        
        # 索引状态管理
        self.index_ready = False
        self._rebuild_thread: Optional[threading.Thread] = None
        self._rebuild_lock = threading.Lock()
        
        # 对话配置
        self.max_history_length = settings.get_model_config('qa_system', 'history_length', 10)
        self.enable_compression = settings.get_model_config('qa_system', 'enable_compression', True)
        self.max_context_length = settings.get_model_config('qa_system', 'max_context_length', 4000)
        
        # 会话存储路径（支持用户隔离）
        self._init_sessions_dir()
        
        # 初始化多查询生成器（仅使用模型扩展器）
        models_dir = settings.PROJECT_ROOT / "models"
        self.multi_query = MultiQueryGenerator(
            cache_dir=str(models_dir)
        )
        
        self.logger.info(f"对话链初始化完成，会话ID: {self.session_id}")
    
    def _init_sessions_dir(self):
        """初始化会话存储目录（支持用户隔离）"""
        # 获取当前用户ID
        user_id = self._get_current_user_id()
        
        if user_id:
            # 用户隔离模式
            from deploy.utils.path_manager import get_path_manager
            path_manager = get_path_manager(user_id)
            self.sessions_dir = path_manager.get_conversations_dir() / "sessions"
        else:
            # 共享模式
            self.sessions_dir = settings.MEMORY_DIR / "sessions"
        
        # 确保目录存在
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_current_user_id(self) -> Optional[str]:
        """获取当前用户ID"""
        # 优先使用构造函数传入的user_id
        if self.user_id:
            return self.user_id
            
        # 其次尝试从用户上下文获取
        try:
            from deploy.utils.user_context import get_current_user_id
            return get_current_user_id()
        except ImportError:
            return None
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        import random
        # 使用毫秒+随机数确保唯一性
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S_%f')[:-3]  # 精确到毫秒
        random_suffix = random.randint(1000, 9999)  # 4位随机数
        return f"session_{timestamp}_{random_suffix}"
    
    def _retrieve_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回文档数量
            
        Returns:
            检索到的文档列表
        """
        try:
            # 使用多查询生成器扩展查询
            multi_query_result = self.multi_query.generate_queries(query)
            expanded_queries = [gq.query for gq in multi_query_result.generated_queries]
            
            # 添加原始查询
            all_queries = [query] + expanded_queries
            
            # 使用检索器对所有查询进行检索
            if self.retriever is not None:
                all_results = []
                seen_docs = set()  # 用于去重
                
                # 对每个查询进行检索
                for i, search_query in enumerate(all_queries):
                    if isinstance(self.retriever, HybridRetriever):
                        # 混合检索器
                        results = self.retriever.search(search_query, top_k=top_k)
                    else:
                        # 单一检索器
                        results = self.retriever.search(search_query, top_k=top_k)
                    
                    # 去重并添加到结果列表
                    for result in results:
                        # 使用文档内容作为唯一标识
                        doc_text = result.get('document', {}).get('text', '')
                        if doc_text and doc_text not in seen_docs:
                            all_results.append(result)
                            seen_docs.add(doc_text)
                
                # 按相似度/分数排序并限制数量
                all_results.sort(key=lambda x: x.get('similarity', x.get('score', 0)), reverse=True)
                final_results = all_results[:top_k]
                
                self.logger.info(f"使用 {len(all_queries)} 个查询检索到 {len(final_results)} 个不重复文档")
                return final_results
            else:
                self.logger.warning("未配置检索器")
                return []
                
        except Exception as e:
            self.logger.error(f"文档检索失败: {e}")
            return []
    
    def _build_context(self, retrieved_docs: List[Dict[str, Any]], query: str) -> str:
        """
        构建上下文
        
        Args:
            retrieved_docs: 检索到的文档
            query: 用户查询
            
        Returns:
            构建的上下文文本
        """
        if not retrieved_docs:
            # 返回空字符串，不发送"未找到相关内容"给LLM
            return ""
        
        # 构建上下文文本
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            # 从不同的可能字段中获取文档文本
            if 'document' in doc:
                doc_text = doc['document'].get('text', '')
                start_time = doc['document'].get('start', 0)
                end_time = doc['document'].get('end', 0)
            else:
                doc_text = doc.get('text', '')
                start_time = doc.get('start', 0)
                end_time = doc.get('end', 0)
            
            # 格式化时间戳
            start_str = f"{int(start_time//60):02d}:{int(start_time%60):02d}"
            end_str = f"{int(end_time//60):02d}:{int(end_time%60):02d}"
            
            context_part = f"[{start_str}-{end_str}] {doc_text}"
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        # 检查上下文长度
        if len(context) > self.max_context_length and self.enable_compression:
            context = self._compress_context(context, query)
        
        return context
    
    def _compress_context(self, context: str, query: str) -> str:
        """
        压缩上下文
        
        Args:
            context: 原始上下文
            query: 用户查询
            
        Returns:
            压缩后的上下文
        """
        # 简单的截断策略，实际应用中可以使用更复杂的压缩算法
        lines = context.split('\n')
        compressed_lines = []
        current_length = 0
        
        for line in lines:
            if current_length + len(line) <= self.max_context_length:
                compressed_lines.append(line)
                current_length += len(line)
            else:
                break
        
        return '\n'.join(compressed_lines)
    
    def _generate_response(self, query: str, context: str) -> str:
        """
        生成回答
        
        Args:
            query: 用户查询
            context: 上下文
            
        Returns:
            生成的回答
        """
        try:
            # 根据配置选择LLM提供商
            provider = self.llm_config.get('provider', 'local')
            
            if provider == 'openai':
                response = self._call_openai(query, context)
            elif provider == 'anthropic':
                response = self._call_anthropic(query, context)
            elif provider == 'local':
                response = self._call_local_llm(query, context)
            elif provider == 'huggingface':
                response = self._call_huggingface(query, context)
            else:
                response = "抱歉，当前没有配置可用的语言模型。"
            
            return response
            
        except Exception as e:
            self.logger.error(f"生成回答失败: {e}")
            return f"生成回答时出现错误: {str(e)}"
    
    def _build_messages(self, query: str, context: str) -> List[Dict[str, str]]:
        """
        构建完整的消息列表，每次都发送完整视频内容，不包含历史对话
        
        Args:
            query: 用户查询
            context: 视频内容上下文
            
        Returns:
            完整的消息列表
        """
        messages = []
        
        # 1. 系统提示 - 设置角色和背景
        system_prompt = self._build_system_prompt()
        messages.append({"role": "system", "content": system_prompt})
        
        # 2. 完整视频内容 - 如果有完整转录内容则发送
        if hasattr(self, 'full_transcript') and self.full_transcript:
            full_content = self._build_full_context()
            if full_content:
                messages.append({"role": "system", "content": f"以下是视频的完整转录内容：\n\n{full_content}"})
                self.logger.info(f"已发送完整视频内容，长度: {len(full_content)} 字符")
        else:
            self.logger.warning("没有完整视频内容可发送")
        
        # 3. 检索到的相关内容 - 如果有检索结果则发送
        if context and context.strip():
            messages.append({"role": "system", "content": f"以下是与问题相关的视频片段：\n\n{context}"})
        
        # 4. 当前问题
        messages.append({"role": "user", "content": query})
        
        return messages
    
    def _build_full_context(self) -> str:
        """构建完整的视频内容上下文"""
        # 防御性检查：确保full_transcript属性存在
        if not hasattr(self, 'full_transcript') or not self.full_transcript:
            return ""
        
        # 如果有缓存，直接返回
        if self._full_context_cache:
            return self._full_context_cache
        
        # 构建完整内容（不包含时间戳）
        full_content = []
        for segment in self.full_transcript:
            text = segment.get('text', '').strip()
            
            if text:
                # 直接添加文本内容，不包含时间戳
                full_content.append(text)
        
        # 合并内容并缓存
        result = "\n".join(full_content)
        self._full_context_cache = result
        return result
    
    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为 HH:MM:SS 格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def set_full_transcript(self, transcript: List[Dict[str, Any]]) -> None:
        """
        设置完整的转录内容
        
        Args:
            transcript: 转录文本列表，每个元素包含 text, start, end 等字段
        """
        self.full_transcript = transcript
        # 清除缓存，下次使用时重新构建
        self._full_context_cache = None
        self.logger.info(f"已设置完整转录内容，共 {len(transcript)} 个片段")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return """你是一个专业的视频内容助手，能够根据提供的视频转录内容回答用户问题。

请遵循以下原则：
1. 基于提供的视频内容回答问题，不要编造信息
2. 如果视频中没有相关信息，请明确说明
3. 回答要准确、简洁、有条理
4. 可以引用视频中的具体内容来支持你的回答
5. 保持友好和专业的语气

特别注意：
- 如果用户的问题涉及特定时间点（如"第几秒"、"开头"、"结尾"等），请参考带时间戳的内容片段
- 带时间戳的内容（格式如 [00:00:00 - 00:00:05]）表示视频中的具体时间段，用户可能希望了解这些时间点的内容
- 在回答时间相关问题时，可以提及具体的时间戳，帮助用户定位视频位置"""
    
    def _build_history_messages(self) -> List[Dict[str, str]]:
        """构建历史对话消息"""
        history_messages = []
        
        # 获取最近的对话历史（根据配置的数量）
        recent_history = self.conversation_history[-self.max_history_length:]
        
        for turn in recent_history:
            # 添加用户问题
            history_messages.append({"role": "user", "content": turn.user_query})
            # 添加AI回答
            if turn.response:
                history_messages.append({"role": "assistant", "content": turn.response})
        
        return history_messages
    
    def _manage_token_limit(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        管理token限制，确保消息列表在合理范围内
        
        Args:
            messages: 原始消息列表
            
        Returns:
            处理后的消息列表
        """
        # 估算token数量（中文约1.5字符=1token）
        def estimate_tokens(text: str) -> int:
            # 简单估算：中文约1.5字符=1token，英文约4字符=1token
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + english_chars / 4)
        
        # 计算总token数
        total_tokens = sum(estimate_tokens(msg['content']) for msg in messages)
        
        # 设置最大上下文token数（为生成留出空间）
        max_context_tokens = 6000  # 假设模型最大token为8192
        
        if total_tokens <= max_context_tokens:
            return messages
        
        # 如果超出限制，进行压缩
        self.logger.warning(f"消息token数({total_tokens})超出限制，开始压缩...")
        
        # 1. 首先压缩视频内容
        if len(messages) >= 2 and messages[1]['role'] == 'system':
            video_content = messages[1]['content']
            if len(video_content) > 2000:  # 如果视频内容过长
                # 保留前1000字符和后1000字符
                compressed_content = video_content[:1000] + "\n\n...[内容已压缩]...\n\n" + video_content[-1000:]
                messages[1]['content'] = compressed_content
                self.logger.info("视频内容已压缩")
        
        # 2. 如果还是超出，减少历史对话
        total_tokens = sum(estimate_tokens(msg['content']) for msg in messages)
        if total_tokens > max_context_tokens:
            # 计算需要保留的历史对话轮数
            system_tokens = estimate_tokens(messages[0]['content']) + estimate_tokens(messages[1]['content'])
            available_tokens = max_context_tokens - system_tokens
            
            # 假设每轮对话平均token数
            avg_tokens_per_turn = 200
            max_history_turns = max(1, available_tokens // avg_tokens_per_turn // 2)  # 除以2因为每轮有user和assistant
            
            # 重新构建历史消息
            new_messages = messages[:2]  # 保留系统提示和视频内容
            
            recent_history = self.conversation_history[-max_history_turns:]
            for turn in recent_history:
                new_messages.append({"role": "user", "content": turn.user_query})
                if turn.response:
                    new_messages.append({"role": "assistant", "content": turn.response})
            
            # 添加当前问题
            new_messages.append(messages[-1])
            
            self.logger.info(f"历史对话已压缩到{max_history_turns}轮")
            return new_messages
        
        return messages
    
    def _call_openai(self, query: str, context: str) -> str:
        """调用讯飞星火API（使用OpenAI兼容接口）"""
        try:
            from openai import OpenAI
            
            # 使用配置中的API密钥和地址
            api_key = self.openai_config.get('api_key')
            base_url = self.openai_config.get('base_url')
            
            if not api_key:
                raise ValueError("未配置API密钥")
            if not base_url:
                raise ValueError("未配置API地址")
            
            # 创建客户端
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 构建完整消息列表
            messages = self._build_messages(query, context)
            
            self.logger.info(f"发送消息到讯飞星火API，消息数量: {len(messages)}")
            
            # 调用API
            response = client.chat.completions.create(
                model=self.openai_config.get('model_name', 'xop3qwen1b7'),
                messages=messages,  # 使用完整的消息列表
                max_tokens=self.openai_config.get('max_tokens', 2048),
                temperature=self.openai_config.get('temperature', 0.7),
                stream=False  # 暂时不使用流式输出
            )
            
            if response and response.choices:
                answer = response.choices[0].message.content
                self.logger.info(f"讯飞星火API调用成功，回答长度: {len(answer)}")
                
                # 记录token使用情况
                if hasattr(response, 'usage') and response.usage:
                    usage = response.usage
                    self.logger.info(f"Token使用情况 - 输入: {usage.prompt_tokens}, "
                                   f"输出: {usage.completion_tokens}, "
                                   f"总计: {usage.total_tokens}")
                
                return answer
            else:
                self.logger.error("讯飞星火API响应为空")
                return "抱歉，无法获取回答，请稍后重试。"
            
        except ImportError:
            self.logger.error("OpenAI库未安装")
            return "OpenAI库未安装，请安装: pip install openai"
        except Exception as e:
            self.logger.error(f"讯飞星火API调用失败: {e}")
            return f"调用大模型API时出现错误: {str(e)}"
    
    def _call_anthropic(self, query: str, context: str) -> str:
        """调用Anthropic API"""
        try:
            import anthropic
            
            # 配置API
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("未配置Anthropic API密钥")
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # 构建消息列表（Anthropic格式稍有不同）
            messages = self._build_messages(query, context)
            
            # 转换为Anthropic格式（移除system消息，将其合并到第一个user消息）
            anthropic_messages = []
            system_message = ""
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message += msg['content'] + "\n\n"
                else:
                    anthropic_messages.append(msg)
            
            # 将系统消息添加到第一个user消息
            if system_message and anthropic_messages:
                anthropic_messages[0]['content'] = system_message + anthropic_messages[0]['content']
            
            # 调用API
            response = client.messages.create(
                model=self.llm_config.get('anthropic', {}).get('model_name', 'claude-3-sonnet-20240229'),
                max_tokens=self.llm_config.get('anthropic', {}).get('max_tokens', 2048),
                messages=anthropic_messages
            )
            
            return response.content[0].text
            
        except ImportError:
            return "Anthropic库未安装，请安装: pip install anthropic"
        except Exception as e:
            self.logger.error(f"Anthropic API调用失败: {e}")
            return f"Anthropic API调用失败: {str(e)}"
    
    def _call_local_llm(self, query: str, context: str) -> str:
        """调用本地LLM（使用OpenAI兼容接口）"""
        try:
            self.logger.info("调用本地LLM")
            
            # 使用OpenAI客户端调用本地LLM
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.openai_config.get('api_key'),
                base_url=self.openai_config.get('base_url')
            )
            
            # 构建完整消息列表
            messages = self._build_messages(query, context)
            
            response = client.chat.completions.create(
                model=self.openai_config.get('model_name'),
                messages=messages,  # 使用完整的消息列表
                max_tokens=self.openai_config.get('max_tokens', 2048),
                temperature=self.openai_config.get('temperature', 0.7)
            )
            
            if response and response.choices:
                answer = response.choices[0].message.content
                self.logger.info(f"本地LLM调用成功，回答长度: {len(answer)}")
                return answer
            else:
                self.logger.error("本地LLM响应为空")
                return "抱歉，无法获取回答，请稍后重试。"
            
        except ImportError:
            self.logger.error("OpenAI库未安装，请安装: pip install openai")
            return "抱歉，OpenAI库未安装，无法调用大模型API。"
        except Exception as e:
            self.logger.error(f"本地LLM调用失败: {e}")
            return f"调用大模型API时出现错误: {str(e)}"
    
    def _call_huggingface(self, query: str, context: str) -> str:
        """调用HuggingFace模型"""
        try:
            from transformers import pipeline
            
            # 加载模型
            model_name = self.llm_config.get('huggingface', {}).get('model_name', 'microsoft/DialoGPT-medium')
            generator = pipeline('text-generation', model=model_name)
            
            # 构建提示（HuggingFace模型通常使用简单的文本格式）
            prompt = self._build_huggingface_prompt(query, context)
            
            # 生成回答
            response = generator(
                prompt,
                max_length=self.llm_config.get('huggingface', {}).get('generation', {}).get('max_tokens', 2048),
                temperature=self.llm_config.get('huggingface', {}).get('generation', {}).get('temperature', 0.7),
                do_sample=self.llm_config.get('huggingface', {}).get('generation', {}).get('do_sample', True)
            )
            
            # 提取生成的部分（去除原始提示）
            generated_text = response[0]['generated_text']
            if generated_text.startswith(prompt):
                answer = generated_text[len(prompt):].strip()
            else:
                answer = generated_text
            
            return answer
            
        except ImportError:
            return "Transformers库未安装，请安装: pip install transformers"
        except Exception as e:
            self.logger.error(f"HuggingFace模型调用失败: {e}")
            return f"HuggingFace模型调用失败: {str(e)}"
    
    def _build_huggingface_prompt(self, query: str, context: str) -> str:
        """为HuggingFace模型构建提示"""
        prompt_parts = []
        
        # 系统提示
        prompt_parts.append("你是一个专业的视频内容助手。")
        
        # 视频内容
        if context:
            prompt_parts.append(f"视频内容：{context}")
        
        # 历史对话
        recent_history = self.conversation_history[-3:]  # 最近3轮
        for turn in recent_history:
            prompt_parts.append(f"用户：{turn.user_query}")
            prompt_parts.append(f"助手：{turn.response}")
        
        # 当前问题
        prompt_parts.append(f"用户：{query}")
        prompt_parts.append("助手：")
        
        return "\n".join(prompt_parts)
    
    def _get_history_summary(self) -> str:
        """获取对话历史摘要"""
        if not self.conversation_history:
            return ""
        
        # 获取最近的对话历史
        recent_history = self.conversation_history[-3:]  # 最近3轮对话
        
        summary_parts = []
        for turn in recent_history:
            summary_parts.append(f"Q: {turn.user_query}")
            summary_parts.append(f"A: {turn.response}")
        
        return "\n".join(summary_parts)
    
    def _update_history(self, turn: ConversationTurn):
        """更新对话历史"""
        self.conversation_history.append(turn)
        
        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
        
        # 更新记忆
        self.memory.add_turn(turn)
    
    def chat(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        处理对话
        
        Args:
            query: 用户查询
            top_k: 检索文档数量
            
        Returns:
            对话结果字典
        """
        try:
            self.logger.info(f"处理用户查询: {query}")
            
            # 创建新的对话轮次
            self.current_turn_id += 1
            current_turn = ConversationTurn(
                turn_id=self.current_turn_id,
                user_query=query
            )
            
            # 根据索引状态选择检索策略
            if self.index_ready and self.retriever:
                # 使用完整的混合检索
                retrieved_docs = self._retrieve_documents(query, top_k)
                retrieval_method = 'hybrid'
            else:
                # 使用降级检索策略
                retrieved_docs = self._fallback_retrieve(query, top_k)
                retrieval_method = 'fallback'
            
            current_turn.retrieved_docs = retrieved_docs
            
            # 构建上下文
            context = self._build_context(retrieved_docs, query)
            current_turn.context = context
            
            # 生成回答
            response = self._generate_response(query, context)
            current_turn.response = response
            
            # 添加到对话历史
            self.conversation_history.append(current_turn)
            
            # 如果有会话数据，同步更新
            if self.session_data:
                self.session_data.add_conversation_turn(current_turn)
            
            # 构建返回结果
            result = {
                'session_id': self.session_id,
                'turn_id': current_turn.turn_id,
                'query': query,
                'response': response,
                'retrieved_docs': retrieved_docs,
                'context': context,
                'timestamp': current_turn.timestamp.isoformat(),
                'metadata': {
                    'total_turns': len(self.conversation_history),
                    'retrieved_count': len(retrieved_docs),
                    'context_length': len(context),
                    'retrieval_method': retrieval_method,
                    'index_ready': self.index_ready
                }
            }
            
            self.logger.info(f"对话处理完成，返回 {len(retrieved_docs)} 个检索结果，方法: {retrieval_method}")
            return result
            
        except Exception as e:
            self.logger.error(f"对话处理失败: {e}")
            return {
                'session_id': self.session_id,
                'turn_id': self.current_turn_id,
                'query': query,
                'response': f"处理查询时出现错误: {str(e)}",
                'retrieved_docs': [],
                'context': "",
                'timestamp': datetime.now().isoformat(),
                'metadata': {'error': str(e)}
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return [turn.to_dict() for turn in self.conversation_history]
    
    def clear_history(self):
        """清空对话历史"""
        # 清空对话历史
        self.conversation_history.clear()
        self.current_turn_id = 0
        
        # 清空记忆
        self.memory.clear()
        
        # 如果有会话数据，同步更新
        if self.session_data:
            self.session_data.conversation_history.clear()
            self.session_data.update_timestamp()
            
            # 保存更改
            self.save_session()
            self.logger.info(f"会话 {self.session_id} 的对话历史已清空并保存")
        else:
            self.logger.info("对话历史已清空（无会话数据）")
    
    def clear_current_session(self):
        """完全清空当前会话"""
        self._reset_all_state()
        self.logger.info(f"当前会话已完全清空，新会话ID: {self.session_id}")
    
    def save_conversation(self, file_path: str):
        """保存对话历史"""
        try:
            conversation_data = {
                'session_id': self.session_id,
                'created_at': datetime.now().isoformat(),
                'history': self.get_conversation_history(),
                'config': {
                    'max_history_length': self.max_history_length,
                    'enable_compression': self.enable_compression,
                    'max_context_length': self.max_context_length
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"对话历史已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存对话历史失败: {e}")
    
    def load_conversation(self, file_path: str):
        """加载对话历史"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            self.session_id = conversation_data.get('session_id', self.session_id)
            self.conversation_history = [
                ConversationTurn.from_dict(turn_data) 
                for turn_data in conversation_data.get('history', [])
            ]
            self.current_turn_id = max([turn.turn_id for turn in self.conversation_history], default=0)
            
            self.logger.info(f"对话历史已从 {file_path} 加载")
            
        except Exception as e:
            self.logger.error(f"加载对话历史失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取对话链统计信息"""
        return {
            'session_id': self.session_id,
            'total_turns': len(self.conversation_history),
            'current_turn_id': self.current_turn_id,
            'memory_stats': self.memory.get_stats(),
            'retriever_type': type(self.retriever).__name__ if self.retriever else None,
            'llm_provider': self.llm_config.get('provider', 'unknown'),
            'index_ready': self.index_ready,
            'session_loaded': self.session_data is not None,
            'config': {
                'max_history_length': self.max_history_length,
                'enable_compression': self.enable_compression,
                'max_context_length': self.max_context_length
            }
        }
    
    def set_video_info(self, filename: str, duration: float, language: str = "zh", 
                      file_size: Optional[int] = None, resolution: Optional[str] = None):
        """
        设置视频信息
        
        Args:
            filename: 视频文件名
            duration: 视频时长（秒）
            language: 视频语言
            file_size: 文件大小（字节）
            resolution: 视频分辨率
        """
        self.video_info = VideoInfo(
            filename=filename,
            duration=duration,
            language=language,
            file_size=file_size,
            resolution=resolution
        )
        
        # 如果会话数据已存在，更新视频信息
        if self.session_data:
            self.session_data.video_info = self.video_info
            self.session_data.update_timestamp()
        
        self.logger.info(f"设置视频信息: {filename}, 时长: {duration}秒")
    
    def create_session(self, transcript: List[Dict[str, Any]]) -> str:
        """
        创建新会话
        
        Args:
            transcript: 转录文本列表
            
        Returns:
            会话ID
        """
        if not self.video_info:
            raise ValueError("请先设置视频信息")
        
        # 创建会话数据
        self.session_data = SessionData(
            session_id=self.session_id,
            video_info=self.video_info,
            transcript=transcript,
            conversation_history=[]
        )
        
        # 设置转录文本
        self.set_full_transcript(transcript)
        
        # 保存会话
        self.save_session()
        
        self.logger.info(f"创建新会话: {self.session_id}")
        return self.session_id
    
    def new_conversation(self, video_filename: str, duration: float, 
                        transcript: List[Dict[str, Any]], language: str = "zh",
                        file_size: Optional[int] = None, resolution: Optional[str] = None) -> str:
        """
        创建全新的对话（新会话）
        
        Args:
            video_filename: 视频文件名
            duration: 视频时长
            transcript: 转录文本列表
            language: 视频语言
            file_size: 文件大小
            resolution: 视频分辨率
            
        Returns:
            新会话ID
        """
        # 完全重置当前状态
        self._reset_all_state()
        
        # 设置视频信息
        self.set_video_info(
            filename=video_filename,
            duration=duration,
            language=language,
            file_size=file_size,
            resolution=resolution
        )
        
        # 创建新会话
        session_id = self.create_session(transcript)
        
        self.logger.info(f"创建全新对话，会话ID: {session_id}")
        return session_id
    
    def _reset_all_state(self):
        """重置所有状态"""
        # 清空对话历史
        self.conversation_history.clear()
        self.current_turn_id = 0
        
        # 清空转录相关
        self.full_transcript = None
        self._full_context_cache = None
        self.full_context_sent = False
        
        # 清空会话数据
        self.session_data = None
        self.video_info = None
        
        # 重置索引状态
        self.index_ready = False
        
        # 停止后台重建线程
        if self._rebuild_thread and self._rebuild_thread.is_alive():
            # 线程会自动结束，因为我们清空了数据
            pass
        
        # 清空检索器
        if self.retriever:
            if hasattr(self.retriever, 'vector_store'):
                self.retriever.vector_store.clear()
            if hasattr(self.retriever, 'bm25_retriever'):
                self.retriever.bm25_retriever.clear()
        
        # 清空记忆
        self.memory.clear()
        
        # 生成新的会话ID
        self.session_id = self._generate_session_id()
        
        self.logger.info(f"所有状态已重置，新会话ID: {self.session_id}")
    
    def save_session(self) -> bool:
        """
        保存当前会话
        
        Returns:
            是否保存成功
        """
        if not self.session_data:
            self.logger.warning("没有会话数据可保存")
            return False
        
        try:
            # 更新会话数据
            self.session_data.conversation_history = self.conversation_history
            self.session_data.update_timestamp()
            
            # 保存到文件
            session_file = self.sessions_dir / f"{self.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data.to_dict(), f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"会话已保存: {session_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存会话失败: {e}")
            return False
    
    def load_session(self, session_id: str) -> bool:
        """
        加载历史会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否加载成功
        """
        try:
            # 加载会话文件
            session_file = self.sessions_dir / f"{session_id}.json"
            if not session_file.exists():
                self.logger.error(f"会话文件不存在: {session_file}")
                return False
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_dict = json.load(f)
            
            # 恢复会话数据
            self.session_data = SessionData.from_dict(session_dict)
            self.session_id = session_id
            self.video_info = self.session_data.video_info
            
            # 恢复对话历史
            self.conversation_history = self.session_data.conversation_history
            self.current_turn_id = max([turn.turn_id for turn in self.conversation_history], default=0)
            
            # 恢复转录文本
            self.set_full_transcript(self.session_data.transcript)
            
            # 重置索引状态
            self.index_ready = False
            
            # 启动后台索引重建
            self._start_index_rebuild()
            
            self.logger.info(f"会话加载成功: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载会话失败: {e}")
            return False
    
    def _start_index_rebuild(self):
        """启动后台索引重建"""
        with self._rebuild_lock:
            if self._rebuild_thread and self._rebuild_thread.is_alive():
                self.logger.info("索引重建线程已在运行")
                return
            
            self._rebuild_thread = threading.Thread(
                target=self._rebuild_indexes,
                daemon=True
            )
            self._rebuild_thread.start()
            self.logger.info("启动后台索引重建")
    
    def _rebuild_indexes(self):
        """重建索引（在后台线程中执行）"""
        try:
            if not self.full_transcript:
                self.logger.warning("没有转录文本，跳过索引重建")
                return
            
            self.logger.info("开始重建索引")
            
            # 准备文档数据
            documents = []
            for segment in self.full_transcript:
                documents.append({
                    'text': segment['text'],
                    'start': segment['start'],
                    'end': segment['end'],
                    'confidence': segment.get('confidence', 1.0)
                })
            
            # 清空现有索引
            if self.retriever:
                if hasattr(self.retriever, 'vector_store'):
                    self.retriever.vector_store.clear()
                if hasattr(self.retriever, 'bm25_retriever'):
                    self.retriever.bm25_retriever.clear()
            
            # 重建索引
            if self.retriever:
                self.retriever.add_documents(documents)
            
            # 标记索引准备就绪
            self.index_ready = True
            self.logger.info("索引重建完成")
            
        except Exception as e:
            self.logger.error(f"索引重建失败: {e}")
            # 即使失败，也可以使用简单的文本检索
            self.index_ready = False
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        获取会话状态
        
        Returns:
            会话状态信息
        """
        return {
            'session_id': self.session_id,
            'session_loaded': self.session_data is not None,
            'video_info': self.video_info.to_dict() if self.video_info else None,
            'conversation_turns': len(self.conversation_history),
            'index_ready': self.index_ready,
            'index_building': self._rebuild_thread and self._rebuild_thread.is_alive(),
            'transcript_segments': len(self.full_transcript) if self.full_transcript else 0
        }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有保存的会话
        
        Returns:
            会话列表
        """
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_dict = json.load(f)
                
                session_info = {
                    'session_id': session_dict['session_id'],
                    'video_filename': session_dict['video_info']['filename'],
                    'video_duration': session_dict['video_info']['duration'],
                    'conversation_turns': len(session_dict.get('conversation_history', [])),
                    'transcript_segments': len(session_dict.get('transcript', [])),
                    'created_at': session_dict['created_at'],
                    'updated_at': session_dict['updated_at']
                }
                sessions.append(session_info)
                
            except Exception as e:
                self.logger.error(f"读取会话文件失败 {session_file}: {e}")
        
        # 按更新时间排序
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                self.logger.info(f"会话已删除: {session_id}")
                return True
            else:
                self.logger.warning(f"会话文件不存在: {session_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除会话失败: {e}")
            return False
    
    def _fallback_retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        降级检索策略（当索引未准备好时使用）
        
        Args:
            query: 查询文本
            top_k: 返回文档数量
            
        Returns:
            检索结果
        """
        if not self.full_transcript:
            return []
        
        # 简单的文本匹配
        results = []
        query_lower = query.lower()
        
        for segment in self.full_transcript:
            text = segment.get('text', '')
            if query_lower in text.lower():
                # 计算简单的相关性分数
                score = min(1.0, text.lower().count(query_lower) * 0.1 + 0.5)
                
                result = {
                    'document': segment,
                    'metadata': {},
                    'score': score,
                    'similarity': score,
                    'bm25_score': score,
                    'index': len(results)
                }
                results.append(result)
        
        # 按分数排序并限制数量
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]