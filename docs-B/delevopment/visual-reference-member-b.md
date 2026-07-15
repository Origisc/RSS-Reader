# Member B Visual Reference Refresh

## Goal

根据老师参考图，将当前 Mock UI 调整为更成熟的 RSS 阅读器形态。

本次只调整成员 B 负责的界面层与运行时文案，不接入真实 Feed、数据库、网络请求或 LLM。

## Changes

- 默认使用深色高密度阅读器视觉。
- 左侧增加 Feeds / Tags 分段按钮和底部状态栏。
- 中间文章列表改为 Entries 风格，展示标题、来源和本地 Mock 元信息。
- 阅读区使用更接近文章正文的排版、深色背景和局部信息卡片。
- 右侧增加常驻 Tags 面板，当前为静态入口，等待后续 TagService / Tag Agent 接入。
- 底部增加 Summary 条，当前为静态入口，等待 Summary Agent 接入。

## Verification

自动验证：

```powershell
uv run python -m unittest discover
```

人工验证：

1. 运行 `uv run python src/mercury/main.py`。
2. 确认默认打开为深色三栏阅读器。
3. 点击不同 Feed，确认 Entries 列表正常刷新。
4. 点击文章，确认 Reader 正文排版正常。
5. 确认右侧 Tags 面板和底部 Summary 条可见。
6. 通过 Settings 切换浅色/深色，确认界面可恢复显示。

## AGENTS.md Check

- 不新增网络请求。
- 不上传用户数据。
- 不写死 LLM 厂商、模型、Base URL 或 API Key。
- UI 仍通过 Mock Service 读取数据。
- 新增测试不依赖真实网络、真实 API Key 或真实 LLM。
