# Mercury Project Plan

> 目标：按“先可用、再好用、最后智能化”的顺序递进。每个阶段都必须产出一个可运行、可测试、可演示、可回滚的版本；不得把后续阶段功能作为当前阶段验收前提。

## 0. 全局原则

- **本地优先**：不需要注册、登录、订阅即可使用；订阅源、文章缓存、阅读记录、笔记、标签、配置默认保存在本地。
- **隐私优先**：除拉取 Feed、抓取文章、用户主动配置的 LLM 调用外，不主动上传用户数据。
- **跨平台**：目标平台为 Windows、Linux、macOS；文件读写显式使用 UTF-8。
- **LLM 中立**：AI 能力必须通过统一 Provider 抽象调用，不在业务逻辑中写死厂商、模型名、Base URL 或 API Key。
- **基础阅读不依赖 AI**：Feed、文章列表、文章详情、Reader 模式必须在没有任何 LLM 配置时正常工作。
- **可维护架构**：UI 层只负责展示与交互，不直接承担 Feed 抓取、数据库、清洗、LLM 调用等业务逻辑。
- **测试留痕**：涉及 Feed / OPML、文章去重、Reader 清洗、HTML / Markdown 转换、LLM Provider、Summary / Translation、本地存储和迁移的改动必须有测试。

## 1. 阶段总览

| 阶段 | 阶段名称 | 目标 | 独立可验证产物 |
| --- | --- | --- | --- |
| 第一阶段 | 基础阅读器原型 | 完成本地优先 RSS 阅读器最小闭环 | 可导入 OPML / 添加 Feed、刷新订阅、查看文章列表与详情、本地缓存可复用 |
| 第二阶段 | 阅读体验增强 | 完成 Reader 模式、内容清洗、Markdown / HTML 转换、多语言 UI 与基础跨平台验证 | 可展示 Cleaned HTML / Cleaned Markdown，切换中英界面，无 AI 配置也可完整阅读 |
| 第三阶段 | AI 功能接入 | 完成 LLM Provider 抽象、Summary Agent、Translation Agent 与失败 fallback | 使用 Mock Provider 可自动测试摘要/翻译，使用用户配置 Provider 可人工验证真实调用 |
| 第四阶段 | 信息整理与导出 | 完成笔记、标签、筛选、单篇/多篇导出；Tag Agent 作为选做增强 | 可对文章做整理、筛选与导出；即使不启用 Tag Agent，手动标签和导出仍可使用 |

---

# 第一阶段｜基础阅读器原型

## Overall Goal

建立 Mercury 的最小可用版本：用户无需账号即可在本地添加订阅源、导入 OPML、刷新订阅、查看文章列表和文章详情，并能在重启后继续读取本地缓存。

## Completion Definition

本阶段完成后，即使没有 Reader 清洗、AI、导出和标签功能，用户也可以完成“添加订阅源 → 刷新 → 浏览文章列表 → 打开文章详情 → 关闭并重启应用后数据仍存在”的完整流程。

## Sub-phases

### 1.1 项目骨架与运行入口

#### Task 1.1.1 初始化 Python 3.13 + uv 项目

- **Overall Goal**：建立统一的项目结构、依赖管理和开发命令。
- **Task Detail**：
  - 创建 `pyproject.toml`、`README.md`、基础包目录。
  - 使用 `uv` 管理依赖、运行、测试。
  - 配置基础测试框架。
- **Affected Files**：
  - `pyproject.toml`
  - `README.md`
  - `src/mercury/__init__.py`
  - `tests/`
- **Key Design**：
  - 不引入 Poetry、Pipenv、Conda 作为主流程。
  - 依赖保持轻量，新增依赖必须说明用途。
- **Verification**：
  - `uv run python -c "import mercury"` 成功。
  - `uv run pytest` 成功。
  - README 中包含安装、运行、测试命令。

#### Task 1.1.2 建立分层架构

- **Overall Goal**：避免 UI 直接承担抓取、解析、数据库和业务逻辑。
- **Task Detail**：
  - 定义 `domain`、`services`、`storage`、`ui`、`config` 等模块边界。
  - 为 Feed、Article、Subscription 建立基础实体模型。
- **Affected Files**：
  - `src/mercury/domain/`
  - `src/mercury/services/`
  - `src/mercury/storage/`
  - `src/mercury/ui/`
