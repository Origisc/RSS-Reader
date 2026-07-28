# Stage 3 AI 功能验收

本文用于独立验收 Provider 抽象、摘要、段落翻译、对照 UI 和失败
fallback。自动验收只使用内存中的 `MockLLMProvider`，不读取真实 API
Key，也不访问网络。

## 1. 验收前提

- Python 3.13。
- 使用项目约定的 `uv` 管理环境。
- 从仓库根目录执行命令。
- 不把真实 API Key、私有文章或生产 Base URL 放进仓库、测试 fixture、
  命令输出或截图。

首次准备开发环境：

```powershell
uv sync --group dev
```

离线 fixture 位于 `tests/fixtures/llm/stage3_article.json`。其中只有公开的
测试文本、固定摘要和固定译文；`tests/fixtures/llm/README.md` 记录了隐私
边界。

## 2. 自动 Mock Provider 验收

运行 Stage 3 验收集合：

```powershell
uv run pytest `
  tests/test_llm_provider.py `
  tests/test_http_llm_provider.py `
  tests/test_ai_persistence.py `
  tests/test_ai_provider_integration.py `
  tests/test_summary_agent.py `
  tests/test_summary_panel.py `
  tests/test_translation_agent.py `
  tests/test_translation_panel.py `
  tests/test_article_reader.py `
  tests/test_bilingual_document.py `
  tests/test_stage3_acceptance.py
```

也可以用标准库 `unittest` 运行同一批核心验收：

```powershell
uv run python -m unittest `
  tests.test_llm_provider `
  tests.test_http_llm_provider `
  tests.test_ai_persistence `
  tests.test_ai_provider_integration `
  tests.test_summary_agent `
  tests.test_summary_panel `
  tests.test_translation_agent `
  tests.test_translation_panel `
  tests.test_article_reader `
  tests.test_bilingual_document `
  tests.test_stage3_acceptance
```

验收点：

| 范围 | 通过条件 |
| --- | --- |
| Provider | 配置校验、连接结果、API Key 脱敏、固定 Mock 响应和本地配置重启恢复通过 |
| 本地 AI 存储 | Provider 配置、摘要和逐段翻译可从临时 SQLite 重建；后台线程写入、UTF-8、结构化失败信息和现有 Reader 表共存通过 |
| Summary Agent | Cleaned Markdown 优先、可配置语言/详细度/Prompt、失败返回结构化错误 |
| Summary UI | 后台生成、重新生成、缓存、双语状态和正文不被替换 |
| Translation Agent | 优先使用 Cleaned HTML 的 `p/ul/ol` Reader 段落边界；旧式 RSS 裸文本按连续 `<br>` 恢复段落；段落顺序稳定、长段分段、部分失败继续处理、原文完整保留 |
| Translation UI | 翻译设置位于 Reader 内；首段完成后立即渐进显示，不等待整篇；原始 HTML/Markdown 的段落和富文本结构保持不变，每段译文卡片插入对应原文块下方，整块列表只对应一块译文；旧式 RSS 无法插回时使用结构化双语对兜底；支持原文/双语切换、重新翻译、错误提示和失败原文兜底 |
| Stage 3 fixture | 固定摘要和三段译文与 fixture 一致；故意失败时三段原文仍可读取 |

完整回归：

```powershell
uv run python -m unittest discover -s tests -p "test_*.py"
```

通过标准是命令以 `OK` 结束，没有真实网络依赖，也不需要任何真实凭据。

## 3. 无 Provider 时的人工验收

当前默认应用组合不会静默创建 Provider，也不会用 Mock Provider 冒充真实
服务。运行应用：

```powershell
uv run python main.py
```

逐项检查：

1. 不配置 AI Provider，仍可添加/导入 Feed、刷新、选择文章、切换 Raw /
   Cleaned HTML / Markdown，并使用已读、未读和标签功能。
2. 选择文章后按 `Ctrl+Shift+S` 展开 Summary；点击生成入口时应提示配置
   AI，正文保持可读。
3. 按 `Ctrl+Shift+T` 展开 Reader 内的翻译设置；点击翻译入口时应提示配置
   AI，Reader 正文保持可读，页面下方不应出现类似 Summary 的翻译结果区。
4. 在设置中将界面从简体中文切换到 English；Summary、Translation、
   按钮、状态和错误文案应立即更新，无需重启。
5. 收起或重新展开 Summary 与翻译设置，当前文章不应被清空。

## 4. 可选真实 Provider 人工验收

真实 Provider 验收不是自动测试的一部分，必须由用户主动配置并明确发起。
生产入口为 `SummaryAgent`、`TranslationAgent` 和 `TagAgent` 分别创建
`HTTPChatCompletionsProvider`，三者使用独立的动态配置存储，但复用同一个
Provider 抽象。

适配器发送标准 Chat Completions 请求。如果 Base URL 是
`https://provider.example/v1`，请求地址为
`https://provider.example/v1/chat/completions`；如果设置中已经填写完整的
`.../chat/completions` 地址，则不会重复追加。

