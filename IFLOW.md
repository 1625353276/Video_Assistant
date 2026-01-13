# AI视频助手项目 - iFlow 上下文文件

## 项目概述

AI视频助手是一个基于视频内容的智能语音转文本系统，支持用户上传任意视频，通过多模态技术栈实现"视频内容解析-音频提取-语音识别-多格式输出"全流程自动化，最终输出精准的视频转写结果和多种格式的字幕文件。

## 核心技术栈

- **视频处理**: OpenCV, FFmpeg
- **语音识别**: OpenAI Whisper (支持多语言)
- **音频处理**: FFmpeg-python
- **后端框架**: Python 3.10+
- **部署**: Docker + Flask (待完善)

## 项目结构

```
Video_Assistant/
├── main.py                 # 主程序入口 - 视频到文本处理流水线
├── test_pipeline.py        # 后端流程测试脚本
├── requirements.txt        # Python依赖包列表
├── README.md              # 项目说明文档
├── README_backend.md      # 后端系统详细文档
├── 项目介绍.md             # 中文项目介绍
├── modules/               # 核心功能模块
│   ├── video/            # 视频处理模块
│   │   ├── video_loader.py     # 视频加载和验证
│   │   └── audio_extractor.py  # 音频提取
│   ├── speech/           # 语音识别模块
│   │   ├── whisper_asr.py      # Whisper语音识别
│   │   └── multimodal_refine.py # 多模态优化(待开发)
│   ├── text/             # 文本处理模块
│   │   ├── segmenter.py        # 文本分段
│   │   ├── text_cleaner.py     # 文本清理
│   │   └── translator.py       # 文本翻译(待开发)
│   ├── retrieval/        # 检索系统模块(待开发)
│   │   ├── vector_store.py     # 向量存储
│   │   ├── bm25_retriever.py   # BM25检索器
│   │   ├── hybrid_retriever.py # 混合检索器
│   │   └── multi_query.py      # 多查询生成
│   ├── qa/               # 问答系统模块(待开发)
│   │   ├── conversation_chain.py # 对话链
│   │   ├── memory.py           # 记忆管理
│   │   └── prompt.py           # 提示模板
│   └── utils/            # 工具模块
│       ├── file_manager.py     # 文件管理
│       ├── file_utils.py       # 文件工具
│       └── logger.py           # 日志管理
├── config/               # 配置文件
│   ├── model_config.yaml # 模型配置(待完善)
│   └── settings.py       # 系统设置(待完善)
├── data/                 # 数据目录
│   ├── raw_videos/       # 原始视频文件
│   └── transcripts/      # 转写结果
├── deploy/               # 部署相关(待开发)
│   ├── app.py           # Flask应用
│   └── Dockerfile       # Docker配置
└── tests/               # 测试文件
    ├── test_asr.py      # ASR测试
    ├── test_qa.py       # QA测试(待开发)
    └── test_retrieval.py # 检索测试(待开发)
```

## 核心功能流程

### 1. 视频处理流水线
```
视频文件输入
    ↓
视频合法性校验 (VideoLoader)
    ↓
音频提取 (AudioExtractor)
    ↓
Whisper语音识别 (WhisperASR)
    ↓
多格式结果保存 (FileManager)
```

### 2. 输出格式支持
- JSON格式：结构化数据，包含分段和时间戳
- TXT格式：纯文本，便于阅读
- SRT格式：标准字幕文件
- VTT格式：Web视频字幕格式

## 安装和运行

### 1. 环境准备
```bash
# 创建conda环境 (推荐)
conda create -n video_assistant python=3.10
conda activate video_assistant

# 安装依赖
pip install -r requirements.txt

# 安装系统依赖 (FFmpeg)
# Windows: 下载并添加到PATH
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

### 2. 基本使用
```bash
# 处理单个视频文件
python main.py --video /path/to/video.mp4 --model base

# 指定输出目录
python main.py --video /path/to/video.mp4 --output ./output

# 使用不同大小的模型
python main.py --video /path/to/video.mp4 --model small
```

### 3. 测试系统
```bash
# 运行测试脚本
python test_pipeline.py
```

## 模型选择指南

| 模型 | 大小 | 速度 | 准确性 | 适用场景 |
|------|------|------|--------|----------|
| tiny | 75MB | 最快 | 基础 | 快速测试 |
| base | 142MB | 快速 | 良好 | 日常使用 |
| small | 466MB | 中等 | 较好 | 平衡选择 |
| medium | 1.5GB | 较慢 | 很好 | 高质量需求 |
| large | 2.9GB | 最慢 | 最佳 | 专业用途 |

## 输出格式

### JSON格式 (推荐)
```json
{
  "audio_file": "video.mp4",
  "audio_file_name": "video.mp4",
  "language": "zh",
  "language_probability": 0.95,
  "text": "完整的转写文本...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "第一段文本",
      "confidence": 0.95,
      "no_speech_prob": 0.01,
      "words": []
    }
  ],
  "words": [],
  "model_used": "base",
  "device_used": "cuda",
  "total_duration": 120.5,
  "avg_confidence": 0.92,
  "speech_duration": 115.3,
  "speech_ratio": 0.957,
  "export_info": {
    "export_time": "2024-01-12T16:06:00",
    "export_format": "json",
    "export_version": "1.0"
  }
}
```

### 文本格式
```
==================================================
AI视频助手 - 转写结果
==================================================
文件: video.mp4
语言: zh
模型: base
总时长: 120.5 秒
平均置信度: 0.92
导出时间: 2024-01-12 16:06:00
==================================================

