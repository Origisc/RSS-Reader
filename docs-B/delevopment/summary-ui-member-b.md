# Summary UI 摘要面板（成员 B）

## 完成内容

- 将摘要区域嵌入 Reader 右栏下方，并加入语言、详细程度和自定义 Prompt 控件；摘要不再横跨 Feeds 和 Entries。
- Reader 与 Summary 使用纵向分割器，可拖动调整高度；隐藏 Summary 后 Reader 自动占满右栏。
- 支持生成摘要、重新生成、显示生成时间和加载当前文章已有摘要。
- 摘要任务通过 `QThreadPool` 后台运行，生成期间正文仍可阅读。
- 文章切换使用请求令牌隔离，旧文章的迟到结果不会覆盖新文章。
- 重新生成失败时保留上一版摘要。
- Provider、空响应、本地读取和本地保存错误均显示中英文提示。
- 未接入摘要服务时显示可理解提示并通过生成按钮引导到 AI 设置，不伪装成功。

## 可见性修正

- 选中文章后生成按钮始终以清晰的主按钮显示。
- 尚未注入摘要服务时，点击生成按钮会打开 AI 设置，不再以低对比度禁用态静默显示。
- 深色主题显式设置输入文字、占位文字、下拉弹出列表、状态文字和按钮颜色，避免不同操作系统的原生调色板回退成黑字。
- 关闭摘要面板后，可通过“视图 → 摘要面板”重新打开；同一运行会话中的摘要状态不会因隐藏面板而重建。
- Reader 工具栏提供可勾选的“摘要”按钮和 `Ctrl+Shift+S` 快捷键；收起后仅保留 Reader 底部的窄标题条，再次点击恢复，后台任务和会话内摘要不受影响。
- Summary 标题条本身可以展开或收起；仍可通过 Reader 工具栏、“视图 → 摘要面板”或 `Ctrl+Shift+S` 控制。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_summary_panel tests.test_summary_agent tests.test_i18n tests.test_theme -v
```

测试使用 `MockLLMProvider`，覆盖即时完成、延迟完成、失败、重新生成、文章切换、结果加载和主窗口正文保护，不依赖网络或真实 API Key。

## 当前接入状态

正式应用尚未提供具体在线 Provider adapter，因此默认摘要面板只展示可理解的配置提示。后续在应用组合入口注入 `SummaryGenerator` 和 `SummaryResultLoader` 后即可启用，无需修改面板。

当前后端文章适配器只提供 raw HTML；面板和 Summary Agent 已支持 Cleaned Markdown / Cleaned HTML，待清洗服务在组合层提供对应内容后即可按既定优先级使用。