当前生产入口使用 `SQLiteProviderConfigStore`、
`SQLiteSummaryResultStore` 和 `SQLiteTranslationResultStore`，统一写入
现有本地 `database.db`。重启后会恢复 Provider 配置以及每篇文章最近一次
摘要和翻译。数据库文件被 Git 忽略，Mercury 不会主动同步或上传其中内容。
不得在 Agent、UI 或文章业务逻辑中写死厂商、模型、Base URL 或 API Key。

人工步骤：

1. 打开“Agents 设置”，分别为 Summary、Translation 和 Tag 填写用户选择
   的 Base URL、模型、超时和可选 API Key。三个 Agent 可选择不同配置，也
   可单独禁用。凭据只放入本次验收允许的本地配置位置，不写入仓库。
2. 主动执行“测试连接”。该操作只发送一个简短确认提示，不发送文章内容；
   在此之前不应出现 Provider 网络请求。
3. 选择一篇非敏感测试文章，展开 Summary 并主动生成。确认摘要语言、
   详细程度和自定义 Prompt 生效，正文始终可读。选择“简体中文”时，即使
   填写自定义 Prompt，摘要标题、开场、正文和结论也必须保持简体中文；
   旧的英文摘要不得在本次失败后继续显示为当前结果。
4. 展开 Reader 内的翻译设置，选择目标语言，填写可选 Prompt 并主动翻译。
   生成完成后设置区应自动收起，Reader 正文应切换为双语对照：第一段原文
   后紧跟第一段译文，再显示第二段原文及第二段译文，依此类推。使用 Reader
   工具栏的“显示原文 / 双语对照”可以来回切换，并可重新展开设置执行
   “重新翻译”。原文中的标题、粗体、链接、图片、引用、列表和表格不应因
   翻译而变成连续纯文本。
5. 临时使用无效地址或适配器的测试失败模式，分别触发摘要和翻译失败。
   确认 UI 显示可理解错误；Reader 中所有原文仍可读，失败段落不会被空白
   译文替换。
6. 恢复有效配置后重新执行，确认失败不会破坏后续生成。
7. 关闭并重新启动 Mercury，确认三个 Agent 的独立 Provider 配置仍在；
   重新选择同一篇文章后，最近一次摘要和逐段翻译无需重新调用 Provider
   即可恢复。
8. 验收结束后清除临时凭据，并检查 `git status --short`，确保没有凭据、
   本地数据库或私有文章进入待提交文件。

### 4.1 零 API 费用的本地 DeepSeek 验收

DeepSeek 官方云 API 按 Token 计费。“本地 DeepSeek（Ollama，零 API
费用）”模板才是无需云端 API 余额的方案。模型仍会占用本机磁盘、内存和
计算资源。

1. 从 Ollama 官方渠道安装适用于当前系统的版本。
2. 在终端下载轻量模型：

   ```powershell
   ollama pull deepseek-r1:1.5b
   ```

3. 确认 Ollama 正在运行，然后打开 Mercury 的“Agents 设置”，选择需要
   使用本地模型的 Agent。
4. 选择“本地 DeepSeek（Ollama，零 API 费用）”。确认 Base URL 为
   `http://127.0.0.1:11434/v1`、模型为 `deepseek-r1:1.5b`，API Key
   留空。
5. 点击“测试连接”。首次加载模型可能较慢，模板默认超时为 120 秒。
6. 使用非敏感测试文章分别验证摘要和逐段翻译。请求应只发送到本机回环
   地址；关闭 Ollama 后应显示 Provider 失败，正文仍保持可读。

### 4.2 DeepSeek 官方 API 验收

如果选择“DeepSeek 官方 API（按量计费）”，必须使用用户自己的 DeepSeek
API Key 和可用余额。模板仅填写当前官方 Base URL 和模型名，不附带凭据，
也不会把其他服务已填写的 API Key 带入该模板。

## 5. Stage 3 Gate

交付前必须同时满足：

- Mock Provider 自动验收和完整回归通过。
- 未配置 Provider 时，基础阅读功能完全可用。
- Provider 失败时，摘要/翻译给出可理解错误，文章和翻译原文仍可读。
- 三个 Agent 的独立 Provider 配置、摘要和结构化逐段翻译在重启后可从本地
  数据库恢复。
- SQLite 存储失败不会导致应用崩溃，也不会影响基础阅读。
- 翻译对照严格使用结构化 `TranslationResult`，不从整篇字符串猜测段落。
- 翻译结果渲染在 Reader 正文区域，严格保持“原文段落 → 对应译文”的顺序，
  不在页面底部创建类似 Summary 的结果面板。
- UI 不直接访问数据库、网络或 Provider 协议。
- 业务逻辑没有硬编码具体厂商、生产模型、Base URL 或 API Key。
- `git status --short` 中没有凭据、私有 fixture 或无关本地数据。
