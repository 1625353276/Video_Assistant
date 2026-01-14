#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频助手 - 系统设置文件
System Settings for AI Video Assistant

包含路径配置、设备配置、日志配置、缓存配置等系统级设置
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import logging
from logging.handlers import RotatingFileHandler


class Settings:
    """系统设置管理类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化设置
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config/model_config.yaml
        """
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "model_config.yaml"
        
        # 加载模型配置
        self.model_config = self._load_model_config()
        
        # 初始化路径设置
        self._init_paths()
        
        # 初始化设备设置
        self._init_device()
        
        # 初始化日志设置
        self._init_logging()
        
        # 初始化缓存设置
        self._init_cache()
        
        # 初始化环境变量
        self._init_env_vars()
    
    def _load_model_config(self) -> Dict[str, Any]:
        """加载模型配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config or {}
        except FileNotFoundError:
            print(f"警告: 配置文件 {self.config_path} 不存在，使用默认配置")
            return {}
        except yaml.YAMLError as e:
            print(f"警告: 配置文件解析失败: {e}，使用默认配置")
            return {}
    
    def _init_paths(self):
        """初始化路径配置"""
        # 基础路径
        self.PROJECT_ROOT = self.project_root
        self.CONFIG_DIR = self.project_root / "config"
        self.DATA_DIR = self.project_root / "data"
        self.MODELS_DIR = self.project_root / "models"
        self.DEPLOY_DIR = self.project_root / "deploy"
        self.TESTS_DIR = self.project_root / "tests"
        self.MODULES_DIR = self.project_root / "modules"
        
        # 数据路径
        self.RAW_VIDEOS_DIR = self.DATA_DIR / "raw_videos"
        self.TRANSCRIPTS_DIR = self.DATA_DIR / "transcripts"
        self.CACHE_DIR = self.DATA_DIR / "cache"
        self.MEMORY_DIR = self.DATA_DIR / "memory"
        self.LOGS_DIR = self.project_root / "logs"
        
        # 模型路径
        self.WHISPER_MODEL_DIR = self.MODELS_DIR / "whisper"
        self.SENTENCE_TRANSFORMERS_DIR = self.MODELS_DIR / "sentence-transformers"
        self.LLM_MODEL_DIR = self.MODELS_DIR / "llm"
        
        # 配置文件路径
        self.SYNONYM_DICT_PATH = self.CONFIG_DIR / "synonyms.json"
        self.DOMAIN_DICT_PATH = self.CONFIG_DIR / "domain_terms.json"
        self.PATTERN_CONFIG_PATH = self.CONFIG_DIR / "patterns.json"
        self.QA_EXAMPLES_PATH = self.CONFIG_DIR / "qa_examples.json"
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.DATA_DIR,
            self.RAW_VIDEOS_DIR,
            self.TRANSCRIPTS_DIR,
            self.CACHE_DIR,
            self.MEMORY_DIR,
            self.LOGS_DIR,
            self.MODELS_DIR,
            self.WHISPER_MODEL_DIR,
            self.SENTENCE_TRANSFORMERS_DIR,
            self.LLM_MODEL_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _init_device(self):
        """初始化设备配置"""
        import torch
        
        # 检查CUDA可用性
        self.CUDA_AVAILABLE = torch.cuda.is_available()
        self.CUDA_DEVICE_COUNT = torch.cuda.device_count() if self.CUDA_AVAILABLE else 0
        
        # 检查MPS可用性（Apple Silicon）
        self.MPS_AVAILABLE = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        
        # 默认设备选择逻辑
        device_config = self.model_config.get('whisper', {}).get('device', 'auto')
        
        if device_config == 'auto':
            if self.CUDA_AVAILABLE:
                self.DEFAULT_DEVICE = 'cuda'
            elif self.MPS_AVAILABLE:
                self.DEFAULT_DEVICE = 'mps'
            else:
                self.DEFAULT_DEVICE = 'cpu'
        else:
            self.DEFAULT_DEVICE = device_config
        
        # 验证设备选择
        if self.DEFAULT_DEVICE == 'cuda' and not self.CUDA_AVAILABLE:
            print("警告: CUDA不可用，切换到CPU")
            self.DEFAULT_DEVICE = 'cpu'
        elif self.DEFAULT_DEVICE == 'mps' and not self.MPS_AVAILABLE:
            print("警告: MPS不可用，切换到CPU")
            self.DEFAULT_DEVICE = 'cpu'
        
        # GPU内存设置
        if self.CUDA_AVAILABLE:
            self.GPU_MEMORY_TOTAL = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
            self.GPU_MEMORY_RESERVED = torch.cuda.memory_reserved(0) / 1024**3  # GB
            self.GPU_MEMORY_ALLOCATED = torch.cuda.memory_allocated(0) / 1024**3  # GB
        else:
            self.GPU_MEMORY_TOTAL = 0
            self.GPU_MEMORY_RESERVED = 0
            self.GPU_MEMORY_ALLOCATED = 0
    
    def _init_logging(self):
        """初始化日志配置"""
        # 从配置文件获取日志设置
        logging_config = self.model_config.get('development', {}).get('logging', {})
        
        # 日志级别
        level_str = logging_config.get('level', 'INFO')
        self.LOG_LEVEL = getattr(logging, level_str.upper(), logging.INFO)
        
        # 日志格式
        self.LOG_FORMAT = logging_config.get(
            'format', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 日志文件路径
        log_file_name = logging_config.get('file_path', 'app.log')
        # 确保文件名不包含路径
        log_file_name = Path(log_file_name).name
        self.LOG_FILE_PATH = self.LOGS_DIR / log_file_name
        
        # 是否启用控制台输出
        self.LOG_CONSOLE_OUTPUT = logging_config.get('console_output', True)
        
        # 日志文件设置
        self.LOG_MAX_FILE_SIZE = logging_config.get('max_file_size', 100) * 1024 * 1024  # MB to bytes
        self.LOG_BACKUP_COUNT = logging_config.get('backup_count', 5)
        
        # 配置根日志记录器
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建根日志记录器
        logger = logging.getLogger()
        logger.setLevel(self.LOG_LEVEL)
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(self.LOG_FORMAT)
        
        # 文件处理器
        file_handler = RotatingFileHandler(
            self.LOG_FILE_PATH,
            maxBytes=self.LOG_MAX_FILE_SIZE,
            backupCount=self.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(self.LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        if self.LOG_CONSOLE_OUTPUT:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.LOG_LEVEL)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    def _init_cache(self):
        """初始化缓存配置"""
        # 从配置文件获取缓存设置
        cache_config = self.model_config.get('performance', {}).get('cache', {})
        
        # 缓存开关
        self.CACHE_ENABLED = cache_config.get('enabled', True)
        
        # 缓存类型
        self.CACHE_TYPE = cache_config.get('cache_type', 'disk')
        
        # 磁盘缓存路径
        self.CACHE_DISK_PATH = self.CACHE_DIR
        
        # 最大缓存大小
        self.CACHE_MAX_SIZE = cache_config.get('max_cache_size', 2048) * 1024 * 1024  # MB to bytes
        
        # 缓存TTL（小时）
        self.CACHE_TTL = cache_config.get('cache_ttl', 24) * 3600  # hours to seconds
        
        # 确保缓存目录存在
        if self.CACHE_ENABLED and self.CACHE_TYPE == 'disk':
            self.CACHE_DISK_PATH.mkdir(parents=True, exist_ok=True)
    
    def _init_env_vars(self):
        """初始化环境变量"""
        # API密钥环境变量
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        self.BAIDU_APP_ID = os.getenv('BAIDU_APP_ID')
        self.BAIDU_SECRET_KEY = os.getenv('BAIDU_SECRET_KEY')
        self.YOUDAO_APP_KEY = os.getenv('YOUDAO_APP_KEY')
        self.YOUDAO_APP_SECRET = os.getenv('YOUDAO_APP_SECRET')
        
        # 系统环境变量
        self.PYTHONPATH = os.getenv('PYTHONPATH', str(self.PROJECT_ROOT))
        
        # 开发模式
        self.DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'False').lower() == 'true'
        
        # 调试模式
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    def get_model_config(self, model_type: str, key: str = None, default: Any = None) -> Any:
        """
        获取模型配置
        
        Args:
            model_type: 模型类型 (whisper, vector_store, llm等)
            key: 配置键，如果为None则返回整个模型配置
            default: 默认值
            
        Returns:
            配置值
        """
        model_config = self.model_config.get(model_type, {})
        
        if key is None:
            return model_config
        
        return model_config.get(key, default)
    
    def update_config(self, model_type: str, key: str, value: Any):
        """
        更新配置值
        
        Args:
            model_type: 模型类型
            key: 配置键
            value: 配置值
        """
        if model_type not in self.model_config:
            self.model_config[model_type] = {}
        
        self.model_config[model_type][key] = value
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.model_config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False
    
    def get_device_for_model(self, model_type: str) -> str:
        """
        根据模型类型获取推荐设备
        
        Args:
            model_type: 模型类型
            
        Returns:
            设备字符串 (cuda, mps, cpu)
        """
        device_config = self.get_model_config(model_type, 'device', 'auto')
        
        if device_config == 'auto':
            return self.DEFAULT_DEVICE
        else:
            # 验证设备可用性
            if device_config == 'cuda' and not self.CUDA_AVAILABLE:
                return 'cpu'
            elif device_config == 'mps' and not self.MPS_AVAILABLE:
                return 'cpu'
            else:
                return device_config
    
    def get_model_path(self, model_type: str, model_name: str = None) -> Path:
        """
        获取模型存储路径
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            模型路径
        """
        if model_type == 'whisper':
            return self.WHISPER_MODEL_DIR
        elif model_type == 'sentence_transformers':
            return self.SENTENCE_TRANSFORMERS_DIR
        elif model_type == 'llm':
            return self.LLM_MODEL_DIR
        else:
            return self.MODELS_DIR / model_type
    
    def get_cache_path(self, cache_type: str, cache_name: str) -> Path:
        """
        获取缓存文件路径
        
        Args:
            cache_type: 缓存类型
            cache_name: 缓存名称
            
        Returns:
            缓存文件路径
        """
        return self.CACHE_DISK_PATH / cache_type / f"{cache_name}.pkl"
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        验证API密钥是否配置
        
        Returns:
            API密钥配置状态字典
        """
        return {
            'openai': bool(self.OPENAI_API_KEY),
            'anthropic': bool(self.ANTHROPIC_API_KEY),
            'baidu': bool(self.BAIDU_APP_ID and self.BAIDU_SECRET_KEY),
            'youdao': bool(self.YOUDAO_APP_KEY and self.YOUDAO_APP_SECRET)
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        import platform
        import psutil
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total / 1024**3,  # GB
            'disk_free': psutil.disk_usage(self.PROJECT_ROOT).free / 1024**3,  # GB
            'cuda_available': self.CUDA_AVAILABLE,
            'cuda_device_count': self.CUDA_DEVICE_COUNT,
            'mps_available': self.MPS_AVAILABLE,
            'default_device': self.DEFAULT_DEVICE,
            'gpu_memory_total': self.GPU_MEMORY_TOTAL,
            'project_root': str(self.PROJECT_ROOT),
            'cache_enabled': self.CACHE_ENABLED,
            'cache_type': self.CACHE_TYPE,
            'log_level': logging.getLevelName(self.LOG_LEVEL)
        }
    
    def __str__(self) -> str:
        """返回设置的字符串表示"""
        return f"Settings(project_root={self.PROJECT_ROOT}, device={self.DEFAULT_DEVICE})"
    
    def __repr__(self) -> str:
        """返回设置的详细表示"""
        return self.__str__()


# 创建全局设置实例
settings = Settings()

# 导出常用设置
__all__ = [
    'Settings',
    'settings',
    # 路径常量
    'PROJECT_ROOT',
    'DATA_DIR',
    'MODELS_DIR',
    'TRANSCRIPTS_DIR',
    'CACHE_DIR',
    'LOGS_DIR',
    # 设备常量
    'DEFAULT_DEVICE',
    'CUDA_AVAILABLE',
    'MPS_AVAILABLE',
    # 日志常量
    'LOG_LEVEL',
    'LOG_FORMAT',
    # 缓存常量
    'CACHE_ENABLED',
    'CACHE_TYPE',
    'CACHE_TTL'
]

# 动态添加路径常量到模块命名空间
for attr in dir(settings):
    if attr.isupper() and not attr.startswith('_'):
        globals()[attr] = getattr(settings, attr)