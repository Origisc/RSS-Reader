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
uv run python main.py
```

不要运行 `uv init`，也不需要逐个安装 PySide6、feedparser 或 requests；
`uv sync --locked` 会按照仓库中的 `uv.lock` 创建一致的环境。

### Windows

在 VS Code 中打开整个 `RSS-Reader` 文件夹，然后选择“终端 → 新建终端”并执行
上面的三条命令。不要直接使用系统中旧版本的 `python main.py`。

### macOS / Linux

在 Terminal 中进入仓库目录，再执行上面的三条命令。macOS 首次打开下载的
未签名测试构建时，可能需要在“系统设置 → 隐私与安全性”中确认打开。

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
