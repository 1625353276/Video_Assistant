# AI视频助手项目 - iFlow 上下文文件

## 项目概述

AI视频助手是一个基于视频内容的智能语音转文本和检索系统，支持用户上传任意视频，通过多模态技术栈实现"视频内容解析-音频提取-语音识别-向量检索-智能问答"全流程自动化，最终输出精准的视频转写结果、多种格式的字幕文件和基于内容的智能检索功能。

## 核心技术栈

- **视频处理**: OpenCV, FFmpeg
- **语音识别**: OpenAI Whisper (支持多语言)
- **音频处理**: FFmpeg-python
- **文本向量化**: Sentence-Transformers (all-MiniLM-L6-v2)
- **向量检索**: NumPy, SciPy
- **后端框架**: Python 3.10+
- **机器学习**: PyTorch, Transformers, HuggingFace Hub
- **文本翻译**: Googletrans
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
├── .gitignore             # Git忽略文件配置
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
│   │   └── translator.py       # 文本翻译
│   ├── retrieval/        # 检索系统模块
│   │   ├── vector_store.py     # 向量存储 ✅
│   │   ├── bm25_retriever.py   # BM25检索器 ⏳
│   │   ├── hybrid_retriever.py # 混合检索器 ⏳
│   │   └── multi_query.py      # 多查询生成 ⏳
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
├── models/               # 模型缓存目录
│   └── sentence-transformers/  # 向量模型文件
├── deploy/               # 部署相关(待开发)
│   ├── app.py           # Flask应用
│   └── Dockerfile       # Docker配置
└── tests/               # 测试文件
    ├── test_asr.py      # ASR测试
    ├── test_qa.py       # QA测试(待开发)
    ├── test_retrieval.py # 检索测试(待开发)
    └── test_vector_store.py # 向量存储测试 ✅
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

### 2. 向量检索流程 (新增)
```
JSON转写数据
    ↓
文本分段和向量化 (VectorStore)
    ↓
向量索引构建和保存
    ↓
语义相似度检索
    ↓
返回相关内容片段和时间戳
```

### 3. 智能问答流程 (规划中)
```
用户查询
    ↓
检索相关内容 (VectorStore + BM25)
    ↓
多查询生成 (MultiQuery)
    ↓
结果融合 (HybridRetriever)
    ↓
LLM生成回答 (QA模块)
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
# 运行基础流水线测试
python test_pipeline.py

# 运行向量存储测试
python tests/test_vector_store.py
```

### 4. 向量检索使用
```python
from modules.retrieval.vector_store import VectorStore

# 创建向量存储
vector_store = VectorStore()

# 加载转写数据并建立索引
with open('data/transcripts/video_transcript.json', 'r') as f:
    transcript_data = json.load(f)

# 提取文本片段
documents = []
for segment in transcript_data['segments']:
    documents.append({
        'text': segment['text'],
        'start': segment['start'],
        'end': segment['end'],
        'confidence': segment['confidence']
    })

# 添加到向量存储
vector_store.add_documents(documents)

# 检索相关内容
results = vector_store.search("智能手机定位原理", top_k=5)

# 保存索引以供后续使用
vector_store.save_index("data/vector_index.pkl")
```

## 模型选择指南

### Whisper语音识别模型
| 模型 | 大小 | 速度 | 准确性 | 适用场景 |
|------|------|------|--------|----------|
| tiny | 75MB | 最快 | 基础 | 快速测试 |
| base | 142MB | 快速 | 良好 | 日常使用 |
| small | 466MB | 中等 | 较好 | 平衡选择 |
| medium | 1.5GB | 较慢 | 很好 | 高质量需求 |
| large | 2.9GB | 最慢 | 最佳 | 专业用途 |

### 向量化模型
| 模型 | 大小 | 向量维度 | 特点 | 适用场景 |
|------|------|----------|------|----------|
| all-MiniLM-L6-v2 | 90MB | 384 | 轻量级，多语言 | 通用语义检索 |
| paraphrase-MiniLM-L6-v2 | 80MB | 384 | 专门优化句子相似度 | 相似度匹配 |

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

## 向量检索功能

### 检索结果格式
```python
[
    {
        'text': '相关的文本内容',
        'start': 10.5,
        'end': 15.2,
        'confidence': 0.92,
        'similarity': 0.85,
        'metadata': {...}
    },
    ...
]
```

### 索引管理
```python
# 保存索引
vector_store.save_index("data/vector_index.pkl")

# 加载索引
vector_store.load_index("data/vector_index.pkl")

# 获取统计信息
stats = vector_store.get_stats()
print(f"文档数量: {stats['document_count']}")
print(f"向量维度: {stats['vector_dimension']}")
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

### 向量检索优化
- 模型缓存到项目本地目录 (models/)
- 支持向量索引持久化存储
- 批量文本向量化处理
- 余弦相似度高效计算

## 开发指南

### 项目当前状态
- **已完成**: 视频处理、音频提取、Whisper语音识别、多格式输出、向量存储和检索
- **开发中**: 多模态优化、文本处理、BM25检索器、多查询生成、混合检索器
- **待开发**: 问答系统、Web部署、配置文件完善

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

5. **问题解决规范**
   - 解决bug、环境问题或依赖冲突时，必须先制定解决计划并告知
   - 修改系统配置、依赖版本或核心文件前需获得批准
   - 紧急问题处理需记录操作步骤，事后补充文档和测试
   - 任何临时解决方案都应有明确的后续处理计划

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
   错误: 模型下载失败
   解决: 检查网络连接，或手动下载模型到缓存目录
   ```

