# 测试目录说明

## 测试文件列表

### 核心模块测试
- `test_vector_store.py` - 向量存储模块测试
- `test_bm25_retriever.py` - BM25检索器测试
- `test_hybrid_retriever.py` - 混合检索器测试
- `test_multi_query.py` - 多查询生成器测试
- `test_video_cleaner.py` - 视频清理模块测试

### 集成测试
- `test_pipeline.py` - 基础流水线测试
- `test_qa_integration.py` - QA系统集成测试
- `test_retrieval_integration.py` - 检索系统集成测试
- `test_transcript_flow.py` - 转写流程测试

### 系统功能测试
- `test_complete_qa_flow.py` - 完整QA流程测试
- `test_qa_system.py` - QA系统全面测试
- `test_simple_conversation.py` - 简单对话测试
- `test_llm_api.py` - LLM API测试

### 测试工具
- `run_tests.py` - 批量测试运行脚本
- `data/` - 测试数据目录

## 运行测试

### 运行所有测试
```bash
cd tests
python run_tests.py
```

### 运行单个测试
```bash
cd tests
python test_vector_store.py
```

### 按分类运行测试

#### 核心模块测试
```bash
cd tests
python test_vector_store.py
python test_bm25_retriever.py
python test_hybrid_retriever.py
python test_multi_query.py
python test_video_cleaner.py
```

#### 集成测试
```bash
cd tests
python test_pipeline.py
python test_qa_integration.py
python test_retrieval_integration.py
python test_transcript_flow.py
```

#### 系统功能测试
```bash
cd tests
python test_complete_qa_flow.py
python test_qa_system.py
python test_simple_conversation.py
python test_llm_api.py
```

## 测试顺序建议

1. **核心模块测试** - 首先运行确保基础功能正常
   - test_vector_store.py
   - test_bm25_retriever.py
   - test_hybrid_retriever.py
   - test_multi_query.py
   - test_video_cleaner.py

2. **集成测试** - 验证模块间协作
   - test_pipeline.py
   - test_qa_integration.py
   - test_retrieval_integration.py
   - test_transcript_flow.py

3. **系统功能测试** - 验证端到端功能
   - test_complete_qa_flow.py
   - test_qa_system.py
   - test_simple_conversation.py
   - test_llm_api.py

## 注意事项

- 测试文件已修复路径问题，可以直接在tests目录中运行
- 所有测试都依赖项目根目录的配置和模块
- 建议在运行测试前确保环境配置正确
- 部分测试需要网络连接（如LLM API测试）
- 测试数据存储在 `data/` 目录中
- 运行完整测试套件前请确保模型文件已下载到 `models/` 目录