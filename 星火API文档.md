# 推理服务_HTTP协议

## [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_1-接口说明)1. 接口说明

协议 ：HTTP 请求方法：POST 默认请求地址如下： (请根据服务发布时间及在线推理页面展示，选择对应的接口地址)

```http
https://maas-api.cn-huabei-1.xf-yun.com/v2（2026年1月10日及后发布服务的用户，请直接使用此新地址）
http://maas-api.cn-huabei-1.xf-yun.com/v1（2026年1月10日前已发布服务的存量用户，无需修改接口地址，仍可继续使用旧地址）
```

部分模型因为部署原因可能略有差异，具体可参考**服务管控** > **模型服务列表**右侧调用信息。技术咨询可直接提交[工单](https://console.xfyun.cn/workorder/commit)

## [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_2-接口请求)2. 接口请求

### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_2-1-请求示例)2.1 请求示例

下面是一个通用的 HTTP 请求 Python Demo 示例，展示了包括普通对话、流式对话和 JSON Mode 在内的多种调用方式。

```python
from openai import OpenAI  

# 必填：从服务管控页面获取对应服务的APIKey和API Base
api_key = "<YOUR_API_KEY>"
api_base = "http://maas-api.cn-huabei-1.xf-yun.com/v1"

client = OpenAI(api_key=api_key, base_url=api_base)

def unified_chat_test(model_id, messages, use_stream=False, extra_body={}):
    """
    一个统一的函数，用于演示多种调用场景。

    :param model_id: 要调用的模型ID。
    :param messages: 对话消息列表。
    :param use_stream: 是否使用流式输出。
    :param extra_body: 包含额外请求参数的字典，如 response_format。
    """
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=use_stream,
            temperature=0.7,
            max_tokens=4096,
            extra_headers={"lora_id": "0"},  # 调用微调大模型时,对应替换为模型服务卡片上的resourceId
            stream_options={"include_usage": True},
            extra_body=extra_body
        )

        if use_stream:
            # 处理流式响应
            full_response = ""
            print("--- 流式输出 ---")
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            print("\n\n--- 完整响应 ---")
            print(full_response)
        else:
            # 处理非流式响应
            print("--- 非流式输出 ---")
            message = response.choices[0].message
            print(message.content)

    except Exception as e:
        print(f"请求出错: {e}")

if __name__ == "__main__":
    model_id = "<YOUR_MODEL_ID>" # 必填：调用大模型时，对应为推理服务的模型卡片上对应的modelId

    # 1. 普通非流式调用
    print("********* 1. 普通非流式调用 *********")
    plain_messages = [{"role": "user", "content": "你好，请介绍一下自己。"}]
    unified_chat_test(model_id, plain_messages, use_stream=False)

    # 2. 普通流式调用
    print("\n********* 2. 普通流式调用 *********")
    stream_messages = [{"role": "user", "content": "写一首关于夏天的诗。"}]
    unified_chat_test(model_id, stream_messages, use_stream=True)

    # 3. JSON Mode 调用
    print("\n********* 3. JSON Mode 调用 *********")
    json_messages = [{"role": "user", "content": "请给我一个关于上海的JSON对象，包含城市名称(city)和人口数量(population)。"}]
    json_extra_body = {
        "response_format": {"type": "json_object"},
        "search_disable": True # JSON Mode下建议关闭搜索
    }
    unified_chat_test(model_id, json_messages, use_stream=False, extra_body=json_extra_body)

    # 4. 测试stop和前缀续写功能
    print("\n********* 4. 测试stop和前缀续写功能 *********")
    print("设置stop词: ['。', '！'] - 模型遇到句号或感叹号时会停止生成")
    stream_messages = [{"role": "user", "content": "给我解释下1加1等于多少。"}]
    unified_chat_test(model_id, stream_messages, use_stream=True, extra_body={"stop": ["。","！"],"continue_final_message":True})
```

**注意**：在使用demo之前，请务必替换 `api_key` 为您的API Key。

### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_2-2-请求参数)2.2 请求参数

| 参数                   | 类型     | 是否必填 | 要求                                                         | 说明                                                         |
| ---------------------- | -------- | -------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| model                  | string   | 是       |                                                              | 指定要调用的对话生成模型ID                                   |
| messages               | array    | 是       | `[{"role": "user", "content":"用户输入内容"}]`               | 表示对话上下文的消息列表，支持多轮对话交互。其中，`role` 用于标识消息发送方（例如 `user` 表示用户、`assistant` 表示模型回复），`content` 则为实际文本内容。 **注意**：仅限DeepSeekV3&R1使用对话前缀续写时，用户需确保 `messages` 列表里最后一条消息的 `role` 为 `assistant` |
| stream                 | boolean  | 否       | 取值为 `true` 或 `false`，默认值为 `false`                   | 指定是否采用流式响应模式。若设置为 `true`，系统将逐步返回生成的回复内容；否则，将一次性返回完整响应 |
| temperature            | float    | 否       | 取值为`[0,1]`,默认值为`0.7`                                  | 核采样阈值。用于决定结果随机性，取值越高随机性越强即相同的问题得到的不同答案的可能性越高 |
| max_tokens             | int      | 否       | 取值为`[1,32768]`，默认值为`2048`                            | 限制生成回复的最大 token 数量，不同模型限制生成内容的最大 token 数有差异，DeepSeekV3&R1 支持最大 32k，其他模型默认上限 8K。 |
| reasoning_effort       | string   | 否       | `low`, `medium`, `high`, 默认`high`                          | 指导模型在对提示做出响应之前应生成多少推理内容。`low` 优先考虑速度和节省token，`high` 优先考虑更完整的推理。**仅针对OpenAI开源的OSS模型生效**。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body` 对象中。 |
| `lora_id`              | string   | 否       | 调用微调模型时使用，对应模型服务卡片上的 `resourceId`。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_headers` 对象中。 |                                                              |
| stop                   | string[] | 否       | 仅限DeepSeekV3&R1支持                                        | 模型遇到 stop 字段所指定的字符串时将停止继续生成，这个词语本身不会输出。最多支持4个字符串如["你好”,"天气”] |
| continue_final_message | boolean  | 否       | 仅限DeepSeekV3&R1支持，取值为 `true` 或 `false`，默认值为 `false` | 指定是否开启对话前缀续写功能，若设置为`true`，系统将对 `messages` 列表里最后一条消息的 `role` 为 `assistant`的内容进行续写。 |
| `search_disable`       | boolean  | 否       | `true` 或 `false`，默认 `true`                               | 关闭联网搜索。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body` 对象中。 |
| `show_ref_label`       | boolean  | 否       | 默认为 `false`。`true` 表示在联网搜索时返回信源信息。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body` 对象中。 |                                                              |
| `enable_thinking`      | boolean  | 否       | 默认为 `false`。`true` 表示开启深度思考模式（**仅部分模型支持**）。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body` 对象中。 |                                                              |
| `response_format`      | object   | 否       | 用于指定模型的输出为 JSON 对象格式。设置为 `{"type": "json_object"}` 即可。**仅支持 DeepSeek R1 和 V3 模型**。详情见 `2.2.2 response_format 参数说明`。 |                                                              |
| stream_options         | object   | 否       | 默认值为`{"include_usage": True}`                            | 针对流式响应模式的扩展配置，如控制是否在响应中包含API调用统计信息等附加数据。 |

#### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_2-2-1-messages-参数说明)2.2.1 `messages` 参数说明

messages 参数用于传递对话内容，包括用户输入和 AI 回复

| 字段    | 含义     | 数据类型 | 取值范围              | 默认值 | 说明                                                         |
| ------- | -------- | -------- | --------------------- | ------ | ------------------------------------------------------------ |
| role    | 角色     | string   | system,user,assistant |        | **通过system设置对话背景信息，user表示用户的问题，assistant表示AI的回复** |
| content | 文本内容 | string   | --                    |        | 该角色的对话内容                                             |

**示例：单轮交互** 单轮交互只需要传递一个user角色的数据

```json
[
    {"role": "user", "content": "你会做什么？"}  
]
```

**示例：多轮交互** 多轮交互需要将之前的交互历史按照user->assistant->user->assistant规则进行拼接，并保证最后一条是user的当前问题。

```json
[
    {"role": "system", "content": "你是一个乐于助人的AI助手。"},
    {"role": "user", "content": "你好，你是谁？"},
    {"role": "assistant", "content": "我是AI助手，有什么可以帮您？"},
    {"role": "user", "content": "你会做什么？"}
]
```

#### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_2-2-2-response-format-参数说明)2.2.2 `response_format` 参数说明

`response_format` 参数用于强制模型输出严格符合 RFC 8259 规范的 JSON 对象。

**开启方法**

将 `response_format` 参数设置为 `{"type": "json_object"}`。

**功能优势**

- **可靠性**：确保模型输出的是一个语法正确的 JSON 对象。
- **简化开发**：无需在 prompt 中反复强调输出 JSON，也无需对模型输出进行复杂的后处理和校验。

**支持模型**

目前仅 DeepSeek R1 和 V3 模型支持 `json_object` 模式。

**Prompt 建议**

为了让模型更好地理解您的意图并生成符合期望的 JSON，建议在 Prompt 中明确指示模型输出 JSON。例如：

```json
[
    {"role": "user", "content": "请给我一个关于上海的JSON对象，包含城市名称（city）和人口数量（population）。"}
]
```

**错误处理**

如果 Prompt 的内容与 JSON 输出要求存在冲突，或模型无法生成有效的 JSON，可能会导致输出不完整或返回错误。请确保 Prompt 的引导内容清晰、无歧义。

## [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_3-接口响应)3. 接口响应

### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_3-1-响应示例)3.1 响应示例

#### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_3-1-1-成功响应示例)3.1.1 成功响应示例

关闭联网检索或不返回检索信源时，返回结构如下：

```python
Response: ChatCompletion(
    id='cht000b920a@dx194e0205ccbb8f3700',
    choices=[
        Choice(
            finish_reason='stop',
            index=0,
            logprobs=None,
            message=ChatCompletionMessage(
                content='大模型回复',
                refusal=None,
                role='assistant',
                audio=None,
                function_call=None,
                tool_calls=None
            )
        )
    ],
    created=1738927005,
    model=None,
    object='chat.completion',
    service_tier=None,
    system_fingerprint=None,
    usage=CompletionUsage(
        completion_tokens=42,
        prompt_tokens=44,
        total_tokens=86,
        completion_tokens_details=None,
        prompt_tokens_details=None
    )
```

开启联网检索且返回检索信源是，返回结构如下：

```python
ChatCompletion(
    id='cht000b8e42@dx19590107ba3b8f2700', 
    choices=[
        Choice(
            finish_reason='stop', 
            index=0, 
            logprobs=None, 
            message=ChatCompletionMessage(
                content='大模型回复', 
                refusal=None, 
                role='assistant', 
                audio=None, 
                function_call=None, 
                tool_calls=None, 
                reasoning_content='', 
                plugins_content=[
                    {
                        'name': 'ifly_search', 
                        'content': '[{"index":1,"url":"https://xxx.com/xxx/doc.html","title":"信源标题"}]'
                    }
                ]
            )
        )
    ], 
    created=1741878776, 
    model='xdeepseekv3', 
    object='chat.completion', 
    service_tier=None, 
    system_fingerprint=None, 
    usage=CompletionUsage(
        completion_tokens=346, 
        prompt_tokens=1124, 
        total_tokens=1470, 
        completion_tokens_details=None, 
        prompt_tokens_details=None
    )
)
```

#### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_3-1-2-异常结果示例)3.1.2 异常结果示例

```json
Error: Error code: 403 - {'error': {'message': '该令牌无权使用模型：xqwen257bxxx (request id: 2025020809381060443349905703260)', 'type': 'one_api_error'}}
```

### [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_3-2-响应数据参数)3.2 响应数据参数

字段说明如下：

| 字段名                     | 类型   | 字段说明                                                     |
| -------------------------- | ------ | ------------------------------------------------------------ |
| id                         | string | 唯一标识符，标识本次对话调用的唯一ID，用于跟踪和调试         |
| choices                    | array  | 包含模型生成回复候选项的数组                                 |
| •finish_reason             | string | 指示回复生成结束的原因，如`"stop"`                           |
| •index                     | int    | 回复候选项在数组中的索引位置，从0开始                        |
| •logprobs                  | object | 如启用token概率日志，则返回具体信息                          |
| •message                   | object | 描述回复消息内容的对象，其内部字段如下                       |
| ◦content                   | string | 模型生成的回复文本内容                                       |
| ◦reasoning_content         | string | 模型生成的思考文本内容(支持深度思考的模型才有此字段)         |
| ◦plugins_content           | array  | 联网检索的信源结果列表(支持联网检索的模型才有此字段)         |
| ◦name                      | string | 联网检索插件名称ifly_search等                                |
| ◦name                      | string | 联网检索插件结果，此为信源结果列表，`index`序号，`url`信源地址，`title`信源标题 |
| ◦refusal                   | object | 模型拒绝回答时返回拒绝信息                                   |
| ◦role                      | string | 消息发送方，通常为`"assistant"`                              |
| ◦audio                     | object | 如支持语音回复则返回音频数据                                 |
| ◦function_call             | objec  | 模型调用外部函数时返回调用信息                               |
| ◦tool_calls                | object | 模型调用工具时返回调用详情，                                 |
| created                    | int    | 响应生成时间的Unix时间戳（秒级）                             |
| model                      | string | 实际调用的模型名称                                           |
| object                     | string | 表示响应对象类型                                             |
| service_tier               | string | 表示调用所属的服务层级                                       |
| system_fingerprint         | string | 系统指纹或配置标识                                           |
| usage                      | object | 包含token使用统计信息，其内部字段如下：                      |
| •completion_tokens         | int    | 回复文本消耗的token数量                                      |
| •prompt_tokens             | int    | 输入prompt消耗的token数量                                    |
| •total_tokens              | int    | prompt与回复消耗token数量的总和                              |
| •completion_tokens_details | object | 回复生成过程中token的详细统计信息，若无则为`null`            |
| •prompt_tokens_details     | object | prompt部分token的详细统计信息                                |

## [#](https://www.xfyun.cn/doc/spark/推理服务-http.html#_4-错误码列表)4 . 错误码列表

| 错误码                                 | 原因                                      | 解决方案                                                |
| -------------------------------------- | ----------------------------------------- | ------------------------------------------------------- |
| 401-无效的身份验证                     | 身份验证无效。                            | 确保使用正确的API密钥及请求组织。                       |
| 401-提供的API密钥不正确                | 请求的API密钥不正确。                     | 检查所用API密钥是否正确，清除浏览器缓存或生成新的密钥。 |
| 403-不支持的国家、地区或领土           | 您正在从不支持的国家、地区或领土访问API。 | 请参考相关页面获取更多信息。                            |
| 429-请求速率限制已达上限               | 您发送请求过快。                          | 控制请求频率，阅读速率限制指南。                        |
| 429-超出当前配额，请检查计划和计费详情 | 您的额度已用尽或已达到每月最高消费限制。  | 购买更多额度或了解如何提高使用限制。                    |
| 500-服务器处理请求时发生错误           | 服务器内部出现问题。                      | 稍后重试请求；若问题持续，请联系我们查看状态页面。      |
| 503-引擎当前过载，请稍后重试           | 服务器流量过大。                          | 稍候重试您的请求。                                      |