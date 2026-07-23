# 紧凑阅读界面（成员 B）

## 本次调整

- 主界面改为紧凑三栏：左侧 Feeds/Tags、中间 Entries、右侧 Reader。
- Feeds 和 Tags 使用同一栏的页签切换，不再为标签浏览增加固定宽度。
- 当前文章的标签编辑器改为 Reader 右上角的小型浮层，可关闭，并可从 Reader 顶部或“视图”菜单恢复。
- 移除与侧栏、菜单重复的主工具栏；添加 Feed、导入 OPML、刷新继续由 Feeds 标题旁的按钮和下拉菜单提供。
- Entries 标题栏加入“未读”筛选，使用现有本地阅读状态。
- Reader 正常视图状态不再常驻占位，仅在 fallback 或清洗失败时显示提示。
- Summary 默认收起为 Reader 底部窄条，展开后仍只占 Reader 列。
- Starred 暂不实现，也不构造虚假的存储或交互。

## 独立验证

```powershell
uv run python -m unittest tests.test_compact_layout tests.test_sidebar tests.test_article_list tests.test_article_reader tests.test_summary_panel -v
```

验证覆盖三栏结构、Feed/Tags 页签、标签浮层关闭与恢复、未读筛选、Reader fallback 提示和 Summary 折叠状态；不依赖网络、账号或真实 API Key。
