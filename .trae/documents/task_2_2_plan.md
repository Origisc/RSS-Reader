# Task 2.2 Reader 清洗与转换实现计划

## 1. 需求分析

### 1.1 任务目标
根据 plan.md 中 Task 2.2 的要求，实现 Reader 清洗与转换功能：

**Task 2.2.1 生成 Cleaned HTML**：
- 从原始 HTML 中提取适合阅读的正文结构
- 清理脚本、广告、导航等无关内容
- 保留标题层级、链接、图片、列表、表格、代码块
- 清洗失败时返回 fallback

**Task 2.2.2 生成 Cleaned Markdown**：
- 将 Cleaned HTML 转换为可导出、可阅读的 Markdown
- 转换标题、段落、链接、图片、列表、表格、代码块
- 保留基础语义结构

### 1.2 现有架构分析

**当前模型** (`src/mercury/models/article.py`)：
- `Article` 已有 `original_html` 字段存储抓取的原始 HTML
- 缺少存储清洗后内容的字段

**当前数据库** (`core/database.py`)：
- `articles` 表已有 `original_html`、`fetched_at`、`fetch_status`、`fetch_error`
- 缺少存储清洗后内容的字段

**当前服务** (`src/mercury/services/`)：
- `BackendArticleService` 已有文章抓取功能
- 缺少清洗和转换功能

## 2. 实现方案

### 2.1 模块设计

| 文件 | 职责 | 变更类型 |
|------|------|----------|
| `src/mercury/models/article.py` | 增强 Article 模型，添加清洗相关字段 | 修改 |
| `core/database.py` | 扩展 articles 表，添加清洗后内容字段 | 修改 |
| `src/mercury/services/reader_cleaner.py` | 新增 Reader 清洗服务，提取正文结构 | 新建 |
| `src/mercury/services/markdown_converter.py` | 新增 Markdown 转换服务 | 新建 |
| `src/mercury/services/backend_article_service.py` | 集成清洗和转换功能，提供服务调用接口 | 修改 |
| `tests/test_reader_cleaner.py` | Reader 清洗功能测试，使用本地 fixture | 新建 |
| `tests/test_markdown_converter.py` | Markdown 转换功能测试 | 新建 |

### 2.2 数据模型增强

```python
# Article 模型新增字段：
- cleaned_html: str       # 清洗后的 HTML
- cleaned_markdown: str   # 转换后的 Markdown
- cleaned_at: str | None  # 清洗时间
- clean_status: str       # 清洗状态: 'pending' | 'success' | 'failed'
- clean_error: str | None # 清洗错误信息
```

### 2.3 数据库扩展

```sql
ALTER TABLE articles ADD COLUMN cleaned_html TEXT;
ALTER TABLE articles ADD COLUMN cleaned_markdown TEXT;
ALTER TABLE articles ADD COLUMN cleaned_at TEXT;
ALTER TABLE articles ADD COLUMN clean_status TEXT DEFAULT 'pending';
ALTER TABLE articles ADD COLUMN clean_error TEXT;
```

### 2.4 清洗服务设计

**`ReaderCleaner` 类职责**：
- 接收原始 HTML 输入
- 使用正则表达式或解析器清理无关内容（脚本、样式、导航、广告）
- 提取文章正文：标题、段落、链接、图片、列表、表格、代码块
- 返回结构化结果（成功/失败、清洗后内容、错误信息）

### 2.5 Markdown 转换服务设计

**`MarkdownConverter` 类职责**：
- 接收 Cleaned HTML 输入
- 转换为 Markdown 格式
- 支持标题、段落、链接、图片、列表、表格、代码块转换
- 返回结构化结果（成功/失败、转换后内容、错误信息）

## 3. 实施步骤

### 步骤 1：增强 Article 模型
- 在 `src/mercury/models/article.py` 中为 `Article` 添加清洗相关字段