- **Key Design**：
  - UI 只调用 service 接口。
  - storage 不依赖 PySide6。
  - services 不直接依赖具体 UI 控件。
- **Verification**：
  - 单元测试可以在无 GUI 环境下运行。
  - `domain` 与 `services` 模块不导入 `PySide6`。

### 1.2 Feed / OPML 解析

#### Task 1.2.1 支持 RSS / Atom Feed 解析

- **Overall Goal**：能从常见 RSS / Atom Feed 中解析订阅源信息和文章条目。
- **Task Detail**：
  - 解析 Feed 标题、站点链接、描述。
  - 解析文章标题、链接、发布时间、作者、摘要、原始内容。
  - 处理缺失字段和格式异常。
- **Affected Files**：
  - `src/mercury/services/feed_parser.py`
  - `src/mercury/domain/feed.py`
  - `src/mercury/domain/article.py`
  - `tests/fixtures/feeds/`
  - `tests/test_feed_parser.py`
- **Key Design**：
  - 解析逻辑只返回结构化对象，不直接写数据库。
  - 测试使用本地 fixture，不依赖真实网络。
- **Verification**：
  - 本地 RSS fixture 可解析成功。
  - 本地 Atom fixture 可解析成功。
  - 缺少发布时间、作者或摘要时不会崩溃。

#### Task 1.2.2 支持 OPML 导入

- **Overall Goal**：用户可以通过 OPML 批量导入订阅源。
- **Task Detail**：
  - 解析 OPML 分组。
  - 识别重复订阅源。
  - 跳过或报告无效订阅源。
- **Affected Files**：
  - `src/mercury/services/opml_parser.py`
  - `src/mercury/domain/subscription.py`
  - `tests/fixtures/opml/`
  - `tests/test_opml_parser.py`
- **Key Design**：
  - OPML 导入结果包含成功、重复、无效三类信息。
  - 不因为单个无效源导致整个导入失败。
- **Verification**：
  - 含分组 OPML 可正确保留分组信息。
  - 重复源只保留一份。
  - 无效源被记录为导入警告。

### 1.3 本地存储与缓存

#### Task 1.3.1 建立本地数据库结构

- **Overall Goal**：订阅源、文章、阅读状态和基础配置默认保存到本地。
- **Task Detail**：
  - 设计 subscriptions、articles、article_contents、reading_states、settings 表或等价模块。
  - 保存原始 Feed 内容和文章基础元数据。
  - 所有文件读写使用 UTF-8。
- **Affected Files**：
  - `src/mercury/storage/database.py`
  - `src/mercury/storage/migrations/`
  - `src/mercury/storage/repositories.py`
  - `tests/test_storage.py`
- **Key Design**：
  - 数据库默认位于用户本地应用数据目录。
  - 不引入账号系统或云同步作为前置条件。
  - 数据访问通过 repository 封装。
- **Verification**：
  - 新建数据库后 schema 可自动初始化。
  - 写入订阅源和文章后，重启进程仍可读取。
  - 测试使用临时目录，不污染用户真实数据。

#### Task 1.3.2 实现文章去重

- **Overall Goal**：刷新订阅时避免重复文章。
- **Task Detail**：
  - 基于文章链接、GUID、Feed ID 等组合键去重。
  - 禁止只按标题去重。
  - 重复文章更新必要元数据但不重复插入。
- **Affected Files**：
  - `src/mercury/services/sync_service.py`
  - `src/mercury/storage/repositories.py`
  - `tests/test_article_deduplication.py`
- **Key Design**：
  - 去重策略可测试、可解释。
  - 保留同标题但不同链接的文章。
- **Verification**：
  - 同 GUID / 同链接文章不会重复插入。
  - 同标题不同链接文章可以同时存在。
  - 多次刷新同一 Feed 后文章数量稳定。

### 1.4 基础 UI 闭环

#### Task 1.4.1 PySide6 主窗口与列表/详情布局

- **Overall Goal**：提供最小可用桌面界面。
- **Task Detail**：
  - 实现订阅源列表、文章列表、文章详情三栏或等价布局。
  - 支持添加 Feed URL。
  - 支持刷新订阅。
- **Affected Files**：
  - `src/mercury/ui/app.py`
  - `src/mercury/ui/main_window.py`
  - `src/mercury/ui/models.py`
