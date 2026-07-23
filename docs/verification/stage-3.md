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
  tests/test_summary_agent.py `
  tests/test_summary_panel.py `
  tests/test_translation_agent.py `
  tests/test_translation_panel.py `
  tests/test_stage3_acceptance.py
```

也可以用标准库 `unittest` 运行同一批核心验收：

```powershell
uv run python -m unittest `
  tests.test_llm_provider `
  tests.test_summary_agent `
  tests.test_summary_panel `
  tests.test_translation_agent `
  tests.test_translation_panel `
  tests.test_stage3_acceptance
```

验收点：

| 范围 | 通过条件 |
| --- | --- |
| Provider | 配置校验、连接结果、API Key 脱敏和固定 Mock 响应通过 |
| Summary Agent | Cleaned Markdown 优先、可配置语言/详细度/Prompt、失败返回结构化错误 |
| Summary UI | 后台生成、重新生成、缓存、双语状态和正文不被替换 |
| Translation Agent | 段落顺序稳定、长段分段、部分失败继续处理、原文完整保留 |
| Translation UI | 每段原文在上、对应译文在下；支持重新翻译、双语状态/错误和失败原文兜底 |
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
uv run python -m mercury.main
```

逐项检查：

1. 不配置 AI Provider，仍可添加/导入 Feed、刷新、选择文章、切换 Raw /
   Cleaned HTML / Markdown，并使用已读、未读和标签功能。
2. 选择文章后按 `Ctrl+Shift+S` 展开 Summary；点击生成入口时应提示配置
   AI，正文保持可读。
3. 按 `Ctrl+Shift+T` 展开 Translation；点击翻译入口时应提示配置 AI，
   正文保持可读。
4. 在设置中将界面从简体中文切换到 English；Summary、Translation、
   按钮、状态和错误文案应立即更新，无需重启。
5. 收起或重新展开两个 AI 面板，当前文章不应被清空。

## 4. 可选真实 Provider 人工验收

真实 Provider 验收不是自动测试的一部分，必须由用户主动配置并明确发起。
当前仓库的 `main.py` 没有内置具体厂商的网络适配器；执行本节前，集成环境
必须已经提供实现统一 `LLMProvider` 协议的适配器，并把：

- `SummaryAgent(provider).summarize` 注入 `MainWindow.summary_generator`；
- `TranslationAgent(provider).translate` 注入
  `MainWindow.translation_generator`。

不得在 Agent、UI 或文章业务逻辑中写死厂商、模型、Base URL 或 API Key。

人工步骤：

1. 在 AI 设置中填写用户选择的 Base URL、模型、超时和可选 API Key。
   凭据只放入本次验收允许的本地配置位置，不写入仓库。
2. 主动执行“测试连接”。在此之前不应出现 Provider 网络请求。
3. 选择一篇非敏感测试文章，展开 Summary 并主动生成。确认摘要语言、
   详细程度和自定义 Prompt 生效，正文始终可读。
4. 展开 Translation，选择目标语言，填写可选 Prompt 并主动翻译。确认每组
   内容均为原文在上、同序号译文在下，并可“重新翻译”。
5. 临时使用无效地址或适配器的测试失败模式，分别触发摘要和翻译失败。
   确认 UI 显示可理解错误；文章正文不消失，翻译区仍显示所有原文。
6. 恢复有效配置后重新执行，确认失败不会破坏后续生成。
7. 验收结束后清除临时凭据，并检查 `git status --short`，确保没有凭据、
   本地数据库或私有文章进入待提交文件。

## 5. Stage 3 Gate

交付前必须同时满足：

- Mock Provider 自动验收和完整回归通过。
- 未配置 Provider 时，基础阅读功能完全可用。
- Provider 失败时，摘要/翻译给出可理解错误，文章和翻译原文仍可读。
- 翻译对照严格使用结构化 `TranslationResult`，不从整篇字符串猜测段落。
- UI 不直接访问数据库、网络或 Provider 协议。
- 业务逻辑没有硬编码具体厂商、生产模型、Base URL 或 API Key。
- `git status --short` 中没有凭据、私有 fixture 或无关本地数据。
