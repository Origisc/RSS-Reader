# 修复翻译段落完成后页面跳转到开头的问题

## 问题分析

翻译功能在每翻译完一个段落后，会刷新整个文章内容的 HTML，导致 `QTextBrowser.setHtml()` 重置滚动位置到页面顶部，打断用户阅读体验。

**调用链：**
```
_TranslationWorker._emit_progress()
  → TranslationPanel._handle_progress()
    → MainWindow._show_translation_progress()
      → ArticleReader.set_translation_result()
        → ArticleReader._render_current_view()
          → ArticleReader._show_bilingual_result()
            → ArticleReader._show_bilingual_html()
              → QTextBrowser.setHtml()  ← 滚动位置丢失
```

## 修复方案

在 `ArticleReader` 中添加滚动位置保存和恢复机制：

### 1. 修改 `_show_bilingual_html()` 方法
在设置 HTML 内容之前保存当前滚动位置，设置完成后恢复滚动位置。

### 2. 修改 `_show_html()` 方法
同样添加滚动位置保存和恢复机制，确保其他视图切换时也不会丢失滚动位置。

### 3. 修改 `_apply_image_replacements()` 方法
图片下载完成后应用替换时也会调用 `setHtml()`，需要同样处理。

## 修改文件

| 文件 | 修改内容 |
|------|---------|
| `src/mercury/ui/article_reader.py` | 在多个方法中添加滚动位置保存/恢复逻辑 |

## 技术实现

使用 `QTextBrowser.verticalScrollBar()` 获取滚动条，通过 `value()` 和 `setValue()` 方法保存和恢复滚动位置。

```python
# 保存滚动位置
scroll_pos = self.content.verticalScrollBar().value()

# 设置 HTML 内容
self.content.setHtml(html)

# 恢复滚动位置
self.content.verticalScrollBar().setValue(scroll_pos)
```

## 风险评估

- **低风险**：只是添加滚动位置保存和恢复逻辑，不会影响翻译功能的核心逻辑
- **兼容性**：使用 Qt 标准 API，跨平台兼容
- **性能**：滚动位置保存和恢复操作非常快速，不会造成性能问题

## 验证步骤

1. 打开一篇英文文章
2. 开启双语视图
3. 点击翻译按钮开始翻译
4. 滚动到文章中间位置等待翻译
5. 观察每翻译完一个段落时，页面是否保持在当前滚动位置，不再跳转到开头