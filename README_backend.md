# AI视频助手 - 后端系统

## 概述

AI视频助手后端系统专注于视频内容分析，提供从视频文件到结构化文本的完整处理流水线。系统采用模块化设计，支持多种视频格式，使用OpenAI Whisper进行高质量的语音转文本。

## 核心功能

- ✅ **视频格式支持**: MP4, AVI, MKV, MOV, WMV, FLV, WebM
- ✅ **视频完整性校验**: 自动检测视频文件完整性和基本信息
- ✅ **音频提取**: 从视频中提取高质量音频流
- ✅ **语音转文本**: 使用Whisper模型进行多语言语音识别
- ✅ **文本清洗**: 去除口语填充词、重复句、异常符号，规范化标点
- ✅ **智能分段**: 支持按句子、时间戳、token数、语义等多种分段策略
- ✅ **多语言翻译**: 解决视频语言与模型语言不匹配问题，支持中英文互译
- ✅ **结构化输出**: 支持JSON、TXT、SRT、VTT多种输出格式
- ✅ **时间戳保留**: 精确的词级别和段落级别时间戳

## 系统架构

```
视频文件输入
    ↓
视频合法性校验 (VideoLoader)
    ↓
音频提取 (AudioExtractor)
    ↓
Whisper语音识别 (WhisperASR)
    ↓
文本清洗 (TextCleaner)
    ↓
文本分段 (TextSegmenter)
    ↓
文本翻译 (TextTranslator)
    ↓
结构化结果保存 (FileManager)
```

## 安装依赖

### 1. Python依赖

```bash
pip install -r requirements.txt
```

### 2. 系统依赖

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
1. 下载FFmpeg: https://ffmpeg.org/download.html
2. 解压并添加到系统PATH

## 使用方法

### 基本用法

```bash
python main.py --video /path/to/your/video.mp4 --model base
```

### 参数说明

- `--video`: 输入视频文件路径（必需）
- `--output`: 输出目录路径（默认: data/transcripts）
- `--model`: Whisper模型大小（默认: base）
  - 可选值: tiny, base, small, medium, large
- `--no-clean`: 跳过文本清洗步骤
- `--no-segment`: 跳过文本分段步骤
- `--no-translate`: 跳过文本翻译步骤
- `--target-lang`: 翻译目标语言（默认: en）
  - 可选值: zh, en
- `--max-tokens`: 分段最大token数（默认: 400）

### 模型选择建议

| 模型 | 大小 | 速度 | 准确性 | 适用场景 |
|------|------|------|--------|----------|
| tiny | 75MB | 最快 | 基础 | 快速测试 |
| base | 142MB | 快速 | 良好 | 日常使用 |
| small | 466MB | 中等 | 较好 | 平衡选择 |
| medium | 1.5GB | 较慢 | 很好 | 高质量需求 |
| large | 2.9GB | 最慢 | 最佳 | 专业用途 |

## 输出格式

系统会生成多个处理阶段的文件：

### 1. 原始转录结果 (original.json)
Whisper直接输出的原始转录结果，包含完整的语音识别信息。

### 2. 清洗后结果 (cleaned.json)
经过TextCleaner处理后的结果，去除了口语填充词和异常符号：

```json
{
  "audio_file": "video.mp4",
  "language": "zh",
  "text": "清洗后的转写文本...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "清洗后的第一段文本",
      "confidence": 0.95
    }
  ],
  "model_used": "base",
  "total_duration": 120.5,
  "avg_confidence": 0.92
}
```

### 3. 翻译后结果 (translated.json)
经过TextTranslator翻译后的结果，用于embedding模型或跨语言问答：

```json
{
  "audio_file": "video.mp4",
  "language": "zh",
  "text": "Translated text...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Translated first segment",
      "confidence": 0.95,
      "translation_metadata": {
        "original_text": "清洗后的第一段文本",
        "source_lang": "zh",
        "target_lang": "en",
        "method": "googletrans"
      }
    }
  ],
  "model_used": "base",
  "total_duration": 120.5,
  "avg_confidence": 0.92,
  "translation_metadata": {
    "original_text": "清洗后的转写文本...",
    "source_lang": "zh",
    "target_lang": "en",
    "method": "deep-translator"
  }
}
```

### 4. 分段结果 (segments.json)
TextSegmenter的分段结果，包含详细的分段信息和统计数据：

```json
{
  "segments": [
    {
      "segment_id": 0,
      "text": "第一段文本内容...",
      "start_time": 0.0,
      "end_time": 30.5,
      "token_count": 385
    },
    {
      "segment_id": 1,
      "text": "第二段文本内容...",
      "start_time": 30.5,
      "end_time": 65.2,
      "token_count": 412
    }
  ],
  "statistics": {
    "total_segments": 5,
    "total_tokens": 1856,
    "avg_tokens_per_segment": 371.2,
    "min_tokens": 256,
    "max_tokens": 458,
    "has_timestamps": true
  }
}
```

### 5. 清洗文本文件 (cleaned.txt)
纯文本格式的清洗后结果，便于阅读和进一步处理。

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

