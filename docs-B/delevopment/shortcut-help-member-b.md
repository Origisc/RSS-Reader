# 快捷键帮助入口（成员 B）

## 目标

在主窗口顶部工具栏增加“快捷键 / Shortcuts”按钮，让用户无需查阅外部文档即可查看当前页面所有键盘快捷键及其功能。

## 实现

- 顶部主工具栏和“帮助”菜单复用同一个 QAction；`F1` 可直接打开说明。
- 弹窗自动扫描主窗口下所有设置了快捷键的 QAction，读取实际快捷键文本，并优先使用本地化 `statusTip` 说明功能；未设置说明时使用 QAction 名称。
- 当前列出 `F1`、`Ctrl+,`、`Ctrl+Shift+S`、`Ctrl+Q`。
- 弹窗使用独立深浅主题表格颜色，语言切换后重新打开即可显示当前语言。

## 后续约束

以后每次新增 QAction 快捷键，都必须设置可翻译的功能说明。自动扫描会把新快捷键加入弹窗，`test_new_action_shortcut_is_discovered_automatically` 用于防止该约束失效。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_shortcut_help tests.test_i18n
```

人工验证：启动 Mercury，点击最上方“快捷键”按钮，确认弹窗列出四项快捷键；切换中英文界面后重新打开，确认标题、表头、功能说明和关闭按钮同步切换。
