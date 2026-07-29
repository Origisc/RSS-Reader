# Feed 与 OPML 本地路径导入验证

## 自动验证

```powershell
uv run python -m unittest tests.test_feed_import_paths -v
```

测试使用临时 UTF-8 RSS 和 OPML 文件，不访问真实网络，也不修改用户数据库。

覆盖范围：

- 使用绝对路径添加本地 RSS Feed。
- 使用相对于当前工作目录的路径添加本地 RSS Feed。
- 使用绝对路径导入 OPML。
- 使用相对路径导入 OPML。
- OPML 中的相对 Feed 路径以 OPML 文件所在目录为基准解析。
- OPML 中的绝对 Feed 路径保持为规范化绝对路径。
- 文件不存在、路径不是文件、UTF-8 读取失败、Feed 格式无效、OPML 格式
  无效及 OPML 不包含 Feed 时返回不同错误。

## 人工验证

从仓库根目录启动 Mercury：

```powershell
uv run python main.py
```

### 添加本地 Feed

1. 准备一个 UTF-8 编码的 RSS 或 Atom XML 文件。
2. 在“添加 Feed”中分别输入：
   - 相对路径，例如 `tests/fixtures/feeds/sample.xml`；
   - 绝对路径，例如 `E:\feeds\sample.xml`。
3. 确认两种输入都能新增订阅源并显示文章。
4. 输入不存在的路径，确认对话框明确显示解析后的文件位置。
5. 输入普通文本或损坏的 XML，确认提示“不是有效的 RSS 或 Atom Feed”。

### 导入 OPML

1. 分别通过相对路径和绝对路径调用 `ArticleService.import_opml`。
2. OPML 的 `xmlUrl` 可以是 HTTP(S) URL、绝对本地 Feed 路径，也可以是
   相对于 OPML 文件所在目录的本地 Feed 路径。
3. 确认导入后本地 Feed 路径以规范化绝对路径保存，重启或刷新时不依赖
   原来的相对工作目录。
4. 分别验证不存在的 OPML、损坏的 XML 和不含 `xmlUrl` 的 OPML，确认
   界面显示不同且可理解的错误信息，不再显示“新增 0 个”的伪成功结果。
