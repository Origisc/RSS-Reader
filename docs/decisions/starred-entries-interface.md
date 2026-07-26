# 星标收藏接口与交互决策

## 状态

已实现。参考
[`neolee/mercury` 的 Starred Entries 设计](https://github.com/neolee/mercury/blob/main/docs/features/star.md)，
在 PySide6 和现有 Mercury 分层架构中保持相同的用户行为。

## 范围

- 星标是文章的本地用户状态，不依赖账号、云同步或 AI。
- “星标”是跨所有订阅源的虚拟集合，位于“全部文章”和真实 Feed 之间。
- 文章列表提供行级星标按钮；点击按钮不得改变当前文章选择。
- 星标集合可继续使用现有“仅未读”筛选。
- 标签、导出和笔记不属于本次实现；笔记面板继续暂缓。

## 数据与 Service 边界

`articles.is_starred` 使用 SQLite 整数布尔值，默认值为 `0`。迁移使用
`ALTER TABLE` 并创建星标查询索引，兼容已有本地数据库。

UI 只调用 `StarredEntryService`：

```python
def set_starred(article_id: str, is_starred: bool) -> None: ...
def list_starred_articles() -> list[Article]: ...
def count_starred_articles() -> int: ...
```

数据库写入成功后 UI 才更新本地投影；失败时保留原状态，并通过可翻译状态消息提示。

Feed 同步使用冲突忽略策略，且抓取、清洗、翻译等更新语句不包含
`is_starred`，因此不会覆盖用户星标。

## UI 行为

- 未星标：显示轮廓星，仅在悬停或选中时绘制。
- 已星标：显示黄色实心星，始终绘制。
- 侧栏星标入口显示实时总数。
- 星标视图标题显示“星标”或 `Starred`。
- 在星标视图取消当前文章星标：
  1. 优先选择下一篇；
  2. 没有下一篇时选择上一篇；
  3. 列表为空时清空选择和 Reader；
  4. 系统接续选择不自动标记为已读。

## 本地优先与跨平台

- 星标只写入本地 SQLite。
- 不产生任何额外网络请求。
- 不引入新依赖。
- 图标由 Qt 绘制，不依赖 macOS 专用资源，可在 Windows、Linux、macOS 使用。

## 测试

自动测试使用内存或临时 SQLite 数据库及 Mock Service，不访问真实网络。
覆盖迁移、重启恢复、同步不覆盖、全局查询、数量、点击隔离、UI 状态更新和
选择接续。
