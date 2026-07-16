# Member B Reader Style Settings

## Goal

继续完成第二阶段中成员 B 负责的阅读样式界面：

- 正文字号。
- 正文行高。
- 正文最大宽度。
- 设置确认后立即应用，不需要重启。

## Boundary

本次只实现 UI、展示模型和可替换的 `ReaderStyleStore` 协议。默认使用 `InMemoryReaderStyleStore`，不读写文件、数据库或网络。

成员 A 提供本地设置 repository 后，可在应用入口注入持久化 adapter；UI 不需要直接操作数据库，也不需要修改现有设置控件。

## Offline Verification

```powershell
uv run python -m unittest tests.test_reader_style tests.test_settings_dialog tests.test_article_reader tests.test_i18n -v
```

测试覆盖：

1. 阅读样式默认值和边界限制。
2. 内存 Mock Store 的读取与保存。
3. 设置窗口正确返回字号、行高和正文宽度。
4. SpinBox 上下按钮可以通过真实鼠标点击调整数值。
5. Reader 应用样式后保持当前文章不变。
6. 新增设置项具有中英文文案。

## Manual Verification

1. 运行 `uv run python src/mercury/main.py`。
2. 打开“设置 / 首选项”。
3. 分别调整正文字号、正文行高和正文宽度。
4. 分别点击三个输入框右侧的上调、下调按钮，确认数值按步长变化。
5. 展开界面语言和界面主题，确认普通选项与选中项均清晰可读。
6. 点击“确定”，确认当前文章立即重新排版。
7. 切换 English，确认三个设置项即时显示英文。

## Current Limitation

样式当前只在本次应用运行期间保留。重启持久化等待成员 A 的设置 repository 接口，不在 UI 中临时写数据库或配置文件。