5. **向量检索慢**
   ```
   问题: 大量文档检索速度慢
   解决: 考虑使用BM25检索或混合检索
   ```

## 扩展性

系统采用模块化设计，易于扩展：
- **新视频格式**: 在VideoLoader中添加格式支持
- **新音频处理**: 在AudioExtractor中添加处理逻辑
- **新输出格式**: 在FileManager中添加格式支持
- **新ASR模型**: 在WhisperASR中添加模型支持
- **文本处理**: 在text模块中添加清理、分段、翻译功能
- **检索系统**: 在retrieval模块中实现BM25检索、多查询生成、混合检索
- **问答系统**: 在qa模块中实现对话链和记忆管理

## 注意事项

1. **首次运行**: Whisper模型和Sentence-Transformers模型会在首次使用时自动下载
2. **模型存储**: 模型文件保存到项目的models目录，便于管理和部署
3. **大文件处理**: 建议视频文件不超过2GB
4. **语言支持**: Whisper支持99种语言的自动识别
5. **隐私保护**: 所有处理都在本地完成，不会上传数据
6. **临时文件**: 系统会自动清理临时音频文件
7. **GPU支持**: 自动检测并使用GPU加速（如果可用）
8. **Git忽略**: 模型文件和转写结果已配置.gitignore，不会上传到版本控制

## 项目进展总结

### ✅ 已完成的核心功能

#### 向量存储模块 (VectorStore)
- **文本向量化**: 使用sentence-transformers/all-MiniLM-L6-v2模型，384维向量表示
- **向量检索**: 基于余弦相似度的语义搜索，支持top-k和阈值过滤
- **索引管理**: 支持向量索引的保存/加载，使用pickle格式持久化
- **模型缓存**: 模型文件自动保存到项目本地目录(87.4MB)
- **镜像支持**: 多镜像站点配置，默认使用官方源，支持手动切换

#### 项目管理
- **Git配置**: 完善的.gitignore规则，忽略模型文件、__pycache__和转写结果
- **依赖管理**: requirements.txt包含所有必需依赖，版本固定确保稳定性
- **文档更新**: IFLOW.md完整反映项目当前状态和架构

### 📊 项目当前状态

#### 已完成模块
- ✅ 视频处理 (VideoLoader, AudioExtractor) - 完整实现并测试
- ✅ 语音识别 (WhisperASR) - 支持多种模型，GPU/CPU自动检测
- ✅ 文件管理 (FileManager) - 多格式输出，JSON/TXT/SRT/VTT
- ✅ 向量存储 (VectorStore) - 完整实现，支持JSON转写数据检索

#### 待开发模块
- ⏳ BM25检索器 (bm25_retriever.py) - 关键词匹配检索
- ⏳ 多查询生成 (multi_query.py) - 查询扩展和多样化
- ⏳ 混合检索器 (hybrid_retriever.py) - 向量和BM25结果融合
- ⏳ QA系统模块 - 对话链、记忆管理、提示模板
- ⏳ 配置文件完善 - 模型配置、系统设置

### 🔧 技术栈配置

#### 核心依赖
- **PyTorch 2.5.0+**: 深度学习框架，支持GPU加速
- **Sentence-Transformers**: 文本向量化，多语言支持
- **OpenAI Whisper**: 语音识别，99种语言自动检测
- **FFmpeg**: 音视频处理，格式转换和提取
- **SciPy**: 向量计算，相似度计算优化

#### 模型文件
- **Whisper模型**: tiny/base/small/medium/large，按需下载
- **向量模型**: all-MiniLM-L6-v2 (87.4MB)，已下载到models目录

### 🎯 开发流程规范

#### 遵循的原则
1. **TodoList审查**: 所有开发前必须提供详细计划供审查
2. **逐步开发**: 严格按步骤完成，每步等待审查确认
3. **测试驱动**: 完成功能模块后编写单元测试
4. **变更审批**: 重要操作需提前告知并获得同意
5. **问题解决**: Bug修复和环境问题也需遵循规范

### 📁 项目结构
```
Video_Assistant/
├── modules/retrieval/vector_store.py ✅
├── modules/video/ ✅
├── modules/speech/ ✅
├── modules/utils/ ✅
├── models/sentence-transformers/ ✅
├── data/transcripts/ ✅
├── .gitignore ✅
└── IFLOW.md ✅
```

### 🚀 下一步建议

基于当前进度，建议按优先级继续开发：

1. **高优先级**: BM25检索器实现 - 关键词匹配补充向量检索
2. **中优先级**: 多查询生成和混合检索 - 提高检索准确性
3. **低优先级**: QA系统模块和配置文件完善

### 💡 重要经验教训

1. **开发规范的重要性**: 避免了随意修改文件和版本控制问题
2. **依赖版本管理**: 需要特别注意版本兼容性，如httpx与googletrans冲突
3. **模型缓存策略**: 本地缓存提高了部署便利性和离线使用能力
4. **Git忽略配置**: 避免大文件上传到版本控制，保持仓库清洁

## 许可证

本项目采用MIT许可证，详见LICENSE文件。