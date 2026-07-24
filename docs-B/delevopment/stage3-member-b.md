# Stage 3 - Member B Completion Log

## Completion Summary

第三阶段已形成完整的可运行闭环：

- 厂商中立的 `LLMProvider` 与标准 Chat Completions HTTP 适配器。
- 可配置 Base URL、模型、API Key、超时和连接测试的 AI 设置界面。
- 可配置语言、详细度和 Prompt 的 Summary Agent 与异步 Summary UI。
- 可配置目标语言和 Prompt 的 Translation Agent、长文分段、纠错重试、
  渐进式逐段显示和 Reader 内原文/译文对照。
- Provider、摘要和结构化翻译结果默认保存到现有本地 SQLite 数据库，应用
  重启后可恢复。
- Provider、存储或单段翻译失败时，基础阅读和所有原文继续可用。

## Local-first and Privacy Boundary

- 未配置 Provider 时不会发送网络请求。
- 只有用户主动执行连接测试、摘要或翻译时才调用所选 Provider。
- 自动测试全部使用 Mock Provider、内存 HTTP transport 和临时数据库。
- API Key 不进入对象 `repr`、状态栏、异常提示、fixture 或测试输出。
- `database.db` 被 Git 忽略，Mercury 不主动同步用户配置和 AI 结果。
- UI 只调用 Store/Agent 接口，不直接执行 SQL 或 Provider 请求。

## Persistence Design

`src/mercury/storage/ai_repository.py` 提供：

- `SQLiteProviderConfigStore`
- `SQLiteSummaryResultStore`
- `SQLiteTranslationResultStore`

每次数据库操作使用短连接并显式提交、回滚和关闭，支持 Summary/Translation
在线程池中写入。逐段翻译头信息和段落行在同一事务中保存；每篇文章只保留
有限数量的历史结果，避免本地数据库无限增长。

## Verification

Stage 3 定向验收：

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

完整离线回归：

```powershell
uv run python -m unittest discover -s tests -p "test_*.py"
```

人工验收以 `docs/verification/stage-3.md` 为准，尤其检查：

1. 无 Provider 时基础 Reader 正常。
2. 原文和译文逐段一一对应，单段失败仍保留原文。
3. 关闭并重启应用后，Provider 配置、摘要和翻译可以恢复。
4. 本地数据库、真实凭据和私有文章未进入 Git 待提交文件。

## Scope Boundary

本记录只完成 `plan.md` 第三阶段。第四阶段的笔记面板未实现，也不属于本次
交付范围。
