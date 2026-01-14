# QA系统API接口文档

## 概述

AI视频助手QA系统提供完整的问答功能，支持基于视频内容的智能对话。本文档详细描述了系统的API接口、使用方法和示例代码。

## 核心模块

### 1. 对话链 (ConversationChain)

负责管理整个问答流程，包括检索、记忆管理和LLM调用。

#### 初始化

```python
from modules.qa import ConversationChain, Memory, PromptTemplate

# 创建记忆管理器
memory = Memory(memory_type="buffer")

# 创建提示模板
prompt_template = PromptTemplate()

# 创建对话链
conversation_chain = ConversationChain(
    memory=memory,
    prompt_template=prompt_template
)
```

#### 主要方法

##### chat(query, top_k=5)

执行问答对话。

**参数：**
- `query` (str): 用户问题
- `top_k` (int): 检索返回的文档数量，默认5

**返回：**
```python
{
    'response': str,        # LLM生成的回答
    'retrieved_docs': list, # 检索到的文档列表
    'session_id': str,      # 会话ID
    'timestamp': str        # 时间戳
}
```

**示例：**
```python
result = conversation_chain.chat("什么是人工智能？")
print(result['response'])
```

##### set_retriever(retriever)

设置检索器。

**参数：**
- `retriever`: 检索器实例 (VectorStore, BM25Retriever, HybridRetriever)

**示例：**
```python
from modules.retrieval.hybrid_retriever import HybridRetriever

# 创建混合检索器
retriever = HybridRetriever(
    vector_store=vector_store,
    bm25_retriever=bm25_retriever,
    vector_weight=0.6,
    bm25_weight=0.4
)

# 设置到对话链
conversation_chain.set_retriever(retriever)
```

### 2. 记忆管理 (Memory)

负责管理对话历史和上下文记忆。

#### 初始化

```python
from modules.qa import Memory

# 创建记忆管理器
memory = Memory(memory_type="buffer")  # 支持 "buffer" | "file"
```

#### 主要方法

##### add_exchange(user_input, ai_response)

添加对话记录。

**参数：**
- `user_input` (str): 用户输入
- `ai_response` (str): AI回答

**示例：**
```python
memory.add_exchange("什么是人工智能？", "人工智能是计算机科学的一个分支...")
```

##### get_history(limit=10)

获取对话历史。

**参数：**
- `limit` (int): 返回的历史记录数量

**返回：**
```python
[
    {"user": str, "ai": str, "timestamp": str},
    ...
]
```

##### clear()

清空记忆。

### 3. 提示模板 (PromptTemplate)

管理LLM的提示模板和few-shot示例。

#### 初始化

```python
from modules.qa import PromptTemplate

prompt_template = PromptTemplate()
```

#### 主要方法

##### build_system_prompt(video_info="", custom_instructions="")

构建系统提示。

**参数：**
- `video_info` (str): 视频相关信息
- `custom_instructions` (str): 自定义指令

**返回：**
- `str`: 构建的系统提示

### 4. 向量存储 (VectorStore)

基于sentence-transformers的语义检索。

#### 初始化

```python
from modules.retrieval.vector_store import VectorStore

vector_store = VectorStore(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    mirror_site="tuna"  # 可选: "official" | "tuna" | "bfsu"
)
```

#### 主要方法

##### add_documents(documents, text_field="text")

添加文档到向量存储。

**参数：**
- `documents` (list): 文档列表
- `text_field` (str): 文档中文本字段名

**示例：**
```python
documents = [
    {"text": "人工智能是计算机科学的一个分支", "id": 1},
    {"text": "机器学习是人工智能的子领域", "id": 2}
]
vector_store.add_documents(documents)
```

##### search(query, top_k=5, threshold=0.0)

语义搜索。

**参数：**
- `query` (str): 查询文本
- `top_k` (int): 返回结果数量
- `threshold` (float): 相似度阈值

**返回：**
```python
[
    {
        'document': dict,    # 文档内容
        'similarity': float  # 相似度分数
    },
    ...
]
```

##### save_index(file_path)

保存索引到文件。

##### load_index(file_path)

从文件加载索引。

### 5. BM25检索器 (BM25Retriever)

基于BM25算法的关键词检索。

#### 初始化

```python
from modules.retrieval.bm25_retriever import BM25Retriever

bm25_retriever = BM25Retriever(
    k1=1.2,           # BM25参数
    b=0.75,           # BM25参数
    language='auto'   # 'zh' | 'en' | 'auto'
)
```

#### 主要方法

##### add_documents(documents, text_field="text")

添加文档到BM25索引。

##### search(query, top_k=5)

关键词搜索。

**返回：**
```python
[
    {
        'document': dict,  # 文档内容
        'score': float      # BM25分数
    },
    ...
]
```

### 6. 多查询生成器 (MultiQueryGenerator)

生成多个查询以提高检索效果。

#### 初始化

```python
from modules.retrieval.multi_query import MultiQueryGenerator

multi_query = MultiQueryGenerator(
    max_queries=10,     # 最大生成查询数量
    cache_dir="models"   # 模型缓存目录
)
```

#### 主要方法

##### generate_queries(query)

生成多个查询。

**参数：**
- `query` (str): 原始查询

**返回：**
```python
MultiQueryResult(
    original_query=str,
    generated_queries=[
        GeneratedQuery(
            query=str,
            method=str,      # "original" | "semantic"
            weight=float
        ),
        ...
    ],
    generation_time=str,
    total_queries=int,
    generation_methods=list
)
```