- **Key Design**：
  - UI 通过 service 获取数据。
  - 长时间刷新任务不得阻塞 UI。
- **Verification**：
  - `uv run mercury` 可以启动主窗口。
  - 添加本地测试 Feed 后能显示文章列表。
  - 点击文章后能显示文章原始详情。

#### Task 1.4.2 第一阶段人工验收脚本

- **Overall Goal**：让任何开发者都能独立验证第一阶段是否完成。
- **Task Detail**：
  - 准备本地 Feed / OPML fixture。
  - 编写 `docs/verification/stage-1.md`。
- **Affected Files**：
  - `docs/verification/stage-1.md`
  - `tests/fixtures/`
- **Key Design**：
  - 验收流程不依赖真实网络。
  - 可选提供真实 Feed URL 作为补充人工测试。
- **Verification**：
  - 按文档执行后，可完成导入、刷新、列表、详情、本地持久化验证。

## Stage 1 Verification Gate

- `uv run pytest tests/test_feed_parser.py tests/test_opml_parser.py tests/test_storage.py tests/test_article_deduplication.py`
- `uv run mercury` 可启动。
- 无账号、无 LLM 配置、无云服务时，基础阅读闭环可用。
- 应用重启后订阅源和文章仍存在。

---

# 第二阶段｜阅读体验增强

## Overall Goal

让 Mercury 从“能读”提升为“好读”：实现 Reader 模式、内容清洗、Cleaned HTML / Cleaned Markdown、自定义阅读样式、界面中英双语切换和基础跨平台验证。

## Completion Definition

本阶段完成后，用户打开文章时可以在原始内容、Cleaned HTML、Cleaned Markdown / Reader 视图之间查看；清洗失败时仍能回退到可读内容；界面可在英文和简体中文之间切换且无需重启。

## Sub-phases

### 2.1 文章抓取与内容模型增强

#### Task 2.1.1 抓取文章正文

- **Overall Goal**：为 Reader 清洗提供原始文章正文。
- **Task Detail**：
  - 根据文章链接抓取网页正文。
  - 保存原始 HTML。
  - 处理超时、编码、网络失败。
- **Affected Files**：
  - `src/mercury/services/article_fetcher.py`
  - `src/mercury/domain/article_content.py`
  - `src/mercury/storage/repositories.py`
  - `tests/test_article_fetcher.py`
- **Key Design**：
  - 网络请求只用于用户明确触发的文章抓取或订阅刷新。
  - 抓取失败不影响 Feed 中已有摘要阅读。
- **Verification**：
  - 使用本地 HTML fixture 模拟抓取成功。
  - 模拟 404、超时、编码异常时返回可理解错误。
  - 失败后文章详情仍能显示 Feed 摘要或原始内容 fallback。

### 2.2 Reader 清洗与转换

#### Task 2.2.1 生成 Cleaned HTML

- **Overall Goal**：从原始 HTML 中提取适合阅读的正文结构。
- **Task Detail**：
  - 清理脚本、广告、导航等无关内容。
  - 保留标题层级、链接、图片、列表、表格、代码块。
  - 清洗失败时返回 fallback。
- **Affected Files**：
  - `src/mercury/services/reader_cleaner.py`
  - `tests/fixtures/html/`
  - `tests/test_reader_cleaner.py`
- **Key Design**：
  - 不无理由删除关键信息。
  - 清洗结果和原始内容同时保存。
- **Verification**：
  - 含图片、表格、列表、代码块的 fixture 清洗后结构仍存在。
  - 清洗异常时文章仍可读。

#### Task 2.2.2 生成 Cleaned Markdown

- **Overall Goal**：将 Cleaned HTML 转换为可导出、可阅读的 Markdown。
- **Task Detail**：
  - 转换标题、段落、链接、图片、列表、表格、代码块。
  - 保留基础语义结构。
- **Affected Files**：
  - `src/mercury/services/markdown_converter.py`
  - `tests/test_markdown_converter.py`
- **Key Design**：
  - Markdown 转换输入优先使用 Cleaned HTML。
  - 转换失败不覆盖已有 Cleaned HTML。
- **Verification**：
  - fixture 中的标题、链接、图片、表格、代码块转换后可被断言。
  - Markdown 输出使用 UTF-8。

