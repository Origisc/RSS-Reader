# Cleaned HTML/Markdown 视图不可用问题修复指南

## 问题描述

用户导入 Feed 或 OPML 后，点击文章查看 Cleaned HTML 或 Markdown 视图时，始终提示"暂不可用，已显示原始内容"。

## 根本原因

前端 `_show_article()` 方法只读取数据库中已有的文章数据，**没有触发抓取和清洗流程**。

### 数据流转问题

```
导入Feed → 文章保存到数据库（只有content_html，无original_html）
    ↓
用户点击文章 → get_article() 获取文章（original_html为空）
    ↓
创建ReaderDocument → cleaned_html/cleaned_markdown都为空
    ↓
用户切换到Cleaned HTML视图 → resolve()检查为空 → 返回fallback
    ↓
显示"暂不可用，已显示原始内容"
```

### 关键代码位置

[src/mercury/ui/main_window.py#L402-L412](file:///d:/RSS-Reader/src/mercury/ui/main_window.py#L402-L412)

```python
def _show_article(self, article_id: str) -> None:
    article = self.article_service.get_article(article_id)
    # ...
    document = ReaderDocument.from_article(article)  # ← 只读取，不触发抓取/清洗
    self.article_reader.show_article(article, document)
```

## 修复方案

### 修改文件

**文件**: `src/mercury/ui/main_window.py`

### 修改位置

在 `_show_article()` 方法中，创建 `ReaderDocument` 之前，添加后台任务触发抓取和清洗。

### 参考代码

```python
def _show_article(self, article_id: str) -> None:
    article = self.article_service.get_article(article_id)

    if article is None:
        self.article_reader.show_welcome()
        self.summary_panel.clear_article()
        self.translation_panel.clear_article()
        return

    # ============ 新增：自动触发抓取和清洗 ============
    self._ensure_article_processed(article_id)
    # ==================== 结束 ====================

    document = ReaderDocument.from_article(article)
    self.article_reader.show_article(article, document)
    # ... 后续代码不变
```

### 添加后台处理方法

在 `MainWindow` 类中添加以下方法：

```python
def _ensure_article_processed(self, article_id: str) -> None:
    """确保文章已完成抓取和清洗，在后台异步执行。"""
    from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject

    class _ArticleProcessor(QRunnable):
        def __init__(self, service, article_id):
            super().__init__()
            self.service = service
            self.article_id = article_id

        def run(self):
            article = self.service.get_article(self.article_id)
            if article is None:
                return

            # 步骤1：如果没有原始HTML，先抓取
            if not article.original_html:
                self.service.fetch_article_content(self.article_id)
                article = self.service.get_article(self.article_id)
                if article is None or not article.original_html:
                    return  # 抓取失败，放弃清洗

            # 步骤2：如果已抓取但未清洗，执行清洗
            if article.original_html and article.clean_status != "success":
                self.service.clean_article_content(self.article_id)

    worker = _ArticleProcessor(self.article_service, article_id)
    QThreadPool.globalInstance().start(worker)
```

### 完整修改示例

```python
# 在 _show_article 方法之前添加
def _ensure_article_processed(self, article_id: str) -> None:
    from PySide6.QtCore import QRunnable, QThreadPool

    class _ArticleProcessor(QRunnable):
        def __init__(self, service, article_id):
            super().__init__()
            self.service = service
            self.article_id = article_id

        def run(self):
            article = self.service.get_article(self.article_id)
            if article is None:
                return

            if not article.original_html:
                self.service.fetch_article_content(self.article_id)
                article = self.service.get_article(self.article_id)
                if article is None or not article.original_html:
                    return

            if article.original_html and article.clean_status != "success":
                self.service.clean_article_content(self.article_id)

    worker = _ArticleProcessor(self.article_service, article_id)
    QThreadPool.globalInstance().start(worker)


def _show_article(self, article_id: str) -> None:
    article = self.article_service.get_article(article_id)

    if article is None:
        self.article_reader.show_welcome()
        self.summary_panel.clear_article()
        self.translation_panel.clear_article()
        return

    # 新增：自动触发抓取和清洗
    self._ensure_article_processed(article_id)

    document = ReaderDocument.from_article(article)
    self.article_reader.show_article(article, document)
    # ... 后续代码不变
```

## 验证方法

### 步骤1：运行应用

```bash
uv run python main.py
```

### 步骤2：导入测试 Feed

添加一个 Feed（如 https://example.com/feed）。

### 步骤3：点击文章并切换视图

1. 点击一篇文章
2. 等待几秒（后台抓取和清洗）
3. 切换到 Cleaned HTML 视图
4. 切换到 Markdown 视图

### 预期结果

- 首次切换可能仍显示"暂不可用"（因为后台任务还在执行）
- 等待几秒后再次切换，应该能看到 Cleaned HTML 和 Markdown 内容
- 刷新文章列表或重新打开文章后，应该立即显示处理后的内容

## 可选优化（后续迭代）

### 优化1：添加状态提示

在 Reader 区域添加"正在抓取..."、"正在清洗..."的状态提示。

### 优化2：处理完成后刷新视图

在后台任务完成后，通过信号通知前端刷新当前文章视图。

### 优化3：批量处理

在导入 OPML 后，批量触发所有文章的抓取和清洗。

## 关键注意事项

1. **异步执行**：必须使用 `QRunnable` 在后台线程执行，避免阻塞 UI。
2. **错误处理**：抓取或清洗失败时不影响主流程，保留原文显示。
3. **幂等性**：`fetch_article_content()` 和 `clean_article_content()` 已实现防重复，无需额外判断。
4. **数据库更新**：后台任务修改数据库后，下次调用 `get_article()` 会返回最新数据。
