# Summary Agent 摘要工作流（成员 B）

## 完成内容

- Provider 中立的 `SummaryAgent`。
- 摘要语言、简略/标准/详细三级详细程度、自定义 Prompt。
- Cleaned Markdown → Cleaned HTML → raw HTML 内容优先级。
- 结构化成功、生成但未保存、失败三种结果状态。
- 未配置 Provider、Provider 异常、空响应、无正文、保存失败的 fallback。
- API Key 从 Provider 失败信息中脱敏。
- 可替换的 `SummaryResultStore` 和离线内存实现。

本任务不提前实现 Task 3.2.2 的 UI。基础阅读不导入或依赖 Summary Agent；生成失败只返回结果对象，不会替换、隐藏或清空文章正文。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_summary_agent tests.test_llm_provider -v
```

测试全部使用 `MockLLMProvider`，不访问网络、不使用真实 API Key，也不写入用户数据库。

## 成员 A 接口

本地持久化适配器实现以下方法即可接入：

```python
def save(self, result: SummaryResult) -> None: ...
def latest_for_article(self, article_id: str) -> SummaryResult | None: ...
```

当前 `InMemorySummaryResultStore` 仅用于独立开发、测试和后续 UI 联调，不提供跨进程持久化。
