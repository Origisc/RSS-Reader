# Translation Agent 翻译工作流（成员 B）

## 完成内容

- Provider 中立的 `TranslationAgent`。
- 目标语言、自定义 Prompt 和可配置长文切片长度。
- Cleaned HTML → Cleaned Markdown → raw HTML 内容优先级；优先复用 Reader
  实际渲染内容的段落边界。
- HTML 分段与老师项目保持同一基线：有文本的 `<p>`、整块 `<ul>`、整块
  `<ol>` 各算一个源段落；列表内部元素不重复拆段。Markdown 仅在 Cleaned
  HTML 不可用时按空行分段。
- 对没有 Cleaned HTML/Markdown、正文仅由 RSS 裸文本与连续 `<br>` 组成的
  旧式 Feed，按双换行恢复段落；即使后端在末尾追加了单独的 `<p>` 来源
  链接，也不会误把该链接当成全文唯一段落。兼容 Unicode 行/段分隔符。
- 较长段落默认按不超过 160 字符的内部片段处理，优先在句号、问号、
  感叹号处分割，其次使用逗号等从句边界；片段译文仍按原顺序合并成
  一个段落译文，避免小模型只翻译首句而遗漏 `However` 等后续内容。
- 切片后若产生过短尾片段，会将其合并回前一片段，避免模型直接复制
  `the cluster.` 等失去上下文的短语。
- 对界面支持的简体中文和英文目标做本地字符脚本校验；若 Provider 返回
  原文语言的摘要、扩写或复制内容，最多发送两次强化纠正请求。简体中文
  请求使用中文强约束指令和 `temperature=0`，并拒绝把“应准确翻译”等
  任务说明当作译文。
- 对长度不少于 80 字符的源片段进行本地完整性校验；译文明显过短时自动
  要求 Provider 从头到尾重新翻译一次，重试后仍不完整则丢弃半段译文。
- 多片段段落若仍有片段校验失败，会在 1200 字符以内携带完整原段执行
  段落级恢复；恢复成功后使用完整段落译文替换零散结果，只有恢复也失败
  时才显示“译文暂不可用”并保留原文。
- 每个源段落完成后通过可选进度回调发送结构化快照；回调异常不会中断
  Provider 翻译或最终结果保存。
- 段落级成功、部分成功、失败状态；单段失败后继续翻译后文。
- 所有结果始终保留原文，Provider 错误中的 API Key 会被遮盖。
- 可替换的 `TranslationResultStore`、进程内测试实现和生产 SQLite 实现。

Agent 层只返回结构化结果，不直接修改或隐藏 Article Reader 的正文。当前
Task 3.3.2 的 Reader 双语对照展示已完成，详见
`docs-B/delevopment/translation-ui-member-b.md`。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_translation_agent tests.test_llm_provider -v
```

测试全部使用 `MockLLMProvider`，覆盖 Markdown/HTML 段落提取、`p/ul/ol`
稳定边界、旧式 RSS 正文与末尾来源链接的混合结构、长文切片、顺序保持、
目标语言偏离后的纠正重试与错误输出丢弃、部分失败、空响应、未配置
Provider、密钥脱敏和存储失败，不访问网络或真实 API Key。

## 本地持久化

正式应用通过 `SQLiteTranslationResultStore` 实现以下接口：

```python
def save(self, result: TranslationResult) -> None: ...
def latest_for_article(self, article_id: str) -> TranslationResult | None: ...
```

翻译头信息和所有段落在一个 SQLite 事务中保存，重启后仍按段落顺序恢复，
失败段落的原文和错误状态不会丢失。`InMemoryTranslationResultStore` 仅保留
给独立测试和 Mock 联调。
