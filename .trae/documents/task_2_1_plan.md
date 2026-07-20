# Task 2.1 抓取文章实现计划

## 1. 需求分析

### 1.1 任务目标
根据 plan.md 中 Task 2.1.1 的要求，实现文章正文抓取功能：
- 根据文章链接抓取网页正文
- 保存原始 HTML
- 处理超时、编码、网络失败
- 抓取失败不影响 Feed 中已有摘要阅读

### 1.2 现有架构分析

**当前模型** (`src/mercury/models/article.py`)：
- `Article` 只有 `content_html` 字段，没有存储原始抓取内容的字段

**当前数据库** (`core/database.py`)：
- `articles` 表只有 `title`, `link`, `description`, `published`
- 缺少存储抓取 HTML 的字段

**当前服务** (`src/mercury/services/`)：
- `BackendArticleService` 只返回 Feed 中的摘要，没有抓取功能

## 2. 实现方案

### 2.1 模块设计

| 文件 | 职责 | 变更类型 |
|------|------|----------|
| `src/mercury/models/article.py` | 增强 Article 模型，添加原始 HTML 相关字段 | 修改 |
| `core/database.py` | 扩展 articles 表，添加 original_html 和 fetched_at 字段 | 修改 |
| `src/mercury/services/article_fetcher.py` | 新增文章抓取服务，处理 HTTP 请求和错误 | 新建 |
| `src/mercury/services/backend_article_service.py` | 集成抓取功能，提供服务调用接口 | 修改 |
| `tests/test_article_fetcher.py` | 文章抓取功能测试，使用本地 fixture | 新建 |
| `tests/fixtures/html/` | 测试用 HTML 示例文件 | 新建 |

### 2.2 数据模型增强

```python
# Article 模型新增字段：
- original_html: str       # 抓取的原始网页 HTML
- fetched_at: str | None   # 抓取时间
- fetch_status: str        # 抓取状态: 'pending' | 'success' | 'failed'
- fetch_error: str | None  # 抓取错误信息
```

### 2.3 数据库扩展

```sql
ALTER TABLE articles ADD COLUMN original_html TEXT;
ALTER TABLE articles ADD COLUMN fetched_at TEXT;
ALTER TABLE articles ADD COLUMN fetch_status TEXT DEFAULT 'pending';
ALTER TABLE articles ADD COLUMN fetch_error TEXT;
```

### 2.4 抓取服务设计

**`ArticleFetcher` 类职责**：
- 根据 URL 抓取网页内容
- 处理 HTTP 超时（默认 15 秒）
- 处理编码问题（自动检测 UTF-8/GBK 等）
- 处理网络失败、4xx/5xx 错误
- 返回结构化结果（成功/失败、内容、错误信息）

## 3. 实施步骤

### 步骤 1：增强 Article 模型
- 在 `src/mercury/models/article.py` 中为 `Article` 添加新字段

### 步骤 2：扩展数据库表结构
- 在 `core/database.py` 中添加 `original_html`、`fetched_at`、`fetch_status`、`fetch_error` 字段
- 添加文章抓取相关的数据库操作方法

### 步骤 3：创建文章抓取服务
- 创建 `src/mercury/services/article_fetcher.py`
- 实现 `ArticleFetcher` 类，包含抓取逻辑和错误处理

### 步骤 4：更新后端服务集成
- 修改 `src/mercury/services/backend_article_service.py`
- 添加 `fetch_article_content()` 方法，提供服务调用接口

### 步骤 5：创建测试和 Fixture
- 创建 `tests/fixtures/html/` 目录
- 添加测试用 HTML 示例文件
- 创建 `tests/test_article_fetcher.py` 测试抓取功能

## 4. 关键设计决策

### 4.1 抓取触发时机
- 服务层触发抓取
- 抓取完成后更新本地缓存
- 下次获取同一文章时优先使用缓存

### 4.2 错误处理策略
- 网络超时：返回超时错误，保留 Feed 摘要
- 404/500 错误：返回 HTTP 错误信息，保留 Feed 摘要
- 编码错误：尝试多种编码解码，失败则返回错误
- 所有失败情况都不影响 Feed 中已有内容的获取

### 4.3 防重复抓取
- 已抓取成功的文章（`fetch_status='success'`）不再重复抓取
- 可通过参数触发重新抓取

### 4.4 跨平台兼容性
- 文件读写统一使用 UTF-8
- 不依赖平台特定的 HTTP 实现

## 5. 验证标准

### 5.1 自动测试
- `uv run pytest tests/test_article_fetcher.py` 通过
- 模拟抓取成功、404、超时、编码异常的测试用例

### 5.2 功能验证
- 抓取成功时，数据库中存储完整原始 HTML
- 抓取失败时，保留 Feed 摘要作为 fallback
- 错误信息可被上层服务理解

## 6. 依赖与风险

### 6.1 依赖
- `requests`：已在项目依赖中（`pyproject.toml`）

### 6.2 风险
- 部分网站反爬机制可能导致抓取失败 → 解决方案：设置合理的 User-Agent，添加超时
- 大型网页可能导致内存占用过高 → 解决方案：限制响应大小，截断超大内容