### 7. 混合检索器 (HybridRetriever)

结合向量检索和BM25检索的结果。

#### 初始化

```python
from modules.retrieval.hybrid_retriever import HybridRetriever

hybrid_retriever = HybridRetriever(
    vector_store=vector_store,
    bm25_retriever=bm25_retriever,
    vector_weight=0.6,     # 向量检索权重
    bm25_weight=0.4,       # BM25检索权重
    fusion_method="weighted_average"  # "weighted_average" | "rrf"
)
```

#### 主要方法

##### search(query, top_k=5)

混合搜索。

**返回：**
```python
[
    {
        'document': dict,
        'vector_similarity': float,  # 向量相似度
        'bm25_score': float,         # BM25分数
        'hybrid_score': float        # 混合分数
    },
    ...
]
```

## 完整使用示例

### 基础问答流程

```python
from modules.qa import ConversationChain, Memory, PromptTemplate
from modules.retrieval.vector_store import VectorStore
from modules.retrieval.bm25_retriever import BM25Retriever
from modules.retrieval.hybrid_retriever import HybridRetriever

# 1. 准备文档数据
documents = [
    {"text": "人工智能是计算机科学的一个分支，试图理解和构建智能体", "id": 1},
    {"text": "机器学习是人工智能的子领域，专注于算法和统计模型", "id": 2},
    {"text": "深度学习使用多层神经网络来模拟人脑的学习过程", "id": 3}
]

# 2. 创建检索器
vector_store = VectorStore()
vector_store.add_documents(documents)

bm25_retriever = BM25Retriever()
bm25_retriever.add_documents(documents)

hybrid_retriever = HybridRetriever(
    vector_store=vector_store,
    bm25_retriever=bm25_retriever
)

# 3. 创建QA系统
memory = Memory()
prompt_template = PromptTemplate()
conversation_chain = ConversationChain(
    memory=memory,
    prompt_template=prompt_template
)

# 4. 设置检索器
conversation_chain.set_retriever(hybrid_retriever)

# 5. 执行问答
result = conversation_chain.chat("什么是机器学习？")
print(f"回答: {result['response']}")
print(f"检索到 {len(result['retrieved_docs'])} 个相关文档")
```

### 多轮对话示例

```python
# 第一轮对话
result1 = conversation_chain.chat("什么是人工智能？")
print(f"AI: {result1['response']}")

# 第二轮对话（有记忆）
result2 = conversation_chain.chat("它有哪些应用领域？")
print(f"AI: {result2['response']}")

# 第三轮对话（有记忆）
result3 = conversation_chain.chat("这些应用中哪个最重要？")
print(f"AI: {result3['response']}")
```

### 配置管理

```python
from config.settings import settings

# 获取QA系统配置
qa_config = settings.get_model_config("qa_system")

# 获取LLM配置
llm_config = settings.get_model_config("llm")

# 获取检索配置
retrieval_config = settings.get_model_config("retrieval")
```

## 配置参数

### QA系统配置 (config/model_config.yaml)

```yaml
qa_system:
  conversation_chain:
    history_length: 15          # 对话历史长度
    max_context_length: 8000    # 最大上下文长度
    token_limit: 6000          # Token限制
  
  multi_query:
    max_queries: 10            # 最大生成查询数
    similarity_threshold: 0.7   # 相似度阈值
  
  retrieval:
    hybrid:
      fusion_method: "weighted_average"  # 融合方法
      vector_weight: 0.6       # 向量权重
      bm25_weight: 0.4         # BM25权重
```

### LLM配置

```yaml
llm:
  provider: "openai"
  model_name: "xop3qwen1b7"
  api_key: "your_api_key"
  base_url: "https://maas-api.cn-huabei-1.xf-yun.com/v2"
  max_tokens: 4096
  temperature: 0.7
```

## 错误处理

### 常见错误及解决方案

1. **模型加载失败**
   ```
   错误: 模型下载失败
   解决: 检查网络连接，或使用本地缓存
   ```

2. **API调用失败**
   ```
   错误: 讯飞星火API调用失败
   解决: 检查API密钥和网络连接
   ```

3. **内存不足**
   ```
   错误: CUDA内存不足
   解决: 使用CPU模式或减少文档数量
   ```

4. **检索无结果**
   ```
   错误: 检索返回空结果
   解决: 调整相似度阈值或检查文档内容
   ```

## 性能优化

### 1. 模型缓存
- 模型文件自动缓存到本地目录
- 支持离线使用已缓存的模型

### 2. 索引持久化
- 向量索引可保存到文件
- 支持快速加载已构建的索引

### 3. 批量处理
- 支持批量文档添加
- 优化向量计算效率

### 4. 内存管理
- 自动清理临时文件
- 模型按需加载和卸载

## 扩展性

### 添加新的检索器
```python
class CustomRetriever:
    def search(self, query, top_k=5):
        # 实现自定义检索逻辑
        pass

# 集成到混合检索器
hybrid_retriever = HybridRetriever(
    vector_store=vector_store,
    custom_retriever=CustomRetriever(),
    custom_weight=0.3
)
```

### 添加新的记忆类型
```python
class CustomMemory:
    def add_exchange(self, user_input, ai_response):
        # 实现自定义记忆逻辑
        pass
```
