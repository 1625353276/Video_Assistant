# 测试目录说明

## 测试文件列表

### 核心模块测试
- `test_vector_store.py` - 向量存储模块测试
- `test_bm25_retriever.py` - BM25检索器测试
- `test_hybrid_retriever.py` - 混合检索器测试
- `test_multi_query.py` - 多查询生成器测试

### 集成测试
- `test_local_model.py` - 本地模型加载测试
- `test_pipeline.py` - 基础流水线测试
- `test_qa_integration.py` - QA系统集成测试
- `test_complete_qa_flow.py` - 完整QA流程测试
- `test_qa_system.py` - QA系统全面测试
- `test_retrieval_integration.py` - 检索系统集成测试
- `test_llm_api.py` - LLM API测试

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

## 测试顺序建议

1. 首先运行核心模块测试确保基础功能正常
2. 然后运行集成测试验证系统整体功能
3. 最后运行完整流程测试确保端到端功能正常

## 注意事项

- 测试文件已修复路径问题，可以直接在tests目录中运行
- 所有测试都依赖项目根目录的配置和模块
- 建议在运行测试前确保环境配置正确