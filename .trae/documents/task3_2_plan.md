# Task 3.2 - 翻译文章功能实现计划

## 项目研究结论

根据对项目架构的分析，当前项目已完成：
- Stage 1：文章抓取、Feed解析、本地存储
- Stage 2：文章清洗（ReaderCleaner）、Markdown转换（MarkdownConverter）

尚未实现的AI功能（Stage 3）：
- LLM Provider抽象层（完全缺失）
- Translation Agent（完全缺失）
- Summary Agent（完全缺失）

**翻译功能的前置条件**：必须先实现LLM Provider抽象层，所有AI调用通过统一接口进行，支持Mock测试。

## 文件和模块修改清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `src/mercury/llm/provider.py` | Provider接口定义 + MockProvider实现 |
| `src/mercury/llm/config.py` | Provider配置模型 + 本地存储 |
| `src/mercury/services/translation_service.py` | 翻译服务，包含段落切分和合并逻辑 |
| `tests/test_llm_provider.py` | LLM Provider测试 |
| `tests/test_translation_service.py` | 翻译服务测试 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `src/mercury/models/article.py` | 新增翻译相关字段 |
| `core/database.py` | 扩展articles表 + 新增save_article_translated()方法 |
| `src/mercury/services/article_service.py` | 新增translate_article_content()接口 |
| `src/mercury/services/backend_article_service.py` | 实现翻译方法 |
| `src/mercury/services/mock_article_service.py` | Mock翻译方法 |

## 实现步骤

### Step 1: LLM Provider抽象层

**目标**：创建统一的AI调用接口，支持Mock测试

**文件**：`src/mercury/llm/provider.py`

**设计要点**：
- 使用Protocol定义Provider接口
- 最小化接口：`chat(messages, **kwargs) -> str`
- MockProvider返回确定性响应用于测试
- 错误处理：网络异常、API错误、超时

### Step 2: Provider配置模型

**目标**：支持用户配置Base URL、API Key、模型名、超时等

**文件**：`src/mercury/llm/config.py`

**设计要点**：
- 配置本地保存（JSON文件）
- API Key不进入日志
- 支持OpenAI兼容接口
- 默认使用MockProvider

### Step 3: 数据模型扩展

**目标**：为Article模型和数据库添加翻译字段

**修改文件**：
- `src/mercury/models/article.py`
- `core/database.py`

**新增字段**：
- `translated_text`: 翻译后的文本（段落对照格式）
- `translated_at`: 翻译时间
- `translate_status`: 翻译状态（pending/success/failed）
- `translate_error`: 翻译错误信息
- `target_language`: 目标语言（默认zh）

### Step 4: TranslationService实现

**目标**：实现翻译核心逻辑，支持长文章分段处理

**文件**：`src/mercury/services/translation_service.py`

**设计要点**：
- 输入优先级：cleaned_markdown > cleaned_html > original_html
- 段落切分：按空行或段落标签分割
- 分段翻译：对每段独立调用LLM
- 结果合并：保留段落顺序
- 失败处理：某段失败不影响其他段落，保留原文

### Step 5: Service接口集成

**目标**：将翻译功能集成到现有的服务层

**修改文件**：
- `src/mercury/services/article_service.py` - 新增接口定义
- `src/mercury/services/backend_article_service.py` - 实现翻译方法
- `src/mercury/services/mock_article_service.py` - Mock实现

**设计要点**：
- 自动触发清洗：如果clean_status != 'success'，先清洗再翻译
- 防重复翻译：已成功翻译的文章不重复翻译（除非force=True）
- 错误返回：用户可理解的错误信息

### Step 6: 单元测试

**目标**：覆盖翻译功能的所有场景

**文件**：
- `tests/test_llm_provider.py`
- `tests/test_translation_service.py`

**测试场景**：
- MockProvider正常返回
- Provider错误处理
- 段落切分正确性
- 长文章分段翻译
- 某段翻译失败时保留原文
- 已翻译文章防重复
- 自动触发清洗

## 潜在依赖和注意事项

### 依赖
- 无新增第三方依赖，使用标准库
- 网络请求使用urllib或requests（需确认项目已有）

### 注意事项
- **本地优先**：用户数据默认本地保存，不主动上传
- **LLM中立**：不把任何厂商、模型名、Base URL、API Key写死
- **错误隔离**：AI功能失败不影响基础阅读功能
- **测试隔离**：测试使用MockProvider，不依赖真实在线LLM

## 风险处理

| 风险 | 处理方式 |
|------|---------|
| Provider调用超时 | 设置超时时间（默认15秒），超时返回错误 |
| API Key泄露 | 配置本地保存，不进入日志，UI不显示完整Key |
| 长文章翻译失败 | 分段处理，失败段落保留原文 |
| 清洗失败影响翻译 | 翻译前检查清洗状态，失败时使用原始HTML |
| 数据库字段冲突 | 使用ALTER TABLE ADD COLUMN并捕获OperationalError |

## 验收标准

- `uv run pytest tests/test_llm_provider.py tests/test_translation_service.py` 通过
- MockProvider下可生成确定性翻译结果
- 长文章被分段处理，段落顺序一致
- 某段失败时仍保留原文和错误信息
- 代码中不存在硬编码具体LLM厂商配置
- 未配置Provider时基础阅读功能正常
