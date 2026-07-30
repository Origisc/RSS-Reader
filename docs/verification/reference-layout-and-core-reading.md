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
- 应用 UI 使用跨平台无衬线字体栈：Windows 优先 Segoe UI Variable 与
  Microsoft YaHei UI，macOS / Linux 分别回退到 PingFang SC 和
  Noto Sans CJK SC；Reader 长文正文仍保留衬线阅读字体。
- Agents 设置左侧使用无外框导航轨道、固定行高和明确的悬停/选中状态，
  以右侧分隔线替代占满整列的列表框边框。
- AI Provider 表单校验会逐项指出缺失或无效的 Base URL、模型和超时时间，
  并聚焦第一个需要修正的字段。
- Provider 连接测试会区分认证、权限、404、限流、超时、代理、TLS、
  返回格式和本地/远程不可达；远程不可达时列出网络、DNS、VPN/代理及
  Base URL 等可能原因，本地不可达时提示检查 Ollama/本地服务和端口。
- 本地 AI 配置读取或保存失败时区分权限、数据库、本地存储不可用和未知
  错误，同时不展示 API Key 或底层数据库细节。

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
- Reader 会将纯图片 `p` / `figure` / `div` 及其链接、`picture`
  包装规范化为 Qt 可正确计算行高的展示段落；对 WordPress 常见的
  “嵌套 `div` + 图片 + 说明段落”结构，图片块使用 100% 行高，
  说明段落恢复正常行高，避免正文行高按图片高度重复预留空白。
- Reader 图片同时受阅读宽度设置和当前可见区域约束；缩窄窗口时按
  原始宽高比重新计算尺寸，不再被右侧边界裁切。
- Reader 会移除图片所属 `div` / `figure` / `p` 上由源站写死的宽高，
  并在图片尚未下载完成时先按 HTML 声明比例缩放占位尺寸。WordPress
  `wp-caption` 因此不会把窄窗口中的 Qt 文档强制撑宽。
- 原文、Cleaned HTML、Markdown 与双语对照共用当前文章的本地图片
  缓存；生成翻译后会保留图片，并避免为视图切换重复下载。
- 图片下载完成后以 `60ms` 去抖批次渐进显示，不再等待最慢图片；瞬时网络
  失败会在 `250ms` 后重试一次。下载结果注册为 Qt 文档内部图片资源，
  翻译/取消翻译时不再反复生成和解析 Base64 HTML。
- Reader 以文章链接为基准，将相对图片 `src` 规范化为绝对 URL；因此
  原始 Feed 的绝对地址、Cleaned HTML/Markdown 的相对地址和双语对照
  会命中同一个内存缓存。图片批次部分或全部失败后仍会重新渲染当前视图，
  继续发现尚未请求的图片，同时避免对已失败 URL 无限重试。
- 双语对照中的裸 `<img>` 会放入独立媒体块，不再继承前一条译文卡片的
  背景和比例行高，图片下方不会保留与图片高度成比例的空白。
- 原始内容会比较 Feed 正文与已抓取网页的可见文本长度；当 Feed 只是摘要时
  使用完整的本地网页缓存，抓取失败、尚未完成或仅得到较短脚本空壳时仍保留
  Feed 内容作为可读回退。
- 已抓取内容是完整网页时，原始视图只使用主题安全的文章片段，不嵌入源站
  `<head>`、脚本、样式、广告导航或评论外壳；源站白底与文字颜色不会覆盖
  Mercury 当前主题，完整原始网页仍原样保存在本地缓存中。
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

本轮执行结果：`373` 项测试全部通过；`compileall` 与
`git diff --check` 同时通过。

## 手动验收

1. 分别切换浅色和深色主题，确认侧栏、文章列表、Reader 和 Summary 的颜色层级一致。
2. 缩窄 Reader，确认长标题自动换行，正文图片完整显示且保持原始比例。
3. 从左侧 `+` 导入单个 Feed，再从更多菜单导入 OPML。
4. 点击顶栏同步按钮，确认成功结果出现在状态栏；让某个源不可访问后再次同步，确认状态栏包含失败源和原因。
5. 选择文章并切换原始内容、Cleaned HTML、Markdown，确认标题、正文、图片、列表、表格和代码块仍可阅读。
6. 对含图片的文章生成翻译并打开双语对照，确认原文段落、译文段落和
   图片都存在；随后再次缩窄窗口，确认图片仍完整显示。
7. 在 Agents 设置中分别测试空配置、本地 Ollama 未启动、远程地址不可达
   和错误 API Key，确认提示给出不同原因和可操作的排查方向。
8. 打开包含 WordPress 图片说明的文章，在原始内容和 Cleaned HTML 中
   确认图片紧接说明文字、说明后仅保留正常段落间距；本轮以本地缓存文章
   `Scattered Spider Hackers Plead Guilty on Day 1 of Trial` 实测两种
   视图的两张大图，图片到说明的额外间距均为 `0px`。
9. 对本地缓存文章
   `Build your own Dial-up ISP with a Raspberry Pi` 的真实
   `cleaned_html` 与 56 段翻译执行双语渲染：段落完全对齐，相对图片地址
   成功命中绝对 URL 缓存，渲染结果包含图片数据且不再保留损坏的相对地址。
10. 同一文章的 Feed 内容仅有 `853` 个字符，抓取缓存有 `24784` 个字符；
    原始内容现选择完整抓取缓存，并确认包含 `Hardware`、`Software`、
    `Dial-up over WiFi` 与 `Conclusion` 等后续章节。
11. 使用该文章的 `14` 张图片和 `56` 段翻译连续执行十次翻译/取消翻译
    往返（共二十次视图渲染）：图片全部使用 Qt 内部资源、HTML 中不含
    Base64，本机离线总耗时约 `0.26s`。
12. 使用 `krebsonsecurity.com` 的真实 Feed 正文和图片进行窄窗口渲染：
    修复前 604px 可视区域会产生 832px 文档和 228px 横向溢出；修复后
    文档宽度保持 604px、横向溢出为 `0px`，图片及说明文字均完整显示。
13. 抓取 `krebsonsecurity.com` 的完整网页并生成原始视图：展示内容包含
    文章结尾，但不包含 `<head>`、源站 `<style>`、Post navigation 或评论；
    深色 Reader 背景保持 `#191b1f`，不再被源站白底覆盖。
