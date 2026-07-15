# Stage 2 - Member B Development Log

## Overview

本阶段完成了 Mercury UI 原型的工程化重构。

目标是在保持现有界面功能不变的前提下，将界面、数据模型和数据服务进行解耦，为后续接入真实 Feed 数据、数据库以及 AI 功能做好准备。

本阶段仍然使用 Mock 数据，不依赖成员 A 的业务逻辑。

---

# Objectives

- UI 组件化
- 建立数据模型（Model）
- 建立数据服务接口（Service）
- 使用 Mock Service 驱动界面
- 降低 UI 与数据层的耦合

---

# Completed Features

## 1. UI 组件拆分

原有 MainWindow 中的所有 UI 逻辑被拆分为独立组件。

```
src/mercury/ui/
├── main_window.py
├── sidebar.py
├── article_list.py
└── article_reader.py
```

各组件职责如下：

| 组件 | 职责 |
|------|------|
| MainWindow | 主窗口与组件组合 |
| Sidebar | 显示订阅源 |
| ArticleList | 显示文章列表 |
| ArticleReader | 显示文章正文 |

实现了 UI 组件职责单一，降低后续维护成本。

---

## 2. 建立数据模型

新增：

```
src/mercury/models/
```

包括：

```
Feed
Article
```

所有界面数据均通过数据模型传递，而不是直接使用字符串。

---

## 3. 建立 Service 层

新增：

```
src/mercury/services/
```

包括：

```
ArticleService
MockArticleService
```

其中：

ArticleService 定义统一的数据接口。

MockArticleService 提供用于开发阶段的模拟数据。

MainWindow 不再直接维护文章数据。

---

## 4. UI 与数据解耦

重构前：

```
MainWindow

├── 保存 Feed 数据
├── 保存 Article 数据
└── 控制所有界面
```

重构后：

```
MainWindow
      │
      ▼
ArticleService
      │
      ▼
MockArticleService
```

UI 不关心数据来源。

未来可直接替换为：

- SQLite Service
- Feed Service
- API Service

无需修改界面代码。

---

## 5. Mock 数据驱动

当前所有数据均来自：

```
MockArticleService
```

包括：

Feed：

- OpenAI Blog
- Python Weekly
- Hacker News

Article：

- Mercury 项目启动
- PySide6 三栏布局
- 如何设计本地优先应用

---

## 6. 信号与组件通信

组件之间不再直接互相访问。

采用 Qt Signal：

```
Sidebar
    │
feed_selected
    ▼

MainWindow
    │
    ▼

ArticleList
    │
article_selected
    ▼

ArticleReader
```

MainWindow 负责协调各组件通信。

---

# Verification

本阶段可独立验证：

- 程序可正常启动
- 三栏布局正常显示
- Sidebar 正常显示 Feed
- ArticleList 正常显示文章
- 点击 Feed 可切换文章列表
- 点击文章可更新阅读区
- UI 与 Mock 数据成功解耦
- 不依赖数据库
- 不依赖网络
- 不依赖成员 A

---

# Architecture

当前 UI 架构：

```
MainWindow
│
├── Sidebar
├── ArticleList
└── ArticleReader
        │
        ▼
ArticleService
        │
        ▼
MockArticleService
```

---

# Current Limitations

当前仍未接入：

- SQLite
- Feed Parser
- HTML Cleaner
- Summary Agent
- Translation Agent
- LLM Provider

所有数据仍为 Mock 数据。

---

# Next Stage

下一阶段计划：

- 添加菜单栏（Menu Bar）
- 添加工具栏（Tool Bar）
- 创建设置窗口（Settings）
- 支持主题切换
- 支持多语言（i18n）
- 预留 AI 面板入口

---

# Git Commit

```
refactor(ui): connect components through mock article service
```