### 2.3 Reader UI 与阅读样式

#### Task 2.3.1 Reader 模式展示

- **Overall Goal**：提供更稳定、简洁的文章阅读体验。
- **Task Detail**：
  - 在文章详情中展示 Reader 视图。
  - 支持原始内容 / Cleaned HTML / Markdown 预览切换。
  - 显示清洗状态和错误提示。
- **Affected Files**：
  - `src/mercury/ui/article_view.py`
  - `src/mercury/ui/main_window.py`
  - `src/mercury/services/reader_service.py`
- **Key Design**：
  - UI 不直接执行清洗逻辑。
  - 大文本渲染避免明显卡顿。
- **Verification**：
  - 打开含复杂结构文章时，Reader 视图可显示。
  - 切换视图不会丢失文章选择状态。
  - 清洗失败时 UI 显示 fallback 内容和可理解提示。

#### Task 2.3.2 自定义阅读样式

- **Overall Goal**：允许用户调整基础阅读体验。
- **Task Detail**：
  - 支持字体大小、行高、内容宽度、主题等基础设置。
  - 设置保存到本地。
- **Affected Files**：
  - `src/mercury/ui/preferences.py`
  - `src/mercury/config/settings.py`
  - `src/mercury/storage/repositories.py`
- **Key Design**：
  - 设置默认本地保存。
  - 设置变更即时生效或明确提示。
- **Verification**：
  - 修改阅读设置后 Reader 视图变化可见。
  - 重启应用后设置仍存在。

### 2.4 国际化与跨平台冒烟验证

#### Task 2.4.1 UI 中英文切换

- **Overall Goal**：界面支持英文和简体中文，无需重启即可切换。
- **Task Detail**：
  - 抽取按钮、菜单、设置项、错误提示文案。
  - 实现语言切换设置。
- **Affected Files**：
  - `src/mercury/i18n/`
  - `src/mercury/ui/`
  - `tests/test_i18n.py`
- **Key Design**：
  - 不把用户可见字符串散落在业务逻辑中。
  - 缺失翻译时有明确 fallback。
- **Verification**：
  - 切换语言后主窗口、按钮、菜单、设置项、错误提示更新。
  - 不需要重启应用。

#### Task 2.4.2 第二阶段人工验收脚本

- **Overall Goal**：独立验证阅读体验增强是否完成。
- **Task Detail**：
  - 编写 `docs/verification/stage-2.md`。
  - 准备复杂 HTML fixture。
- **Affected Files**：
  - `docs/verification/stage-2.md`
  - `tests/fixtures/html/`
- **Key Design**：
  - 验证不依赖 AI。
  - 验证不依赖不稳定网络。
- **Verification**：
  - 按文档可验证 Cleaned HTML、Cleaned Markdown、Reader 视图、语言切换、样式设置。

## Stage 2 Verification Gate

- `uv run pytest tests/test_reader_cleaner.py tests/test_markdown_converter.py tests/test_i18n.py`
- 清洗失败不会导致文章不可读。
- Cleaned HTML / Markdown 保留标题、链接、图片、列表、表格、代码块。
- 英文和简体中文可无需重启切换。
- 无 LLM 配置时，第一阶段和第二阶段功能全部可用。

---

# 第三阶段｜AI 功能接入

## Overall Goal

在不破坏基础阅读功能的前提下，引入可配置、可替换、可测试的 AI 能力：统一 LLM Provider、Summary Agent、Translation Agent，并保证失败时不会影响阅读。

## Completion Definition

本阶段完成后，用户可以配置任意兼容标准 API 的 LLM Provider 来生成摘要和翻译；测试环境可以使用 Mock Provider 完成全自动验证；没有 API Key 或调用失败时，文章仍然可正常阅读。

## Sub-phases

### 3.1 LLM Provider 抽象

#### Task 3.1.1 定义 Provider 接口与配置模型

- **Overall Goal**：所有 AI 调用都通过统一抽象完成。
- **Task Detail**：
  - 定义 Provider 接口。
  - 支持 Base URL、模型名、API Key、超时等用户配置。
  - 配置默认本地保存。
- **Affected Files**：
  - `src/mercury/llm/provider.py`
  - `src/mercury/llm/config.py`
  - `src/mercury/storage/repositories.py`
  - `tests/test_llm_provider.py`
