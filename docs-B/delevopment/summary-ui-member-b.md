# Summary UI 摘要面板（成员 B）

## 完成内容

- 在主窗口底部摘要区域加入语言、详细程度和自定义 Prompt 控件。
- 支持生成摘要、重新生成、显示生成时间和加载当前文章已有摘要。
- 摘要任务通过 `QThreadPool` 后台运行，生成期间正文仍可阅读。
- 文章切换使用请求令牌隔离，旧文章的迟到结果不会覆盖新文章。
- 重新生成失败时保留上一版摘要。
- Provider、空响应、本地读取和本地保存错误均显示中英文提示。
- 未接入摘要服务时禁用生成按钮并提供 AI 设置入口，不伪装成功。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_summary_panel tests.test_summary_agent tests.test_i18n tests.test_theme -v
```

测试使用 `MockLLMProvider`，覆盖即时完成、延迟完成、失败、重新生成、文章切换、结果加载和主窗口正文保护，不依赖网络或真实 API Key。

## 当前接入状态

正式应用尚未提供具体在线 Provider adapter，因此默认摘要面板只展示可理解的配置提示。后续在应用组合入口注入 `SummaryGenerator` 和 `SummaryResultLoader` 后即可启用，无需修改面板。

当前后端文章适配器只提供 raw HTML；面板和 Summary Agent 已支持 Cleaned Markdown / Cleaned HTML，待清洗服务在组合层提供对应内容后即可按既定优先级使用。
