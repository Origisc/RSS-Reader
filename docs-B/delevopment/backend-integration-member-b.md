# Member B Backend Integration

## Goal

把成员 B 的 PySide6 UI 从 Mock Service 接到成员 A 已完成的第一阶段后端能力：

- 添加订阅 Feed
- 导入 OPML
- 批量刷新订阅源
- 文章列表与详情读取

## Implementation

新增：

```text
src/mercury/services/backend_article_service.py
```

该文件是 UI 和成员 A 后端之间的 adapter：

- UI 仍只依赖 `ArticleService` 协议。
- adapter 内部调用 `DBManager`、`FeedUseCase` 和 OPML 导入函数。
- Mock Service 保留，便于成员 B 独立调 UI。

## Verification

自动验证：

```powershell
uv run python -m unittest discover
```

人工验证：

1. 运行 `uv run python src/mercury/main.py`。
2. 点击 Add Feed，输入一个 Feed URL。
3. 点击 Import OPML，选择本地 OPML 文件。
4. 点击 Refresh。
5. 点击左侧 Feed，确认中间 Entries 更新。
6. 点击文章，确认 Reader 显示文章详情。
7. 关闭应用后重新打开，确认本地数据库中的 Feed 和文章仍可读取。

## Notes

- 当前刷新和添加 Feed 暂为同步调用，后续应接入 worker，避免网络慢时阻塞 UI。
- 当前不新增任何 LLM 调用。
- 自动测试不依赖真实网络、真实 API Key 或真实 LLM。
