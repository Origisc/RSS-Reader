# Stage 1 - Member B Development Log

## Overview

本阶段完成了 Mercury 项目的 UI 原型搭建，目标是在不依赖后端逻辑的情况下，构建一个可独立运行、可验证的桌面阅读器界面。

当前所有数据均为 Mock 数据，不依赖 Feed 解析、数据库或 AI 服务。

---

# Objectives

- 搭建 PySide6 开发环境
- 建立独立的 UI 原型
- 完成 RSS 阅读器三栏布局
- 为后续成员 A 的数据接口预留接入位置

---

# Completed Features

## 1. 开发环境搭建

已完成：

- Python 3.13
- uv 项目初始化
- 虚拟环境（.venv）
- PySide6 安装
- pyproject.toml
- uv.lock

---

## 2. UI 工程结构

建立了独立开发目录：

```
src/
└── mercury/
    ├── __init__.py
    ├── main.py
    └── ui/
        ├── __init__.py
        └── main_window.py
```

该目录作为成员 B 的独立开发环境，不影响现有主工程。

---

## 3. 主窗口

完成：

- Mercury 主窗口
- 默认窗口大小
- 主窗口标题

---

## 4. 三栏布局

完成经典 RSS Reader 布局：

```
+-------------+----------------+--------------------------+
| Feed List   | Article List   | Reader                   |
|             |                |                          |
|             |                |                          |
+-------------+----------------+--------------------------+
```

包含：

- 左侧：订阅源列表
- 中间：文章列表
- 右侧：文章阅读区

---

## 5. Mock 数据

提供用于界面开发的示例数据：

### Feed

- OpenAI Blog
- Python Weekly
- Hacker News

### Articles

- Mercury 项目启动
- PySide6 三栏布局
- 如何设计本地优先应用

---

## 6. 阅读区

实现：

- HTML 内容展示
- 标题显示
- 来源显示
- 正文显示

点击文章后可动态切换阅读内容。

---

# Verification

当前阶段可独立验证：

- 可以启动 Mercury
- 主窗口正常显示
- 三栏布局正常
- Feed 列表正常显示
- Article 列表正常显示
- 点击文章后阅读区更新
- 不依赖数据库
- 不依赖 Feed
- 不依赖 AI
- 不依赖成员 A

---

# Current Limitations

当前仍使用 Mock 数据。

尚未接入：

- Feed Service
- SQLite
- Reader Service
- Summary Agent
- Translation Agent
- LLM Provider

---

# Next Stage

下一阶段计划：

- 拆分 MainWindow
- Sidebar 独立组件
- ArticleList 独立组件
- Reader 独立组件
- 引入 Mock Service
- 为成员 A 的接口预留 Adapter
- 接入真实数据

---

# Git Commit

```
feat(ui): add standalone three-panel prototype
```