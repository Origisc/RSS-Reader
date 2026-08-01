# Mercury RSS Reader

Mercury 是一个本地优先、跨平台的 RSS 阅读器。订阅源、文章缓存、阅读状态、
标签和 AI 配置默认只保存在本机；只有刷新 Feed 或用户主动调用已配置的
LLM Provider 时才会发起相应网络请求。

## 最简单的使用方式

如果只想使用软件，请打开仓库右侧的 **Releases**，下载与你的系统对应的文件：

- Windows：`Mercury-Windows-x64.exe`
- macOS：`Mercury-macOS.dmg`
- Linux：`Mercury-Linux-x64`

GitHub 页面中的 **Code → Download ZIP** 下载的是源代码，不是已经安装好依赖的
应用程序。源码 ZIP 不能像 `.exe` 或 `.app` 一样直接双击运行。

如果 Releases 暂时没有文件，仓库维护者需要先在 GitHub Actions 中手动运行
`Cross-Platform Build and Release`，或者推送一个 `v` 开头的版本标签。

## 从源代码运行

要求：

- Windows、macOS 或 Linux
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.13（uv 可以自动安装）

在仓库根目录执行：

```bash
uv python install 3.13
uv sync --locked
uv run mercury
```

不要运行 `uv init`，也不需要逐个安装 PySide6、feedparser 或 requests；
`uv sync --locked` 会按照仓库中的 `uv.lock` 创建一致的环境。

### Windows

在 VS Code 中打开整个 `RSS-Reader` 文件夹，然后选择“终端 → 新建终端”并执行
上面的三条命令。不要直接使用系统中旧版本的 `python main.py`。

### macOS / Linux

在 Terminal 中进入仓库目录，再执行上面的三条命令。macOS 首次打开下载的
未签名测试构建时，可能需要在“系统设置 → 隐私与安全性”中确认打开。

## 第一次启动

Mercury 不需要注册、登录或配置 AI。启动后可以直接：

1. 点击订阅源区域的 `+`，添加 HTTP/HTTPS Feed URL 或本地 RSS/Atom 文件。
2. 通过导入功能选择 OPML 文件；OPML 内的相对 Feed 路径会相对于 OPML 所在目录解析。
3. 刷新订阅源，选择文章并在原始内容、Cleaned HTML 和 Markdown 视图之间切换。
4. 使用星标和手动标签整理文章；这些功能不依赖 AI。

无法导入 Feed/OPML 时，界面会区分文件不存在、目录、编码、格式、网络和 HTTP 错误，并显示实际解析后的本地路径。

## 可选 AI 配置

摘要、翻译和 Tag Agent 都是可选功能，未配置时不会影响 Feed、文章列表或 Reader。每个 Agent 可以使用独立配置。

选择“自定义（OpenAI 兼容）”后，Base URL 和模型字段为空，由用户自行填写，不会自动带入千问或其他预设模型。Mercury 会在 Base URL 后自动追加 `/chat/completions`。

常用配置方式：

| 服务 | Base URL | 模型 | API Key |
| --- | --- | --- | --- |
| OpenAI API | `https://api.openai.com/v1` | 填写你的 API 账户可用模型 ID | OpenAI API Key |
| Google Gemini API | `https://generativelanguage.googleapis.com/v1beta/openai/` | 填写你的 Gemini API 账户可用模型 ID | Gemini API Key |
| 其他兼容服务 | 服务商给出的 OpenAI-compatible 根地址 | 服务商提供的模型 ID | 按服务商要求 |

点击“测试连接”后再保存。失败信息会明确区分：

- Base URL 或模型不受支持；
- API Key 缺失、无效或过期；
- 权限、账单、额度或限流问题；
- 404 路径/模型错误；
- 网络、DNS、VPN/代理、TLS 或超时；
- 返回内容不是兼容的 Chat Completions 格式。

模型名称和可用范围会随 API 账户及服务商更新，请以 [OpenAI 模型列表](https://platform.openai.com/docs/models) 和 [Gemini OpenAI compatibility 文档](https://ai.google.dev/gemini-api/docs/openai)为准。不要把 API Key 写入仓库、截图或提交记录。

## 本地数据位置

Mercury 会把 `database.db` 放在当前用户可写的数据目录，而不是启动时碰巧所在的
工作目录：

- Windows：`%LOCALAPPDATA%\Mercury\database.db`
- macOS：`~/Library/Application Support/Mercury/database.db`
- Linux：`${XDG_DATA_HOME:-~/.local/share}/Mercury/database.db`

如果项目根目录存在旧版 `database.db`，首次启动会将它复制到新位置；已有目标
数据库不会被覆盖。需要便携或测试目录时，可设置 `MERCURY_DATA_DIR`。

## 验证

测试不调用真实 LLM、不需要 API Key，也不依赖不稳定网络：

```bash
uv run pytest -q
```

## 创建可下载版本

在 GitHub 仓库的 **Actions** 页面选择
`Cross-Platform Build and Release` 并点击 **Run workflow**，可以验证三个平台并
生成临时下载产物。正式发布时推送版本标签：

```bash
git tag v0.1.0
git push origin v0.1.0
```

工作流会使用 Python 3.13、锁定依赖和 PyInstaller 分别构建 Windows、macOS 和
Linux 版本，并把它们附加到对应的 GitHub Release。
