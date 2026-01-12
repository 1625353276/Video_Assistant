# AI视频助手项目 - iFlow 上下文文件

## 项目概述

AI视频助手是一个基于视频内容的大模型驱动型问答系统，支持用户上传任意视频，通过多模态技术栈实现"视频内容解析-文本化转换-智能检索-对话式问答"全流程自动化，最终输出精准的视频摘要与多轮QA问答结果。

## 核心技术栈

- **视频处理**: OpenCV, FFmpeg
- **语音识别**: OpenAI Whisper (支持多语言)
- **检索系统**: 混合检索器 (向量检索 + BM25)
- **对话链**: LangChain + HuggingFace模型
- **后端框架**: Python 3.11+
- **部署**: Docker + Flask

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
│   │   └── whisper_asr.py      # Whisper语音识别
│   ├── retrieval/        # 检索系统模块
│   │   ├── vector_store.py     # 向量存储
│   │   ├── bm25_retriever.py   # BM25检索器
│   │   ├── hybrid_retriever.py # 混合检索器
│   │   └── multi_query.py      # 多查询生成
│   ├── qa/               # 问答系统模块
│   │   ├── conversation_chain.py # 对话链
│   │   ├── memory.py           # 记忆管理
│   │   └── prompt.py           # 提示模板
│   ├── text/             # 文本处理模块
│   └── utils/            # 工具模块
│       └── file_manager.py     # 文件管理
├── config/               # 配置文件
│   ├── model_config.yaml # 模型配置
│   └── settings.py       # 系统设置
├── data/                 # 数据目录
│   ├── raw_videos/       # 原始视频文件
│   └── transcripts/      # 转写结果
├── deploy/               # 部署相关
│   ├── app.py           # Flask应用
│   └── Dockerfile       # Docker配置
└── tests/               # 测试文件
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
结构化结果保存 (FileManager)
```

### 2. 智能问答流程
```
转写文本
    ↓
文本分段和向量化
    ↓
混合检索 (向量检索 + BM25)
    ↓
多查询生成
    ↓
对话链生成回答
```

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

### 4. 部署服务
```bash
# 使用Docker部署
cd deploy
docker build -t video-assistant .
docker run -p 5000:5000 video-assistant
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
  "language": "zh",
  "text": "完整的转写文本...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "第一段文本",
      "confidence": 0.95
    }
  ],
  "model_used": "base",
  "total_duration": 120.5,
  "avg_confidence": 0.92
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

## 支持的视频格式

- MP4, AVI, MKV, MOV, WMV, FLV, WebM
- 最大文件大小: 2GB
- 自动检测视频完整性和基本信息

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

## 开发指南

### 添加新功能
1. 在对应模块中实现功能
2. 更新测试脚本
3. 更新文档
4. 运行测试验证

### 代码规范
- 使用Python 3.11+类型提示
- 遵循PEP 8代码风格
- 添加详细的文档字符串
- 编写单元测试

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

## 扩展性

系统采用模块化设计，易于扩展：
- **新视频格式**: 在VideoLoader中添加格式支持
- **新音频处理**: 在AudioExtractor中添加处理逻辑
- **新输出格式**: 在FileManager中添加格式支持
- **新ASR模型**: 在WhisperASR中添加模型支持

## 注意事项

1. **首次运行**: Whisper模型会在首次使用时自动下载
2. **大文件处理**: 建议视频文件不超过2GB
3. **语言支持**: Whisper支持99种语言的自动识别
4. **隐私保护**: 所有处理都在本地完成，不会上传数据

## 许可证

本项目采用MIT许可证，详见LICENSE文件。