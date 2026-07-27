# 导入Feed后自动刷新文章列表计划

## 问题分析

**当前流程：**
1. 用户点击"添加feed"，输入URL后调用 `_add_feed()`
2. `_add_feed()` 调用 `_run_service_action()` 执行 `article_service.add_feed()`
3. `add_feed()` 内部调用 `FeedUseCase.add_single_feed()` 下载并保存文章
4. `_run_service_action()` 执行完后调用 `_load_initial_data()` 刷新数据
5. `_load_initial_data()` 刷新侧边栏和文章列表，但**不会自动选中新添加的feed**

**问题根源：**
添加feed后，虽然文章已保存到数据库，但当前选中的feed可能仍是"全部文章"或其他feed，用户需要手动点击新feed才能看到文章列表。

## 修复方案

### 修改文件列表

| 文件 | 修改内容 |
|------|---------|
| `domain/feed/use_cases.py` | `add_single_feed()` 返回新添加feed的ID |
| `src/mercury/services/backend_article_service.py` | `add_feed()` 返回feed ID信息 |
| `src/mercury/ui/main_window.py` | `_run_service_action()` 支持回调函数；`_add_feed()` 在添加成功后自动选中新feed |

### 具体修改步骤

#### 1. 修改 `FeedUseCase.add_single_feed()` (domain/feed/use_cases.py)

当前实现只打印成功信息，需要修改为返回新添加feed的ID：

```python
def add_single_feed(self, xml_url:str) -> int | None:
    print(f"正在下载并解析: {xml_url} ...")
    try:
        res = requests.get(xml_url, timeout=10)
        feed_data = feedparser.parse(res.text)
        # ... 现有逻辑 ...
        feed_id = self.db.add_feed(feed_title, xml_url, html_url)
        self.db.save_articles(feed_id, feed_data.entries)
        print(f"成功添加订阅源: {feed_title}，抓取了 {len(feed_data.entries)} 篇文章。")
        return feed_id  # 返回feed ID
    except Exception as e:
        print(f"添加失败: {e}")
        return None
```

#### 2. 修改 `BackendArticleService.add_feed()` (src/mercury/services/backend_article_service.py)

当前实现返回字符串消息，需要修改为返回包含feed ID的消息，以便UI层识别：

```python
def add_feed(self, xml_url: str) -> str:
    before_count = len(self._db.get_all_feeds())
    feed_id = self._feed_use_case.add_single_feed(xml_url)
    after_count = len(self._db.get_all_feeds())

    if after_count > before_count and feed_id:
        return f"Feed added and refreshed. feed_id:{feed_id}"
    elif after_count > before_count:
        return "Feed added and refreshed."

    return "Feed add request finished. It may already exist or failed validation."
```

#### 3. 修改 `MainWindow._run_service_action()` (src/mercury/ui/main_window.py)

添加可选的回调函数参数，在服务操作完成后执行：

```python
def _run_service_action(self, action, started_message: str, callback=None) -> None:
    self.statusBar().showMessage(started_message, 5000)
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    try:
        message = action()
    except Exception as exc:
        QMessageBox.warning(...)
        self.statusBar().showMessage(str(exc), 8000)
        return
    finally:
        QApplication.restoreOverrideCursor()

    self._load_initial_data()
    if callback:
        callback(message)
    self.statusBar().showMessage(message, 8000)
```

#### 4. 修改 `MainWindow._add_feed()` (src/mercury/ui/main_window.py)

在添加feed成功后，从返回消息中提取feed ID并自动选中：

```python
def _add_feed(self) -> None:
    xml_url, accepted = QInputDialog.getText(...)
    if not accepted or not xml_url.strip():
        return

    self._run_service_action(
        lambda: self.article_service.add_feed(xml_url.strip()),
        self.translator.text("status.add_feed_started"),
        callback=self._on_feed_added,
    )

def _on_feed_added(self, message: str) -> None:
    feed_id_start = message.find("feed_id:")
    if feed_id_start != -1:
        feed_id = message[feed_id_start + 8:].strip()
        if feed_id:
            self._show_feed_articles(feed_id)
```

### 风险与注意事项

1. **兼容性**：修改后 `_run_service_action()` 的回调参数是可选的，不会影响现有调用
2. **错误处理**：如果feed添加失败（返回None），不会尝试选中不存在的feed
3. **feed已存在**：如果feed已存在，返回消息不包含feed_id，不会触发选中操作

## 验证步骤

1. 启动应用：`python main.py`
2. 添加新的feed URL
3. 验证：添加成功后，侧边栏自动选中新feed，文章列表自动显示该feed的文章
4. 验证：添加已存在的feed时，不会自动选中（因为消息不包含feed_id）