【完整转写文本】
完整的转写文本...

【分段转写文本】
------------------------------
段落 1 [00:00 - 00:05]
第一段文本
置信度: 0.95
```

### SRT格式
```
1
00:00:00,000 --> 00:00:05,200
第一段文本

2
00:00:05,200 --> 00:00:10,400
第二段文本
```

### VTT格式
```
WEBVTT

00:00:00.000 --> 00:00:05.200
第一段文本

00:00:05.200 --> 00:00:10.400
第二段文本
```

## 支持的视频格式

- MP4, AVI, MKV, MOV, WMV, FLV, WebM
- 最大文件大小: 2GB
- 自动检测视频完整性和基本信息
- 支持多种视频编码格式: H264, H265, AVC, HEVC, VP9, AV1

## 性能优化

### GPU加速
系统自动检测并使用可用的计算设备：
- CUDA (NVIDIA GPU)
- MPS (Apple Silicon GPU)
- CPU (默认)

### 内存管理
- 自动清理临时文件
- 模型按需加载和卸载
- GPU内存缓存管理
- 支持大文件分块处理

## 开发指南

### 项目当前状态
- **已完成**: 视频处理、音频提取、Whisper语音识别、多格式输出
- **开发中**: 多模态优化、文本处理
- **待开发**: 检索系统、问答系统、Web部署

### 添加新功能
1. 在对应模块中实现功能
2. 更新测试脚本
3. 更新文档
4. 运行测试验证

### 代码规范
- 使用Python 3.10+类型提示
- 遵循PEP 8代码风格
- 添加详细的文档字符串
- 编写单元测试

### 开发规范
为确保项目开发质量和可维护性，所有开发工作必须遵循以下规范：

1. **TodoList审查制度**
   - 开发前必须先提供详细的TodoList供审查
   - TodoList应包含明确的任务分解和优先级
   - 未经审查确认不得开始开发工作

2. **逐步开发原则**
   - 严格按照TodoList逐步完成，不得跳步或并行处理多个任务
   - 每完成一个TodoList项后需等待审查确认
   - 确保每个步骤都可追溯和验证，防止错误堆积

3. **单元测试要求**
   - 每完成一定功能模块后必须编写单元测试
   - 测试应覆盖核心功能和边界情况
   - 采用产品级测试标准，确保代码质量

4. **变更审批流程**
   - 创建新脚本或文件前必须提前告知并获取批准
   - 重要操作和修改需事先说明并获得同意
   - 所有变更都应有明确的开发目的和预期效果

### 常见问题解决

1. **ffmpeg未找到**
   ```
   错误: ffmpeg未找到，请确保已安装ffmpeg
   解决: 按照安装说明安装ffmpeg
   ```

2. **内存不足**
   ```
   错误: CUDA内存不足
   解决: 使用更小的模型或切换到CPU模式
   ```

3. **视频格式不支持**
   ```
   错误: 不支持的视频格式
   解决: 使用支持的视频格式或添加格式支持
   ```

4. **模型下载失败**
   ```
   错误: Whisper模型下载失败
   解决: 检查网络连接，或手动下载模型到缓存目录
   ```

## 扩展性

系统采用模块化设计，易于扩展：
- **新视频格式**: 在VideoLoader中添加格式支持
- **新音频处理**: 在AudioExtractor中添加处理逻辑
- **新输出格式**: 在FileManager中添加格式支持
- **新ASR模型**: 在WhisperASR中添加模型支持
- **文本处理**: 在text模块中添加清理、分段、翻译功能
- **检索系统**: 在retrieval模块中实现向量检索和BM25检索
- **问答系统**: 在qa模块中实现对话链和记忆管理

## 注意事项

1. **首次运行**: Whisper模型会在首次使用时自动下载
2. **大文件处理**: 建议视频文件不超过2GB
3. **语言支持**: Whisper支持99种语言的自动识别
4. **隐私保护**: 所有处理都在本地完成，不会上传数据
5. **临时文件**: 系统会自动清理临时音频文件
6. **GPU支持**: 自动检测并使用GPU加速（如果可用）

## 许可证

本项目采用MIT许可证，详见LICENSE文件。