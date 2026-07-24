# Reader 双语对照 UI（成员 B）

## 完成内容

- 翻译设置作为紧凑控件嵌入 Reader，不再创建位于页面底部的翻译结果面板。
- 翻译完成后直接在 Reader 正文区域显示双语对照。
- 严格消费结构化 `TranslationResult`，按“原文段落 → 对应译文”交替渲染，
  不从整篇译文字符串重新猜测段落。
- HTML 对照使用与 Translation Agent 相同的 `p/ul/ol` 段落契约：普通段落
  后立即插入一块译文，列表则在整个列表后插入一块译文；标题、图片等不含
  可翻译正文的块不会误占译文位置。
- 对旧式 RSS 的裸文本/`<br><br>` 片段，如果无法安全插回原 HTML，则使用
  `TranslationResult` 中的结构化原文/译文对兜底，仍保持逐段交替而不是只
  显示原文。
- 长文章不再等全部段落完成后才显示：每段 Provider 请求完成后立即更新
  Reader，未完成段落继续保留原文和占位状态，最终结果完成后再进入缓存。
- RAW/Cleaned HTML 不再被转换成纯文本后重建。原始段落、标题、粗体、链接、
  图片、引用、列表和表格保持原有结构，仅在对应内容块结束处插入译文卡片。
- Reader 工具栏提供“显示原文 / 双语对照”切换；双语模式不会改变用户原先
  选择的 Raw、Cleaned HTML 或 Markdown 原文视图。
- Markdown 原文段落继续保留链接、图片、列表等富文本能力。
- 通用翻译响应清理会移除模型返回开头的 `<think>...</think>` 思考区，避免
  本地推理模型把英文分析混入中文译文；正常译文中的同名标签文本不会被误删。
- 部分失败和完全失败的段落始终保留原文，并显示可本地化的失败说明。
- 切换简体中文或 English 时，按钮、提示和状态无需重启即可更新。
- Summary 保持原有独立区域和工作流，不受翻译展示迁移影响。

## 数据流边界

`TranslationPanel` 只负责目标语言、Prompt、触发操作和生成状态。
`TranslationAgent` 负责 Provider 调用与段落结构，`ArticleReader` 只消费
`TranslationResult` 进行展示。UI 不直接访问数据库、网络或 Provider 协议。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.test_article_reader `
  tests.test_bilingual_document `
  tests.test_translation_agent `
  tests.test_translation_panel `
  tests.test_ai_provider_integration -v
```

测试全部使用 Mock Provider 或固定结构化结果，不访问网络或真实 API Key。
覆盖原文/译文逐段交替顺序、Reader 模式切换、Markdown 富文本、RAW HTML
原始结构、列表整块对应、空图片段落过滤、思考区过滤、失败原文兜底、翻译
设置布局、缓存结果恢复和主窗口集成。

## 人工验收

1. 打开一篇至少包含两段英文的文章。
2. 在 Reader 工具栏打开“翻译设置”，选择简体中文并执行翻译。
3. 确认翻译完成后设置自动收起，Reader 显示第一段英文、第一段中文、
   第二段英文、第二段中文，而不是在 Summary 下方显示整篇译文。
4. 点击“显示原文”，确认原始 Reader 内容恢复；再点“双语对照”，确认已生成
   的结构化结果直接恢复，无需再次请求 Provider。
5. 模拟某一段翻译失败，确认该段英文仍完整可读，其他段落继续正常显示译文。
