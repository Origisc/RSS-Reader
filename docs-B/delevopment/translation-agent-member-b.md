# Translation Agent 翻译工作流（成员 B）

## 完成内容

- Provider 中立的 `TranslationAgent`。
- 目标语言、自定义 Prompt 和可配置长文切片长度。
- Cleaned Markdown → Cleaned HTML → raw HTML 内容优先级。
- Markdown 段落切分及标准库 HTML 段落提取。
- 超长段落按标点或空白边界切片，并按原顺序合并译文。
- 段落级成功、部分成功、失败状态；单段失败后继续翻译后文。
- 所有结果始终保留原文，Provider 错误中的 API Key 会被遮盖。
- 可替换的 `TranslationResultStore` 和进程内测试实现。

本任务不提前实现 Task 3.3.2 的对照 UI。翻译失败只返回结构化结果，不会修改或隐藏 Article Reader 的正文。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_translation_agent tests.test_llm_provider -v
```

测试全部使用 `MockLLMProvider`，覆盖 Markdown/HTML 段落提取、长文切片、顺序保持、部分失败、空响应、未配置 Provider、密钥脱敏和存储失败，不访问网络或真实 API Key。

## 成员 A 接口

本地持久化适配器实现以下接口即可接入：

```python
def save(self, result: TranslationResult) -> None: ...
def latest_for_article(self, article_id: str) -> TranslationResult | None: ...
```

当前 `InMemoryTranslationResultStore` 仅用于独立开发、测试和下一步 UI 联调，不提供跨进程持久化。