- **Key Design**：
  - 不在业务逻辑中写死厂商、模型名、Base URL、API Key。
  - API Key 不进入日志。
  - Provider 可被 Mock。
- **Verification**：
  - Mock Provider 可返回固定响应。
  - 配置保存和读取成功。
  - 搜索代码确认业务逻辑没有硬编码具体厂商配置。

#### Task 3.1.2 AI 设置界面

- **Overall Goal**：用户可以主动配置和启用 AI 功能。
- **Task Detail**：
  - 提供 Provider 配置页面。
  - 提供连接测试入口。
  - 明确提示文章内容只会在用户主动触发 AI 功能时发送。
- **Affected Files**：
  - `src/mercury/ui/ai_settings.py`
  - `src/mercury/ui/preferences.py`
  - `src/mercury/llm/config.py`
- **Key Design**：
  - AI 功能默认不阻塞基础阅读。
  - 用户未配置 Provider 时，摘要/翻译入口显示可理解提示。
- **Verification**：
  - 未配置 Provider 时基础阅读功能正常。
  - 使用 Mock Provider 可通过连接测试。
  - UI 不显示或记录完整 API Key。

### 3.2 Summary Agent

#### Task 3.2.1 摘要工作流

- **Overall Goal**：为文章生成可配置摘要。
- **Task Detail**：
  - 支持摘要语言设置。
  - 支持详细程度设置。
  - 支持自定义 Prompt。
  - 保存摘要结果到本地。
- **Affected Files**：
  - `src/mercury/agents/summary_agent.py`
  - `src/mercury/domain/ai_result.py`
  - `src/mercury/storage/repositories.py`
  - `tests/test_summary_agent.py`
- **Key Design**：
  - 输入优先使用 Cleaned Markdown 或 Cleaned HTML。
  - 调用失败时返回可理解错误，不影响文章阅读。
  - 测试不依赖真实在线 LLM。
- **Verification**：
  - Mock Provider 下可生成确定性摘要。
  - 不同语言和详细程度会进入 Prompt 构造。
  - Provider 失败时 UI 和 service 返回可理解错误。

#### Task 3.2.2 摘要 UI

- **Overall Goal**：用户可以在文章详情中查看、重新生成摘要。
- **Task Detail**：
  - 在文章详情页增加摘要区域。
  - 支持生成、重新生成、查看生成时间。
- **Affected Files**：
  - `src/mercury/ui/article_view.py`
  - `src/mercury/ui/summary_panel.py`
- **Key Design**：
  - 摘要生成异步执行，避免 UI 卡顿。
  - 摘要失败不影响正文显示。
- **Verification**：
  - Mock Provider 下点击生成后出现摘要。
  - 失败时正文仍可阅读。

### 3.3 Translation Agent

#### Task 3.3.1 翻译工作流

- **Overall Goal**：为文章生成段落对照翻译。
- **Task Detail**：
  - 支持自定义 Prompt。
  - 长文章分段处理。
  - 保留段落顺序。
  - 失败时保留原文可读。
- **Affected Files**：
  - `src/mercury/agents/translation_agent.py`
  - `src/mercury/domain/translation.py`
  - `src/mercury/storage/repositories.py`
  - `tests/test_translation_agent.py`
- **Key Design**：
  - 段落切分和结果合并必须可测试。
  - 不因某个分段失败丢失全文原文。
- **Verification**：
  - Mock Provider 下多段文章翻译后顺序一致。
  - 长文章被分段处理。
  - 某一段失败时仍保留原文和错误信息。

#### Task 3.3.2 原文译文对照 UI

- **Overall Goal**：用户可以在阅读文章时对照查看原文和译文。
- **Task Detail**：
  - 实现段落对照展示。
  - 支持重新翻译。
  - 显示翻译状态和错误。
- **Affected Files**：
  - `src/mercury/ui/translation_panel.py`
  - `src/mercury/ui/article_view.py`
- **Key Design**：
  - 对照 UI 使用 translation service 的结构化结果。
  - 翻译失败不隐藏原文。
- **Verification**：
  - Mock Provider 下原文和译文按段落对应显示。
  - 失败时仍显示原文。

### 3.4 第三阶段验收文档

#### Task 3.4.1 AI 功能验收脚本

