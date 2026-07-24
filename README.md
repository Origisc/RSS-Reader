# RSS-Reader

## Run from source

From the repository root:

```powershell
uv run python main.py
```

When using an existing virtual environment directly:

```powershell
.\.venv\Scripts\python.exe main.py
```

Restart the process after changing application composition or Provider wiring;
an already-open PySide6 window does not hot-reload Python code.
