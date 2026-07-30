# 修复 Markdown 视图渲染异常问题

## 问题分析

### 现象（截图）
1. 长 URL 逐字符竖排显示（如 `https://www.lukesavage.com/p/the-enshittification-of-life-the-` 被拆成单行一个字符）
2. 列表项文本也出现逐字符竖排（如 "Cory Doctorow" 每个字符一行）
3. 列表缩进异常

### 根因
Markdown 视图的渲染管线为：
```
cleaned_markdown → QTextDocument.setMarkdown() → HTML → QTextBrowser 显示
```

**核心问题**：`QTextDocument.setMarkdown()` 是 Qt 内置的 Markdown 渲染器，存在以下已知限制：
1. 对**长内联链接**（`[text](very-long-url)`）处理不当——当 URL 长度超过可用宽度时，Qt 渲染器无法将其作为整体超链接渲染，退化为逐字符渲染
2. 对**嵌套列表缩进**支持不完善
3. 其生成的 HTML 结构不稳定，与我们在 `_wrap_html()` 中定制的 CSS 配合不顺畅

### 涉及的文件
- `src/mercury/ui/article_reader.py` — `_markdown_fragment()` 静态方法（第 809-836 行），当前使用 `QTextDocument.setMarkdown()` 做 Markdown→HTML 转换
- `src/mercury/services/markdown_converter.py` — Markdown 生成器，需确保生成的 Markdown 格式简单规范
- `tests/test_article_reader.py` — 需更新 Markdown 视图相关测试
- `tests/test_markdown_converter.py` — Markdown 转换器测试

---

## 修复方案

### 策略：替换 `QTextDocument.setMarkdown()` 为轻量级自写 Markdown→HTML 转换器

**理由**：
- 我们的 `MarkdownConverter` 只生成有限的 Markdown 子集（标题、段落、列表、链接、图片、代码块、表格、引用、加粗/斜体）
- 针对这个子集自写转换器完全可行，且能精确控制输出 HTML 结构
- 零新增依赖（仅使用 Python stdlib 的 `re` 模块）
- 输出的 HTML 结构可控，能与 `_wrap_html()` 中的自定义 CSS 完美配合

### 步骤 1：在 `markdown_converter.py` 中添加 Markdown→HTML 渲染器

在 `markdown_converter.py` 中新增 `MarkdownRenderer` 类，负责将 Markdown 文本转为结构化 HTML：

**支持的 Markdown 语法**（与 `MarkdownConverter` 生成的子集一致）：
- 标题：`#` ~ `######`
- 段落：空行分隔的普通文本
- 行内格式：`**粗体**`、`*斜体*`、`` `代码` ``、`[文本](链接)`、`![alt](图片)`
- 列表：`- ` / `* `（无序）、`1. `（有序），支持嵌套缩进
- 代码块：```` ``` ````
- 引用：`> `
- 表格：`| col1 | col2 |` 格式
- 水平线：`---`
- 换行：`  ` 或 `\n`

**关键设计要点**：
- 链接渲染为 `<a href="...">文本</a>`，URL 保持完整，通过 CSS `word-break: break-all` 允许换行
- 列表使用 `<ul>/<ol>/<li>` + `style` 属性精确控制缩进
- 代码块使用 `<pre><code>` 结构
- 输出纯净 HTML，不依赖 Qt 的 Markdown 渲染能力

### 步骤 2：修改 `article_reader.py` 的 `_markdown_fragment()` 方法

将当前实现：
```python
document = QTextDocument()
document.setMarkdown(markdown, QTextDocument.MarkdownFeature.MarkdownDialectGitHub)
full_html = document.toHtml()
# ... 提取 body ...
```

替换为：
```python
from mercury.services.markdown_converter import MarkdownRenderer
renderer = MarkdownRenderer()
html = renderer.render(markdown)
# 直接返回完整 HTML body，不再需要从 QTextDocument 提取
```

同时保留现有的段落间距恢复逻辑（`_MARKDOWN_PARAGRAPH_STYLE_PATTERN` 处理）。

### 步骤 3：添加列表样式 CSS

在 `_wrap_html()` 的 CSS 中为 Markdown 渲染生成的列表添加样式：
```css
.reader-article ul, .reader-article ol {
    margin: 0 0 {paragraph_spacing}px;
    padding-left: 2em;
}
.reader-article li {
    margin: 0.3em 0;
}
```

### 步骤 4：更新测试

更新 `tests/test_article_reader.py` 中与 Markdown 视图相关的测试：
- `test_markdown_view_uses_dark_reader_text_color` — 验证新渲染器输出的 HTML 包含正确的标签
- `test_markdown_view_preserves_structural_formatting` — 验证标题、列表等结构
- `test_markdown_paragraph_gap_exceeds_intra_paragraph_line_height` — 验证段落间距
- 添加新测试：长 URL 链接渲染正确（不逐字符分解）
- 添加新测试：嵌套列表缩进正确

在 `tests/test_markdown_converter.py` 中添加 `MarkdownRenderer` 的单元测试。

---

## 风险评估

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 自写渲染器可能遗漏某些 Markdown 边界情况 | Markdown 视图显示异常 | 严格限定支持的语法子集与 MarkdownConverter 输出一致；添加充分的单元测试 |
| 新渲染器与旧 QTextDocument 输出结构不同 | 现有测试可能失败 | 更新测试断言以匹配新输出结构 |
| 列表样式与 Cleaned HTML 视图不一致 | UI 视觉差异 | 在 CSS 中使用与 Cleaned HTML 一致的间距参数 |

## 不采用的方案

- **添加第三方 Markdown 库**（如 `markdown-it-py`）：违反"避免新增重型依赖"原则
- **仅修复 MarkdownConverter 输出**：治标不治本，Qt 渲染器对长 URL 的处理缺陷无法通过调整输入完全规避
- **对 Markdown 视图直接显示 Cleaned HTML**：丧失了 Markdown 视图的独立价值