- **Overall Goal**：独立验证 AI 功能接入，不依赖真实 API Key。
- **Task Detail**：
  - 编写 `docs/verification/stage-3.md`。
  - 提供 Mock Provider 验收方式。
  - 提供真实 Provider 的可选人工验收步骤。
- **Affected Files**：
  - `docs/verification/stage-3.md`
  - `tests/fixtures/llm/`
- **Key Design**：
  - 自动测试不访问真实网络。
  - 真实 Provider 验证必须由用户主动配置。
- **Verification**：
  - 按文档可验证 Provider、摘要、翻译、失败 fallback。

## Stage 3 Verification Gate

- `uv run pytest tests/test_llm_provider.py tests/test_summary_agent.py tests/test_translation_agent.py`
- 未配置 LLM 时，第一阶段和第二阶段功能完全可用。
- Mock Provider 自动测试通过。
- Provider 调用失败时，摘要/翻译显示可理解错误且文章仍可阅读。
- 代码中不存在硬编码具体 LLM 厂商、模型、Base URL 或 API Key 的业务逻辑。

---

# 第四阶段｜信息整理与导出

## Overall Goal

在核心阅读和 AI 能力稳定后，增加信息整理能力：笔记、标签、筛选、单篇与多篇导出。Tag Agent 作为选做增强，不得为了它提前复杂化核心架构。

## Completion Definition

本阶段完成后，用户可以给文章添加笔记和标签，按标签筛选文章，并导出单篇或多篇文章。即使不启用 Tag Agent，手动标签、筛选和导出也必须可用。

## Sub-phases

### 4.1 笔记与文摘

#### Task 4.1.1 文章笔记

- **Overall Goal**：用户可以为文章保存本地笔记。
- **Task Detail**：
  - 支持为文章新增、编辑、删除笔记。
  - 笔记默认保存在本地。
  - 删除前避免误删。
- **Affected Files**：
  - `src/mercury/domain/note.py`
  - `src/mercury/storage/repositories.py`
  - `src/mercury/ui/notes_panel.py`
  - `tests/test_notes.py`
- **Key Design**：
  - 笔记与文章通过稳定 ID 关联。
  - 删除笔记需要明确用户动作。
- **Verification**：
  - 新增、编辑、删除笔记可自动测试。
  - 重启应用后笔记仍存在。

### 4.2 标签与筛选

#### Task 4.2.1 手动标签管理

- **Overall Goal**：用户可以用标签整理文章。
- **Task Detail**：
  - 支持创建、重命名、删除标签。
  - 支持给文章添加/移除标签。
  - 支持按标签筛选文章。
- **Affected Files**：
  - `src/mercury/domain/tag.py`
  - `src/mercury/storage/repositories.py`
  - `src/mercury/ui/tag_panel.py`
  - `tests/test_tags.py`
- **Key Design**：
  - 标签系统本身不依赖 AI。
  - 删除标签前避免误删。
- **Verification**：
  - 手动标签增删改查通过自动测试。
  - 按标签筛选结果正确。
  - 未启用 Tag Agent 时标签系统仍可用。

#### Task 4.2.2 Tag Agent（选做）

- **Overall Goal**：在不影响手动标签功能的前提下，支持自动打标。
- **Task Detail**：
  - 复用统一 LLM Provider。
  - 支持自定义 Prompt。
  - 生成标签建议，由用户确认后应用。
- **Affected Files**：
  - `src/mercury/agents/tag_agent.py`
  - `src/mercury/ui/tag_suggestion_panel.py`
  - `tests/test_tag_agent.py`
- **Key Design**：
  - 选做功能，不作为第四阶段基础验收的阻塞项。
  - 自动打标不得绕过用户确认直接修改大量文章。
- **Verification**：
  - Mock Provider 下可生成标签建议。
  - 用户拒绝建议时不修改文章标签。
  - 未实现或未启用 Tag Agent 时，手动标签功能不受影响。

### 4.3 单篇与多篇导出

#### Task 4.3.1 单篇文章导出

- **Overall Goal**：用户可以导出当前文章。
- **Task Detail**：
  - 支持导出 Cleaned Markdown。
  - 可选择包含摘要、翻译、笔记、标签。
  - 文件写出使用 UTF-8。
- **Affected Files**：
  - `src/mercury/services/export_service.py`
  - `src/mercury/ui/export_dialog.py`
  - `tests/test_export_single.py`
