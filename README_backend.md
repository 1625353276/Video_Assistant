# AI视频助手 - 后端系统

## 概述

AI视频助手后端系统专注于视频内容分析，提供从视频文件到结构化文本的完整处理流水线。系统采用模块化设计，支持多种视频格式，使用OpenAI Whisper进行高质量的语音转文本。

## 核心功能

- ✅ **视频格式支持**: MP4, AVI, MKV, MOV, WMV, FLV, WebM
- ✅ **视频完整性校验**: 自动检测视频文件完整性和基本信息
- ✅ **音频提取**: 从视频中提取高质量音频流
- ✅ **语音转文本**: 使用Whisper模型进行多语言语音识别
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

### 模型选择建议

| 模型 | 大小 | 速度 | 准确性 | 适用场景 |
|------|------|------|--------|----------|
| tiny | 75MB | 最快 | 基础 | 快速测试 |
| base | 142MB | 快速 | 良好 | 日常使用 |
| small | 466MB | 中等 | 较好 | 平衡选择 |
| medium | 1.5GB | 较慢 | 很好 | 高质量需求 |
| large | 2.9GB | 最慢 | 最佳 | 专业用途 |

## 输出格式

### JSON格式（推荐）

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

## 许可证

本项目采用MIT许可证，详见LICENSE文件。