# Markdown 渲染验证

## 验证范围

Markdown 阅读视图需要在“HTML 转换为 Markdown”和“Markdown 渲染到 Reader”两层保留以下结构：

- 标题层级
- 有序列表、无序列表及嵌套层级
- 粗体与斜体
- 行内代码与围栏代码块
- 表格及表格单元格内的强调、代码和链接

Reader 使用 Qt 的 GitHub Markdown 方言解析内容。自动化测试不仅检查文本是否存在，还检查最终 `QTextDocument` 的标题层级、列表对象、粗体字重、斜体属性和等宽代码字体。

## 自动验证

```powershell
uv run python -m unittest tests.test_markdown_converter tests.test_article_reader -v
```

完整回归：

```powershell
uv run python -m unittest discover -s tests -v
```

## 手动验证

1. 打开同时包含标题、嵌套列表、粗体、斜体、行内代码和代码块的文章。
2. 切换到“Markdown”视图。
3. 确认列表符号和缩进可见，粗体与斜体样式正确，代码使用等宽字体且代码块保持独立区域。
4. 若文章包含表格，确认表格单元格中的强调、代码和链接仍能正常显示。
