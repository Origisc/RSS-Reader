# Member B Reader View Switching

## Goal

完成第二阶段中由成员 B 负责的 Reader 展示部分：

- 原始内容、Cleaned HTML、Cleaned Markdown 三种视图入口。
- 视图切换时保留当前文章选择。
- 清洗结果缺失或清洗失败时显示原始内容 fallback。
- 所有新增状态、按钮和错误提示支持简体中文与英文运行时切换。

本次只新增 UI 展示契约和离线测试，不实现成员 A 负责的抓取、清洗、Markdown 转换或数据库持久化。

## Interface

`ReaderDocument` 是 Reader UI 使用的结构化展示对象，字段包括：

- `raw_html`
- `cleaned_html`
- `cleaned_markdown`
- `cleaning_error`

成员 A 的 `ReaderService` 接口稳定后，可以直接把服务结果适配成此对象。当前第一阶段后端只有原始内容时，`ReaderDocument.from_article()` 会保证文章仍可读。

## Offline Verification

自动验证不需要网络、真实数据库、API Key 或 LLM：

```powershell
uv run python -m unittest tests.test_article_reader tests.test_i18n tests.test_theme -v
```

测试覆盖：

1. 三种 Reader 视图可切换。
2. 切换视图不会改变当前文章 ID。
3. 清洗失败时原始内容和错误信息仍可见。
4. 第一阶段文章在没有清洗结果时仍可阅读。

## Manual Verification

1. 运行 `uv run python src/mercury/main.py`。
2. 选择任意本地缓存文章。
3. 确认 Reader 顶部出现“原始内容 / Cleaned HTML / Markdown”切换入口。
4. 当前后端尚无清洗结果时，点击 Cleaned HTML 或 Markdown，确认界面提示不可用并继续显示原始内容。
5. 打开设置切换到 English，确认 Reader 按钮和状态提示即时更新。

## AGENTS.md Check

- 不新增网络请求或数据上传。
- 不在 UI 中实现清洗或 Markdown 转换业务逻辑。
- 不引入 LLM 厂商、模型、Base URL 或 API Key。
- fallback 保证清洗缺失或失败时文章仍可读。
- 自动测试只使用本地结构化 Mock 数据和 Qt 离屏平台。
