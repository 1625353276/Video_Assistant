#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 提示模板模块
Prompt Template Module for AI Video Assistant

实现各种场景的提示模板，支持少样本学习和动态模板生成
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

# 导入配置
from config.settings import settings


@dataclass
class PromptExample:
    """提示示例数据类"""
    question: str
    answer: str
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'question': self.question,
            'answer': self.answer,
            'context': self.context,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptExample':
        """从字典创建实例"""
        return cls(
            question=data['question'],
            answer=data['answer'],
            context=data.get('context', ''),
            metadata=data.get('metadata', {})
        )


class PromptTemplate:
    """提示模板管理类"""
    
    def __init__(self):
        """初始化提示模板"""
        self.logger = logging.getLogger(__name__)
        
        # 模板配置
        self.enable_few_shot = settings.get_model_config('qa_system', 'enable_few_shot', True)
        self.few_shot_examples = settings.get_model_config('qa_system', 'few_shot_examples', 3)
        self.examples_path = settings.QA_EXAMPLES_PATH
        
        # 默认模板
        self.system_template = settings.get_model_config(
            'qa_system', 'system_template',
            "你是一个专业的视频内容助手，能够根据提供的视频转录内容回答用户问题。请基于以下内容回答问题：\n\n{context}\n\n问题：{question}"
        )
        
        self.user_template = settings.get_model_config(
            'qa_system', 'user_template',
            "{question}"
        )
        
        # 示例数据
        self.examples: List[PromptExample] = []
        
        # 模板变量
        self.template_vars = {
            'context': '视频内容上下文',
            'question': '用户问题',
            'history': '对话历史',
            'examples': '示例对话',
            'timestamp': '当前时间',
            'video_info': '视频信息'
        }
        
        # 加载示例
        self._load_examples()
        
        self.logger.info("提示模板初始化完成")
    
    def _load_examples(self):
        """加载示例数据"""
        try:
            if self.examples_path.exists():
                with open(self.examples_path, 'r', encoding='utf-8') as f:
                    examples_data = json.load(f)
                
                self.examples = [
                    PromptExample.from_dict(example_data)
                    for example_data in examples_data.get('examples', [])
                ]
                
                self.logger.info(f"加载了 {len(self.examples)} 个示例")
            else:
                # 创建默认示例
                self._create_default_examples()
                self._save_examples()
                
        except Exception as e:
            self.logger.error(f"加载示例失败: {e}")
            self._create_default_examples()
    
    def _create_default_examples(self):
        """创建默认示例"""
        self.examples = [
            PromptExample(
                question="这个视频主要讲了什么内容？",
                answer="根据视频内容，这是一个关于人工智能技术的介绍视频，主要讲解了AI的基本概念、发展历史和应用领域。",
                context="人工智能是计算机科学的一个分支，它试图理解和构建智能体，这些智能体能够感知环境并采取行动以最大化其成功的机会。",
                metadata={'category': 'summary', 'difficulty': 'easy'}
            ),
            PromptExample(
                question="视频中提到了哪些应用领域？",
                answer="视频中提到了AI在医疗诊断、自动驾驶、金融风控、智能客服等领域的应用。",
                context="人工智能已经在多个领域得到广泛应用，包括医疗诊断、自动驾驶汽车、金融风险控制和智能客服系统等。",
                metadata={'category': 'detail', 'difficulty': 'medium'}
            ),
            PromptExample(
                question="AI的发展历史是怎样的？",
                answer="视频介绍了AI从1950年代的概念提出，到经历多次发展浪潮，再到当前深度学习突破的完整发展历程。",
                context="人工智能的概念最早在1950年代被提出，经历了多次发展浪潮，包括符号主义、连接主义等不同范式，当前正处于深度学习驱动的快速发展期。",
                metadata={'category': 'history', 'difficulty': 'hard'}
            )
        ]
    
    def _save_examples(self):
        """保存示例数据"""
        try:
            # 确保目录存在
            self.examples_path.parent.mkdir(parents=True, exist_ok=True)
            
            examples_data = {
                'examples': [example.to_dict() for example in self.examples],
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.examples_path, 'w', encoding='utf-8') as f:
                json.dump(examples_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"示例数据已保存到: {self.examples_path}")
            
        except Exception as e:
            self.logger.error(f"保存示例数据失败: {e}")
    
    def build_system_prompt(self, 
                        video_info: str = "",
                        custom_instructions: str = "") -> str:
        """
        构建系统提示
        
        Args:
            video_info: 视频信息
            custom_instructions: 自定义指令
            
        Returns:
            系统提示文本
        """
        try:
            # 基础系统提示
            base_prompt = """你是一个专业的视频内容助手，能够根据提供的视频转录内容回答用户问题。

请遵循以下原则：
1. 基于提供的视频内容回答问题，不要编造信息
2. 如果视频中没有相关信息，请明确说明
3. 回答要准确、简洁、有条理
4. 可以引用视频中的具体内容来支持你的回答
5. 保持友好和专业的语气"""
            
            # 添加视频信息
            if video_info:
                base_prompt += f"\n\n视频信息：{video_info}"
            
            # 添加自定义指令
            if custom_instructions:
                base_prompt += f"\n\n特殊要求：{custom_instructions}"
            
            return base_prompt
            
        except Exception as e:
            self.logger.error(f"构建系统提示失败: {e}")
            return "你是一个专业的视频内容助手。"
    
    def build_prompt(self, 
                    query: str, 
                    context: str = "",
                    history: str = "",
                    examples: Optional[List[PromptExample]] = None,
                    template_type: str = "qa",
                    **kwargs) -> str:
        """
        构建提示
        
        Args:
            query: 用户查询
            context: 上下文内容
            history: 对话历史
            examples: 示例列表
            template_type: 模板类型
            **kwargs: 其他模板变量
            
        Returns:
            构建的提示文本
        """
        try:
            # 选择模板
            if template_type == "qa":
                template = self.system_template
            elif template_type == "user":
                template = self.user_template
            elif template_type == "custom":
                template = kwargs.get('custom_template', self.system_template)
            else:
                template = self.system_template
            
            # 准备模板变量
            template_vars = {
                'context': context,
                'question': query,
                'history': history,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'video_info': kwargs.get('video_info', ''),
                **kwargs
            }
            
            # 添加示例
            if self.enable_few_shot and template_type == "qa":
                selected_examples = examples or self._select_examples(query, context)
                if selected_examples:
                    examples_text = self._format_examples(selected_examples)
                    template_vars['examples'] = examples_text
            
            # 替换模板变量
            prompt = template
            for var_name, var_value in template_vars.items():
                placeholder = f"{{{var_name}}}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(var_value))
            
            # 处理未替换的变量
            import re
            unresolved_vars = re.findall(r'\{(\w+)\}', prompt)
            if unresolved_vars:
                self.logger.warning(f"未解析的模板变量: {unresolved_vars}")
                for var in unresolved_vars:
                    prompt = prompt.replace(f"{{{var}}}", "")
            
            self.logger.debug(f"构建提示完成，长度: {len(prompt)}")
            return prompt
            
        except Exception as e:
            self.logger.error(f"构建提示失败: {e}")
            return f"请基于以下内容回答问题：\n\n{context}\n\n问题：{query}"
    
    def _select_examples(self, query: str, context: str, max_examples: Optional[int] = None) -> List[PromptExample]:
        """
        选择相关示例
        
        Args:
            query: 用户查询
            context: 上下文
            max_examples: 最大示例数量
            
        Returns:
            选择的示例列表
        """
        if not self.examples:
            return []
        
        max_examples = max_examples or self.few_shot_examples
        if max_examples <= 0:
            return []
        
        # 简单的选择策略：基于查询相似度
        # 这里可以使用更复杂的相似度计算
        selected_examples = []
        
        # 按类别和难度选择示例
        query_lower = query.lower()
        
        # 根据查询内容选择相关示例
        if '主要' in query_lower or '总结' in query_lower or '概括' in query_lower:
            # 选择总结类示例
            summary_examples = [ex for ex in self.examples if ex.metadata.get('category') == 'summary']
            if summary_examples:
                selected_examples.extend(summary_examples[:1])
        
        if '哪些' in query_lower or '什么' in query_lower or '如何' in query_lower:
            # 选择细节类示例
            detail_examples = [ex for ex in self.examples if ex.metadata.get('category') == 'detail']
            if detail_examples:
                selected_examples.extend(detail_examples[:1])
        
        if '历史' in query_lower or '发展' in query_lower or '起源' in query_lower:
            # 选择历史类示例
            history_examples = [ex for ex in self.examples if ex.metadata.get('category') == 'history']
            if history_examples:
                selected_examples.extend(history_examples[:1])
        
        # 如果没有匹配的示例，使用默认选择
        if not selected_examples:
            selected_examples = self.examples[:max_examples]
        
        return selected_examples[:max_examples]
    
    def _format_examples(self, examples: List[PromptExample]) -> str:
        """
        格式化示例
        
        Args:
            examples: 示例列表
            
        Returns:
            格式化的示例文本
        """
        if not examples:
            return ""
        
        examples_text = "示例对话：\n\n"
        
        for i, example in enumerate(examples, 1):
            examples_text += f"示例 {i}：\n"
            examples_text += f"问题：{example.question}\n"
            
            if example.context:
                examples_text += f"上下文：{example.context}\n"
            
            examples_text += f"回答：{example.answer}\n\n"
        
        return examples_text
    
    def add_example(self, 
                   question: str, 
                   answer: str, 
                   context: str = "",
                   category: str = "general",
                   difficulty: str = "medium",
                   metadata: Optional[Dict[str, Any]] = None):
        """
        添加示例
        
        Args:
            question: 问题
            answer: 回答
            context: 上下文
            category: 类别
            difficulty: 难度
            metadata: 元数据
        """
        example = PromptExample(
            question=question,
            answer=answer,
            context=context,
            metadata={
                'category': category,
                'difficulty': difficulty,
                'created_at': datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        
        self.examples.append(example)
        self._save_examples()
        
        self.logger.info(f"添加示例: {question[:50]}...")
    
    def remove_example(self, index: int) -> bool:
        """
        删除示例
        
        Args:
            index: 示例索引
            
        Returns:
            是否删除成功
        """
        if 0 <= index < len(self.examples):
            removed_example = self.examples.pop(index)
            self._save_examples()
            self.logger.info(f"删除示例: {removed_example.question[:50]}...")
            return True
        return False
    
    def update_example(self, index: int, **kwargs) -> bool:
        """
        更新示例
        
        Args:
            index: 示例索引
            **kwargs: 更新的属性
            
        Returns:
            是否更新成功
        """
        if 0 <= index < len(self.examples):
            example = self.examples[index]
            
            for key, value in kwargs.items():
                if hasattr(example, key):
                    setattr(example, key, value)
            
            # 更新元数据
            if 'metadata' in kwargs:
                example.metadata.update(kwargs['metadata'])
            
            example.metadata['updated_at'] = datetime.now().isoformat()
            
            self._save_examples()
            self.logger.info(f"更新示例: {example.question[:50]}...")
            return True
        return False
    
    def get_examples(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> List[PromptExample]:
        """
        获取示例
        
        Args:
            category: 类别过滤
            difficulty: 难度过滤
            
        Returns:
            示例列表
        """
        examples = self.examples
        
        if category:
            examples = [ex for ex in examples if ex.metadata.get('category') == category]
        
        if difficulty:
            examples = [ex for ex in examples if ex.metadata.get('difficulty') == difficulty]
        
        return examples
    
    def set_template(self, template_type: str, template: str):
        """
        设置模板
        
        Args:
            template_type: 模板类型
            template: 模板内容
        """
        if template_type == "system":
            self.system_template = template
        elif template_type == "user":
            self.user_template = template
        elif template_type == "custom":
            # 自定义模板需要特殊处理
            pass
        
        self.logger.info(f"设置模板: {template_type}")
    
    def get_template(self, template_type: str) -> str:
        """
        获取模板
        
        Args:
            template_type: 模板类型
            
        Returns:
            模板内容
        """
        if template_type == "system":
            return self.system_template
        elif template_type == "user":
            return self.user_template
        else:
            return self.system_template
    
    def validate_template(self, template: str) -> Dict[str, Any]:
        """
        验证模板
        
        Args:
            template: 模板内容
            
        Returns:
            验证结果
        """
        import re
        
        # 查找模板变量
        variables = re.findall(r'\{(\w+)\}', template)
        
        # 检查变量是否在预定义变量中
        undefined_vars = []
        for var in variables:
            if var not in self.template_vars:
                undefined_vars.append(var)
        
        return {
            'valid': len(undefined_vars) == 0,
            'variables': variables,
            'undefined_variables': undefined_vars,
            'variable_count': len(variables)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        # 示例统计
        category_stats = {}
        difficulty_stats = {}
        
        for example in self.examples:
            category = example.metadata.get('category', 'unknown')
            difficulty = example.metadata.get('difficulty', 'unknown')
            
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
            
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = 0
            difficulty_stats[difficulty] += 1
        
        return {
            'total_examples': len(self.examples),
            'few_shot_enabled': self.enable_few_shot,
            'few_shot_count': self.few_shot_examples,
            'category_distribution': category_stats,
            'difficulty_distribution': difficulty_stats,
            'system_template_length': len(self.system_template),
            'user_template_length': len(self.user_template),
            'examples_path': str(self.examples_path),
            'template_variables': list(self.template_vars.keys())
        }
    
    def export_templates(self, file_path: str):
        """
        导出模板和示例
        
        Args:
            file_path: 导出文件路径
        """
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'system_template': self.system_template,
                'user_template': self.user_template,
                'template_variables': self.template_vars,
                'examples': [example.to_dict() for example in self.examples],
                'config': {
                    'few_shot_enabled': self.enable_few_shot,
                    'few_shot_count': self.few_shot_examples
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"模板和示例已导出到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"导出模板失败: {e}")
    
    def import_templates(self, file_path: str):
        """
        导入模板和示例
        
        Args:
            file_path: 导入文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 导入模板
            if 'system_template' in import_data:
                self.system_template = import_data['system_template']
            
            if 'user_template' in import_data:
                self.user_template = import_data['user_template']
            
            # 导入示例
            if 'examples' in import_data:
                self.examples = [
                    PromptExample.from_dict(example_data)
                    for example_data in import_data['examples']
                ]
            
            # 导入配置
            if 'config' in import_data:
                config = import_data['config']
                self.enable_few_shot = config.get('few_shot_enabled', self.enable_few_shot)
                self.few_shot_examples = config.get('few_shot_count', self.few_shot_examples)
            
            # 保存示例
            self._save_examples()
            
            self.logger.info(f"模板和示例已从 {file_path} 导入")
            
        except Exception as e:
            self.logger.error(f"导入模板失败: {e}")