### SRT/VTT字幕格式

支持标准的SRT和VTT字幕格式，可直接用于视频播放器。

## 测试系统

运行测试脚本验证系统功能：

```bash
python test_pipeline.py
```

测试脚本会检查：
- 依赖项安装状态
- 各模块基本功能
- 文件输出格式

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

## 错误处理

系统包含完善的错误处理机制：

- **视频格式错误**: 不支持的格式会给出明确提示
- **文件损坏检测**: 自动检测视频文件完整性
- **内存不足**: 自动降级到CPU模式
- **网络错误**: 模型下载失败的重试机制

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

## 故障排除

### 常见问题

1. **ffmpeg未找到**
   ```
   错误: ffmpeg未找到，请确保已安装ffmpeg
   解决: 按照上述说明安装ffmpeg
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

### 日志查看

系统使用Python logging模块，可通过环境变量控制日志级别：

```bash
export PYTHONPATH=/path/to/project
python main.py --video video.mp4
```

## 开发指南

### 项目结构

```
AI_Video_Assistant/
├── main.py                 # 主程序入口
├── modules/
│   ├── video/
│   │   ├── video_loader.py     # 视频处理服务
│   │   └── audio_extractor.py  # 音频提取模块
│   ├── speech/
│   │   └── whisper_asr.py      # Whisper语音识别
│   ├── text/                   # 文本处理模块
│   │   ├── text_cleaner.py     # 文本清洗模块
│   │   ├── segmenter.py        # 文本分段模块
│   │   └── translator.py       # 翻译模块
│   └── utils/
│       └── file_manager.py     # 文件管理工具
├── data/                    # 数据目录
│   ├── raw_videos/          # 原始视频
│   ├── audio/               # 临时音频
│   └── transcripts/         # 转写结果
├── config/                  # 配置文件
└── tests/                   # 测试文件
```

### 添加新功能

1. 在对应模块中实现功能
2. 更新测试脚本
3. 更新文档
4. 运行测试验证

## Text模块详解

### TextCleaner - 文本清洗模块

**功能**：对语音识别生成的文本进行清洗和规范化

**主要处理内容**：
- 去除口语填充词（"呃""嗯""那个"等）
- 去掉重复句
- 去掉异常符号
- 基本标点规范化

**使用示例**：
```python
from modules.text import TextCleaner

cleaner = TextCleaner()
cleaned_text = cleaner.clean_text("嗯我们今天主要讲一下深度学习啊")
# 输出: "我们今天主要讲解深度学习。"
```

### TextSegmenter - 文本分段模块

**功能**：将长文本切分成适合模型处理的小段

**支持的分段策略**：
- 按句子分段
- 按时间戳分段（基于Whisper转录结果）
- 按固定token长度分段
- 智能语义分段
- 混合分段策略

**使用示例**：
```python
from modules.text import TextSegmenter

segmenter = TextSegmenter(max_tokens=400)
segments = segmenter.hybrid_segment(text, transcript)
```

### TextTranslator - 翻译模块

**功能**：解决视频语言与模型语言不匹配问题

**支持场景**：
- 中文视频 + 英文embedding模型
- 英文视频 + 中文问答系统

**使用示例**：
```python
from modules.text import TextTranslator

translator = TextTranslator()
result = translator.translate("深度学习", target_lang="en")
# 输出: "deep learning"
```

### 完整使用流程

```python
from modules.text import TextCleaner, TextSegmenter, TextTranslator

# 初始化
cleaner = TextCleaner()
segmenter = TextSegmenter(max_tokens=400)
translator = TextTranslator()

# 处理流程
# 1. 清洗文本
cleaned_transcript = cleaner.clean_transcript(transcript_result)

# 2. 文本分段
segments = segmenter.hybrid_segment(
    cleaned_transcript.get("text", ""), 
    cleaned_transcript
)

# 3. 翻译文本
translated_transcript = translator.translate_transcript(
    cleaned_transcript, 
    target_lang="en"
)
```

### 高级配置

#### 自定义填充词
```python
cleaner = TextCleaner()
cleaner.filler_words.extend(["你知道", "就是说"])  # 添加自定义填充词
cleaner.filler_pattern = cleaner._build_filler_pattern()  # 重建正则表达式
```

#### 分段策略选择
```python
# 按句子分段，每段最多3个句子
segments = segmenter.segment_by_sentences(text, max_sentences=3)

# 按时间戳分段，每段最多30秒
segments = segmenter.segment_by_timestamp(transcript, max_duration=30.0)

# 按token分段，每段最多500个token
segments = segmenter.segment_by_tokens(text, max_tokens=500)

# 按语义分段，相似度阈值0.3
segments = segmenter.segment_by_semantic(text, similarity_threshold=0.3)
```

#### 翻译配置
```python
# 使用Google翻译
translator = TextTranslator(default_method="deep-translator")

# 使用模拟翻译（用于测试）
translator = TextTranslator(default_method="mock")

# 加载/保存翻译缓存
translator.load_translation_cache("cache.json")
translator.save_translation_cache("cache.json")
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。