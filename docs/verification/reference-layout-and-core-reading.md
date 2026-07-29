# 参考布局与基础阅读链路验证

## 视觉参考

本轮布局参考 `neolee/mercury` 的主界面、标签界面和主题界面，但保留 Mercury 当前的 PySide6、Windows / Linux / macOS 跨平台实现。

落实的视觉结构：

- 统一应用顶栏，提供清晰的产品标题、同步和设置入口。
- 左侧 Feed / Tag 导航、中间文章列表、右侧 Reader 三栏布局。
- 默认列宽调整为约 `230 / 360 / 弹性 Reader`，并设置合理最小宽度。
- Feed 批量操作收进更多菜单，普通状态只保留新增和更多操作。
- 文章列表分别呈现未读圆点、标题、来源、元信息和收藏按钮。
- 侧栏与文章选中项使用圆角整行高亮。
- Reader 使用有限正文宽度、更大的页面留白和随主题变化的纸张配色。
- Summary 保持为 Reader 底部的可折叠区域。

参考来源：

- <https://github.com/neolee/mercury>
- `screenshots/mercury-main.png`
- `screenshots/mercury-tags.png`
- `screenshots/mercury-theme.png`

## 基础链路自动验收

端到端测试覆盖以下顺序：

1. 导入本地 RSS Feed。
2. 重复 Sync，确认文章不会重复。
3. Feed 增加文章后再次 Sync，确认只增加新文章。
4. 导入带分组和重复源的 OPML。
5. 确认 OPML 导入后首批文章立即可读，无需额外手动刷新。
6. 抓取缓存进入清洗与 Markdown 转换流程。
7. 在原始内容、Cleaned HTML、Markdown 三种 Reader 视图中确认内容可见。
8. 删除一个本地 Feed 文件后再次 Sync，确认其他源继续更新，并返回失败源及具体原因。

Reader 处理策略：

- Feed 已缓存正文时，优先在本地直接生成 Cleaned HTML 和 Markdown，
  不等待文章网页请求。
- 网页抓取成功后可在后台升级为完整正文，不阻塞第一次切换。
- 后台正文升级不会清空正在生成或已经显示的 Summary / Translation。
- Agents 设置窗口为启用、禁用控件提供明确的深浅主题文字对比度。
- Reader 会将纯图片 `figure` / `div` 规范化为 Qt 可正确计算
  行高的展示段落，避免图片后出现成百上千像素的空白。
- Reader 图片同时受阅读宽度设置和当前可见区域约束；缩窄窗口时按
  原始宽高比重新计算尺寸，不再被右侧边界裁切。
- 原文、Cleaned HTML、Markdown 与双语对照共用当前文章的本地图片
  缓存；生成翻译后会保留图片，并避免为视图切换重复下载。
- 仅包含网站链接的 Feed 条目会显示本地状态提示，明确区分后台加载、
  404/链接失效和其他抓取错误，同时保留可点击的原网址。

定向验证：

```powershell
uv run python -m unittest tests.test_core_reading_acceptance tests.test_feed_import_paths tests.test_article_list tests.test_article_reader tests.test_sidebar tests.test_compact_layout tests.test_theme -v
```

完整回归：

```powershell
uv run python -m unittest discover -s tests -v
```

本轮执行结果：`349` 项测试全部通过；`compileall` 与
`git diff --check` 同时通过。

## 手动验收

1. 分别切换浅色和深色主题，确认侧栏、文章列表、Reader 和 Summary 的颜色层级一致。
2. 缩窄 Reader，确认长标题自动换行，正文图片完整显示且保持原始比例。
3. 从左侧 `+` 导入单个 Feed，再从更多菜单导入 OPML。
4. 点击顶栏同步按钮，确认成功结果出现在状态栏；让某个源不可访问后再次同步，确认状态栏包含失败源和原因。
5. 选择文章并切换原始内容、Cleaned HTML、Markdown，确认标题、正文、图片、列表、表格和代码块仍可阅读。
6. 对含图片的文章生成翻译并打开双语对照，确认原文段落、译文段落和
   图片都存在；随后再次缩窄窗口，确认图片仍完整显示。