### 步骤 2：扩展数据库表结构
- 在 `core/database.py` 中添加 `cleaned_html`、`cleaned_markdown`、`cleaned_at`、`clean_status`、`clean_error` 字段
- 添加文章清洗相关的数据库操作方法

### 步骤 3：创建 Reader 清洗服务
- 创建 `src/mercury/services/reader_cleaner.py`
- 实现 `ReaderCleaner` 类，包含清洗逻辑和错误处理

### 步骤 4：创建 Markdown 转换服务
- 创建 `src/mercury/services/markdown_converter.py`
- 实现 `MarkdownConverter` 类，包含转换逻辑和错误处理

### 步骤 5：更新后端服务集成
- 修改 `src/mercury/services/backend_article_service.py`
- 添加 `clean_article_content()` 方法，提供清洗服务调用接口
- 添加 `convert_to_markdown()` 方法，提供转换服务调用接口

### 步骤 6：更新数据库查询方法
- 修改 `get_article_full_detail()` 返回清洗相关字段
- 添加 `save_article_cleaned()` 方法保存清洗结果

### 步骤 7：创建测试和 Fixture
- 创建 `tests/test_reader_cleaner.py` 测试清洗功能
- 创建 `tests/test_markdown_converter.py` 测试转换功能

## 4. 关键设计决策

### 4.1 清洗触发时机
- 服务层触发清洗
- 优先使用已抓取的原始 HTML
- 清洗完成后更新本地缓存
- 下次获取同一文章时优先使用缓存

### 4.2 错误处理策略
- 清洗失败：保留原始 HTML 作为 fallback
- 转换失败：保留 Cleaned HTML 作为 fallback
- 所有失败情况都不影响文章阅读

### 4.3 防重复清洗
- 已清洗成功的文章（`clean_status='success'`）不再重复清洗
- 可通过参数触发重新清洗

### 4.4 跨平台兼容性
- 所有文件读写统一使用 UTF-8
- 不依赖平台特定的 HTML 解析实现

### 4.5 内容保留原则
- 不无理由删除关键信息
- 保留标题层级（h1-h6）
- 保留链接、图片、列表、表格、代码块

## 5. 验证标准

### 5.1 自动测试
- `uv run pytest tests/test_reader_cleaner.py` 通过
- `uv run pytest tests/test_markdown_converter.py` 通过
- 模拟清洗成功、清洗失败、转换成功、转换失败的测试用例

### 5.2 功能验证
- 清洗成功时，数据库中存储完整 Cleaned HTML
- 转换成功时，数据库中存储完整 Cleaned Markdown
- 清洗失败时，保留原始 HTML 作为 fallback
- 转换失败时，保留 Cleaned HTML 作为 fallback
- 错误信息可被上层服务理解

## 6. 依赖与风险

### 6.1 依赖
- 考虑添加 `beautifulsoup4` 作为 HTML 解析依赖（轻量级、成熟稳定）

### 6.2 风险
- 复杂网页结构可能导致清洗不完整 → 解决方案：多策略匹配，保留原始内容作为 fallback
- 特殊编码的 HTML 可能导致解析错误 → 解决方案：统一使用 UTF-8 解码
- Markdown 表格转换可能丢失样式 → 解决方案：保留基础表格结构，不追求复杂样式

## 7. 接口设计

### 7.1 ReaderCleaner 接口

```python
class ReaderCleaner:
    def clean(self, html: str) -> CleanResult:
        """清洗 HTML，提取正文结构"""
        ...
```

### 7.2 MarkdownConverter 接口

```python
class MarkdownConverter:
    def convert(self, html: str) -> ConvertResult:
        """将 HTML 转换为 Markdown"""
        ...
```

### 7.3 BackendArticleService 新增接口

```python
def clean_article_content(self, article_id: str, force: bool = False) -> str:
    """清洗文章内容，返回结果说明"""
    ...

def convert_to_markdown(self, article_id: str, force: bool = False) -> str:
    """将文章内容转换为 Markdown，返回结果说明"""
    ...
```
