# Stage 3 - Member B Development Log

## Overview

本阶段继续沿用 Mock Service，不接入真实 Feed、数据库或 LLM 服务。

目标是在现有三栏阅读器基础上补齐成员 B 下一步 UI 骨架：菜单栏、工具栏、设置窗口、运行时语言切换、主题切换，以及 AI 面板入口。

---

## Completed Features

### 1. Runtime i18n

新增：

```text
src/mercury/i18n/
```

当前支持：

- 简体中文
- English
- 缺失翻译 fallback
- 无需重启即可刷新主窗口、菜单、工具栏、列表标题、阅读区欢迎文案和 AI 面板文案

### 2. Settings Dialog

设置窗口现在可以选择：

- 界面语言
- 界面主题

点击确定后即时应用，不需要重启应用。

### 3. Theme Switching

新增：

```text
src/mercury/ui/theme.py
```

当前支持：

- 跟随系统
- 浅色
- 深色

设置暂时保存在运行时内存中，等待成员 A 的配置/存储接口稳定后再接入本地持久化。

### 4. Menu Bar and Tool Bar

主窗口已提供：

- 添加 Feed 入口
- 刷新入口
- 首选项入口
- AI 面板入口
- 关于窗口
- 退出入口

添加 Feed 与刷新目前只显示“入口已预留”提示，避免 UI 层绕过 service 直接处理网络或数据库逻辑。

### 5. AI Panel Entry

AI 面板入口已预留，并明确提示后续摘要/翻译必须通过可配置 LLM Provider，且用户主动配置和触发前不会发送文章内容。

---

## Verification

自动验证：

```powershell
uv run python -m unittest tests.test_i18n
```

人工验证：

1. 运行 `uv run python src/mercury/main.py`。
2. 打开“设置 / 首选项”。
3. 切换 English，确认菜单、工具栏、列表标题、阅读区欢迎文案更新。
4. 切换深色主题，确认窗口样式更新。
5. 打开 View / AI Panel，确认 AI 面板出现且文案说明未配置前不会发送文章内容。
6. 点击 Add Feed / Refresh，确认只是显示预留入口提示，没有直接发起网络请求。

---

## Notes

- 本阶段仍不依赖数据库、网络或真实 LLM。
- UI 仍只通过 Mock Service 获取文章数据。
- 设置持久化等待后续配置存储接口，不在本阶段硬写本地文件。
