# Summary Agent 摘要工作流（成员 B）

## 完成内容

- Provider 中立的 `SummaryAgent`。
- 摘要语言、简略/标准/详细三级详细程度、自定义 Prompt。
- 所选摘要语言作为强制系统约束；自定义 Prompt 只能调整内容和结构，不能
  覆盖摘要语言。Provider 返回明显错误语言时，后续请求不再重新摘要，而是
  移除自定义 Prompt 干扰并对已生成摘要做专用语言校正，整个流程最多三次
  Provider 调用。
- Cleaned Markdown → Cleaned HTML → raw HTML 内容优先级。
- 结构化成功、生成但未保存、失败三种结果状态。
- 未配置 Provider、Provider 异常、空响应、无正文、保存失败的 fallback。
- API Key 从 Provider 失败信息中脱敏。
- 可替换的 `SummaryResultStore`、离线内存实现和生产 SQLite 实现。

本任务不提前实现 Task 3.2.2 的 UI。基础阅读不导入或依赖 Summary Agent；生成失败只返回结果对象，不会替换、隐藏或清空文章正文。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_summary_agent tests.test_llm_provider -v
```

测试全部使用 `MockLLMProvider` 和临时数据库，不访问网络、不使用真实 API
Key，也不污染用户数据库。

## 本地持久化

正式应用通过 `SQLiteSummaryResultStore` 实现以下边界：

```python
def save(self, result: SummaryResult) -> None: ...
def latest_for_article(self, article_id: str) -> SummaryResult | None: ...
```

摘要保存在现有本地 `database.db`，重新启动应用后会按文章加载最近一次结果。
`InMemorySummaryResultStore` 仅保留给独立测试和 Mock 联调。