- **Key Design**：
  - 导出逻辑不依赖 UI。
  - 缺少摘要或翻译时不阻塞导出。
- **Verification**：
  - 导出的 Markdown 可包含标题、链接、正文、笔记等选项。
  - UTF-8 内容正确保存。

#### Task 4.3.2 多篇文章批量导出

- **Overall Goal**：用户可以批量导出筛选后的文章。
- **Task Detail**：
  - 支持按选中文章、订阅源、标签范围导出。
  - 支持导出为多个 Markdown 文件或合并文件。
  - 处理文件名冲突。
- **Affected Files**：
  - `src/mercury/services/export_service.py`
  - `src/mercury/ui/export_dialog.py`
  - `tests/test_export_batch.py`
- **Key Design**：
  - 批量导出过程可取消或至少有进度提示。
  - 文件名做跨平台安全处理。
- **Verification**：
  - 多篇导出数量正确。
  - 同标题文章不会互相覆盖。
  - Windows/Linux/macOS 非法文件名字符被安全处理。

### 4.4 第四阶段验收文档

#### Task 4.4.1 信息整理与导出验收脚本

- **Overall Goal**：独立验证第四阶段功能。
- **Task Detail**：
  - 编写 `docs/verification/stage-4.md`。
  - 覆盖笔记、标签、筛选、单篇导出、多篇导出。
  - Tag Agent 写入选做验收项。
- **Affected Files**：
  - `docs/verification/stage-4.md`
- **Key Design**：
  - 基础验收不依赖 AI。
  - 选做验收单独列出。
- **Verification**：
  - 按文档可完成手动整理和导出。
  - 可选验证 Tag Agent，不影响基础验收结论。

## Stage 4 Verification Gate

- `uv run pytest tests/test_notes.py tests/test_tags.py tests/test_export_single.py tests/test_export_batch.py`
- 笔记、标签、配置默认本地保存。
- 删除笔记或标签前有防误删机制。
- 单篇和多篇导出文件使用 UTF-8。
- 未启用 AI 时，笔记、手动标签、筛选、导出仍可用。
- Tag Agent 如实现，必须复用统一 LLM Provider 和 Prompt 配置机制。

---

# 2. 交付节奏建议

## 每个阶段的固定交付物

每个阶段结束时至少提交：

1. 可运行代码。
2. 自动测试。
3. 人工验收文档。
4. 决策记录或阶段总结。
5. 清晰、聚焦的 Git 提交。

## 每个阶段的通用检查清单

- 是否仍然符合本地优先？
- 是否泄露或上传了用户数据？
- 是否破坏 Windows、Linux、macOS 兼容性？
- 是否把 LLM 厂商、模型、Base URL、API Key 写死了？
- 是否为必要模块增加或更新测试？
- 是否更新了相关文档？
- 是否留下了无用依赖、临时代码或大而混乱的提交？

## 推荐目录结构

```text
mercury/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── INITIAL.md
├── plan.md
├── docs/
│   ├── decisions/
│   └── verification/
│       ├── stage-1.md
│       ├── stage-2.md
│       ├── stage-3.md
│       └── stage-4.md
├── src/
│   └── mercury/
│       ├── agents/
│       ├── config/
│       ├── domain/
│       ├── i18n/
│       ├── llm/
│       ├── services/
│       ├── storage/
│       └── ui/
└── tests/
    ├── fixtures/
    ├── test_feed_parser.py
    ├── test_opml_parser.py
    ├── test_storage.py
    ├── test_article_deduplication.py
    ├── test_reader_cleaner.py
    ├── test_markdown_converter.py
    ├── test_i18n.py
    ├── test_llm_provider.py
    ├── test_summary_agent.py
    ├── test_translation_agent.py
    ├── test_notes.py
    ├── test_tags.py
    ├── test_export_single.py
    └── test_export_batch.py
```

# 3. 非目标 / 延后事项

以下内容不进入前四阶段核心目标，除非另行调整计划：

- 云同步。
- 账号系统。
- 订阅付费系统。
- 将任一 LLM 厂商作为唯一支持对象。
- 依赖真实在线 LLM 或真实 API Key 的自动测试。
- 为 Tag Agent 提前复杂化核心阅读、标签或 Provider 架构。
