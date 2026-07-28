# Mercury 开发环境搭建（Windows）

本文档用于从零开始搭建 Mercury 项目的开发环境。项目已经包含完整的
`pyproject.toml` 和 `uv.lock`，不要重新初始化项目或逐个添加依赖。

---

# 1. 克隆项目

```bash
git clone https://github.com/Origisc/RSS-Reader.git
```

或者使用 VS Code：

```
Ctrl + Shift + P
Git: Clone
```

克隆完成后，使用 **Open Folder** 打开整个项目目录。

例如：

```
RSS-Reader/
├── AGENTS.md
├── INITIAL.md
├── README.md
└── ...
```

---

# 2. 安装 Python

项目要求：

- Python 3.13

检查当前 Python：

```powershell
python --version
```

检查系统安装了哪些 Python：

```powershell
py -0p
```

确认能够看到：

```
Python 3.13
```

---

# 3. 安装 uv

安装：

```powershell
py -3.13 -m pip install uv
```

检查版本：

```powershell
uv --version
```

例如：

```
uv 0.11.x
```

---

# 4. 同步锁定环境

进入项目目录：

```powershell
cd RSS-Reader
```

在仓库根目录同步 Python 与依赖：

```powershell
uv python install 3.13
uv sync --locked
```

`uv sync --locked` 会根据仓库已有的锁文件创建 `.venv`。不要执行 `uv init`，
否则会改写已经存在的项目配置。

---

# 5. 创建虚拟环境

第 4 步完成后，项目目录会自动出现：

```
.venv/
```

---

# 6. 选择 Python 解释器

VS Code：

```
Ctrl + Shift + P
```

输入：

```
Python: Select Interpreter
```

选择：

```
RSS-Reader (.venv)
```

或者

```
.venv\Scripts\python.exe
```

确认：

```powershell
python --version
```

输出：

```
Python 3.13.x
```

---

# 7. 检查已锁定依赖

检查 PySide6 是否可导入：

```powershell
uv run python -c "import PySide6; print(PySide6.__version__)"
```

不要执行 `uv add pyside6`；PySide6、feedparser 和 requests 已由
`uv sync --locked` 安装。

---

# 8. 创建项目目录

推荐目录结构：

```
RSS-Reader
│
├── src
│   └── mercury
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── ui
│       ├── ai
│       ├── services
│       ├── models
│       └── i18n
│
├── tests
│
├── AGENTS.md
├── INITIAL.md
├── README.md
├── plan.md
├── pyproject.toml
└── uv.lock
```

> 根目录中的 `main.py` 是稳定启动入口，会转发到 `src/mercury/main.py`。

---

# 9. 创建第一个 PySide6 程序

文件：

```
src/mercury/main.py
```

代码：

```python
import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


def main() -> int:
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Mercury")
    window.resize(900, 600)

    label = QLabel("Hello Mercury!")
    label.setStyleSheet("font-size: 28px;")
    window.setCentralWidget(label)

    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

---

# 10. 运行程序

```powershell
uv run python main.py
```

运行成功后，应弹出窗口：

```
Mercury
------------------
Hello Mercury!
```

关闭窗口后终端恢复。

---

# 当前开发成果

已完成：

- GitHub 项目克隆
- Python 3.13
- uv 锁定环境
- Python 3.13
- 自动创建的 `.venv`
- 锁定版本的 PySide6、feedparser 和 requests
- 项目基础目录
- 第一个 PySide6 窗口

环境已经准备完成，可以开始 Mercury 项目的正式开发。
